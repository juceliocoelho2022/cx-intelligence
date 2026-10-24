"""Advanced CX contracts: no real customers, no need for running PostgreSQL."""
import pandas as pd
import pytest

from src.advanced_cx import (
    observed_repeat_30d, segment_benchmarks, weekly_cx_trends, wilson_95,
    WEEK_COLUMNS, BENCHMARK_COLUMNS, REPEAT_COLUMNS,
)
from src.pipeline import generate_data


def record(ticket, customer, day, channel="Chat", topic="Pix", csat=5, resolved=1):
    return {
        "ticket_id": ticket, "customer_id": customer, "date": day,
        "channel": channel, "topic": topic, "csat": csat,
        "resolved": resolved, "resolution_hours": 2.0,
        "repeat_contact_30d": 0,
    }


def test_wilson_interval_endpoints_and_empty():
    assert wilson_95(0, 0) == (None, None)
    assert wilson_95(0, 5)[0] == 0.0
    assert wilson_95(5, 5)[1] == 100.0
    lo, hi = wilson_95(5, 10)
    assert lo < 50 < hi
    assert round((lo + hi) / 2, 2) == 50.0


@pytest.mark.parametrize("successes,total", [(-1, 5), (6, 5), (1, -1), (0.5, 5), (True, 5)])
def test_wilson_rejects_bad_counts(successes, total):
    with pytest.raises(ValueError):
        wilson_95(successes, total)


def test_weekly_aggregates_mon_monday_and_marks_boundary_weeks():
    df = pd.DataFrame([
        record("T1", "C1", "2026-08-01", csat=5),
        record("T2", "C2", "2026-08-02", csat=2, resolved=0),
        record("T3", "C3", "2026-08-03", csat=4),
    ])
    weeks = weekly_cx_trends(df)
    assert list(weeks.columns) == WEEK_COLUMNS
    assert len(weeks) == 2
    assert weeks.iloc[0].week_start.strftime("%Y-%m-%d") == "2026-07-27"
    assert weeks.iloc[0].tickets == 2
    assert weeks.iloc[0].csat_pct == 50
    assert weeks.iloc[0].resolved_pct == 50
    assert bool(weeks.iloc[0].edge_week)
    assert bool(weeks.iloc[1].edge_week)


def test_weekly_full_middle_week_not_marked_boundary():
    df = generate_data(n=700, seed=2)
    weeks = weekly_cx_trends(df)
    assert weeks.tickets.sum() == 700
    assert len(weeks[~weeks.edge_week]) >= 1
    assert weeks.ci_lower_pct.le(weeks.csat_pct).all()
    assert weeks.csat_pct.le(weeks.ci_upper_pct).all()


def test_segment_comparison_uses_filtered_baseline_not_global():
    df = pd.DataFrame([
        record("T1", "C1", "2026-08-01", "Chat", csat=5),
        record("T2", "C2", "2026-08-02", "Chat", csat=5),
        record("T3", "C3", "2026-08-03", "Email", csat=1),
        record("T4", "C4", "2026-08-04", "Email", csat=1),
    ])
    result = segment_benchmarks(df, min_sample=2)
    assert list(result.columns) == BENCHMARK_COLUMNS
    assert len(result) == 2
    assert result.baseline_csat_pct.eq(50).all()
    assert result.iloc[0].segment == "Email"
    assert result.iloc[0].csat_gap_pp == -50
    assert result.iloc[1].csat_gap_pp == 50
    assert result.tickets.sum() == len(df)
    assert result.sample_share_pct.sum() == 100


def test_segment_floor_and_topic_dimension():
    df = generate_data(80)
    assert segment_benchmarks(df, dimension="topic", min_sample=81).empty
    result = segment_benchmarks(df, dimension="topic", min_sample=1)
    assert set(result.segment) == set(df.topic.unique())
    assert result.dimension.eq("topic").all()


def test_unknown_dimension_or_minimum_rejected():
    df = generate_data(30)
    with pytest.raises(ValueError, match="Dimensão"):
        segment_benchmarks(df, dimension="customer_id")
    with pytest.raises(ValueError, match="Amostra"):
        segment_benchmarks(df, min_sample=0)


