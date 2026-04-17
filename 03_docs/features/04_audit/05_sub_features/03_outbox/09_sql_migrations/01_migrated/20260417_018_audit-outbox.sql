-- UP ====
-- Migration 018: Audit durable outbox + LISTEN/NOTIFY trigger
--
-- 61_evt_audit_outbox: cursor-based sequential log of every evt_audit insert.
-- BIGSERIAL PK provides a monotonic cursor (consumers track last-seen id).
-- Trigger fires AFTER INSERT on evt_audit: inserts outbox row + pg_notify.
-- pg_notify channel: 'audit_events', payload = the event_id (TEXT).
-- No consumed_at / consumer column: outbox is a broadcast log.
-- Consumers track their own cursor position.

CREATE TABLE IF NOT EXISTS "04_audit"."61_evt_audit_outbox" (
    id          BIGSERIAL   NOT NULL,
    event_id    TEXT        NOT NULL,
    created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_evt_audit_outbox PRIMARY KEY (id)
);

COMMENT ON TABLE  "04_audit"."61_evt_audit_outbox" IS 'Append-only outbox: one row per evt_audit insert. Cursor-based fan-out for downstream consumers (Notify, webhooks, exports). Consumers track their own last-seen id.';
COMMENT ON COLUMN "04_audit"."61_evt_audit_outbox".id         IS 'Monotonic BIGSERIAL — the cursor value consumers track.';
COMMENT ON COLUMN "04_audit"."61_evt_audit_outbox".event_id   IS 'References evt_audit.id (TEXT, no FK to keep emit hot-path clean).';
COMMENT ON COLUMN "04_audit"."61_evt_audit_outbox".created_at IS 'Insert timestamp — matches evt_audit.created_at approximately.';

CREATE INDEX IF NOT EXISTS idx_evt_audit_outbox_created_at
    ON "04_audit"."61_evt_audit_outbox" (created_at DESC);

-- Trigger function: insert outbox row + notify audit_events channel
CREATE OR REPLACE FUNCTION "04_audit".fn_audit_outbox_notify()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO "04_audit"."61_evt_audit_outbox" (event_id)
    VALUES (NEW.id);
    -- Hot-path wake-up for listeners; payload is the event_id for targeted fetch.
    PERFORM pg_notify('audit_events', NEW.id);
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION "04_audit".fn_audit_outbox_notify() IS 'Fires after every evt_audit INSERT: appends to outbox + notifies audit_events channel.';

DROP TRIGGER IF EXISTS trg_audit_outbox_notify ON "04_audit"."60_evt_audit";

CREATE TRIGGER trg_audit_outbox_notify
AFTER INSERT ON "04_audit"."60_evt_audit"
FOR EACH ROW
EXECUTE FUNCTION "04_audit".fn_audit_outbox_notify();

COMMENT ON TRIGGER trg_audit_outbox_notify ON "04_audit"."60_evt_audit" IS 'Populates outbox + notifies audit_events channel on every evt_audit insert.';

-- DOWN ====
-- DROP TRIGGER IF EXISTS trg_audit_outbox_notify ON "04_audit"."60_evt_audit";
-- DROP FUNCTION IF EXISTS "04_audit".fn_audit_outbox_notify();
-- DROP TABLE IF EXISTS "04_audit"."61_evt_audit_outbox";
