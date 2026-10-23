"""Descriptive CX segment investigations. No causal inference."""
import pandas as pd

MIN_SEGMENT_SIZE = 30
MIN_CSAT_GAP_PP = 5.0
MIN_RESOLUTION_GAP_PP = 5.0

def segment_insights(df, min_sample=MIN_SEGMENT_SIZE, min_gap_pp=MIN_CSAT_GAP_PP):
    """Compare topic/channel segments to overall population with transparent denominators.

    Reports descriptive gaps, not confidence intervals or causal attribution.
    """
    columns=["topic","channel","tickets","csat_pct","resolved_pct","avg_resolution_h",
             "reference_csat_pct","csat_gap_pp","resolution_gap_pp","priority","recommendation"]
    required={"topic","channel","ticket_id","csat","resolved","resolution_hours"}
    missing=required.difference(df.columns)
    if missing:
        raise ValueError(f"Campos ausentes: {sorted(missing)}")
    if min_sample < 1 or min_gap_pp < 0:
        raise ValueError("Parâmetros inválidos")
    if df.empty:
        return pd.DataFrame(columns=columns)
    if df[list(required)].isna().any().any():
        raise ValueError("Campos obrigatórios contêm nulos")
    if not df.csat.between(1,5).all() or not df.resolved.isin([0,1]).all() or not df.resolution_hours.ge(0).all():
        raise ValueError("Indicadores com domínio inválido")
    baseline_csat=100*df.csat.ge(4).mean()
    baseline_resolution=100*df.resolved.mean()
    summary=df.groupby(["topic","channel"],as_index=False).agg(
        tickets=("ticket_id","size"),
        csat_pct=("csat",lambda x:100*x.ge(4).mean()),
        resolved_pct=("resolved",lambda x:100*x.mean()),
        avg_resolution_h=("resolution_hours","mean"))
    summary=summary[summary.tickets>=min_sample].copy()
    if summary.empty:
        return pd.DataFrame(columns=columns)
    summary["reference_csat_pct"]=baseline_csat
    summary["csat_gap_pp"]=summary.csat_pct-baseline_csat
    summary["resolution_gap_pp"]=summary.resolved_pct-baseline_resolution
    summary["priority"]="Monitorar"
    critical=(summary.csat_gap_pp<=-min_gap_pp)&(summary.resolution_gap_pp<=-MIN_RESOLUTION_GAP_PP)
    attention=(summary.csat_gap_pp<=-min_gap_pp)|(summary.resolution_gap_pp<=-MIN_RESOLUTION_GAP_PP)
    summary.loc[attention,"priority"]="Investigar"
    summary.loc[critical,"priority"]="Prioritário"
    summary["recommendation"]="Acompanhar tendência e validar tamanho da amostra."
    summary.loc[attention,"recommendation"]="Investigar jornada, scripts de atendimento e motivos da diferença; comparar períodos."
    summary.loc[critical,"recommendation"]="Priorizar diagnóstico com operação CX; revisar motivos e fluxo de resolução antes de agir."
    for col in ["csat_pct","resolved_pct","avg_resolution_h","reference_csat_pct","csat_gap_pp","resolution_gap_pp"]:
        summary[col]=summary[col].round(2)
    ranking={"Prioritário":0,"Investigar":1,"Monitorar":2}
    summary["_rank"]=summary.priority.map(ranking)
    return summary.sort_values(["_rank","csat_gap_pp","tickets"],ascending=[True,True,False]).drop(columns="_rank")[columns].reset_index(drop=True)
