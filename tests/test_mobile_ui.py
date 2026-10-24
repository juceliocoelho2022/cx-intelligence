"""Basic regression checks for the mobile presentation of the Streamlit UI.

These static checks do not replace visual acceptance on a mobile device.
"""
from pathlib import Path


def test_streamlit_mobile_css_and_navigation_hint_present():
    source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert "@media (max-width: 767px)" in source
    assert '[data-testid="stMetric"] {min-height:102px;padding:12px}' in source
    assert '[data-testid="stPlotlyChart"] .modebar' in source
    assert "display:none !important;" in source
    assert "No celular: deslize a faixa de abas" in source


def test_mobile_rules_do_not_turn_off_desktop_chart_toolbar_globally():
    source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert 'st.plotly_chart(fig, width="stretch")' in source
    assert 'config={"displayModeBar": False}' not in source
