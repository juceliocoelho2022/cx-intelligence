-- v1.1 | Registro de eventos inteiramente fictícios
CREATE TABLE IF NOT EXISTS cx_ticket_events (
  event_key VARCHAR(128) PRIMARY KEY,
  ticket_id VARCHAR(20) NOT NULL REFERENCES cx_tickets(ticket_id) ON DELETE RESTRICT,
  status VARCHAR(20) NOT NULL CHECK (status IN ('OPEN','IN_PROGRESS','RESOLVED')),
  occurred_at TIMESTAMPTZ NOT NULL,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  source VARCHAR(32) NOT NULL CHECK (source IN ('synthetic_demo','manual_demo'))
);
CREATE INDEX IF NOT EXISTS idx_cx_event_ticket_date ON cx_ticket_events (ticket_id,occurred_at DESC);
CREATE OR REPLACE FUNCTION cx_reject_event_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'cx_ticket_events is append-only; UPDATE and DELETE are prohibited';
END;
$$;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='cx_ticket_events'::regclass AND tgname='trg_cx_events_immutable') THEN
    CREATE TRIGGER trg_cx_events_immutable BEFORE UPDATE OR DELETE ON cx_ticket_events
      FOR EACH ROW EXECUTE FUNCTION cx_reject_event_mutation();
  END IF;
END;
$$;
