-- UP ====
-- On-call schedules and rotation membership.

-- ── On-call schedules ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "05_monitoring"."10_fct_monitoring_oncall_schedules" (
    id                      VARCHAR(36) NOT NULL,
    org_id                  VARCHAR(36) NOT NULL,
    name                    TEXT NOT NULL,
    description             TEXT,
    timezone                TEXT NOT NULL DEFAULT 'UTC',
    rotation_kind_id        SMALLINT NOT NULL DEFAULT 1,
    rotation_start          TIMESTAMP NOT NULL,
    rotation_period_seconds INT NOT NULL,
    created_by              VARCHAR(36) NOT NULL,
    updated_by              VARCHAR(36) NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at              TIMESTAMP,
    CONSTRAINT pk_fct_monitoring_oncall_schedules PRIMARY KEY (id),
    CONSTRAINT uq_fct_monitoring_oncall_schedules_org_name UNIQUE (org_id, name) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_fct_monitoring_oncall_schedules_created_by FOREIGN KEY (created_by) REFERENCES "03_iam"."10_fct_users"(id),
    CONSTRAINT fk_fct_monitoring_oncall_schedules_updated_by FOREIGN KEY (updated_by) REFERENCES "03_iam"."10_fct_users"(id),
    CONSTRAINT chk_fct_monitoring_oncall_schedules_period CHECK (rotation_period_seconds > 0)
);
COMMENT ON TABLE  "05_monitoring"."10_fct_monitoring_oncall_schedules" IS 'On-call rotation schedule. Defines start time, period, and timezone for rotation calculation.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_oncall_schedules".id IS 'UUID v7.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_oncall_schedules".org_id IS 'Organization owner.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_oncall_schedules".name IS 'User-friendly schedule name (e.g. "Backend On-Call", "SRE Primary").';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_oncall_schedules".description IS 'Optional free-text description.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_oncall_schedules".timezone IS 'IANA timezone (e.g. "America/New_York", "Europe/London", "Asia/Tokyo") for handover calculation.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_oncall_schedules".rotation_kind_id IS 'Reserved for future: kind of rotation (1=simple_round_robin).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_oncall_schedules".rotation_start IS 'Absolute start time (UTC). Handovers happen at periods of rotation_period_seconds from this time, in local timezone.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_oncall_schedules".rotation_period_seconds IS 'Duration of each rotation (e.g. 604800 = 1 week).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_oncall_schedules".deleted_at IS 'Soft delete timestamp.';

CREATE INDEX idx_fct_monitoring_oncall_schedules_org_id ON "05_monitoring"."10_fct_monitoring_oncall_schedules" (org_id);
CREATE INDEX idx_fct_monitoring_oncall_schedules_deleted_at ON "05_monitoring"."10_fct_monitoring_oncall_schedules" (deleted_at);

-- ── On-call schedule members (immutable link) ───────────────────────────

CREATE TABLE IF NOT EXISTS "05_monitoring"."40_lnk_monitoring_oncall_members" (
    schedule_id     VARCHAR(36) NOT NULL,
    member_order    SMALLINT NOT NULL,
    user_id         VARCHAR(36) NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_lnk_monitoring_oncall_members PRIMARY KEY (schedule_id, member_order),
    CONSTRAINT fk_lnk_monitoring_oncall_members_schedule FOREIGN KEY (schedule_id) REFERENCES "05_monitoring"."10_fct_monitoring_oncall_schedules"(id) ON DELETE CASCADE,
    CONSTRAINT fk_lnk_monitoring_oncall_members_user FOREIGN KEY (user_id) REFERENCES "03_iam"."10_fct_users"(id),
    CONSTRAINT fk_lnk_monitoring_oncall_members_created_by FOREIGN KEY (created_by) REFERENCES "03_iam"."10_fct_users"(id)
);
COMMENT ON TABLE  "05_monitoring"."40_lnk_monitoring_oncall_members" IS 'Immutable link: schedule members in rotation order. When updating a schedule, old rows are replaced — never partial mutation.';
COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_oncall_members".schedule_id IS 'FK to schedule.';
COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_oncall_members".member_order IS 'Zero-based position in rotation.';
COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_oncall_members".user_id IS 'FK to user in rotation.';

