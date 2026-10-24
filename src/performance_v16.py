"""v1.6 beta — cached, deterministic analytics for Streamlit reruns.

Caches depend on data and filter arguments, not on the session action plan.
No authentication, shared mutable task state, or persistent writes are added.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.bi_reports import compare_periods
from src.model import train_and_evaluate
from src.nlp import compare_models


@st.cache_data(show_spinner=False, max_entries=3)
def risk_snapshot(universe: pd.DataFrame):
    """Return cached baseline metrics/predictions; never retrain per widget click.

    Streamlit hashes the entire DataFrame, so changed data invalidates the cache.
    The trained estimator itself is not retained in the cached value.
    """
    _estimator, metrics, prediction = train_and_evaluate(universe)
    return metrics, prediction


@st.cache_data(show_spinner=False, max_entries=2)
def nlp_model_comparison():
    """Cache the three-model educational benchmark across Streamlit reruns."""
    return compare_models()


@st.cache_data(show_spinner=False, max_entries=24)
def bi_snapshot(universe: pd.DataFrame, *, end_date, window_days: int,
                dimension: str, topics: tuple[str, ...],
                channels: tuple[str, ...], min_sample: int):
    """Cache the same BI calculation used by the v1.4 and v1.5 tabs.

    Include all filters, timeframe, and current DataFrame in the cache key.
    No action/state data is stored here, and returned values are copied by
    st.cache_data rather than shared as mutable cross-session objects.
    """
    if not isinstance(topics, tuple) or not isinstance(channels, tuple):
        raise ValueError("Filtros do cache devem ser tuplas")
    return compare_periods(
        universe, end_date=end_date, window_days=window_days,
        dimension=dimension, topics=topics, channels=channels,
        min_sample=min_sample,
    )
