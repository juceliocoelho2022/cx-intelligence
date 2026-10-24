"""Private plans: fail-closed OIDC + PostgreSQL row-level tenant isolation.

Integration tests run only against TEST_DATABASE_URL, an isolated test server
(PostgreSQL 16 in CI), using a dedicated non-superuser application role.
"""
from datetime import datetime, timezone
from pathlib import Path
import os
import time

import pytest
from psycopg import connect
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from src.cx_goals import create_action, edit_action
from src.private_plans import (
    PlanConflict, PrivatePlanError, load_private_plan, list_private_plans,
    principal_from_claims, private_storage_enabled, save_private_plan,
)

ISSUER = "https://accounts.example.test"
AUDIENCE = "cx-private-test"
EXP = int(time.time()) + 3600


def principal(sub="user-alpha"):
    return principal_from_claims(
        {"iss": ISSUER, "sub": sub, "aud": AUDIENCE, "exp": EXP},
        issuer=ISSUER, audience=AUDIENCE,
    )


def actions():
    return create_action(
        [], metric="csat_pct", title="Investigar jornada Pix",
        hypothesis="Analisar dificuldades fictícias sem atribuir causas",
        role="CX", due_date="2026-11-07", created_on="2026-10-24",
        period_start="2026-10-06", period_end="2026-10-19",
        topics=["Pix"], channels=["Chat"],
    )


@pytest.mark.parametrize("env,enabled", [
    ({}, False),
    ({"CX_PRIVATE_PLANS_ENABLED": "true"}, True),
    ({"CX_PRIVATE_PLANS_ENABLED": "true", "CX_PUBLIC_DEMO": "true"}, False),
    ({"CX_PRIVATE_PLANS_ENABLED": "TRUE", "CX_PUBLIC_DEMO": "1"}, False),
    ({"CX_PRIVATE_PLANS_ENABLED": "false", "CX_PUBLIC_DEMO": "false"}, False),
])
def test_private_mode_never_enabled_on_public_demo(env, enabled):
    assert private_storage_enabled(env) is enabled


def test_oidc_subject_is_not_email_and_is_tenant_scoped():
    a, b = principal("user-alpha"), principal("user-beta")
    assert a.owner_key != b.owner_key
    assert len(a.owner_key) == 64
    assert "user-alpha" not in a.owner_key
    assert principal("user-alpha").owner_key == a.owner_key
    from_other_issuer = principal_from_claims(
        {"iss": "https://other-idp.example", "sub": "user-alpha",
         "aud": AUDIENCE, "exp": EXP},
        issuer="https://other-idp.example", audience=AUDIENCE,
    )
    assert from_other_issuer.owner_key != a.owner_key


@pytest.mark.parametrize("modified", [
    {"iss": "https://rogue.example"}, {"aud": "other-app"},
    {"sub": ""}, {"sub": 123}, {"exp": None}, {"exp": "9999999999"},
    {"exp": 1}, {"exp": True},
])
def test_reject_invalid_oidc_identity(modified):
    claims = {"iss": ISSUER, "sub": "uid", "aud": AUDIENCE, "exp": EXP}
    claims.update(modified)
    with pytest.raises(PrivatePlanError):
        principal_from_claims(claims, issuer=ISSUER, audience=AUDIENCE)


def test_allow_oidc_audience_list_and_fixed_clock():
    claims = {"iss": ISSUER, "sub": "abc", "aud": ["other", AUDIENCE], "exp": 500}
    p = principal_from_claims(claims, issuer=ISSUER,
                              audience=AUDIENCE, now=400)
    assert len(p.owner_key) == 64
    with pytest.raises(PrivatePlanError):
        principal_from_claims(claims, issuer=ISSUER,
                              audience=AUDIENCE, now=500)


def test_reject_invalid_actions_before_contacting_database():
    # Deliberately unreachable DSN: validation must win before any network I/O.
    unreachable = "postgresql://invalid:invalid@127.0.0.1:1/invalid"
    with pytest.raises(PrivatePlanError):
        save_private_plan(principal(), "Plano", [{"title": "<script>"}],
                          dsn=unreachable)
    with pytest.raises(PrivatePlanError):
        save_private_plan(principal(), "  ", actions(), dsn=unreachable)
    with pytest.raises(PrivatePlanError):
        save_private_plan(principal(), "Teste", actions(), plan_id="bad",
                          expected_revision=1, dsn=unreachable)
    with pytest.raises(PrivatePlanError):
        list_private_plans(principal(), dsn="not-a-postgres-dsn")


