import pandas as pd
import pytest
from src.pipeline import generate_data
from src.database import upsert_tickets, COLUMNS, UPSERT

def test_columns_match_generated_dataset():
    df = generate_data(50)
    assert set(COLUMNS).issubset(df.columns)

def test_sql_is_upsert_and_skips_unchanged_rows():
    assert "ON CONFLICT(ticket_id)" in UPSERT
    assert "IS DISTINCT FROM" in UPSERT

def test_quality_gate_runs_before_connection():
    df = generate_data(30)
    df.loc[0, "csat"] = 10
    with pytest.raises(ValueError, match="CSAT"):
        upsert_tickets(df, "postgresql://invalid:invalid@127.0.0.1:1/invalid")