def test_duplicate_ticket_and_invalid_csat_fail_cleanly():
    df = generate_data(30)
    df.loc[1, "ticket_id"] = df.loc[0, "ticket_id"]
    with pytest.raises(ValueError, match="duplicado"):
        weekly_cx_trends(df)
    df = generate_data(30)
    df.loc[0, "csat"] = 9
    with pytest.raises(ValueError, match="CSAT"):
        weekly_cx_trends(df)


def test_empty_input_keeps_schema():
    df = generate_data(10).iloc[:0]
    assert list(weekly_cx_trends(df).columns) == WEEK_COLUMNS
    assert list(segment_benchmarks(df).columns) == BENCHMARK_COLUMNS
    out = observed_repeat_30d(df)
    assert list(out["groups"].columns) == REPEAT_COLUMNS
    assert out["repeat_pct"] is None


def test_observed_repeat_uses_complete_universe_beyond_filtered_cohort():
    df = pd.DataFrame([
        record("T1", "C1", "2026-08-01", "Chat"),
        record("T2", "C1", "2026-08-15", "Email", "Conta"),
        record("T3", "C2", "2026-08-01", "Chat"),
        record("T4", "C3", "2026-10-15", "Email"),
    ])
    cohort = df[df.channel.eq("Chat")]
    result = observed_repeat_30d(df, cohort=cohort, min_sample=1)
    assert result["cohort_tickets"] == 2
    assert result["eligible_tickets"] == 2
    assert result["repeat_tickets"] == 1
    assert result["repeat_pct"] == 50
    assert result["groups"].iloc[0].eligible_tickets == 2
    assert result["as_of"] == "2026-10-15"
    assert result["cutoff"] == "2026-09-15"


def test_censoring_excludes_last_30_days_even_if_repeat_exists():
    df = pd.DataFrame([
        record("T1", "C1", "2026-09-30"),
        record("T2", "C1", "2026-10-01"),
        record("T3", "C2", "2026-10-15"),
    ])
    result = observed_repeat_30d(df, min_sample=1)
    assert result["eligible_tickets"] == 0
    assert result["censored_tickets"] == 3
    assert result["repeat_pct"] is None


def test_exact_30_day_repeat_counts_but_31_days_does_not():
    df = pd.DataFrame([
        record("T1", "C1", "2026-08-01"),
        record("T2", "C1", "2026-08-31"),
        record("T3", "C2", "2026-08-01"),
        record("T4", "C2", "2026-09-01"),
        record("T5", "C3", "2026-11-01"),
    ])
    cohort = df[df.ticket_id.isin(["T1", "T3"])]
    result = observed_repeat_30d(df, cohort, min_sample=1)
    assert result["repeat_tickets"] == 1
    assert result["repeat_pct"] == 50.0


def test_same_day_contact_not_counted_without_timestamps():
    df = pd.DataFrame([
        record("T1", "C1", "2026-08-01"),
        record("T2", "C1", "2026-08-01"),
        record("T3", "C2", "2026-10-01"),
    ])
    cohort = df.iloc[:2]
    out = observed_repeat_30d(df, cohort, min_sample=1)
    assert out["eligible_tickets"] == 2
    assert out["repeat_tickets"] == 0


def test_synthetic_prediction_label_never_drives_measured_repeat():
    df = pd.DataFrame([
        record("T1", "C1", "2026-08-01"),
        record("T2", "C2", "2026-10-01"),
    ])
    df["repeat_contact_30d"] = [1, 1]
    out = observed_repeat_30d(df, cohort=df.iloc[:1], min_sample=1)
    assert out["repeat_tickets"] == 0


def test_filtered_cohort_unknown_ticket_rejected():
    df = generate_data(40)
    missing = df.iloc[:1].copy()
    missing["ticket_id"] = "UNKNOWN"
    with pytest.raises(ValueError, match="fora do universo"):
        observed_repeat_30d(df, missing)


def test_recontact_groups_respect_minimum_and_reproducibility():
    df = generate_data(500)
    left = observed_repeat_30d(df, dimension="topic", min_sample=10)
    right = observed_repeat_30d(df.sample(frac=1, random_state=3),
                                dimension="topic", min_sample=10)
    assert left["eligible_tickets"] + left["censored_tickets"] == 500
    assert left["repeat_tickets"] <= left["eligible_tickets"]
    assert left["repeat_pct"] == right["repeat_pct"]
    pd.testing.assert_frame_equal(left["groups"], right["groups"])
