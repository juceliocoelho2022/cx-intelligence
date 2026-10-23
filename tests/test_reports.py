import pytest
from src.pipeline import generate_data
from src.reports import build_report, render_markdown

def test_report_matches_filtered_kpis():
    df=generate_data(300)
    subset=df[df.topic.eq("Pix")]
    r=build_report(subset,history=df[df.topic.eq("Pix")],min_sample=5)
    assert r["metrics"]["total_tickets"]==len(subset)
    assert r["top_topic"]["topic"]=="Pix"
    assert r["period_start"]<=r["period_end"]

def test_export_contains_disclaimers_and_metrics():
    report=build_report(generate_data(250),min_sample=5)
    text=render_markdown(report)
    assert "Relatório Executivo" in text
    assert "100% sintéticos" in text
    assert "não é FCR" in text
    assert "causalidade" in text

def test_deterministic_report():
    df=generate_data(250)
    assert build_report(df,min_sample=5)==build_report(df,min_sample=5)

def test_empty_report_rejected():
    with pytest.raises(ValueError, match="pelo menos um"):
        build_report(generate_data(20).iloc[0:0])

def test_bad_data_rejected():
    df=generate_data(50)
    df.loc[0,"csat"]=9
    with pytest.raises(ValueError,match="CSAT"):
        build_report(df)