@pytest.fixture(scope="module")
def private_database():
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Requires explicit isolated TEST_DATABASE_URL")
    # A disposable role created only in the isolated CI / test database.
    role = "cx_private_plan_ci_worker"
    password = "local_ci_test_only_not_for_prod"
    migration = Path(__file__).resolve().parents[1] / "migrations" / "006_private_action_plans.sql"
    with connect(dsn) as admin:
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,))
            if cur.fetchone() is None:
                cur.execute(
                    "CREATE ROLE cx_private_plan_ci_worker LOGIN PASSWORD "
                    "'local_ci_test_only_not_for_prod' NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE"
                )
            cur.execute(migration.read_text(encoding="utf-8"))
            cur.execute("GRANT USAGE ON SCHEMA public TO cx_private_plan_ci_worker")
            cur.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON cx_private_action_plans TO cx_private_plan_ci_worker")
            # Migration always executed by a different owner, not the runtime role.
            cur.execute("""
                SELECT r.rolsuper, r.rolbypassrls, c.relforcerowsecurity, c.relrowsecurity
                  FROM pg_roles r, pg_class c
                 WHERE r.rolname = %s AND c.relname = 'cx_private_action_plans'
            """, (role,))
            assert cur.fetchone() == (False, False, True, True)
    url = make_conninfo(dsn, user=role, password=password)
    yield url


def test_private_db_denies_missing_user_scope(private_database):
    with connect(private_database) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM cx_private_action_plans")
            assert cur.fetchone()[0] == 0
            with pytest.raises(Exception):
                # RLS WITH CHECK denies inserts without a scoped owner.
                cur.execute("""
                    INSERT INTO cx_private_action_plans(owner_key,plan_id,name,payload)
                    VALUES ('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                            gen_random_uuid(), 'Indevido', '{}'::jsonb)
                """)


def test_private_db_isolates_users_and_uses_optimistic_locking(private_database):
    alice, bob = principal("alice"), principal("bob")
    saved = save_private_plan(alice, "Meu planejamento CX", actions(), dsn=private_database)
    assert saved["revision"] == 1
    assert len(list_private_plans(alice, dsn=private_database)) >= 1
    assert list_private_plans(bob, dsn=private_database) == []
    assert load_private_plan(alice, saved["id"], dsn=private_database)["actions"] == actions()
    with pytest.raises(PrivatePlanError, match="não encontrado"):
        load_private_plan(bob, saved["id"], dsn=private_database)
    with pytest.raises(PlanConflict):
        save_private_plan(bob, "Alterar Alice", actions(), plan_id=saved["id"],
                          expected_revision=1, dsn=private_database)

    revised_actions = edit_action(actions(), "A0001",
                                  title="Investigar causas sintéticas na jornada Pix",
                                  hypothesis="Checar frequência e mix",
                                  changed_on="2026-10-24")
    revision2 = save_private_plan(alice, "Meu planejamento CX", revised_actions,
                                  plan_id=saved["id"], expected_revision=1,
                                  dsn=private_database)
    assert revision2 == {"id": saved["id"], "revision": 2}
    with pytest.raises(PlanConflict):
        save_private_plan(alice, "Salvar revisão desatualizada", actions(),
                          plan_id=saved["id"], expected_revision=1, dsn=private_database)
    recovered = load_private_plan(alice, saved["id"], dsn=private_database)
    assert recovered["revision"] == 2
    assert recovered["actions"] == revised_actions
    assert len(recovered["actions"][0]["edits"]) == 1
    assert list_private_plans(bob, dsn=private_database) == []

    # Direct runtime role is also limited by RLS when the principal is absent.
    with connect(private_database) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM cx_private_action_plans")
            assert cur.fetchone()[0] == 0
            cur.execute("SELECT set_config('cx.plan_owner_key', %s, true)",
                        (bob.owner_key,))
            cur.execute("SELECT count(*) FROM cx_private_action_plans")
            assert cur.fetchone()[0] == 0
