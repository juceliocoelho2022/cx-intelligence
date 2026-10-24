-- CX Intelligence v1.6 private-only migration (PostgreSQL 16).
-- Execute as a MIGRATION OWNER, never as cx_plan_app. No public demo DB.
CREATE TABLE IF NOT EXISTS cx_private_action_plans (
    owner_key CHAR(64) NOT NULL CHECK (owner_key ~ '^[0-9a-f]{64}$'),
    plan_id UUID NOT NULL,
    name VARCHAR(80) NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 80),
    payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (owner_key, plan_id)
);
CREATE INDEX IF NOT EXISTS idx_cx_private_plans_owner_updated
    ON cx_private_action_plans(owner_key, updated_at DESC);

ALTER TABLE cx_private_action_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE cx_private_action_plans FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cx_plan_owner_only ON cx_private_action_plans;
CREATE POLICY cx_plan_owner_only ON cx_private_action_plans
    FOR ALL
    USING (owner_key = current_setting('cx.plan_owner_key', true))
    WITH CHECK (owner_key = current_setting('cx.plan_owner_key', true));

-- Provision the dedicated runtime role separately, with no SUPERUSER,
-- BYPASSRLS, table ownership, CREATE or DDL privileges. Example:
-- CREATE ROLE cx_plan_app LOGIN PASSWORD '<random credential>' NOSUPERUSER NOBYPASSRLS;
-- GRANT USAGE ON SCHEMA public TO cx_plan_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON cx_private_action_plans TO cx_plan_app;
-- Revoke PUBLIC permissions for this table if inherited from a nonstandard DB setup.
