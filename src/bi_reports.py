"""CX Intelligence v1.4 — deterministic, synthetic-only period-over-period BI.

Calendar windows are inclusive and equal-length. Comparisons are withheld when
the full previous window predates the available observation history.
No NLP, causal inference, operational forecasting, or external Kaggle data.
"""
from datetime import timedelta
from html import escape
from math import isfinite

import pandas as pd

from src.pipeline import validate_data

METRICS = (
    ("tickets", "Atendimentos", "pct"),
    ("csat_pct", "CSAT positivo", "pp"),
    ("resolved_pct", "Resolvidos", "pp"),
    ("avg_resolution_hours", "Tempo médio (h)", "h"),
)
VALID_DIMENSIONS = ("channel", "topic")


def _prepare(df):
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Esperado DataFrame com tickets sintéticos")
    problems = validate_data(df)
    if problems:
        raise ValueError("; ".join(problems))
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise")
    if out.date.dt.tz is not None:
        raise ValueError("Datas devem ser civis, sem fuso horário")
    out["date"] = out.date.dt.normalize()
    return out


def _kpis(data):
    n = len(data)
    return {
        "tickets": int(n),
        "csat_pct": round(100 * float(data.csat.ge(4).mean()), 2) if n else None,
        "resolved_pct": round(100 * float(data.resolved.mean()), 2) if n else None,
        "avg_resolution_hours": round(float(data.resolution_hours.mean()), 2) if n else None,
    }


def _diffs(current, previous, eligible):
    result = []
    for key, label, unit in METRICS:
        a, b = current[key], previous[key]
        delta = None
        if eligible and a is not None and b is not None:
            if unit == "pct":
                # Relative change undefined when previous count is zero.
                delta = round(100 * (a - b) / b, 2) if b else None
            else:
                delta = round(a - b, 2)
        result.append({
            "metric": key, "label": label, "current": a, "previous": b,
            "delta": delta, "delta_unit": unit,
        })
    return result


def compare_periods(universe, end_date, window_days=14, dimension="channel",
                    topics=None, channels=None, min_sample=30):
    """Compare adjacent, equal calendar-day windows for the same segment filters.

    Baseline observations are selected BEFORE applying a UI date filter.
    Coverage is assessed against the unfiltered universe date range, not an
    individual channel/topic (an empty segment period is otherwise meaningful).
    """
    if type(window_days) is not int or window_days not in (7, 14, 30):
        raise ValueError("Janela deve ser de 7, 14 ou 30 dias")
    if dimension not in VALID_DIMENSIONS:
        raise ValueError("Dimensão deve ser canal ou assunto")
    if type(min_sample) is not int or min_sample < 1:
        raise ValueError("Amostra mínima inválida")
    data = _prepare(universe)
    if data.empty:
        raise ValueError("Comparação exige histórico sintético não vazio")
    end = pd.Timestamp(end_date)
    if pd.isna(end) or end.tzinfo is not None:
        raise ValueError("Data final inválida ou com fuso")
    end = end.normalize()
    first, last = data.date.min(), data.date.max()
    if end < first or end > last:
        raise ValueError("Data final deve estar dentro da série observada")
    current_start = end - timedelta(days=window_days-1)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=window_days-1)
    complete_previous = first <= previous_start
    complete_current = last >= end and first <= current_start

    scope = data
    if topics is not None:
        scope = scope[scope.topic.isin(list(topics))]
    if channels is not None:
        scope = scope[scope.channel.isin(list(channels))]
    current = scope[scope.date.between(current_start, end)]
    previous = scope[scope.date.between(previous_start, previous_end)]
    current_kpi, prev_kpi = _kpis(current), _kpis(previous)
    comparison_valid = bool(complete_previous and complete_current and len(previous) and len(current))
    if not complete_previous or not complete_current:
        status = "insufficient_history"
    elif previous.empty:
        status = "empty_baseline"
    elif current.empty:
        status = "empty_current"
    else:
        status = "comparable"

    groups = []
    excluded = 0
    if comparison_valid:
        values = sorted(set(current[dimension].unique()) | set(previous[dimension].unique()))
        for val in values:
            now = current[current[dimension].eq(val)]
            then = previous[previous[dimension].eq(val)]
            if len(now) < min_sample or len(then) < min_sample:
                excluded += 1
                continue
            m_now, m_then = _kpis(now), _kpis(then)
            groups.append({
                "segment": str(val), "dimension": dimension,
                "current_tickets": len(now), "previous_tickets": len(then),
                "current_csat_pct": m_now["csat_pct"],
                "previous_csat_pct": m_then["csat_pct"],
                "csat_delta_pp": round(m_now["csat_pct"] - m_then["csat_pct"], 2),
                "resolved_delta_pp": round(m_now["resolved_pct"] - m_then["resolved_pct"], 2),
                "hours_delta": round(m_now["avg_resolution_hours"] - m_then["avg_resolution_hours"], 2),
            })
    groups.sort(key=lambda item: (item["csat_delta_pp"], item["segment"]))
    return {
        "period_current": {"start": current_start.date().isoformat(), "end": end.date().isoformat()},
        "period_previous": {"start": previous_start.date().isoformat(), "end": previous_end.date().isoformat()},
        "window_days": window_days, "status": status,
        "scope_tickets": int(len(scope)), "current": current_kpi, "previous": prev_kpi,
        "metrics": _diffs(current_kpi, prev_kpi, comparison_valid),
        "dimension": dimension, "min_sample": min_sample, "segments": groups,
        "segments_excluded_small_sample": excluded,
        "limitations": [
            "Dados exclusivamente sintéticos, não representativos de clientes reais.",
            "Janelas civis adjacentes de igual duração; não há ajuste sazonal ou causal.",
            "A cobertura é estimada pelas datas extremas da base; não certifica ingestão completa.",
            "CSAT positivo considera notas 4 ou 5 no gerador sintético.",
            "Resolvidos não é FCR e o tempo médio está em horas.",
            "Variação de volume é percentual relativa à base anterior; sem base, fica indisponível.",
            "Variações de CSAT e resolução são pontos percentuais; nenhuma diferença é causal ou teste de hipótese.",
            "Segmentos só são exibidos quando AMBOS os períodos alcançam o mínimo amostral.",
        ],
    }


