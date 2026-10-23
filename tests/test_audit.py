import pytest
from src.pipeline import generate_data
from src.reports import build_report
from src.audit import data_fingerprint, audit_manifest, export_manifest

def test_same_data_different_order_has_same_fingerprint():
    df=generate_data(150)
    assert data_fingerprint(df)==data_fingerprint(df.sample(frac=1,random_state=17))

def test_changed_value_changes_fingerprint():
    df=generate_data(150)
    changed=df.copy()
    changed.loc[0,"csat"]=1 if int(df.loc[0,"csat"])!=1 else 2
    assert data_fingerprint(df)!=data_fingerprint(changed)

def test_manifest_matches_report_and_has_no_records():
    df=generate_data(150)
    result=audit_manifest(df,build_report(df,min_sample=5))
    assert result["row_count"]==150
    assert all(result["checks"].values())
    assert "customer_id" not in export_manifest(result)
    assert len(result["dataset_sha256"])==64

def test_manifest_rejects_tampered_metric():
    df=generate_data(150)
    report=build_report(df,min_sample=5)
    report["metrics"]["total_tickets"]+=1
    with pytest.raises(ValueError, match="divergem"):
        audit_manifest(df,report)

def test_invalid_source_rejected():
    df=generate_data(50)
    with pytest.raises(ValueError,match="Origem"):
        audit_manifest(df,build_report(df,min_sample=5),source="unknown")

def test_invalid_dataset_rejected():
    df=generate_data(50)
    df.loc[0,"csat"]=99
    with pytest.raises(ValueError,match="CSAT"):
        data_fingerprint(df)
