"""Deterministic executive CX reporting using only synthetic filtered records."""
from datetime import datetime, timezone
import pandas as pd
from src.pipeline import kpis, validate_data
from src.insights import segment_insights
from src.anomalies import detect_volume_anomalies

def build_report(filtered, history=None, min_sample=30):
    """Build a serializable briefing. History supplies earlier weeks for baselines.

    Alert windows are matched by the start of the week in the filtered date range;
    channel/topic filters should be applied to history before invoking this function.
    """
    if filtered.empty:
        raise ValueError("Relatório exige pelo menos um ticket no recorte")
    errors = validate_data(filtered)
    if errors:
        raise ValueError("; ".join(errors))
    data = filtered.copy()
    data["date"] = pd.to_datetime(data["date"])
    source = data if history is None else history.copy()
    if history is not None:
        errors = validate_data(source)
        if errors:
            raise ValueError("; ".join(errors))
    source["date"] = pd.to_datetime(source["date"])
    metrics = kpis(data)
    segments = segment_insights(data, min_sample=min_sample)
    alerts = detect_volume_anomalies(source)
    start = data.date.min().normalize()
    end = data.date.max().normalize()
    # Alerts represent whole ISO weeks; use week-start as the explicit inclusion rule.
    if not alerts.empty:
        alerts = alerts[alerts.week_start.between(start,end)].copy()
    topic_counts = data.topic.value_counts()
    primary = {"topic": str(topic_counts.index[0]), "tickets": int(topic_counts.iloc[0])}
    focus = segments[segments.priority.isin(["Prioritário","Investigar"])].head(5)
    findings = []
    findings.append(f"O assunto {primary['topic']} concentra {primary['tickets']} de {len(data)} atendimentos ({100*primary['tickets']/len(data):.1f}%).")
    if len(focus):
        item = focus.iloc[0]
        findings.append(f"Segmento {item.topic} / {item.channel}: CSAT {item.csat_gap_pp:+.2f} pp e resolução {item.resolution_gap_pp:+.2f} pp versus a base filtrada; investigar, sem atribuir causalidade.")
    if len(alerts):
        a = alerts.iloc[0]
        findings.append(f"Pico heurístico em {a.topic} na semana de {a.week_start.date()}: {int(a.volume)} tickets versus média {a.baseline_mean:.1f}.")
    actions = ["Revisar os motivos e processos de atendimento com a operação CX antes de propor intervenção."]
    if len(focus):
        actions.insert(0, f"Investigar o segmento {focus.iloc[0].topic} / {focus.iloc[0].channel}, avaliando jornada, amostra e histórico.")
    if len(alerts):
        actions.append("Validar completude da ingestão e mudanças operacionais nas semanas sinalizadas.")
    return {
        "period_start": start.strftime("%Y-%m-%d"),
        "period_end": end.strftime("%Y-%m-%d"),
        "metrics": metrics,
        "top_topic": primary,
        "segment_count": int(len(segments)),
        "priority_count": int(segments.priority.eq("Prioritário").sum()) if not segments.empty else 0,
        "alerts_count": int(len(alerts)),
        "segments": segments.to_dict(orient="records"),
        "alerts": [{**row, "week_start": row["week_start"].strftime("%Y-%m-%d")} for row in alerts.to_dict(orient="records")],
        "findings": findings,
        "actions": actions,
        "limitations": [
            "Dados integralmente sintéticos; não representam clientes reais.",
            "Comparações por segmento são descritivas e não comprovam causalidade.",
            "A reincidência e o sentimento dos tickets são rótulos sintéticos; resolução não é FCR.",
            "Alertas usam limiares heurísticos e completude da ingestão não foi certificada.",
        ],
    }

def render_markdown(report, source_label="Fonte sintética"):
    """Export a readable, versioned Markdown memo (no external services)."""
    m = report["metrics"]
    lines = [
        "# CX Intelligence — Relatório Executivo",
        "",
        f"**Período:** {report['period_start']} a {report['period_end']}",
        f"**Origem:** {source_label}",
        "**Natureza:** demonstração com dados 100% sintéticos",
        "",
        "## Indicadores",
        f"- Atendimentos: {m['total_tickets']}",
        f"- CSAT positivo: {m['csat_pct']:.1f}%",
        f"- Chamados resolvidos: {m['fcr_proxy_pct']:.1f}% (não é FCR)",
        f"- Tempo médio: {m['avg_resolution_hours']:.1f} horas",
        f"- Reincidência simulada: {m['repeat_contact_rate_pct']:.1f}%",
        "",
        "## Achados descritivos",
    ]
    lines.extend(f"- {f}" for f in report["findings"])
    lines.extend(["", "## Ações propostas (hipóteses para investigação)"])
    lines.extend(f"- {a}" for a in report["actions"])
    lines.extend(["", "## Limitações metodológicas"])
    lines.extend(f"- {c}" for c in report["limitations"])
    return "\n".join(lines) + "\n"
