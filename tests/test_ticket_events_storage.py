"""Storage contracts with a fake cursor; live PostgreSQL still needs a smoke check."""
from datetime import datetime, timezone
import pytest
import src.ticket_events as events

TIME = datetime(2026, 8, 1, 10, tzinfo=timezone.utc)

class FakeCursor:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.statements = []
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def execute(self, sql, params=None):
        self.statements.append((sql,params))
        return self
    def fetchone(self):
        return next(self.responses)

class FakeConnection:
    def __init__(self,responses):
        self.cursor_object = FakeCursor(responses)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def cursor(self,**kwargs):
        return self.cursor_object

def stub_connection(monkeypatch,responses):
    fake = FakeConnection(responses)
    monkeypatch.setattr(events.psycopg,"connect",lambda dsn: fake)
    return fake.cursor_object

def test_new_event_locks_parent_then_inserts(monkeypatch):
    cur=stub_connection(monkeypatch,[{"ticket_id":"T000001"},None,None])
    result=events.append_ticket_event("T000001","evt-1","OPEN",TIME)
    assert result["outcome"]=="inserted"
    assert "FOR UPDATE" in cur.statements[0][0]
    assert any("INSERT INTO cx_ticket_events" in sql for sql,_ in cur.statements)

def test_same_key_and_payload_is_idempotent(monkeypatch):
    existing={"ticket_id":"T000001","status":"OPEN","occurred_at":TIME,"source":"synthetic_demo"}
    cur=stub_connection(monkeypatch,[{"ticket_id":"T000001"},existing])
    result=events.append_ticket_event("T000001","evt-1","OPEN",TIME,source="synthetic_demo")
    assert result["outcome"]=="duplicate"
    assert not any("INSERT INTO cx_ticket_events" in sql for sql,_ in cur.statements)

def test_key_conflict_with_other_payload_fails(monkeypatch):
    existing={"ticket_id":"T000001","status":"OPEN","occurred_at":TIME,"source":"synthetic_demo"}
    stub_connection(monkeypatch,[{"ticket_id":"T000001"},existing])
    with pytest.raises(ValueError,match="event_key"):
        events.append_ticket_event("T000001","evt-1","OPEN",TIME,source="manual_demo")

def test_out_of_order_event_is_rejected(monkeypatch):
    stub_connection(monkeypatch,[{"ticket_id":"T000001"},None,
        {"status":"OPEN","occurred_at":TIME}])
    with pytest.raises(ValueError,match="cronológica"):
        events.append_ticket_event("T000001","evt-2","IN_PROGRESS",TIME)

def test_unknown_ticket_fails_before_insert(monkeypatch):
    cur=stub_connection(monkeypatch,[None])
    with pytest.raises(ValueError,match="inexistente"):
        events.append_ticket_event("T999999","evt-1","OPEN",TIME)
    assert not any("INSERT" in sql for sql,_ in cur.statements)


def test_demo_rerun_does_not_seed_additional_tickets(monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    history = {"already_present": False}
    class DemoConn:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def execute(self, sql, params=None):
            row = {"ticket_id": "T000001", "date": date(2026,8,1),
                   "resolved": 1, "has_history": history["already_present"]}
            return SimpleNamespace(fetchall=lambda: [row])

    calls = []
    monkeypatch.setattr(events.psycopg, "connect", lambda *a, **kw: DemoConn())
    monkeypatch.setattr(events, "initialize_event_schema", lambda dsn: None)
    def fake_append(*args, **kwargs):
        calls.append(args)
        return {"outcome": "inserted"}
    monkeypatch.setattr(events, "append_ticket_event", fake_append)

    first = events.seed_demo(dsn="synthetic-test-dsn",limit=1)
    history["already_present"] = True
    second = events.seed_demo(dsn="synthetic-test-dsn",limit=1)
    assert first == {"tickets_seeded": 1, "events_inserted": 3}
    assert second == {"tickets_seeded": 0, "events_inserted": 0}
    assert len(calls) == 3
