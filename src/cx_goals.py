"""CX Intelligence v1.5 beta — synthetic-only CX goals and action tracking.

Pure business logic. No database writes, automation, real client data, or
unverified impact attribution. Streamlit manages volatile per-session state.
"""
from __future__ import annotations

from datetime import date
import json
import math

METRICS = {
    "csat_pct": {"label": "CSAT positivo", "direction": "min", "unit": "pp", "default": 70.0, "bounds": (0.0, 100.0)},
    "resolved_pct": {"label": "Tickets resolvidos", "direction": "min", "unit": "pp", "default": 90.0, "bounds": (0.0, 100.0)},
    "avg_resolution_hours": {"label": "Tempo médio de atendimento", "direction": "max", "unit": "h", "default": 10.0, "bounds": (0.0, 96.0)},
}
ROLES = ("CX", "Atendimento", "Operações", "Produtos", "Tecnologia")
STATUSES = ("Planejada", "Em andamento", "Concluída")
TRANSITIONS = {
    "Planejada": {"Em andamento"},
    "Em andamento": {"Concluída", "Planejada"},
    "Concluída": set(),
}
DISCLAIMER = (
    "Simulação de acompanhamento de gestão com dados 100% sintéticos. "
    "Metas são exemplos configuráveis; ações não foram executadas por equipes reais. "
    "Concluir uma ação não comprova melhoria de KPI, causalidade ou impacto operacional."
)


def _number(value, lower, upper, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} deve ser numérico")
    number = float(value)
    if not math.isfinite(number) or not lower <= number <= upper:
        raise ValueError(f"{name} fora do intervalo permitido")
    return number


def _date(value, label):
    try:
        if isinstance(value, date):
            return value.isoformat()
        if not isinstance(value, str):
            raise ValueError()
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError()
        return parsed.isoformat()
    except ValueError:
        raise ValueError(f"{label}: data ISO inválida") from None


def evaluate_goals(current, targets=None, min_tickets=30, current_covered=True):
    """Score user-proposed targets against ONLY the current synthetic BI period.

    Positive gap_to_target means missing the goal; 0 means met.
    Coverage of a whole date range is an assumption, not ingestion certification.
    """
    if type(min_tickets) is not int or min_tickets < 1:
        raise ValueError("Mínimo de tickets inválido")
    if type(current_covered) is not bool:
        raise ValueError("Cobertura da janela inválida")
    if not isinstance(current, dict):
        raise ValueError("KPIs devem ser um dicionário")
    count = current.get("tickets")
    if type(count) is not int or count < 0:
        raise ValueError("Número de tickets inválido")
    if targets is None:
        targets = {}
    if not isinstance(targets, dict) or set(targets).difference(METRICS):
        raise ValueError("Metas contêm métricas desconhecidas")
    state = ("incomplete_window" if not current_covered else
             "no_data" if count == 0 else
             "insufficient_sample" if count < min_tickets else "eligible")
    result = []
    for key, cfg in METRICS.items():
        lo, hi = cfg["bounds"]
        target = _number(targets.get(key, cfg["default"]), lo, hi, key + " meta")
        value = current.get(key)
        actual = _number(value, 0.0, hi if key != "avg_resolution_hours" else float("inf"),
                         key + " observado") if value is not None else None
        if state != "eligible":
            status, gap, margin = state, None, None
        elif actual is None:
            status, gap, margin = "missing_metric", None, None
        else:
            # positive margin = target met; gap = shortfall, never negative
            margin = round(actual-target if cfg["direction"] == "min" else target-actual, 2)
            gap = round(max(0.0, -margin), 2)
            status = "met" if margin >= 0 else "attention"
        result.append({
            "metric": key, "label": cfg["label"], "direction": cfg["direction"],
            "unit": cfg["unit"], "target": target, "observed": actual,
            "status": status, "gap_to_target": gap, "signed_margin": margin,
            "tickets": count, "min_tickets": min_tickets,
        })
    return result


def _short_text(value, label, limit, required=True):
    if not isinstance(value, str):
        raise ValueError(f"{label}: texto inválido")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{label}: campo obrigatório. Preencha com uma frase que explique o que deseja investigar.")
    if len(value) > limit:
        raise ValueError(f"{label}: texto com {len(value)} caracteres; o máximo permitido é {limit}.")
    # Reject control characters; exporting CSV/Markdown and displaying text must stay safe.
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"{label}: caracteres de controle não permitidos")
    return value


