"""Reproducible, non-persistent audit manifest for synthetic analytics."""
import hashlib
import json
import pandas as pd
from src.pipeline import kpis, validate_data

AUDIT_VERSION = "0.8.0"
CANONICAL_COLUMNS = (
    "ticket_id", "customer_id", "date", "channel", "topic",
    "resolution_hours", "resolved", "sentiment", "csat",
    "previous_tickets", "repeat_contact_30d",
)

def data_fingerprint(df):
    """SHA-256 of canonical record values, independent of input row order."""
    missing = set(CANONICAL_COLUMNS).difference(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")
    if df.empty:
        raise ValueError("Não é possível auditar dataset vazio")
    errors = validate_data(df)
    if errors:
        raise ValueError("; ".join(errors))
    records = df[list(CANONICAL_COLUMNS)].copy()
    records["date"] = pd.to_datetime(records["date"], errors="raise").dt.strftime("%Y-%m-%d")
    records["resolution_hours"] = pd.to_numeric(records["resolution_hours"]).map(lambda x: f"{x:.2f}")
    for col in ("resolved", "csat", "previous_tickets", "repeat_contact_30d"):
        records[col] = pd.to_numeric(records[col]).astype("int64").astype(str)
    records = records.sort_values("ticket_id", kind="stable")
    payload = records.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def audit_manifest(df, report, source="synthetic_csv"):
    """Quality checks and provenance without storing personal information."""
    if source not in {"synthetic_csv", "synthetic_postgres"}:
        raise ValueError("Origem de dados desconhecida")
    errors = validate_data(df)
    if errors:
        raise ValueError("; ".join(errors))
    actual = kpis(df)
    if report["metrics"] != actual:
        raise ValueError("Indicadores do relatório divergem do recorte auditado")
    if report["metrics"]["total_tickets"] != len(df):
        raise ValueError("Denominador de atendimentos inconsistente")
    result = {
        "schema_version": "1.0",
        "analytics_version": AUDIT_VERSION,
        "source": source,
        "dataset_sha256": data_fingerprint(df),
        "row_count": len(df),
        "period_start": report["period_start"],
        "period_end": report["period_end"],
        "checks": {
            "schema_and_domains_valid": True,
            "unique_tickets": bool(df["ticket_id"].is_unique),
            "kpis_match_report": True,
            "date_interval_matches": bool(
                pd.to_datetime(df["date"]).min().strftime("%Y-%m-%d") == report["period_start"]
                and pd.to_datetime(df["date"]).max().strftime("%Y-%m-%d") == report["period_end"]
            ),
        },
        "metrics": actual,
        "limitations": "Dataset sintético; hash identifica conteúdo, não autentica a fonte nem certifica completude.",
    }
    if not all(result["checks"].values()):
        raise ValueError("Inconsistência nos controles do manifesto")
    return result

def export_manifest(manifest):
    return json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
