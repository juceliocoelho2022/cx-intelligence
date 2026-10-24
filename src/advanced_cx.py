"""CX Intelligence v1.3 — advanced *descriptive* analytics on synthetic tickets.

Not operational customer inference. Wilson intervals are illustrative sampling
uncertainty under an independence assumption, not proof of real-world accuracy.
"""
from datetime import timedelta
import math

import pandas as pd

DIMENSIONS = ("channel", "topic")
MIN_SAMPLE = 30

WEEK_COLUMNS = [
    "week_start", "tickets", "csat_positive", "csat_pct",
    "ci_lower_pct", "ci_upper_pct", "resolved_pct",
    "avg_resolution_h", "edge_week",
]
BENCHMARK_COLUMNS = [
    "dimension", "segment", "tickets", "sample_share_pct", "csat_pct",
    "ci_lower_pct", "ci_upper_pct", "resolved_pct", "avg_resolution_h",
    "baseline_csat_pct", "csat_gap_pp",
]
REPEAT_COLUMNS = [
    "segment", "eligible_tickets", "repeat_tickets", "repeat_pct",
    "ci_lower_pct", "ci_upper_pct",
]

REQUIRED = {
    "ticket_id", "customer_id", "date", "topic", "channel",
    "csat", "resolved", "resolution_hours",
}


def wilson_95(positive, total):
    """Wilson score interval, expressed as percentage; no interval for n=0."""
    if (isinstance(positive, bool) or isinstance(total, bool)
            or int(positive) != positive or int(total) != total
            or total < 0 or positive < 0 or positive > total):
        raise ValueError("Contagens inválidas para intervalo de Wilson")
    if total == 0:
        return (None, None)
    p = positive / total
    z = 1.959963984540054
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    half = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    return round(100 * max(0, center - half), 2), round(
        100 * min(1, center + half), 2)


def _validated(df):
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Os dados devem ser um DataFrame")
    missing = REQUIRED.difference(df.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing)}")
    if df.empty:
        return df.copy()
    if df[list(REQUIRED)].isna().any().any() or not df.ticket_id.is_unique:
        raise ValueError("Há nulos obrigatórios ou ticket_id duplicado")
    if not df.csat.isin([1, 2, 3, 4, 5]).all():
        raise ValueError("CSAT deve estar entre 1 e 5")
    if not df.resolved.isin([0, 1]).all():
        raise ValueError("resolved deve ser binário")
    if not pd.to_numeric(df.resolution_hours, errors="coerce").ge(0).all():
        raise ValueError("resolution_hours inválido")
    if not df.customer_id.astype(str).str.strip().ne("").all():
        raise ValueError("customer_id vazio")
    result = df.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise").dt.normalize()
    if result.date.dt.tz is not None:
        raise ValueError("O esquema utiliza datas civis sem fuso horário")
    return result


def weekly_cx_trends(df):
    """Weekly CSAT, resolution and volume. Boundary weeks are marked explicitly."""
    data = _validated(df)
    if data.empty:
        return pd.DataFrame(columns=WEEK_COLUMNS)
    data["week_start"] = data.date - pd.to_timedelta(data.date.dt.weekday, unit="D")
    weekly = data.groupby("week_start", as_index=False).agg(
        tickets=("ticket_id", "size"),
        csat_positive=("csat", lambda x: int(x.ge(4).sum())),
        resolved_count=("resolved", "sum"),
        avg_resolution_h=("resolution_hours", "mean"),
    )
    bounds = [wilson_95(int(row.csat_positive), int(row.tickets))
              for row in weekly.itertuples(index=False)]
    weekly["ci_lower_pct"] = [pair[0] for pair in bounds]
    weekly["ci_upper_pct"] = [pair[1] for pair in bounds]
    weekly["csat_pct"] = (100 * weekly.csat_positive / weekly.tickets).round(2)
    weekly["resolved_pct"] = (100 * weekly.resolved_count / weekly.tickets).round(2)
    weekly["avg_resolution_h"] = weekly.avg_resolution_h.round(2)
    minimum, maximum = data.date.min(), data.date.max()
    weekly["edge_week"] = ((weekly.week_start < minimum)
                           | (weekly.week_start + timedelta(days=6) > maximum))
    return weekly.drop(columns="resolved_count")[WEEK_COLUMNS]


