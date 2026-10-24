"""v1.6 cache contract: reuse results, invalidate on relevant dataset/filter changes.

Assertions use call counts rather than flaky elapsed-time thresholds.
"""
from datetime import date

import pandas as pd
import pytest

from src import performance_v16 as perf
from src.pipeline import generate_data
from src.bi_reports import compare_periods


@pytest.fixture(autouse=True)
def clear_perf_caches():
    perf.risk_snapshot.clear()
    perf.nlp_model_comparison.clear()
    perf.bi_snapshot.clear()
    yield
    perf.risk_snapshot.clear()
    perf.nlp_model_comparison.clear()
    perf.bi_snapshot.clear()


def test_risk_baseline_cached_per_dataset(monkeypatch):
    calls = []
    def fake_train(universe):
        calls.append(len(universe))
        return object(), {"roc_auc": 0.7, "average_precision": 0.5}, pd.DataFrame({
            "ticket_id": universe.ticket_id,
        })
    monkeypatch.setattr(perf, "train_and_evaluate", fake_train)
    a = generate_data(n=120, seed=4)
    metrics, pred = perf.risk_snapshot(a)
    assert len(pred) == 120
    assert perf.risk_snapshot(a.copy())[0] == metrics
    assert calls == [120], "Same dataset must not retrain on a Streamlit rerun"
    changed = a.copy()
    changed.loc[0, "csat"] = 1 if changed.loc[0, "csat"] != 1 else 5
    perf.risk_snapshot(changed)
    assert calls == [120, 120], "Changed data must invalidate cached predictions"


def test_cached_ml_predictions_are_not_mutable_across_callers(monkeypatch):
    def fake_train(universe):
        return object(), {"roc_auc": 0.7}, pd.DataFrame({"score": [1.0]})
    monkeypatch.setattr(perf, "train_and_evaluate", fake_train)
    data = generate_data(n=50, seed=5)
    metrics, pred = perf.risk_snapshot(data)
    pred.loc[0, "score"] = 99
    metrics["roc_auc"] = 0
    metrics2, pred2 = perf.risk_snapshot(data)
    assert pred2.loc[0, "score"] == 1.0
    assert metrics2["roc_auc"] == 0.7


def test_three_model_nlp_comparison_is_not_retrained_every_click(monkeypatch):
    counter = []
    def fake_compare():
        counter.append(1)
        return pd.DataFrame({"f1_macro": [0.6]}), pd.DataFrame({"reason": ["simulated"]})
    monkeypatch.setattr(perf, "compare_models", fake_compare)
    first, errors = perf.nlp_model_comparison()
    second, errors2 = perf.nlp_model_comparison()
    assert first.equals(second) and errors.equals(errors2)
    assert len(counter) == 1


def test_bi_cache_keys_are_sensitive_to_scope_and_window(monkeypatch):
    calls = []
    real_compare = perf.compare_periods
    def counting_compare(*args, **kwargs):
        calls.append(kwargs.copy())
        return real_compare(*args, **kwargs)
    monkeypatch.setattr(perf, "compare_periods", counting_compare)
    data = generate_data(n=400, seed=42)
    kwargs = dict(
        end_date=date(2026, 10, 19), window_days=14, dimension="channel",
        topics=("Pix",), channels=("Chat",), min_sample=10,
    )
    expected = compare_periods(data, **kwargs)
    got = perf.bi_snapshot(data, **kwargs)
    assert got == expected
    assert perf.bi_snapshot(data.copy(), **kwargs) == got
    assert len(calls) == 1
    # User changes the number of days: independent, freshly computed result.
    perf.bi_snapshot(data, **{**kwargs, "window_days": 7})
    # User changes subject filter: independent, freshly computed result.
    perf.bi_snapshot(data, **{**kwargs, "topics": ("Conta",)})
    # User changes input data: independent, freshly computed result.
    revised = data.copy()
    revised.loc[0, "resolved"] = 1 - revised.loc[0, "resolved"]
    perf.bi_snapshot(revised, **kwargs)
    assert len(calls) == 4


def test_bi_cache_does_not_mutate_cached_results():
    data = generate_data(n=200, seed=9)
    kwargs = dict(
        end_date=date(2026, 10, 19), window_days=14, dimension="channel",
        topics=("Pix",), channels=("Chat",), min_sample=10,
    )
    report = perf.bi_snapshot(data, **kwargs)
    report["limitations"].clear()
    report["current"]["tickets"] = -99
    again = perf.bi_snapshot(data, **kwargs)
    assert again["limitations"]
    assert again["current"]["tickets"] >= 0


def test_bi_cache_refuses_unstable_mutable_filter_arguments():
    data = generate_data(n=100, seed=1)
    with pytest.raises(ValueError, match="tuplas"):
        perf.bi_snapshot(data, end_date=date(2026, 10, 19),
            window_days=14, dimension="topic", topics=["Pix"],
            channels=("Chat",), min_sample=10)
