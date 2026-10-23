import pandas as pd
import pytest
from src.anomalies import detect_volume_anomalies

def build_counts(counts, start="2026-01-05"):
    rows=[]
    for offset, n in enumerate(counts):
        monday=pd.Timestamp(start)+pd.Timedelta(weeks=offset)
        for i in range(n):
            rows.append({"topic": "Pix", "ticket_id": f"{offset}-{i}", "date": monday+pd.Timedelta(days=i%7)})
    return pd.DataFrame(rows)

def test_spike_after_four_completed_weeks():
    df=build_counts([10,10,10,10,25])
    # Ensure the last week is complete in observation window.
    df.loc[df.index[-1], "date"] = pd.Timestamp("2026-02-08")
    result=detect_volume_anomalies(df)
    assert len(result)==1
    assert result.iloc[0].volume==25
    assert result.iloc[0].baseline_mean==10
    assert result.iloc[0].severity=="Alta"

def test_no_alert_for_partial_last_week():
    df=build_counts([10,10,10,10,25])
    # The last data day is a Friday, so it is not a fully covered week.
    assert detect_volume_anomalies(df).empty

def test_insufficient_baseline():
    df=build_counts([10,10,30])
    assert detect_volume_anomalies(df).empty

def test_empty_input():
    assert detect_volume_anomalies(pd.DataFrame()).empty

def test_invalid_parameters():
    with pytest.raises(ValueError):
        detect_volume_anomalies(build_counts([10,10]), ratio=1)
