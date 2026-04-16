-- UP ====

-- featureflags.permissions — per-flag role bindings.
-- lnk_role_flag_permissions ties an IAM role to a permission_id (view/toggle/write/admin) on a specific flag.
-- Immutable lnk rows: revoke = DELETE.

CREATE TABLE "09_featureflags"."40_lnk_role_flag_permissions" (
    id              VARCHAR(36) NOT NULL,
    role_id         VARCHAR(36) NOT NULL,
    flag_id         VARCHAR(36) NOT NULL,
    permission_id   SMALLINT NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_ff_lnk_role_flag_permissions PRIMARY KEY (id),
    CONSTRAINT fk_ff_lnk_rfp_role FOREIGN KEY (role_id)
        REFERENCES "03_iam"."13_fct_roles"(id),
    CONSTRAINT fk_ff_lnk_rfp_flag FOREIGN KEY (flag_id)
        REFERENCES "09_featureflags"."10_fct_flags"(id),
    CONSTRAINT fk_ff_lnk_rfp_permission FOREIGN KEY (permission_id)
        REFERENCES "09_featureflags"."04_dim_flag_permissions"(id),
    CONSTRAINT uq_ff_lnk_rfp UNIQUE (role_id, flag_id, permission_id)
);
CREATE INDEX idx_ff_lnk_rfp_role ON "09_featureflags"."40_lnk_role_flag_permissions" (role_id);
CREATE INDEX idx_ff_lnk_rfp_flag ON "09_featureflags"."40_lnk_role_flag_permissions" (flag_id);

COMMENT ON TABLE  "09_featureflags"."40_lnk_role_flag_permissions" IS 'Per-flag role-based permission grants. Check resolution: explicit grant on this flag > role has flags:admin:all scope > deny.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".id IS 'UUID v7.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".role_id IS 'FK to fct_roles.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".flag_id IS 'FK to fct_flags.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".permission_id IS 'FK to dim_flag_permissions (view=1, toggle=2, write=3, admin=4). Higher rank includes lower-rank capabilities.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".created_at IS 'Insert timestamp.';

-- Convenience view: flat denormalized shape joining dims for easy display
CREATE VIEW "09_featureflags"."v_role_flag_permissions" AS
SELECT
    l.id,
    l.role_id,
    l.flag_id,
    fp.code AS permission,
    fp.rank AS permission_rank,
    l.created_by,
    l.created_at
FROM "09_featureflags"."40_lnk_role_flag_permissions" l
JOIN "09_featureflags"."04_dim_flag_permissions" fp ON fp.id = l.permission_id;

COMMENT ON VIEW "09_featureflags"."v_role_flag_permissions" IS 'Flat read shape for lnk_role_flag_permissions — resolves permission code + rank.';

-- DOWN ====

DROP VIEW IF EXISTS "09_featureflags"."v_role_flag_permissions";
DROP TABLE IF EXISTS "09_featureflags"."40_lnk_role_flag_permissions";
