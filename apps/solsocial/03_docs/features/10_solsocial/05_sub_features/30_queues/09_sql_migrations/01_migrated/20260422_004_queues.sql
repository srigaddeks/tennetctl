-- UP ====

-- Queues sub-feature — one queue per channel, with recurring weekly slots.

CREATE TABLE "10_solsocial"."12_fct_queues" (
    id           VARCHAR(36) NOT NULL,
    org_id       VARCHAR(36) NOT NULL,
    workspace_id VARCHAR(36) NOT NULL,
    channel_id   VARCHAR(36) NOT NULL,
    timezone     TEXT        NOT NULL DEFAULT 'UTC',
    is_active    BOOLEAN     NOT NULL DEFAULT TRUE,
    is_test      BOOLEAN     NOT NULL DEFAULT FALSE,
    created_by   VARCHAR(36) NOT NULL,
    updated_by   VARCHAR(36) NOT NULL,
    created_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at   TIMESTAMP,
    CONSTRAINT pk_solsocial_fct_queues PRIMARY KEY (id),
    CONSTRAINT uq_solsocial_fct_queues_channel UNIQUE (channel_id),
    CONSTRAINT fk_solsocial_fct_queues_channel
        FOREIGN KEY (channel_id) REFERENCES "10_solsocial"."10_fct_channels" (id)
);
COMMENT ON TABLE "10_solsocial"."12_fct_queues" IS 'One queue per channel.';

CREATE TABLE "10_solsocial"."23_dtl_queue_slots" (
    id          VARCHAR(36) NOT NULL,
    queue_id    VARCHAR(36) NOT NULL,
    day_of_week SMALLINT    NOT NULL,
    hour        SMALLINT    NOT NULL,
    minute      SMALLINT    NOT NULL,
    created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_solsocial_dtl_queue_slots PRIMARY KEY (id),
    CONSTRAINT uq_solsocial_dtl_queue_slots UNIQUE (queue_id, day_of_week, hour, minute),
    CONSTRAINT fk_solsocial_dtl_queue_slots_queue
        FOREIGN KEY (queue_id) REFERENCES "10_solsocial"."12_fct_queues" (id),
    CONSTRAINT chk_solsocial_dtl_queue_slots_dow    CHECK (day_of_week BETWEEN 0 AND 6),
    CONSTRAINT chk_solsocial_dtl_queue_slots_hour   CHECK (hour BETWEEN 0 AND 23),
    CONSTRAINT chk_solsocial_dtl_queue_slots_minute CHECK (minute BETWEEN 0 AND 59)
);
COMMENT ON TABLE "10_solsocial"."23_dtl_queue_slots" IS 'Recurring weekly publish slots. day_of_week 0=Sunday.';

CREATE VIEW "10_solsocial".v_queues AS
SELECT
    q.id, q.channel_id, q.workspace_id, q.org_id, q.timezone,
    q.is_active, q.is_test,
    q.created_by, q.updated_by, q.created_at, q.updated_at
FROM "10_solsocial"."12_fct_queues" q
WHERE q.deleted_at IS NULL;

-- DOWN ====

DROP VIEW  IF EXISTS "10_solsocial".v_queues;
DROP TABLE IF EXISTS "10_solsocial"."23_dtl_queue_slots";
DROP TABLE IF EXISTS "10_solsocial"."12_fct_queues";
