import pandas as pd
import pytest
from src.insights import segment_insights
from src.pipeline import generate_data

def test_segment_metrics_and_population_reference():
    df=generate_data(500)
    out=segment_insights(df,min_sample=5)
    assert not out.empty
    assert out.tickets.le(len(df)).all()
    assert out.reference_csat_pct.eq(round(100*df.csat.ge(4).mean(),2)).all()
    assert set(out.priority).issubset({"Monitorar","Investigar","Prioritário"})

def test_priority_is_rule_based_and_not_causality():
    rows=[]
    for i in range(100):
        rows.append({"ticket_id":f"T{i}","topic":"Pix" if i<50 else "Conta",
           "channel":"Chat","csat":1 if i<50 else 5,"resolved":0 if i<50 else 1,
           "resolution_hours":2.0})
    result=segment_insights(pd.DataFrame(rows),min_sample=30)
    assert result.loc[result.topic.eq("Pix"),"priority"].item()=="Prioritário"
    assert result.loc[result.topic.eq("Conta"),"priority"].item()=="Monitorar"

def test_sample_floor_excludes_small_groups():
    df=generate_data(100)
    assert segment_insights(df,min_sample=101).empty

def test_invalid_domain_is_rejected():
    df=generate_data(100)
    df.loc[0,"csat"]=6
    with pytest.raises(ValueError,match="domínio"):
        segment_insights(df)

def test_empty_dataset_has_stable_schema():
    df=generate_data(20).iloc[0:0]
    result=segment_insights(df)
    assert result.empty
    assert "csat_gap_pp" in result.columns
