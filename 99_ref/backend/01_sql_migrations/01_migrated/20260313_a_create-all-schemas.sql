-- ============================================================
-- Pre-create ALL schemas so that table-creation migrations
-- (which may have cross-schema FK references) can safely
-- become priority-1 (no CREATE SCHEMA) and run in date order.
--
-- This file is fully idempotent (IF NOT EXISTS on every line).
-- It MUST sort first among priority-0 files (filename: 20260313_a_*).
-- ============================================================

CREATE SCHEMA IF NOT EXISTS "01_dev_features";
CREATE SCHEMA IF NOT EXISTS "03_auth_manage";
CREATE SCHEMA IF NOT EXISTS "03_notifications";
CREATE SCHEMA IF NOT EXISTS "05_grc_library";
CREATE SCHEMA IF NOT EXISTS "08_comments";
CREATE SCHEMA IF NOT EXISTS "08_tasks";
CREATE SCHEMA IF NOT EXISTS "09_assessments";
CREATE SCHEMA IF NOT EXISTS "09_attachments";
CREATE SCHEMA IF NOT EXISTS "09_issues";
CREATE SCHEMA IF NOT EXISTS "10_feedback";
CREATE SCHEMA IF NOT EXISTS "11_docs";
CREATE SCHEMA IF NOT EXISTS "14_risk_registry";
CREATE SCHEMA IF NOT EXISTS "15_sandbox";
CREATE SCHEMA IF NOT EXISTS "17_steampipe";
CREATE SCHEMA IF NOT EXISTS "20_ai";
CREATE SCHEMA IF NOT EXISTS "25_agent_sandbox";
