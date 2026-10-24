"""v1.4 BI contract tests: periods, filters, missing baselines, safe exports."""
import pandas as pd
import pytest
from src.pipeline import generate_data
from src.bi_reports import compare_periods, render_bi_markdown, render_bi_html


def history():
    data = generate_data(n=6, seed=9)
    data["date"] = pd.to_datetime([
        "2026-08-01", "2026-08-16", "2026-08-18",
        "2026-08-23", "2026-08-25", "2026-08-26",
    ])
    data["channel"] = ["Email", "Chat", "Chat", "Chat", "Chat", "Email"]
    data["topic"] = ["Conta", "Pix", "Pix", "Pix", "Pix", "Conta"]
    data["csat"] = [5, 1, 5, 5, 5, 1]
    data["resolved"] = [1, 0, 1, 1, 1, 0]
    data["resolution_hours"] = [2., 4., 4., 2., 2., 12.]
    return data


def test_equal_non_overlapping_windows_and_unrounded_rate_deltas():
    r = compare_periods(history(), "2026-08-28", window_days=7, min_sample=2)
    assert r["period_current"] == {"start": "2026-08-22", "end": "2026-08-28"}
    assert r["period_previous"] == {"start": "2026-08-15", "end": "2026-08-21"}
    assert r["status"] == "comparable"
    assert r["current"]["tickets"] == 3
    assert r["previous"]["tickets"] == 2
    assert r["current"]["csat_pct"] == 66.67
    assert r["previous"]["csat_pct"] == 50.0
    assert {x["metric"]: x["delta"] for x in r["metrics"]} == {
        "tickets": 50.0, "csat_pct": 16.67,
        "resolved_pct": 16.67, "avg_resolution_hours": 1.33,
    }
    assert len(r["segments"]) == 1
    assert r["segments"][0]["segment"] == "Chat"
    assert r["segments"][0]["csat_delta_pp"] == 50


def test_channel_filter_applies_to_both_windows_not_to_coverage():
    r = compare_periods(history(), "2026-08-28", 7, channels=["Email"], min_sample=1)
    assert r["previous"]["tickets"] == 0
    assert r["current"]["tickets"] == 1
    assert r["status"] == "empty_baseline"
    assert all(m["delta"] is None for m in r["metrics"])
    assert all(m["previous"] == 0 or m["previous"] is None for m in r["metrics"])


def test_topic_filter_preserves_equal_dates():
    r = compare_periods(history(), "2026-08-28", 7, topics=["Pix"], min_sample=1)
    assert r["previous"]["tickets"] == 2
    assert r["current"]["tickets"] == 2
    assert r["status"] == "comparable"
    assert r["segments"][0]["current_tickets"] == 2


def test_incomplete_earlier_history_has_no_comparison():
    r = compare_periods(history(), "2026-08-21", window_days=14, min_sample=1)
    assert r["status"] == "insufficient_history"
    assert all(m["delta"] is None for m in r["metrics"])
    text = render_bi_markdown(r)
    assert "N/A" in text
    assert "Comparação não calculada" in text


def test_no_recent_tickets_is_explicitly_unavailable():
    r = compare_periods(history(), "2026-08-22", 7, topics=["Conta"], min_sample=1)
    assert r["status"] == "empty_current"
    assert r["current"]["tickets"] == 0
    assert all(m["delta"] is None for m in r["metrics"])


def test_segment_requires_minimum_in_both_periods():
    r = compare_periods(history(), "2026-08-28", 7, min_sample=3)
    assert r["segments"] == []
    assert r["segments_excluded_small_sample"] >= 1
    assert "Sem segmentos comparáveis" in render_bi_markdown(r)


def test_report_has_transparent_limitations_and_correct_units():
    r = compare_periods(history(), "2026-08-28", 7, min_sample=1)
    md = render_bi_markdown(r)
    html = render_bi_html(r)
    assert "100% sintéticos" in md
    assert "pp" in md
    assert "Não" not in md or "não" in md
    assert "<meta name=\"viewport\"" in html
    assert "Sem clientes reais" in html
    assert "Imprimir" not in html or "PDF" in html
    assert not html.startswith("<script")


def test_html_escapes_segment_names():
    df = history()
    df["channel"] = 'Chat<script>alert("x")</script>'
    r = compare_periods(df, "2026-08-28", 7, min_sample=1)
    html = render_bi_html(r)
    assert "&lt;script&gt;" in html
    assert '<script>alert("x")</script>' not in html
    assert "&quot;x&quot;" in html


def test_markdown_escapes_table_delimiters():
    df = history()
    df["channel"] = "Chat | Unknown"
    r = compare_periods(df, "2026-08-28", 7, min_sample=1)
    assert "Chat \\| Unknown" in render_bi_markdown(r)


def test_empty_and_invalid_data_rejected():
    with pytest.raises(ValueError, match="não vazio"):
        compare_periods(generate_data(10).iloc[0:0], "2026-08-01")
    df = history()
    df.loc[0, "csat"] = 9
    with pytest.raises(ValueError, match="CSAT"):
        compare_periods(df, "2026-08-28")


@pytest.mark.parametrize("days", [0, 1, 15, 31, True, 7.0])
def test_invalid_window(days):
    with pytest.raises(ValueError, match="Janela"):
        compare_periods(history(), "2026-08-28", window_days=days)


@pytest.mark.parametrize("dim", ["account", "", None])
def test_invalid_dimensions(dim):
    with pytest.raises(ValueError, match="Dimensão"):
        compare_periods(history(), "2026-08-28", 7, dimension=dim)


def test_invalid_ends_and_min_sample():
    df = history()
    with pytest.raises(ValueError, match="Data final"):
        compare_periods(df, "2027-01-01", 7)
    with pytest.raises(ValueError, match="Amostra"):
        compare_periods(df, "2026-08-28", 7, min_sample=0)


def test_is_deterministic_and_does_not_mutate_input():
    df = generate_data(700, seed=42)
    original = df.copy(deep=True)
    first = compare_periods(df, df.date.max(), 14, dimension="topic", min_sample=15)
    second = compare_periods(df.sample(frac=1, random_state=17),
                             df.date.max(), 14, dimension="topic", min_sample=15)
    assert first == second
    pd.testing.assert_frame_equal(df, original)
    assert render_bi_markdown(first) == render_bi_markdown(second)
    assert render_bi_html(first) == render_bi_html(second)


def test_noncovered_baseline_renders_honestly():
    data = history()
    result = compare_periods(data, "2026-08-28", 30)
    assert result["status"] == "insufficient_history"
    assert "| N/A | N/A |" in render_bi_markdown(result)
    assert "Comparação não calculada" in render_bi_html(result)
