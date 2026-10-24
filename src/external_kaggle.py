"""v1.2 — Local Kaggle CSV import, isolated from the synthetic CX pipeline.

Target dataset: suraj520/customer-support-ticket-dataset. Import ONLY a strict
operational allowlist. Never persist names, emails, descriptions or raw ticket IDs.
"""
import argparse
import hashlib
from pathlib import Path
import pandas as pd
import psycopg
from psycopg.rows import dict_row
from src.database import connection_string

SOURCE_ID = "kaggle_suraj520_support_tickets"
SOURCE_URL = "https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset"
HEADERS = {
    "Ticket ID": "ticket_id",
    "Ticket Type": "ticket_type",
    "Ticket Status": "ticket_status",
    "Ticket Priority": "ticket_priority",
    "Ticket Channel": "ticket_channel",
    "Customer Satisfaction Rating": "satisfaction_rating",
}
COLUMNS = ["source_id", "ticket_hash", "ticket_type", "ticket_status",
           "ticket_priority", "ticket_channel", "satisfaction_rating"]
CATEGORIES = {
    "ticket_type": {"Technical issue", "Billing inquiry", "Product inquiry",
                    "Cancellation request", "Refund request"},
    "ticket_status": {"Open", "Closed", "Pending Customer Response"},
    "ticket_priority": {"Critical", "High", "Medium", "Low"},
    "ticket_channel": {"Email", "Phone", "Chat", "Social media"},
}
SQL_PATH = Path(__file__).resolve().parents[1] / "sql" / "external_kaggle.sql"
UPSERT = """
INSERT INTO cx_external_support_tickets
 (source_id,ticket_hash,ticket_type,ticket_status,ticket_priority,ticket_channel,satisfaction_rating)
 VALUES (%s,%s,%s,%s,%s,%s,%s)
 ON CONFLICT(source_id,ticket_hash) DO UPDATE SET
 ticket_type=EXCLUDED.ticket_type,ticket_status=EXCLUDED.ticket_status,
 ticket_priority=EXCLUDED.ticket_priority,ticket_channel=EXCLUDED.ticket_channel,
 satisfaction_rating=EXCLUDED.satisfaction_rating,updated_at=NOW()
 WHERE (cx_external_support_tickets.ticket_type,cx_external_support_tickets.ticket_status,
        cx_external_support_tickets.ticket_priority,cx_external_support_tickets.ticket_channel,
        cx_external_support_tickets.satisfaction_rating)
 IS DISTINCT FROM (EXCLUDED.ticket_type,EXCLUDED.ticket_status,EXCLUDED.ticket_priority,
                   EXCLUDED.ticket_channel,EXCLUDED.satisfaction_rating);
"""

def prepare_kaggle_csv(path):
    """Read allowlisted columns only; reject dirty or unexpected categorical data."""
    location = Path(path)
    if location.suffix.lower() != ".csv" or not location.is_file():
        raise ValueError("Informe o caminho de um arquivo CSV local existente")
    if location.stat().st_size > 50_000_000:
        raise ValueError("CSV excede o limite de 50 MB")
    # Sensitive fields never enter the output dataframe or database.
    raw = pd.read_csv(location, encoding="utf-8-sig", dtype=str, keep_default_na=False,
                      usecols=lambda name: name in HEADERS)
    missing = set(HEADERS) - set(raw.columns)
    if missing:
        raise ValueError(f"Campos esperados ausentes: {sorted(missing)}")
    if not 1 <= len(raw) <= 50_000:
        raise ValueError("CSV precisa ter de 1 a 50.000 tickets")
    data = raw.rename(columns=HEADERS).copy()
    for column in data.columns:
        data[column] = data[column].str.strip()
    if not data.ticket_id.str.fullmatch(r"[0-9]{1,20}").all():
        raise ValueError("Ticket ID inválido; esperados identificadores numéricos")
    if data.ticket_id.duplicated().any():
        raise ValueError("Ticket ID duplicado no CSV")
    for col, allowed in CATEGORIES.items():
        if not data[col].isin(allowed).all():
            raise ValueError(f"Valores inválidos em {col}; confira o arquivo de origem")
    rating = data.satisfaction_rating.replace("", None)
    numeric = pd.to_numeric(rating, errors="coerce")
    invalid = rating.notna() & (
        numeric.isna() | ~numeric.isin([1, 2, 3, 4, 5])
    )
    if invalid.any():
        raise ValueError("Customer Satisfaction Rating deve ser inteira de 1 a 5 ou vazia")
    data["satisfaction_rating"] = numeric.astype("Int64")
    data["ticket_hash"] = data.ticket_id.map(
        lambda value: hashlib.sha256((SOURCE_ID + ":" + value).encode("utf-8")).hexdigest())
    data["source_id"] = SOURCE_ID
    return data[COLUMNS].sort_values("ticket_hash").reset_index(drop=True)


