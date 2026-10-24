-- v1.2: isolated external support-ticket dataset, operational fields only.
-- NO customer names/emails/ages/gender/free text/date-of-purchase imported.
CREATE TABLE IF NOT EXISTS cx_external_support_tickets (
 source_id TEXT NOT NULL,
 ticket_hash CHAR(64) NOT NULL,
 ticket_type VARCHAR(60) NOT NULL,
 ticket_status VARCHAR(40) NOT NULL,
 ticket_priority VARCHAR(15) NOT NULL,
 ticket_channel VARCHAR(20) NOT NULL,
 satisfaction_rating SMALLINT CHECK (satisfaction_rating BETWEEN 1 AND 5),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 PRIMARY KEY (source_id, ticket_hash)
);
CREATE INDEX IF NOT EXISTS idx_external_support_type
 ON cx_external_support_tickets(source_id, ticket_type);
CREATE TABLE IF NOT EXISTS cx_external_import_runs (
 run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 source_id TEXT NOT NULL,
 dataset_sha256 CHAR(64) NOT NULL,
 input_rows INTEGER NOT NULL CHECK(input_rows > 0),
 affected_rows INTEGER NOT NULL CHECK(affected_rows >= 0),
 imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
