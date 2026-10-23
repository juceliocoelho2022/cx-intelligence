from src.pipeline import generate_data,validate_data,kpis
from src.model import train_and_evaluate

def test_generation_is_deterministic():
    assert generate_data(200,42).equals(generate_data(200,42))

def test_quality_checks():
    df=generate_data(150)
    assert validate_data(df)==[]
    df.loc[1,'ticket_id']=df.loc[0,'ticket_id']
    assert any('duplicado' in error for error in validate_data(df))

def test_kpis_within_bounds():
    k=kpis(generate_data(200))
    assert 0<=k['csat_pct']<=100

def test_model_temporal_holdout():
    _,metrics,pred=train_and_evaluate(generate_data(500))
    assert metrics['test_rows']==100
    assert pred.risk_score.between(0,1).all()