def _value(v, unit):
    if v is None:
        return "N/A"
    if unit == "count":
        return f"{v:,}".replace(",", ".")
    if unit == "pct":
        return f"{v:.2f}%"
    if unit == "h":
        return f"{v:.2f} h"
    return str(v)


def _delta(metric):
    if metric["delta"] is None:
        return "N/A"
    suffix = {"pct": "%", "pp": " pp", "h": " h"}[metric["delta_unit"]]
    return f'{metric["delta"]:+.2f}{suffix}'


def _findings(report):
    if report["status"] != "comparable":
        return ["Comparação não calculada: histórico ou volume insuficiente para períodos equivalentes."]
    counts = next(m for m in report["metrics"] if m["metric"] == "tickets")
    lines = [f"Volume: {counts['current']} versus {counts['previous']} tickets ({_delta(counts)})."]
    if report["segments"]:
        lowest = report["segments"][0]
        lines.append(
            f"Segmento {lowest['segment']}: variação de CSAT {lowest['csat_delta_pp']:+.2f} pp "
            "entre os períodos; investigar mix, amostra e processos, sem inferir causalidade."
        )
    else:
        lines.append("Nenhum segmento atingiu a amostra mínima nos dois períodos.")
    return lines


def render_bi_markdown(report):
    """Stable executive Markdown, with transparent unavailable comparisons."""
    a, b = report["period_current"], report["period_previous"]
    lines = [
        "# CX Intelligence — Business Intelligence | v1.4 (beta)",
        "",
        "**Dados: 100% sintéticos; nenhuma inferência sobre clientes reais.**",
        f"**Atual ({report['window_days']} dias):** {a['start']} a {a['end']}",
        f"**Anterior ({report['window_days']} dias):** {b['start']} a {b['end']}",
        f"**Comparabilidade:** {report['status']}",
        "",
        "## Indicadores comparativos",
        "| KPI | Atual | Anterior | Variação |",
        "| --- | ---: | ---: | ---: |",
    ]
    for m in report["metrics"]:
        k = m["metric"]
        unit = "count" if k == "tickets" else "h" if k == "avg_resolution_hours" else "pct"
        # Without complete coverage, never present previous as a valid comparator.
        prior = _value(m["previous"], unit) if report["status"] == "comparable" else "N/A"
        lines.append(f"| {m['label']} | {_value(m['current'], unit)} | {prior} | {_delta(m)} |")
    lines.extend(["", "## Achados descritivos"])
    lines.extend(f"- {finding}" for finding in _findings(report))
    lines.extend(["", "## Segmentos comparáveis (mesma amostra mínima nos dois períodos)"])
    if report["segments"]:
        lines.extend(["| Segmento | Atual | Anterior | CSAT (pp) | Resolução (pp) |",
                      "| --- | ---: | ---: | ---: | ---: |"])
        for item in report["segments"]:
            # Prevent a segment label from breaking Markdown tables.
            label = item["segment"].replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {label} | {item['current_tickets']} | {item['previous_tickets']} | "
                         f"{item['csat_delta_pp']:+.2f} | {item['resolved_delta_pp']:+.2f} |")
    else:
        lines.append("Sem segmentos comparáveis com a amostra mínima selecionada.")
    lines.extend(["", "## Ações sugeridas (não automatizadas)",
                  "- Revisar processos e possíveis mudanças no mix de atendimentos antes de propor intervenção.",
                  "- Confirmar integridade, cobertura temporal e variações de volume com a operação.",
                  "", "## Limitações e cautelas"])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


