"""v1.5 pure CX goal and ephemeral action tracker contract."""
from copy import deepcopy
import json

import pytest

from src.cx_goals import (
    METRICS, DISCLAIMER, evaluate_goals, create_action,
    change_action_status, report_payload, export_plan_json, export_plan_markdown,
)

CURRENT = {
    "tickets": 685, "csat_pct": 62.19,
    "resolved_pct": 87.45, "avg_resolution_hours": 10.89,
}

BASE = {
    "metric": "csat_pct", "title": "Investigar jornada Pix",
    "hypothesis": "Conferir motivos de reclamação e mix dos tickets.",
    "role": "CX", "created_on": "2026-10-24",
    "due_date": "2026-11-04", "period_start": "2026-10-06",
    "period_end": "2026-10-19", "topics": ["Pix"], "channels": ["Chat"],
}


def test_goal_defaults_and_units():
    rows = evaluate_goals(CURRENT)
    assert len(rows) == 3
    assert {r["metric"]: r["status"] for r in rows} == {
        "csat_pct": "attention", "resolved_pct": "attention",
        "avg_resolution_hours": "attention",
    }
    assert {r["metric"]: r["gap_to_target"] for r in rows} == {
        "csat_pct": 7.81, "resolved_pct": 2.55, "avg_resolution_hours": 0.89,
    }
    assert [r["unit"] for r in rows] == ["pp", "pp", "h"]


def test_attainment_is_directional_including_equality():
    r = evaluate_goals(CURRENT, {
        "csat_pct": 60.0, "resolved_pct": 87.45,
        "avg_resolution_hours": 11.0,
    })
    assert all(x["status"] == "met" and x["gap_to_target"] == 0 for x in r)
    assert next(x for x in r if x["metric"] == "csat_pct")["signed_margin"] == 2.19


@pytest.mark.parametrize("count,covered,status", [
    (0, True, "no_data"), (12, True, "insufficient_sample"),
    (685, False, "incomplete_window"),
])
def test_goals_suppress_conclusions_on_bad_samples(count, covered, status):
    r = evaluate_goals({**CURRENT, "tickets": count}, current_covered=covered)
    assert all(x["status"] == status for x in r)
    assert all(x["gap_to_target"] is None for x in r)


def test_missing_metric_is_not_a_success():
    r = evaluate_goals({**CURRENT, "csat_pct": None})
    assert r[0]["status"] == "missing_metric"
    assert r[0]["gap_to_target"] is None
    assert r[1]["status"] == "attention"


@pytest.mark.parametrize("bad", [-1, 101, float("nan"), float("inf"), True, "80"])
def test_invalid_goal_target_rejected(bad):
    with pytest.raises(ValueError):
        evaluate_goals(CURRENT, {"csat_pct": bad})


@pytest.mark.parametrize("bad", [0, -1, 3.5, True, "30"])
def test_invalid_minimum_rejected(bad):
    with pytest.raises(ValueError, match="Mínimo"):
        evaluate_goals(CURRENT, min_tickets=bad)


def test_unknown_goals_count_and_flags_rejected():
    with pytest.raises(ValueError):
        evaluate_goals(CURRENT, {"churn_real": 4})
    with pytest.raises(ValueError):
        evaluate_goals({**CURRENT, "tickets": -5})
    with pytest.raises(ValueError):
        evaluate_goals(CURRENT, current_covered=1)


def test_create_actions_does_not_mutate_and_assigns_monotonic_ids():
    actions = create_action([], **BASE)
    assert actions[0]["id"] == "A0001"
    assert actions[0]["status"] == "Planejada"
    assert actions[0]["scope"]["topics"] == ["Pix"]
    saved = deepcopy(actions)
    added = create_action(actions, **{**BASE, "title": "Rever mensagens do app"})
    assert actions == saved
    assert [a["id"] for a in added] == ["A0001", "A0002"]
    assert added[0]["events"] == [{"on": "2026-10-24", "status": "Planejada"}]


def test_status_changes_are_audited_and_immutable():
    original = create_action([], **BASE)
    started = change_action_status(original, "A0001", "Em andamento", "2026-10-25")
    finished = change_action_status(started, "A0001", "Concluída", "2026-11-02")
    assert original[0]["status"] == "Planejada"
    assert started[0]["status"] == "Em andamento"
    assert finished[0]["status"] == "Concluída"
    assert [a["status"] for a in finished[0]["events"]] == [
        "Planejada", "Em andamento", "Concluída",
    ]


def test_illegal_transitions_and_dates_rejected():
    actions = create_action([], **BASE)
    for status in ("Concluída", "Planejada", "Not real"):
        with pytest.raises(ValueError):
            change_action_status(actions, "A0001", status, "2026-10-25")
    with pytest.raises(ValueError, match="evento anterior"):
        change_action_status(actions, "A0001", "Em andamento", "2026-01-01")
    with pytest.raises(ValueError, match="não encontrada"):
        change_action_status(actions, "A9999", "Em andamento", "2026-10-25")


@pytest.mark.parametrize("field,value", [
    ("metric", "fake_metric"), ("role", "Real Person"),
    ("title", ""), ("title", "X"*121),
    ("hypothesis", "X"*401), ("hypothesis", "line\nbreak"),
    ("due_date", "2020-01-01"), ("due_date", "2026-13-15"),
    ("period_start", "2026-11-01"), ("period_end", "2026-10-00"),
    ("channels", ["a\nb"]),
])
def test_action_validation_rejects_invalid_fields(field, value):
    with pytest.raises(ValueError):
        create_action([], **{**BASE, field: value})


def test_json_and_markdown_reports_are_deterministic_and_safe():
    input_actions = create_action([], **{
        **BASE, "title": "Pix | ajustes <img src=x onerror=alert(1)>",
        "hypothesis": "Revisar jornada fictícia",
    })
    goals = evaluate_goals(CURRENT)
    payload = report_payload(goals, input_actions, {
        "start": "2026-10-06", "end": "2026-10-19",
    })
    serialized = export_plan_json(payload)
    assert json.loads(serialized) == payload
    assert serialized == export_plan_json(payload)
    assert payload["persistence"] == "session_only"
    assert payload["disclaimer"] == DISCLAIMER
    md = export_plan_markdown(payload)
    assert "Pix \\| ajustes" in md
    assert "&lt;img src=x onerror=alert(1)&gt;" in md
    assert "<img src=x" not in md
    assert "não representam execução real" in md
    assert "apenas na sessão" in md
    assert "CSAT positivo" in md


def test_export_rejects_wrong_period_and_nonfinite_values():
    with pytest.raises(ValueError):
        report_payload([], [], {"start": "2026-11-01", "end": "2026-10-01"})
    with pytest.raises(ValueError):
        export_plan_json({"bad": float("nan")})


def test_goals_deterministic_and_input_not_modified():
    before = deepcopy(CURRENT)
    targets = {k: v["default"] for k,v in METRICS.items()}
    assert evaluate_goals(CURRENT, targets) == evaluate_goals(CURRENT, targets)
    assert CURRENT == before