def create_action(actions, *, metric, title, hypothesis, role, due_date, created_on,
                  period_start, period_end, topics=(), channels=()):
    """Return a NEW list; IDs and contents are synthetic proposals in this session."""
    if not isinstance(actions, list):
        raise ValueError("Lista de ações inválida")
    if metric not in METRICS or role not in ROLES:
        raise ValueError("Métrica ou área responsável inválida")
    title = _short_text(title, "Título", 120)
    hypothesis = _short_text(hypothesis, "Hipótese de investigação", 400)
    created = _date(created_on, "Criação")
    due = _date(due_date, "Prazo")
    if due < created:
        raise ValueError("Prazo não pode anteceder a criação")
    start, end = _date(period_start, "Início do recorte"), _date(period_end, "Fim do recorte")
    if start > end:
        raise ValueError("Recorte inválido")
    def scope(items):
        if not isinstance(items, (list, tuple)):
            raise ValueError("Escopo inválido")
        return sorted({_short_text(s, "Filtro", 80) for s in items})
    ids = [a.get("id", "") for a in actions]
    if len(ids) != len(set(ids)) or any(not isinstance(x, str) or not x.startswith("A") or not x[1:].isdigit() for x in ids):
        raise ValueError("IDs de ações inválidos")
    next_id = max((int(x[1:]) for x in ids), default=0) + 1
    action = {
        "id": f"A{next_id:04d}", "metric": metric, "title": title,
        "hypothesis": hypothesis, "owner_role": role, "due_date": due,
        "created_on": created, "status": "Planejada",
        "scope": {"period_start": start, "period_end": end,
                  "topics": scope(topics), "channels": scope(channels)},
        "events": [{"on": created, "status": "Planejada"}],
    }
    return [*actions, action]


def change_action_status(actions, action_id, new_status, changed_on):
    """Validate state transition and return a NEW list, without rewriting history."""
    if new_status not in STATUSES:
        raise ValueError("Status desconhecido")
    when = _date(changed_on, "Data da mudança")
    if not isinstance(actions, list) or not any(a.get("id") == action_id for a in actions):
        raise ValueError("Ação não encontrada")
    updated = []
    for a in actions:
        if a["id"] != action_id:
            updated.append(a)
            continue
        if new_status not in TRANSITIONS[a["status"]]:
            raise ValueError("Transição de status não permitida")
        if when < a["events"][-1]["on"]:
            raise ValueError("A mudança não pode anteceder o evento anterior")
        updated.append({**a, "status": new_status,
                        "events": [*a["events"], {"on": when, "status": new_status}]})
    return updated


def report_payload(goals, actions, period):
    """JSON-ready, deterministic snapshot. No persistence or real execution claim."""
    if not isinstance(goals, list) or not isinstance(actions, list):
        raise ValueError("Conteúdo do relatório inválido")
    if not isinstance(period, dict) or "start" not in period or "end" not in period:
        raise ValueError("Período inválido")
    start, end = _date(period["start"], "Início"), _date(period["end"], "Fim")
    if start > end:
        raise ValueError("Período inválido")
    return {
        "schema_version": "1.5.0-beta", "source": "synthetic_primary_only",
        "disclaimer": DISCLAIMER, "period": {"start": start, "end": end},
        "goals": goals, "actions": actions, "persistence": "session_only",
    }


def export_plan_json(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def export_plan_markdown(payload):
    def cell(v):
        return (str(v).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace("\\", "\\\\")
                .replace("|", "\\|").replace("\n", " "))
    p = payload["period"]
    lines = [
        "# CX Intelligence — Metas e Plano de Ação | v1.5 beta",
        "", f"**Período analisado:** {p['start']} a {p['end']}",
        "", "**Aviso:** " + payload["disclaimer"], "",
        "## Metas ilustrativas", "| Indicador | Observado | Meta | Status | Distância |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for goal in payload["goals"]:
        observed = "N/A" if goal["observed"] is None else f'{goal["observed"]:.2f}'
        gap = "N/A" if goal["gap_to_target"] is None else f'{goal["gap_to_target"]:.2f} {goal["unit"]}'
        lines.append(f'| {cell(goal["label"])} | {observed} | {goal["target"]:.2f} | '
                     f'{goal["status"]} | {gap} |')
    lines.extend(["", "## Ações propostas (não representam execução real)",
                  "| ID | Métrica | Ação | Área fictícia | Prazo | Estado |",
                  "| --- | --- | --- | --- | --- | --- |"])
    for a in payload["actions"]:
        lines.append(f'| {cell(a["id"])} | {cell(METRICS[a["metric"]]["label"])} | '
                     f'{cell(a["title"])} | {cell(a["owner_role"])} | '
                     f'{a["due_date"]} | {a["status"]} |')
    lines.extend(["", "As metas não constituem SLA contratual. Mudanças de status não demonstram "
                  "causalidade, redução de reclamações ou melhoria efetiva.",
                  "", "**Persistência:** apenas na sessão aberta; exporte o arquivo para conservar o plano."])
    return "\n".join(lines) + "\n"
