"""Contract smoke checks for a reproducible synthetic portfolio demo."""
from src.pipeline import generate_data, validate_data
from src.reports import build_report, render_markdown
from src.audit import audit_manifest, export_manifest

def test_complete_report_export_roundtrip():
    df = generate_data(n=400, seed=42)
    assert validate_data(df) == []
    report = build_report(df)
    memo = render_markdown(report)
    manifest = audit_manifest(df, report, source="synthetic_csv")
    assert report["metrics"]["total_tickets"] == 400
    assert report["period_start"] <= report["period_end"]
    assert "Relatório Executivo" in memo
    assert "dataset_sha256" in export_manifest(manifest)
    assert all(manifest["checks"].values())

def test_manifest_equal_for_reordered_dataset():
    df = generate_data(n=250, seed=42)
    other = df.sample(frac=1, random_state=99).reset_index(drop=True)
    assert audit_manifest(df, build_report(df))["dataset_sha256"] == audit_manifest(
        other, build_report(other))["dataset_sha256"]
