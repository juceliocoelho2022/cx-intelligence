"""Private synthetic action-plan storage (opt-in). Never enabled on the public demo.

Only a validated OIDC principal may reach the database. Runtime DB role must be
non-superuser, non-BYPASSRLS and distinct from the migration/table owner.
No raw email, access token, real customer data, or passwords are persisted here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from uuid import UUID, uuid4

from psycopg import connect
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from src.cx_goals import export_plan_json, load_plan_actions


class PrivatePlanError(ValueError):
    pass


class PlanConflict(PrivatePlanError):
    pass


@dataclass(frozen=True)
class PrivatePrincipal:
    owner_key: str
    expires_at: int


def private_storage_enabled(environ=None) -> bool:
    """Public mode always wins, even if an enable flag was mistakenly set."""
    env = os.environ if environ is None else environ
    return (str(env.get("CX_PRIVATE_PLANS_ENABLED", "")).lower() == "true"
            and str(env.get("CX_PUBLIC_DEMO", "")).lower() not in ("true", "1", "yes"))


def principal_from_claims(claims, *, issuer: str, audience: str, now=None) -> PrivatePrincipal:
    """Accept claims only AFTER Streamlit verified the OIDC ID token and session.

    Explicit exp check compensates for Streamlit's long-lived identity cookie.
    The configured issuer and client ID are never taken from untrusted claims.
    """
    if not isinstance(claims, dict):
        raise PrivatePlanError("Identidade OIDC ausente")
    if not isinstance(issuer, str) or not issuer or not isinstance(audience, str) or not audience:
        raise PrivatePlanError("Provedor OIDC não configurado")
    iss, sub, aud, exp = (claims.get("iss"), claims.get("sub"),
                          claims.get("aud"), claims.get("exp"))
    if iss != issuer or not isinstance(sub, str) or not 1 <= len(sub) <= 255:
        raise PrivatePlanError("Identidade de usuário ou emissor inválido")
    if not (aud == audience or isinstance(aud, list) and audience in aud):
        raise PrivatePlanError("Aplicativo OIDC não autorizado")
    cutoff = int(datetime.now(timezone.utc).timestamp()) if now is None else int(now)
    if type(exp) is not int or exp <= cutoff:
        raise PrivatePlanError("Sessão de identidade expirada ou inválida; entre novamente")
    owner = sha256((issuer + "\x00" + sub).encode("utf-8")).hexdigest()
    return PrivatePrincipal(owner_key=owner, expires_at=exp)


def _validate_principal(principal: PrivatePrincipal):
    if (not isinstance(principal, PrivatePrincipal)
            or not isinstance(principal.owner_key, str)
            or len(principal.owner_key) != 64
            or any(c not in "0123456789abcdef" for c in principal.owner_key)):
        raise PrivatePlanError("Identidade de armazenamento inválida")
    if principal.expires_at <= int(datetime.now(timezone.utc).timestamp()):
        raise PrivatePlanError("Sessão expirada; entre novamente")


def _dsn(value):
    dsn = value if value is not None else os.getenv("CX_PRIVATE_PLAN_DATABASE_URL")
    if not isinstance(dsn, str) or not dsn.strip():
        raise PrivatePlanError("Banco privado não configurado")
    try:
        settings = conninfo_to_dict(dsn)
    except Exception as exc:
        raise PrivatePlanError("Configuração do banco privado inválida") from exc
    if not settings.get("dbname"):
        raise PrivatePlanError("Banco privado sem nome de base")
    # Validate both host and hostaddr to prevent a misleading local host
    # alias from masking a remote IP without certificate validation.
    hosts = (settings.get("host", ""), settings.get("hostaddr", ""))
    local = ("", "localhost", "127.0.0.1", "::1")
    if any(host not in local for host in hosts) and settings.get("sslmode") != "verify-full":
        raise PrivatePlanError("Banco remoto exige sslmode=verify-full")
    return dsn


def _validated_actions(actions):
    if not isinstance(actions, list):
        raise PrivatePlanError("Plano não é uma lista de ações")
    source = {
        "schema_version": "1.5.0",
        "source": "synthetic_primary_only",
        "persistence": "session_only",
        "actions": actions,
    }
    try:
        data = export_plan_json(source).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise PrivatePlanError("Ações não podem ser serializadas") from exc
    if len(data) > 200_000:
        raise PrivatePlanError("Limite de 200 KB por plano excedido")
    try:
        validated = load_plan_actions(data)
    except ValueError as exc:
        raise PrivatePlanError("Ações inválidas: " + str(exc)) from exc
    return validated, {"schema_version": "1.5.0",
                       "source": "synthetic_primary_only",
                       "actions": validated}


def _title(value):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 80:
        raise PrivatePlanError("Nome do plano deve conter de 1 a 80 caracteres")
    value = value.strip()
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise PrivatePlanError("Nome contém caracteres inválidos")
    return value


def _id(value):
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise PrivatePlanError("Identificador do plano inválido") from exc


def _revision(value):
    if type(value) is not int or not 1 <= value < 2147483647:
        raise PrivatePlanError("Revisão inválida")


def _session(conn, principal):
    """Within the transaction set owner scope, and verify FORCE RLS & runtime role."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""
            SELECT c.relrowsecurity AS rls, c.relforcerowsecurity AS forced,
                   r.rolsuper AS superuser, r.rolbypassrls AS bypass
            FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                            CROSS JOIN pg_roles r
            WHERE n.nspname=current_schema()
              AND c.relname='cx_private_action_plans' AND r.rolname=current_user
        """)
        meta = cur.fetchone()
        if not meta or not meta["rls"] or not meta["forced"] or meta["superuser"] or meta["bypass"]:
            raise PrivatePlanError("Banco não tem isolamento RLS seguro ou usa papel privilegiado")
        cur.execute("SELECT set_config('cx.plan_owner_key', %s, true)",
                    (principal.owner_key,))


def save_private_plan(principal, name, actions, *,
                      plan_id=None, expected_revision=None, dsn=None):
    """Create or optimistic-lock update; never overwrite another owner's plan."""
    _validate_principal(principal)
    name = _title(name)
    _, payload = _validated_actions(actions)
    if plan_id is not None:
        identifier = _id(plan_id)
        _revision(expected_revision)
    else:
        if expected_revision is not None:
            raise PrivatePlanError("Novo plano não pode ter revisão anterior")
        identifier = uuid4()
    with connect(_dsn(dsn), connect_timeout=5) as conn:
        _session(conn, principal)
        with conn.cursor(row_factory=dict_row) as cur:
            if plan_id is None:
                cur.execute("""
                    INSERT INTO cx_private_action_plans
                      (owner_key, plan_id, name, payload, revision)
                    VALUES (%s,%s,%s,%s,1)
                    RETURNING plan_id, revision
                """, (principal.owner_key, identifier, name, Jsonb(payload)))
            else:
                cur.execute("""
                    UPDATE cx_private_action_plans
                       SET name=%s, payload=%s, revision=revision+1, updated_at=now()
                     WHERE owner_key=%s AND plan_id=%s AND revision=%s
                    RETURNING plan_id, revision
                """, (name, Jsonb(payload), principal.owner_key,
                      identifier, expected_revision))
            result = cur.fetchone()
            if result is None:
                raise PlanConflict("Plano alterado em outra sessão ou sem autorização. Recarregue a versão salva.")
            return {"id": str(result["plan_id"]), "revision": result["revision"]}


