-- PostgreSQL | dados fictícios
CREATE TABLE IF NOT EXISTS cx_tickets (
 ticket_id VARCHAR(20) PRIMARY KEY,
 customer_id VARCHAR(20) NOT NULL,
 date DATE NOT NULL,
 channel VARCHAR(30) NOT NULL,
 topic VARCHAR(50) NOT NULL,
 resolution_hours NUMERIC(8,2) NOT NULL CHECK (resolution_hours >= 0),
 resolved SMALLINT NOT NULL CHECK (resolved IN (0,1)),
 sentiment VARCHAR(15) NOT NULL CHECK (sentiment IN ('positivo','neutro','negativo')),
 csat SMALLINT NOT NULL CHECK (csat BETWEEN 1 AND 5),
 previous_tickets INTEGER NOT NULL CHECK (previous_tickets >= 0),
 repeat_contact_30d SMALLINT NOT NULL CHECK (repeat_contact_30d IN (0,1))
);
CREATE INDEX IF NOT EXISTS idx_cx_date ON cx_tickets(date);
CREATE INDEX IF NOT EXISTS idx_cx_topic_date ON cx_tickets(topic,date);