def safe_dataset_hash(prepared):
    """Fingerprint only sanitized operational fields; independent of row order."""
    if list(prepared.columns) != COLUMNS or prepared.empty:
        raise ValueError("Dataset preparado inválido")
    ordered = prepared.sort_values("ticket_hash").copy()
    ordered["satisfaction_rating"] = ordered.satisfaction_rating.astype("string").fillna("")
    payload = ordered.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def overview(prepared):
    rated = prepared.satisfaction_rating.notna()
    total = len(prepared)
    return {
        "source": SOURCE_ID,
        "tickets": total,
        "rated_tickets": int(rated.sum()),
        "csat_positive_pct": (round(100 * prepared.loc[rated, "satisfaction_rating"].ge(4).mean(), 1)
                              if rated.any() else None),
        "closed_pct": round(100 * prepared.ticket_status.eq("Closed").mean(), 1),
        "dataset_sha256": safe_dataset_hash(prepared),
    }


def import_kaggle_csv(path, dsn=None):
    """Transactional UPSERT with import run; unchanged retries affect zero rows."""
    prepared = prepare_kaggle_csv(path)
    snapshot = overview(prepared)
    with psycopg.connect(dsn or connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(SQL_PATH.read_text(encoding="utf-8"))
            affected = 0
            for record in prepared.itertuples(index=False, name=None):
                cur.execute(UPSERT, tuple(None if pd.isna(v) else v for v in record))
                affected += cur.rowcount
            cur.execute("""INSERT INTO cx_external_import_runs
                        (source_id,dataset_sha256,input_rows,affected_rows)
                        VALUES (%s,%s,%s,%s)""",
                        (SOURCE_ID, snapshot["dataset_sha256"], len(prepared), affected))
    return {**snapshot, "affected_rows": affected}


def external_schema_exists(dsn=None):
    with psycopg.connect(dsn or connection_string()) as conn:
        return conn.execute(
            "SELECT to_regclass('public.cx_external_support_tickets')").fetchone()[0] is not None


def load_external_tickets(dsn=None):
    with psycopg.connect(dsn or connection_string(), row_factory=dict_row) as conn:
        rows = conn.execute("""SELECT ticket_type,ticket_status,ticket_priority,
                                ticket_channel,satisfaction_rating
                               FROM cx_external_support_tickets WHERE source_id=%s""",
                            (SOURCE_ID,)).fetchall()
    return pd.DataFrame(rows, columns=COLUMNS[2:])


def main():
    parser = argparse.ArgumentParser(description="Importação local e minimizada de CSV Kaggle")
    parser.add_argument("csv", help="Caminho local do CSV extraído do Kaggle")
    parser.add_argument("--write", action="store_true", help="Autorizar gravação em PostgreSQL")
    args = parser.parse_args()
    if args.write:
        result = import_kaggle_csv(args.csv)
    else:
        result = overview(prepare_kaggle_csv(args.csv))
        print("Pré-visualização apenas: nenhuma conexão ou alteração no banco.")
    for name, value in result.items():
        print(f"{name}: {value}")
    print("A fonte externa não é integrada automaticamente aos KPIs sintéticos ou ao ML.")


if __name__ == "__main__":
    main()