def render_bi_html(report):
    """Self-contained print-friendly HTML; all variable text is HTML-escaped."""
    a, b = report["period_current"], report["period_previous"]
    h = lambda val: escape(str(val), quote=True)
    rows = []
    for m in report["metrics"]:
        unit = "count" if m["metric"] == "tickets" else "h" if m["metric"] == "avg_resolution_hours" else "pct"
        previous = _value(m["previous"], unit) if report["status"] == "comparable" else "N/A"
        rows.append("<tr>" + "".join(
            f"<td>{h(x)}</td>" for x in
            [m["label"], _value(m["current"], unit), previous, _delta(m)]) + "</tr>")
    group_rows = "".join(
        "<tr>" + "".join(f"<td>{h(v)}</td>" for v in
        [x["segment"], x["current_tickets"], x["previous_tickets"],
         f'{x["csat_delta_pp"]:+.2f} pp', f'{x["resolved_delta_pp"]:+.2f} pp']) + "</tr>"
        for x in report["segments"]
    )
    findings = "".join(f"<li>{h(x)}</li>" for x in _findings(report))
    limitations = "".join(f"<li>{h(x)}</li>" for x in report["limitations"])
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CX Intelligence — Relatório BI v1.4</title>
<style>
:root{{font-family:Arial,Helvetica,sans-serif;color:#152338;background:#eef3f8}}
body{{margin:0 auto;max-width:920px;padding:28px}}
main{{background:#fff;border-radius:16px;padding:28px;box-shadow:0 4px 20px #12243a16}}
h1{{border-bottom:4px solid #ff792d;padding-bottom:14px}} h2{{margin-top:28px}}
strong.notice{{display:block;background:#fff2e9;border-left:4px solid #ff792d;padding:14px}}
table{{width:100%;border-collapse:collapse;margin:16px 0}} th,td{{border-bottom:1px solid #cdd7e1;padding:9px;text-align:left}}
th{{background:#e6eff9}}li{{line-height:1.6}}.hint{{color:#526172}}.scroll{{overflow-x:auto}}
@media print{{:root{{background:#fff}}body{{padding:0}}main{{box-shadow:none}}}}
</style></head><body><main>
<h1>CX Intelligence — Business Intelligence v1.4 (beta)</h1>
<strong class="notice">Dados 100% sintéticos. Sem clientes reais, inferência causal ou decisões automatizadas.</strong>
<p><b>Período atual:</b> {h(a["start"])} a {h(a["end"])}<br>
<b>Anterior:</b> {h(b["start"])} a {h(b["end"])}<br>
<b>Comparabilidade:</b> {h(report["status"])}</p>
<h2>Indicadores comparativos</h2><div class="scroll"><table>
<thead><tr><th>Indicador</th><th>Atual</th><th>Anterior</th><th>Variação</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<h2>Principais achados</h2><ul>{findings}</ul>
<h2>Segmentos comparáveis</h2>
<p class="hint">Mínimo de {h(report["min_sample"])} tickets em cada período, por {h(report["dimension"])}.</p>
<div class="scroll"><table><thead><tr><th>Segmento</th><th>Atual</th><th>Anterior</th>
<th>CSAT Δ</th><th>Resolução Δ</th></tr></thead><tbody>{group_rows}</tbody></table></div>
<h2>Próximas investigações</h2><ul><li>Investigar mix de atendimentos e jornada antes de intervir.</li>
<li>Validar cobertura e mudanças operacionais com especialistas de CX.</li></ul>
<h2>Limitações</h2><ul>{limitations}</ul>
<p class="hint">Relatório gerado deterministicamente por regras locais. Pode ser impresso como PDF no navegador.</p>
</main></body></html>"""
