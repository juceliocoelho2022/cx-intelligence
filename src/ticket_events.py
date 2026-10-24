"""Synthetic, append-only ticket events. Never infer past events from cx_tickets."""
import argparse
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from src.database import connection_string

SCHEMA = Path(__file__).resolve().parents[1] / "sql" / "ticket_events.sql"
TRANSITIONS = {
    None: {"OPEN"},
    "OPEN": {"IN_PROGRESS", "RESOLVED"},
    "IN_PROGRESS": {"RESOLVED"},
    "RESOLVED": {"IN_PROGRESS"},
}
STATES = {"OPEN", "IN_PROGRESS", "RESOLVED"}

def normalize_timestamp(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("occurred_at exige datetime com fuso horário explícito")
    return value.astimezone(timezone.utc)

def validate_transition(previous, new_status):
    if new_status not in STATES or new_status not in TRANSITIONS.get(previous, set()):
        raise ValueError(f"Transição inválida: {previous} -> {new_status}")
    return True

def validate_event(ticket_id, event_key, status, occurred_at, source):
    if not isinstance(ticket_id, str) or not 1 <= len(ticket_id) <= 20 or not ticket_id.strip():
        raise ValueError("ticket_id inválido")
    if not isinstance(event_key, str) or not 1 <= len(event_key) <= 128 or not event_key.strip():
        raise ValueError("event_key inválida")
    if status not in STATES:
        raise ValueError("Status inválido")
    if source not in {"synthetic_demo", "manual_demo"}:
        raise ValueError("Origem inválida; apenas dados fictícios")
    return normalize_timestamp(occurred_at)

def initialize_event_schema(dsn=None):
    with psycopg.connect(dsn or connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA.read_text(encoding="utf-8"))

def append_ticket_event(ticket_id, event_key, status, occurred_at,
                        source="manual_demo", dsn=None):
    """Lock parent ticket, check idempotency, enforce chronology and append."""
    timestamp = validate_event(ticket_id, event_key, status, occurred_at, source)
    with psycopg.connect(dsn or connection_string()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT ticket_id FROM cx_tickets WHERE ticket_id=%s FOR UPDATE", (ticket_id,))
            if cur.fetchone() is None:
                raise ValueError(f"Ticket inexistente: {ticket_id}")
            cur.execute("SELECT ticket_id,status,occurred_at,source FROM cx_ticket_events WHERE event_key=%s", (event_key,))
            prior_key = cur.fetchone()
            if prior_key:
                if (prior_key["ticket_id"], prior_key["status"],
                    normalize_timestamp(prior_key["occurred_at"]), prior_key["source"]) != (
                        ticket_id, status, timestamp, source):
                    raise ValueError("event_key reutilizada com dados diferentes")
                return {"outcome": "duplicate", "event_key": event_key}
            cur.execute("""SELECT status,occurred_at FROM cx_ticket_events WHERE ticket_id=%s
                           ORDER BY occurred_at DESC,event_key DESC LIMIT 1""", (ticket_id,))
            last = cur.fetchone()
            validate_transition(last["status"] if last else None, status)
            if last and timestamp <= normalize_timestamp(last["occurred_at"]):
                raise ValueError("Evento fora de ordem cronológica")
            cur.execute("""INSERT INTO cx_ticket_events(event_key,ticket_id,status,occurred_at,source)
                           VALUES (%s,%s,%s,%s,%s)""", (event_key,ticket_id,status,timestamp,source))
    return {"outcome": "inserted", "event_key": event_key}

def demo_plan(ticket_id, opened_on, resolved):
    """Entirely invented times for illustration; not historical reconstruction."""
    if not isinstance(opened_on, date):
        raise ValueError("Data inválida")
    origin = datetime.combine(opened_on, time(9), timezone.utc)
    events = [
        (f"demo-v1:{ticket_id}:open", ticket_id, "OPEN", origin),
        (f"demo-v1:{ticket_id}:progress", ticket_id, "IN_PROGRESS", origin + timedelta(minutes=20)),
    ]
    if resolved:
        events.append((f"demo-v1:{ticket_id}:resolved", ticket_id, "RESOLVED",
                       origin + timedelta(minutes=75)))
    return events

def seed_demo(dsn=None, limit=5):
    if not 1 <= limit <= 100:
        raise ValueError("limit inválido")
    dsn = dsn or connection_string()
    initialize_event_schema(dsn)
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        rows = conn.execute("""SELECT t.ticket_id,t.date,t.resolved FROM cx_tickets t
                               WHERE NOT EXISTS(SELECT 1 FROM cx_ticket_events e WHERE e.ticket_id=t.ticket_id)
                               ORDER BY t.ticket_id LIMIT %s""", (limit,)).fetchall()
    created = 0
    for row in rows:
        for key, ticket_id, status, at in demo_plan(row["ticket_id"], row["date"], bool(row["resolved"])):
            created += append_ticket_event(ticket_id,key,status,at,"synthetic_demo",dsn)["outcome"] == "inserted"
    return {"tickets_seeded": len(rows), "events_inserted": created}

def schema_exists(dsn=None):
    with psycopg.connect(dsn or connection_string()) as conn:
        return conn.execute("SELECT to_regclass('public.cx_ticket_events')").fetchone()[0] is not None

def load_event_history(dsn=None, limit=500):
    with psycopg.connect(dsn or connection_string(), row_factory=dict_row) as conn:
        return conn.execute("""SELECT event_key,ticket_id,status,occurred_at,recorded_at,source
                               FROM cx_ticket_events ORDER BY occurred_at DESC,event_key DESC LIMIT %s""",
                            (limit,)).fetchall()

def load_status_as_of(as_of, dsn=None):
    """Only tickets with recorded events; never reconstruct missing history."""
    timestamp = normalize_timestamp(as_of)
    with psycopg.connect(dsn or connection_string(), row_factory=dict_row) as conn:
        return conn.execute("""SELECT status,COUNT(*) AS tickets FROM (
            SELECT DISTINCT ON(ticket_id) ticket_id,status FROM cx_ticket_events
            WHERE occurred_at<=%s ORDER BY ticket_id,occurred_at DESC,event_key DESC
            ) history GROUP BY status ORDER BY status""", (timestamp,)).fetchall()

def main():
    parser = argparse.ArgumentParser(description="Ticket event history (synthetic)")
    parser.add_argument("action", choices=["init","demo"])
    parser.add_argument("--limit",type=int,default=5)
    args = parser.parse_args()
    if args.action=="init":
        initialize_event_schema()
        print("Histórico criado. Nenhum evento foi inventado automaticamente.")
    else:
        print("ATENÇÃO: horários e transições 100% simulados; não observados.")
        print(seed_demo(limit=args.limit))

if __name__=="__main__":
    main()