def list_private_plans(principal, *, dsn=None):
    _validate_principal(principal)
    with connect(_dsn(dsn), connect_timeout=5) as conn:
        _session(conn, principal)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT plan_id, name, revision, updated_at
                  FROM cx_private_action_plans
                 WHERE owner_key=%s ORDER BY updated_at DESC, plan_id
                 LIMIT 100
            """, (principal.owner_key,))
            return [{"id": str(row["plan_id"]), "name": row["name"],
                     "revision": row["revision"],
                     "updated_at": row["updated_at"].isoformat()}
                    for row in cur.fetchall()]


def load_private_plan(principal, plan_id, *, dsn=None):
    _validate_principal(principal)
    identifier = _id(plan_id)
    with connect(_dsn(dsn), connect_timeout=5) as conn:
        _session(conn, principal)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT plan_id, name, revision, payload
                  FROM cx_private_action_plans
                 WHERE owner_key=%s AND plan_id=%s
            """, (principal.owner_key, identifier))
            row = cur.fetchone()
            if row is None:
                raise PrivatePlanError("Plano não encontrado ou sem autorização")
            blob = {"schema_version": row["payload"]["schema_version"],
                    "source": row["payload"]["source"],
                    "persistence": "session_only", "actions": row["payload"]["actions"]}
            actions = load_plan_actions(export_plan_json(blob).encode("utf-8"))
            return {"id": str(row["plan_id"]), "name": row["name"],
                    "revision": row["revision"], "actions": actions}


def delete_private_plan(principal, plan_id, expected_revision, *, dsn=None):
    """Explicit owner-only deletion. Reject stale versions to avoid accidental loss."""
    _validate_principal(principal)
    identifier = _id(plan_id)
    _revision(expected_revision)
    with connect(_dsn(dsn), connect_timeout=5) as conn:
        _session(conn, principal)
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM cx_private_action_plans
                 WHERE owner_key=%s AND plan_id=%s AND revision=%s
                RETURNING plan_id
            """, (principal.owner_key, identifier, expected_revision))
            if cur.fetchone() is None:
                raise PlanConflict("Plano alterado, excluído ou sem autorização")
    return True
