"""PostgreSQL ETL for 100% synthetic CX records. CLI: python -m src.database."""
import os
import pandas as pd
from psycopg import connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from src.pipeline import get_or_create, validate_data

COLUMNS = ["ticket_id", "customer_id", "date", "channel", "topic", "resolution_hours",
           "resolved", "sentiment", "csat", "previous_tickets", "repeat_contact_30d"]
DDL = """
CREATE TABLE IF NOT EXISTS cx_tickets (
ticket_id VARCHAR(20) PRIMARY KEY, customer_id VARCHAR(20) NOT NULL,
date DATE NOT NULL, channel VARCHAR(30) NOT NULL, topic VARCHAR(50) NOT NULL,
resolution_hours NUMERIC(8,2) NOT NULL CHECK (resolution_hours >= 0),
resolved SMALLINT NOT NULL CHECK (resolved IN (0,1)),
sentiment VARCHAR(15) NOT NULL CHECK (sentiment IN ('positivo','neutro','negativo')),
csat SMALLINT NOT NULL CHECK (csat BETWEEN 1 AND 5),
previous_tickets INTEGER NOT NULL CHECK (previous_tickets >= 0),
repeat_contact_30d SMALLINT NOT NULL CHECK (repeat_contact_30d IN (0,1))
);
CREATE INDEX IF NOT EXISTS idx_cx_date ON cx_tickets(date);
CREATE INDEX IF NOT EXISTS idx_cx_topic_date ON cx_tickets(topic,date);
CREATE TABLE IF NOT EXISTS cx_etl_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    input_count INTEGER NOT NULL CHECK (input_count >= 0),
    affected_count INTEGER NOT NULL CHECK (affected_count >= 0),
    source_name TEXT NOT NULL DEFAULT 'synthetic_csv',
    quality_errors JSONB NOT NULL DEFAULT '[]'::jsonb
);
"""

UPSERT = """
INSERT INTO cx_tickets (ticket_id, customer_id, date, channel, topic, resolution_hours,
 resolved, sentiment, csat, previous_tickets, repeat_contact_30d)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON CONFLICT(ticket_id) DO UPDATE SET
 customer_id=excluded.customer_id, date=excluded.date, channel=excluded.channel,
 topic=excluded.topic, resolution_hours=excluded.resolution_hours,
 resolved=excluded.resolved, sentiment=excluded.sentiment, csat=excluded.csat,
 previous_tickets=excluded.previous_tickets, repeat_contact_30d=excluded.repeat_contact_30d
WHERE (cx_tickets.customer_id,cx_tickets.date,cx_tickets.channel,cx_tickets.topic,
 cx_tickets.resolution_hours,cx_tickets.resolved,cx_tickets.sentiment,
 cx_tickets.csat,cx_tickets.previous_tickets,cx_tickets.repeat_contact_30d)
IS DISTINCT FROM (excluded.customer_id,excluded.date,excluded.channel,excluded.topic,
 excluded.resolution_hours,excluded.resolved,excluded.sentiment,excluded.csat,
 excluded.previous_tickets,excluded.repeat_contact_30d);
"""

def connection_string():
    return os.getenv("DATABASE_URL", "postgresql://cx_user:cx_local_dev_only@localhost:5433/cx_intelligence")

def upsert_tickets(df, dsn=None):
    """Validate before transaction, upsert only changed rows and record the run atomically."""
    errors = validate_data(df)
    if errors:
        raise ValueError("; ".join(errors))
    records = df[COLUMNS].copy()
    records["date"] = pd.to_datetime(records["date"]).dt.date
    records = records.astype(object).where(pd.notna(records), None)
    with connect(dsn or connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            changed = 0
            for record in records.itertuples(index=False, name=None):
                cur.execute(UPSERT, tuple(v.item() if hasattr(v, "item") else v for v in record))
                changed += cur.rowcount
            cur.execute("""INSERT INTO cx_etl_runs (input_count, affected_count, quality_errors)
                           VALUES (%s,%s,%s)""", (len(records), changed, Jsonb([])))
    return {"input_count": len(records), "affected_count": changed}

def load_tickets(dsn=None):
    """Read data in the same shape as local pipeline, for dashboard integration."""
    with connect(dsn or connection_string(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT " + ", ".join(COLUMNS) + " FROM cx_tickets ORDER BY ticket_id")
            rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=COLUMNS)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["resolution_hours"] = df["resolution_hours"].astype(float)
    return df

if __name__ == "__main__":
    result = upsert_tickets(get_or_create())
    print(f"ETL concluído: {result['input_count']} registros, {result['affected_count']} novos/alterados")
