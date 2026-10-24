"""Contract tests for Kaggle sample import; no real Kaggle file or DB required."""
import pandas as pd
import pytest
from src.external_kaggle import (
    COLUMNS, SOURCE_ID, UPSERT, prepare_kaggle_csv, safe_dataset_hash, overview,
)

def sample():
    return pd.DataFrame([
        {"Ticket ID": "1", "Ticket Type": "Technical issue", "Ticket Status": "Closed",
         "Ticket Priority": "Critical", "Ticket Channel": "Chat",
         "Customer Satisfaction Rating": "5",
         "Customer Name": "EXAMPLE ONLY", "Customer Email": "private@example.com",
         "Ticket Description": "Never persist this text"},
        {"Ticket ID": "2", "Ticket Type": "Refund request", "Ticket Status": "Open",
         "Ticket Priority": "Low", "Ticket Channel": "Email",
         "Customer Satisfaction Rating": "",
         "Customer Name": "EXAMPLE ONLY", "Customer Email": "private@example.com",
         "Ticket Description": "Never persist this text"},
    ])

def write_csv(tmp_path, frame):
    path = tmp_path / "customer_support_tickets.csv"
    frame.to_csv(path, index=False)
    return path

def test_import_keeps_operational_allowlist_only(tmp_path):
    source = write_csv(tmp_path, sample())
    sanitized = prepare_kaggle_csv(source)
    assert list(sanitized.columns) == COLUMNS
    assert sanitized.ticket_hash.str.fullmatch(r"[0-9a-f]{64}").all()
    assert not sanitized.astype(str).to_string().find("private@example.com") >= 0
    assert "ticket_id" not in sanitized.columns
    assert sanitized.source_id.eq(SOURCE_ID).all()

def test_missing_ratings_are_not_zero(tmp_path):
    sanitized = prepare_kaggle_csv(write_csv(tmp_path, sample()))
    m = overview(sanitized)
    assert m["tickets"] == 2
    assert m["rated_tickets"] == 1
    assert m["csat_positive_pct"] == 100.0
    assert m["closed_pct"] == 50.0

def test_reordering_does_not_change_safe_fingerprint(tmp_path):
    one = prepare_kaggle_csv(write_csv(tmp_path, sample()))
    two = one.sample(frac=1, random_state=17).reset_index(drop=True)
    assert safe_dataset_hash(one) == safe_dataset_hash(two)

@pytest.mark.parametrize("col,value", [
    ("Ticket Status", "Escalated"),
    ("Ticket Priority", "Unknown"),
    ("Ticket Channel", "Carrier pigeon"),
    ("Customer Satisfaction Rating", "not rated"),
    ("Customer Satisfaction Rating", "2.5"),
    ("Ticket ID", "sensitive-id"),
])
def test_invalid_values_fail_before_database(tmp_path, col, value):
    frame = sample()
    frame.loc[0, col] = value
    with pytest.raises(ValueError):
        prepare_kaggle_csv(write_csv(tmp_path, frame))

def test_duplicate_source_ticket_ids_are_rejected(tmp_path):
    frame = sample()
    frame.loc[1, "Ticket ID"] = frame.loc[0, "Ticket ID"]
    with pytest.raises(ValueError, match="duplicado"):
        prepare_kaggle_csv(write_csv(tmp_path, frame))

def test_missing_header_is_rejected(tmp_path):
    frame = sample().drop(columns=["Ticket Priority"])
    with pytest.raises(ValueError, match="ausentes"):
        prepare_kaggle_csv(write_csv(tmp_path, frame))

def test_sql_does_not_upsert_unchanged_rows():
    assert "ON CONFLICT(source_id,ticket_hash)" in UPSERT
    assert "IS DISTINCT FROM" in UPSERT
    assert "cx_external_support_tickets" in UPSERT

def test_empty_file_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="1 a 50.000"):
        prepare_kaggle_csv(write_csv(tmp_path, sample().iloc[0:0]))