CREATE INDEX idx_lnk_monitoring_oncall_members_schedule ON "05_monitoring"."40_lnk_monitoring_oncall_members" (schedule_id);
CREATE INDEX idx_lnk_monitoring_oncall_members_user ON "05_monitoring"."40_lnk_monitoring_oncall_members" (user_id);

-- ── Helper function: resolve current on-call user ────────────────────────

CREATE OR REPLACE FUNCTION "05_monitoring"."f_monitoring_resolve_oncall"(
    p_schedule_id VARCHAR(36),
    p_at_ts TIMESTAMP
)
RETURNS VARCHAR(36) AS $$
DECLARE
    v_rotation_start TIMESTAMP;
    v_rotation_period_seconds INT;
    v_member_count INT;
    v_timezone TEXT;
    v_index INT;
    v_user_id VARCHAR(36);
BEGIN
    -- Load schedule params
    SELECT rotation_start, rotation_period_seconds, timezone
    INTO v_rotation_start, v_rotation_period_seconds, v_timezone
    FROM "05_monitoring"."10_fct_monitoring_oncall_schedules"
    WHERE id = p_schedule_id AND deleted_at IS NULL;

    IF v_rotation_start IS NULL THEN
        RETURN NULL;
    END IF;

    -- Count members
    SELECT COUNT(*)
    INTO v_member_count
    FROM "05_monitoring"."40_lnk_monitoring_oncall_members"
    WHERE schedule_id = p_schedule_id;

    IF v_member_count = 0 THEN
        RETURN NULL;
    END IF;

    -- Calculate index: floor((elapsed_seconds) / rotation_period_seconds) % member_count
    -- elapsed is in UTC for consistency
    v_index := FLOOR(EXTRACT(EPOCH FROM (p_at_ts - v_rotation_start)) / v_rotation_period_seconds) % v_member_count;

    -- Fetch user at that index
    SELECT user_id
    INTO v_user_id
    FROM "05_monitoring"."40_lnk_monitoring_oncall_members"
    WHERE schedule_id = p_schedule_id
    ORDER BY member_order ASC
    LIMIT 1 OFFSET v_index;

    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
COMMENT ON FUNCTION "05_monitoring"."f_monitoring_resolve_oncall"(VARCHAR(36), TIMESTAMP) IS 'Resolve who is currently on-call for a schedule at a given time. Uses UTC for calculation (timezone is used by application for handover boundary display).';

-- ── Read-model view for on-call schedules ───────────────────────────────

CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_oncall_schedules" AS
SELECT
    s.id,
    s.org_id,
    s.name,
    s.description,
    s.timezone,
    s.rotation_kind_id,
    s.rotation_start,
    s.rotation_period_seconds,
    s.created_by,
    s.updated_by,
    s.created_at,
    s.updated_at,
    s.deleted_at,
    (
        SELECT json_agg(
            json_build_object(
                'member_order', m.member_order,
                'user_id', m.user_id,
                'user_email', u.email
            ) ORDER BY m.member_order ASC
        )
        FROM "05_monitoring"."40_lnk_monitoring_oncall_members" m
        LEFT JOIN "03_iam"."10_fct_users" u ON u.id = m.user_id
        WHERE m.schedule_id = s.id
    ) AS members,
    "05_monitoring"."f_monitoring_resolve_oncall"(s.id, CURRENT_TIMESTAMP) AS current_oncall_user_id
FROM "05_monitoring"."10_fct_monitoring_oncall_schedules" s
WHERE s.deleted_at IS NULL;
COMMENT ON VIEW "05_monitoring"."v_monitoring_oncall_schedules" IS 'Read-model for on-call schedules: aggregates members and resolves current on-call user.';

-- DOWN ====
DROP VIEW IF EXISTS "05_monitoring"."v_monitoring_oncall_schedules";
DROP FUNCTION IF EXISTS "05_monitoring"."f_monitoring_resolve_oncall"(VARCHAR(36), TIMESTAMP);
DROP TABLE IF EXISTS "05_monitoring"."40_lnk_monitoring_oncall_members";
DROP TABLE IF EXISTS "05_monitoring"."10_fct_monitoring_oncall_schedules";