def segment_benchmarks(df, dimension="channel", min_sample=MIN_SAMPLE):
    """Descriptive part-to-whole comparison; intervals do NOT test gap significance."""
    if dimension not in DIMENSIONS:
        raise ValueError("Dimensão deve ser canal ou assunto")
    if not isinstance(min_sample, int) or min_sample < 1:
        raise ValueError("Amostra mínima inválida")
    data = _validated(df)
    if data.empty:
        return pd.DataFrame(columns=BENCHMARK_COLUMNS)
    overall = 100 * data.csat.ge(4).mean()
    grouped = data.groupby(dimension, as_index=False).agg(
        tickets=("ticket_id", "size"),
        csat_positive=("csat", lambda s: int(s.ge(4).sum())),
        resolved_pct=("resolved", lambda s: float(100 * s.mean())),
        avg_resolution_h=("resolution_hours", "mean"),
    )
    grouped = grouped[grouped.tickets.ge(min_sample)].copy()
    if grouped.empty:
        return pd.DataFrame(columns=BENCHMARK_COLUMNS)
    grouped["dimension"] = dimension
    grouped["segment"] = grouped[dimension]
    grouped["sample_share_pct"] = (100 * grouped.tickets / len(data)).round(2)
    grouped["csat_pct"] = (100 * grouped.csat_positive / grouped.tickets).round(2)
    grouped["baseline_csat_pct"] = round(overall, 2)
    grouped["csat_gap_pp"] = (grouped.csat_pct - grouped.baseline_csat_pct).round(2)
    grouped["resolved_pct"] = grouped.resolved_pct.round(2)
    grouped["avg_resolution_h"] = grouped.avg_resolution_h.round(2)
    bounds = [wilson_95(int(row.csat_positive), int(row.tickets))
              for row in grouped.itertuples(index=False)]
    grouped["ci_lower_pct"] = [pair[0] for pair in bounds]
    grouped["ci_upper_pct"] = [pair[1] for pair in bounds]
    return (grouped[BENCHMARK_COLUMNS]
            .sort_values(["csat_gap_pp", "tickets"], ascending=[True, False])
            .reset_index(drop=True))


def observed_repeat_30d(universe, cohort=None, dimension="channel", days=30,
                        min_sample=MIN_SAMPLE):
    """Later DISTINCT-DATE ticket by same customer, within 30 calendar days.

    Entire universe supplies follow-up, even when the displayed cohort is
    filtered by date/channel/topic. Exclude cohort tickets after latest date
    minus 30 days (right censoring). Not the synthetic repeat_contact_30d label.
    Same-day contacts are excluded: this dataset has no within-day timestamps.
    """
    if dimension not in DIMENSIONS:
        raise ValueError("Dimensão inválida")
    if not isinstance(days, int) or not 1 <= days <= 365:
        raise ValueError("Janela inválida")
    if not isinstance(min_sample, int) or min_sample < 1:
        raise ValueError("Amostra mínima inválida")
    all_tickets = _validated(universe)
    if cohort is None:
        candidate = all_tickets
    else:
        if not isinstance(cohort, pd.DataFrame) or "ticket_id" not in cohort:
            raise ValueError("Coorte deve conter ticket_id")
        if cohort.ticket_id.duplicated().any() or cohort.ticket_id.isna().any():
            raise ValueError("Coorte possui ticket_id inválido")
        if not cohort.ticket_id.isin(all_tickets.ticket_id).all():
            raise ValueError("Coorte contém tickets fora do universo de observação")
        candidate = all_tickets[all_tickets.ticket_id.isin(cohort.ticket_id)]
    total_cohort = len(candidate)
    empty = pd.DataFrame(columns=REPEAT_COLUMNS)
    if all_tickets.empty or candidate.empty:
        return {
            "cohort_tickets": total_cohort, "eligible_tickets": 0,
            "censored_tickets": total_cohort, "repeat_tickets": 0,
            "repeat_pct": None, "as_of": None, "cutoff": None, "groups": empty,
        }
    as_of = all_tickets.date.max()
    cutoff = as_of - timedelta(days=days)
    eligible = candidate[candidate.date.le(cutoff)].copy()
    if eligible.empty:
        return {
            "cohort_tickets": total_cohort, "eligible_tickets": 0,
            "censored_tickets": total_cohort, "repeat_tickets": 0,
            "repeat_pct": None, "as_of": as_of.date().isoformat(),
            "cutoff": cutoff.date().isoformat(), "groups": empty,
        }
    # One row per customer/calendar day. shift(-1) gets the next strictly later day.
    customer_days = (all_tickets[["customer_id", "date"]].drop_duplicates()
                     .sort_values(["customer_id", "date"]))
    customer_days["next_contact"] = customer_days.groupby("customer_id").date.shift(-1)
    eligible = eligible.merge(customer_days, on=["customer_id", "date"], how="left", validate="many_to_one")
    eligible["has_repeat"] = (eligible.next_contact.notna()
                              & eligible.next_contact.le(eligible.date + timedelta(days=days)))
    count = int(eligible.has_repeat.sum())
    grouped = eligible.groupby(dimension, as_index=False).agg(
        eligible_tickets=("ticket_id", "size"),
        repeat_tickets=("has_repeat", "sum"),
    )
    grouped = grouped[grouped.eligible_tickets.ge(min_sample)].copy()
    if not grouped.empty:
        grouped["segment"] = grouped[dimension]
        grouped["repeat_pct"] = (100 * grouped.repeat_tickets / grouped.eligible_tickets).round(2)
        intervals = [wilson_95(int(x.repeat_tickets), int(x.eligible_tickets))
                     for x in grouped.itertuples(index=False)]
        grouped["ci_lower_pct"] = [v[0] for v in intervals]
        grouped["ci_upper_pct"] = [v[1] for v in intervals]
        grouped = (grouped[REPEAT_COLUMNS]
                   .sort_values(["repeat_pct", "eligible_tickets"], ascending=[False, False])
                   .reset_index(drop=True))
    else:
        grouped = empty
    return {
        "cohort_tickets": total_cohort, "eligible_tickets": len(eligible),
        "censored_tickets": total_cohort - len(eligible),
        "repeat_tickets": count, "repeat_pct": round(100 * count / len(eligible), 2),
        "as_of": as_of.date().isoformat(), "cutoff": cutoff.date().isoformat(),
        "groups": grouped,
    }
