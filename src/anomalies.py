"""Transparent weekly volume alerting on synthetic CX records.

This is descriptive threshold monitoring, not a trained predictive model.
"""
import pandas as pd
from datetime import timedelta

MIN_BASELINE = 4
MIN_BASELINE_VOLUME = 5
THRESHOLD_RATIO = 1.5
MIN_ABSOLUTE_INCREASE = 5

def weekly_volumes(df):
    """Aggregate by completed ISO Monday-Sunday weeks; fill missing weeks with zero."""
    if df.empty:
        return pd.DataFrame(columns=["topic", "week_start", "volume"])
    needed = {"date", "topic", "ticket_id"}
    if not needed.issubset(df.columns):
        raise ValueError(f"Colunas ausentes: {sorted(needed - set(df.columns))}")
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="raise")
    if data["date"].isna().any():
        raise ValueError("Datas nulas não são permitidas")
    data["week_start"] = data["date"].dt.normalize() - pd.to_timedelta(data["date"].dt.weekday, unit="D")
    aggregated = data.groupby(["topic", "week_start"], as_index=False)["ticket_id"].count().rename(columns={"ticket_id": "volume"})
    all_weeks = pd.date_range(aggregated.week_start.min(), aggregated.week_start.max(), freq="W-MON")
    index = pd.MultiIndex.from_product([sorted(data.topic.unique()), all_weeks], names=["topic", "week_start"])
    return aggregated.set_index(["topic", "week_start"]).reindex(index, fill_value=0).reset_index()

def detect_volume_anomalies(df, baseline_weeks=MIN_BASELINE, ratio=THRESHOLD_RATIO,
                            min_baseline=MIN_BASELINE_VOLUME, min_increase=MIN_ABSOLUTE_INCREASE):
    """Flag weekly topic spikes versus previous *completed* weeks.

    Excludes global edge weeks when the observed data span starts after Monday or
    ends before Sunday. A historical weekly baseline must contain enough weeks.
    No causal or statistical-significance claim is implied.
    """
    if baseline_weeks < 2 or ratio <= 1 or min_baseline < 1 or min_increase < 1:
        raise ValueError("Parâmetros de alertas inválidos")
    cols = ["topic", "week_start", "volume", "baseline_mean", "change_pct", "severity", "recommendation"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    weekly = weekly_volumes(df)
    first_date = pd.to_datetime(df["date"]).min().normalize()
    last_date = pd.to_datetime(df["date"]).max().normalize()
    first_complete = first_date if first_date.weekday() == 0 else first_date + timedelta(days=int(7-first_date.weekday()))
    # Last eligible week starts Monday and finishes no later than the last observed Sunday.
    last_sunday = last_date - timedelta(days=int((last_date.weekday() + 1) % 7))
    last_complete = last_sunday - timedelta(days=6)
    weekly = weekly[weekly.week_start.between(first_complete, last_complete)].copy()
    if weekly.empty:
        return pd.DataFrame(columns=cols)
    weekly = weekly.sort_values(["topic", "week_start"])
    baseline = weekly.groupby("topic")["volume"].transform(
        lambda s: s.shift(1).rolling(baseline_weeks, min_periods=baseline_weeks).mean())
    weekly["baseline_mean"] = baseline
    weekly["change_pct"] = 100 * (weekly.volume / weekly.baseline_mean - 1)
    flagged = weekly[(weekly.baseline_mean >= min_baseline) &
                     (weekly.volume >= weekly.baseline_mean * ratio) &
                     (weekly.volume - weekly.baseline_mean >= min_increase)].copy()
    flagged["severity"] = "Atenção"
    flagged.loc[flagged.volume >= flagged.baseline_mean * 2, "severity"] = "Alta"
    flagged["recommendation"] = "Investigar mudanças operacionais e motivos dos contatos; validar com a equipe CX."
    flagged["baseline_mean"] = flagged.baseline_mean.round(1)
    flagged["change_pct"] = flagged.change_pct.round(1)
    return flagged[cols].sort_values(["week_start", "change_pct"], ascending=[False, False]).reset_index(drop=True)
