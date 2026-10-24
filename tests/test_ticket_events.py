"""Ticket event domain and schema tests; no running PostgreSQL required."""
from datetime import date, datetime
from pathlib import Path

import pytest
from src.ticket_events import (
    validate_transition, validate_event, normalize_timestamp, demo_plan, SCHEMA
)

def test_allowed_status_transitions():
    for before, after in [(None,"OPEN"),("OPEN","IN_PROGRESS"),("OPEN","RESOLVED"),
                          ("IN_PROGRESS","RESOLVED"),("RESOLVED","IN_PROGRESS")]:
        assert validate_transition(before, after)

@pytest.mark.parametrize("before,after", [
    (None,"RESOLVED"), ("OPEN","OPEN"), ("IN_PROGRESS","OPEN"),
    ("RESOLVED","RESOLVED"), ("OPEN","UNKNOWN"),
])
def test_forbidden_status_transitions(before,after):
    with pytest.raises(ValueError):
        validate_transition(before,after)

def test_rejects_naive_datetime():
    with pytest.raises(ValueError, match="fuso"):
        normalize_timestamp(datetime(2026,8,1,9,0))

def test_utc_normalization():
    assert normalize_timestamp("2026-08-01T09:00:00-03:00").isoformat() == "2026-08-01T12:00:00+00:00"

def test_simulated_plan_is_ordered_and_deterministic():
    result=demo_plan("T000001",date(2026,8,1),True)
    assert [item[2] for item in result] == ["OPEN","IN_PROGRESS","RESOLVED"]
    assert [item[3] for item in result] == sorted(item[3] for item in result)
    assert demo_plan("T000001",date(2026,8,1),True) == result

def test_unresolved_demo_has_no_resolution():
    result=demo_plan("T000002",date(2026,8,1),False)
    assert [item[2] for item in result] == ["OPEN","IN_PROGRESS"]

def test_validate_event_rejects_unknown_source():
    with pytest.raises(ValueError,match="Origem"):
        validate_event("T000001","key","OPEN","2026-08-01T09:00:00Z","external_real")

def test_validate_event_rejects_blank_ticket_id():
    with pytest.raises(ValueError,match="ticket_id"):
        validate_event("","key","OPEN","2026-08-01T09:00:00Z","synthetic_demo")

def test_schema_enforces_append_only_and_foreign_key():
    sql=SCHEMA.read_text(encoding="utf-8")
    assert "event_key VARCHAR(128) PRIMARY KEY" in sql
    assert "BEFORE UPDATE OR DELETE" in sql
    assert "REFERENCES cx_tickets(ticket_id)" in sql
