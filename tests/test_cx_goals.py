"""v1.5 pure CX goal and ephemeral action tracker contract."""
from copy import deepcopy
import json

import pytest

from src.cx_goals import (
    METRICS, DISCLAIMER, evaluate_goals, create_action,
    change_action_status, edit_action, load_plan_actions,
    report_payload, export_plan_json, export_plan_markdown,
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


@pytest.mark.parametrize("bad", ["", " ", "   "])
def test_empty_hypothesis_has_clear_required_message(bad):
    with pytest.raises(ValueError, match="Hipótese de investigação: campo obrigatório"):
        create_action([], **{**BASE, "hypothesis": bad})


def test_overlength_hypothesis_has_explicit_character_count():
    with pytest.raises(ValueError, match="texto com 401 caracteres; o máximo permitido é 400"):
        create_action([], **{**BASE, "hypothesis": "X" * 401})


def test_hypothesis_exactly_400_chars_is_accepted():
    actions = create_action([], **{**BASE, "hypothesis": "X" * 400})
    assert len(actions[0]["hypothesis"]) == 400


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


def test_edit_action_preserves_id_scope_status_events_and_records_revision():
    original = create_action([], **BASE)
    started = change_action_status(original, "A0001", "Em andamento", "2026-10-25")
    edited = edit_action(
        started, "A0001",
        title="Investigar insatisfação na jornada Pix",
        hypothesis="Validar dificuldades de uso e mix de atendimentos fictícios.",
        changed_on="2026-10-25",
    )
    assert original[0]["title"] == BASE["title"]
    assert started[0]["title"] == BASE["title"]
    assert edited[0]["title"] == "Investigar insatisfação na jornada Pix"
    assert edited[0]["status"] == "Em andamento"
    assert edited[0]["scope"] == started[0]["scope"]
    assert edited[0]["events"] == started[0]["events"]
    assert edited[0]["edits"][0]["old_title"] == BASE["title"]
    assert edited[0]["edits"][0]["new_hypothesis"] == "Validar dificuldades de uso e mix de atendimentos fictícios."
    assert edit_action(edited, "A0001", title=edited[0]["title"],
                       hypothesis=edited[0]["hypothesis"], changed_on="2026-10-25") == edited


def test_edited_action_can_be_restored_with_audited_revisions():
    original = create_action([], **BASE)
    edited = edit_action(
        original, "A0001", title="Revisar jornada Pix",
        hypothesis="Checar dados sintéticos por canal.",
        changed_on="2026-10-24",
    )
    updated = change_action_status(edited, "A0001", "Em andamento", "2026-10-24")
    payload = report_payload(evaluate_goals(CURRENT), updated,
                             {"start": "2026-10-06", "end": "2026-10-19"})
    restored = load_plan_actions(export_plan_json(payload).encode("utf-8"))
    assert restored == updated
    assert restored is not updated
    assert restored[0]["status"] == "Em andamento"
    assert restored[0]["edits"][0]["old_hypothesis"] == BASE["hypothesis"]


def test_legacy_v15_export_without_edits_restores_exact_action():
    action = create_action([], **BASE)
    payload = report_payload(evaluate_goals(CURRENT), action,
                             {"start": "2026-10-06", "end": "2026-10-19"})
    assert load_plan_actions(export_plan_json(payload).encode("utf-8")) == action


@pytest.mark.parametrize("modified,expected", [
    ({"source": "kaggle_external"}, "sintética"),
    ({"schema_version": "1.4.0"}, "sintética"),
    ({"persistence": "database"}, "sintética"),
])
def test_restore_rejects_non_v15_sources(modified, expected):
    payload = report_payload([], [], {"start": "2026-10-06", "end": "2026-10-19"})
    payload.update(modified)
    with pytest.raises(ValueError, match=expected):
        load_plan_actions(export_plan_json(payload).encode("utf-8"))


@pytest.mark.parametrize("property_name,bad", [
    ("id", "DROP TABLE x"),
    ("status", "Concluída"),
    ("metric", ["csat_pct"]),
    ("owner_role", {"name": "CX"}),
    ("title", ""),
    ("hypothesis", "x" * 401),
])
def test_restore_rejects_invalid_or_forged_actions(property_name, bad):
    payload = report_payload([], create_action([], **BASE),
                             {"start": "2026-10-06", "end": "2026-10-19"})
    payload["actions"][0][property_name] = bad
    with pytest.raises(ValueError):
        load_plan_actions(export_plan_json(payload).encode("utf-8"))


def test_restore_rejects_tampered_events_or_filters():
    payload = report_payload([], create_action([], **BASE),
                             {"start": "2026-10-06", "end": "2026-10-19"})
    payload["actions"][0]["events"].append({"on": "2026-10-25", "status": "Concluída"})
    with pytest.raises(ValueError, match="Transição"):
        load_plan_actions(export_plan_json(payload).encode("utf-8"))
    payload["actions"][0]["events"].pop()
    payload["actions"][0]["scope"]["channels"] = [["Chat"]]
    with pytest.raises(ValueError, match="Filtros"):
        load_plan_actions(export_plan_json(payload).encode("utf-8"))


@pytest.mark.parametrize("data", [
    b"not json",
    b"",
    b'{"schema_version": "1.5.0-beta", "schema_version": "1.5.0-beta"}',
    b'{"schema_version": NaN}',
    b"x" * 200001,
])
def test_restore_rejects_malformed_or_oversized_files(data):
    with pytest.raises(ValueError):
        load_plan_actions(data)


def test_edit_rejects_invalid_inputs_and_earlier_dates():
    actions = create_action([], **BASE)
    with pytest.raises(ValueError, match="Ação não encontrada"):
        edit_action(actions, "A9999", title="Teste", hypothesis="Hipótese",
                    changed_on="2026-10-24")
    with pytest.raises(ValueError, match="campo obrigatório"):
        edit_action(actions, "A0001", title="", hypothesis="Hipótese",
                    changed_on="2026-10-24")
    with pytest.raises(ValueError, match="Data da edição"):
        edit_action(actions, "A0001", title="Teste", hypothesis="Hipótese",
                    changed_on="2026-09-01")

