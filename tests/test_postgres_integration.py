"""Live PostgreSQL integration — opt-in locally, required in GitHub Actions.

Never connect to the user's normal cx_intelligence database. Set TEST_DATABASE_URL
to an isolated database NAMED cx_test (for example a separate Docker service).
"""
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
from psycopg.conninfo import conninfo_to_dict
import pytest
import pandas as pd

from src.database import DDL as SNAPSHOT_DDL
from src.ticket_events import (
    append_ticket_event,
    initialize_event_schema,
    load_event_history,
    load_ticket_status_as_of,
    load_status_as_of,
)
from src.external_kaggle import (
    import_kaggle_csv, external_schema_exists, load_external_tickets,
)


@pytest.fixture(scope="module")
def pg_url():
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Live PostgreSQL integration opt-in via TEST_DATABASE_URL")
    if conninfo_to_dict(dsn).get("dbname") != "cx_test":
        pytest.fail("TEST_DATABASE_URL MUST refer to the isolated cx_test database")
    with psycopg.connect(dsn) as conn:
        conn.execute(SNAPSHOT_DDL)
    initialize_event_schema(dsn)
    return dsn


def new_parent(dsn):
    ticket = "T" + uuid4().hex[:16]
    with psycopg.connect(dsn) as conn:
        conn.execute("""INSERT INTO cx_tickets(
            ticket_id,customer_id,date,channel,topic,resolution_hours,resolved,
            sentiment,csat,previous_tickets,repeat_contact_30d)
            VALUES (%s,'C-SYNTHETIC',DATE '2026-08-01','Chat','Testes',1.0,0,'neutro',3,0,0)""",
                     (ticket,))
    return ticket


def test_ticket_lifecycle_idempotence_and_time_travel(pg_url):
    ticket = new_parent(pg_url)
    t0 = datetime(2026, 8, 1, 9, tzinfo=timezone.utc)
    assert load_ticket_status_as_of(ticket, t0 - timedelta(seconds=1), pg_url) is None

    assert append_ticket_event(ticket, "evt-" + ticket + "-open", "OPEN", t0,
                               dsn=pg_url)["outcome"] == "inserted"
    first = load_ticket_status_as_of(ticket, t0, pg_url)
    assert first["status"] == "OPEN"

    assert append_ticket_event(ticket, "evt-" + ticket + "-progress", "IN_PROGRESS",
                               t0 + timedelta(minutes=20), dsn=pg_url)["outcome"] == "inserted"
    assert append_ticket_event(ticket, "evt-" + ticket + "-resolved", "RESOLVED",
                               t0 + timedelta(minutes=75), dsn=pg_url)["outcome"] == "inserted"
    assert load_ticket_status_as_of(ticket, t0 + timedelta(minutes=30), pg_url)["status"] == "IN_PROGRESS"
    assert load_ticket_status_as_of(ticket, t0 + timedelta(minutes=90), pg_url)["status"] == "RESOLVED"

    key = "evt-" + ticket + "-resolved"
    assert append_ticket_event(ticket, key, "RESOLVED", t0 + timedelta(minutes=75),
                               dsn=pg_url)["outcome"] == "duplicate"
    with pytest.raises(ValueError, match="event_key"):
        append_ticket_event(ticket, key, "IN_PROGRESS", t0 + timedelta(minutes=75), dsn=pg_url)
    with pytest.raises(ValueError, match="cronológica"):
        append_ticket_event(ticket, "evt-" + ticket + "-old", "IN_PROGRESS",
                            t0 + timedelta(minutes=10), dsn=pg_url)

    assert append_ticket_event(ticket, "evt-" + ticket + "-reopen", "IN_PROGRESS",
                               t0 + timedelta(hours=2), dsn=pg_url)["outcome"] == "inserted"
    assert load_ticket_status_as_of(ticket, t0 + timedelta(hours=3), pg_url)["status"] == "IN_PROGRESS"
    assert sum(row["tickets"] for row in load_status_as_of(t0 + timedelta(hours=3), pg_url)) >= 1
    assert any(row["ticket_id"] == ticket for row in load_event_history(pg_url))


def test_database_trigger_blocks_event_update_and_delete(pg_url):
    ticket = new_parent(pg_url)
    key = "evt-" + ticket + "-immutable"
    t0 = datetime(2026, 8, 1, 9, tzinfo=timezone.utc)
    append_ticket_event(ticket, key, "OPEN", t0, dsn=pg_url)

    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        with psycopg.connect(pg_url) as conn:
            conn.execute("UPDATE cx_ticket_events SET status='RESOLVED' WHERE event_key=%s", (key,))
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        with psycopg.connect(pg_url) as conn:
            conn.execute("DELETE FROM cx_ticket_events WHERE event_key=%s", (key,))

    with psycopg.connect(pg_url) as conn:
        assert conn.execute("SELECT COUNT(*) FROM cx_ticket_events WHERE event_key=%s",
                            (key,)).fetchone()[0] == 1


def test_foreign_key_rejects_orphan_event(pg_url):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with psycopg.connect(pg_url) as conn:
            conn.execute("""INSERT INTO cx_ticket_events
                            (event_key,ticket_id,status,occurred_at,source)
                            VALUES (%s,%s,'OPEN',%s,'synthetic_demo')""",
                         ("evt-orphan-" + uuid4().hex, "NONEXISTENT_TICKET",
                          datetime(2026, 8, 1, tzinfo=timezone.utc)))


def test_external_kaggle_import_is_idempotent_in_real_postgres(pg_url, tmp_path):
    ticket_one = str(uuid4().int)[:18]
    ticket_two = str(uuid4().int)[:18]
    frame = pd.DataFrame([
        {"Ticket ID": ticket_one, "Ticket Type": "Technical issue",
         "Ticket Status": "Closed", "Ticket Priority": "High",
         "Ticket Channel": "Chat", "Customer Satisfaction Rating": "5",
         "Customer Email": "must-never-be-stored@example.org"},
        {"Ticket ID": ticket_two, "Ticket Type": "Refund request",
         "Ticket Status": "Open", "Ticket Priority": "Low",
         "Ticket Channel": "Email", "Customer Satisfaction Rating": "",
         "Customer Email": "must-never-be-stored@example.org"},
    ])
    csv = tmp_path / "test_support.csv"
    frame.to_csv(csv, index=False)
    first = import_kaggle_csv(csv, pg_url)
    second = import_kaggle_csv(csv, pg_url)
    assert first["affected_rows"] == 2
    assert second["affected_rows"] == 0
    assert first["dataset_sha256"] == second["dataset_sha256"]
    assert first["rated_tickets"] == 1
    assert external_schema_exists(pg_url)
    stored = load_external_tickets(pg_url)
    assert len(stored) >= 2
    assert "Customer Email" not in stored.columns
    with psycopg.connect(pg_url) as conn:
        assert conn.execute("SELECT COUNT(*) FROM cx_external_import_runs").fetchone()[0] >= 2
