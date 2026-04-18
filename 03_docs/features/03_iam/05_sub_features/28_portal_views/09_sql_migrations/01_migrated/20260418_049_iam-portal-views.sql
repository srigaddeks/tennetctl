-- ============================================================
-- Migration : 20260418_049_iam-portal-views
-- Feature   : 03_iam / 28_portal_views
-- Purpose   : Portal view catalog + role→view grants
--
-- Tables created:
--   "03_iam"."08_dim_portal_views"   — seeded lookup of available UI portals
--   "03_iam"."46_lnk_role_views"     — many-to-many role → portal view
-- ============================================================

-- UP ====

-- ── dim: portal view catalog ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "03_iam"."08_dim_portal_views" (
    id           SMALLINT    NOT NULL,
    code         TEXT        NOT NULL,
    label        TEXT        NOT NULL,
    icon         TEXT,
    color        TEXT,
    default_route TEXT       NOT NULL,
    sort_order   SMALLINT    NOT NULL DEFAULT 0,
    deprecated_at TIMESTAMP,
    CONSTRAINT pk_dim_portal_views PRIMARY KEY (id),
    CONSTRAINT uq_dim_portal_views_code UNIQUE (code)
);

COMMENT ON TABLE  "03_iam"."08_dim_portal_views"               IS 'Lookup catalog of UI portal views. Rows are seeded; never deleted — deprecate via deprecated_at.';
COMMENT ON COLUMN "03_iam"."08_dim_portal_views".id            IS 'Stable SMALLINT PK. Never renumber.';
COMMENT ON COLUMN "03_iam"."08_dim_portal_views".code          IS 'Machine-stable code used in navigation config (e.g. "platform", "iam").';
COMMENT ON COLUMN "03_iam"."08_dim_portal_views".label         IS 'Human-readable nav label.';
COMMENT ON COLUMN "03_iam"."08_dim_portal_views".icon          IS 'Lucide icon name rendered in the nav shell.';
COMMENT ON COLUMN "03_iam"."08_dim_portal_views".color         IS 'Hex colour or Tailwind class for the view accent.';
COMMENT ON COLUMN "03_iam"."08_dim_portal_views".default_route IS 'Frontend route the nav link targets.';
COMMENT ON COLUMN "03_iam"."08_dim_portal_views".sort_order    IS 'Ascending display order in the nav shell.';
COMMENT ON COLUMN "03_iam"."08_dim_portal_views".deprecated_at IS 'Non-NULL = view retired; excluded from active catalogs.';

-- ── seeds ─────────────────────────────────────────────────────────────
INSERT INTO "03_iam"."08_dim_portal_views"
    (id, code, label, icon, color, default_route, sort_order)
VALUES
    (1, 'platform',   'Platform',      'LayoutDashboard', '#3B82F6', '/',                 10),
    (2, 'iam',        'Identity',      'ShieldCheck',     '#8B5CF6', '/iam/orgs',         20),
    (3, 'flags',      'Feature Flags', 'Flag',            '#F59E0B', '/feature-flags',    30),
    (4, 'vault',      'Vault',         'Lock',            '#10B981', '/vault/secrets',    40),
    (5, 'monitoring', 'Monitoring',    'Activity',        '#EF4444', '/monitoring',       50),
    (6, 'audit',      'Audit',         'FileText',        '#6366F1', '/audit',            60),
    (7, 'notify',     'Notify',        'Send',            '#EC4899', '/notify/templates', 70)
ON CONFLICT (id) DO NOTHING;

-- ── lnk: role → portal view ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "03_iam"."46_lnk_role_views" (
    id          VARCHAR(36)  NOT NULL,
    role_id     VARCHAR(36)  NOT NULL,
    view_id     SMALLINT     NOT NULL,
    org_id      VARCHAR(36)  NOT NULL,
    created_by  VARCHAR(36)  NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_lnk_role_views        PRIMARY KEY (id),
    CONSTRAINT uq_lnk_role_views        UNIQUE (role_id, view_id),
    CONSTRAINT fk_lnk_role_views_role   FOREIGN KEY (role_id)  REFERENCES "03_iam"."13_fct_roles"(id),
    CONSTRAINT fk_lnk_role_views_view   FOREIGN KEY (view_id)  REFERENCES "03_iam"."08_dim_portal_views"(id)
);

COMMENT ON TABLE  "03_iam"."46_lnk_role_views"            IS 'Many-to-many: which portal views a role grants access to.';
COMMENT ON COLUMN "03_iam"."46_lnk_role_views".id         IS 'UUID v7 PK.';
COMMENT ON COLUMN "03_iam"."46_lnk_role_views".role_id    IS 'FK → 13_fct_roles.id.';
COMMENT ON COLUMN "03_iam"."46_lnk_role_views".view_id    IS 'FK → 08_dim_portal_views.id.';
COMMENT ON COLUMN "03_iam"."46_lnk_role_views".org_id     IS 'Org that owns this grant (for multi-tenant scoping).';
COMMENT ON COLUMN "03_iam"."46_lnk_role_views".created_by IS 'Actor who created the grant (UUID v7).';
COMMENT ON COLUMN "03_iam"."46_lnk_role_views".created_at IS 'Immutable — lnk tables have no updated_at.';

CREATE INDEX IF NOT EXISTS idx_lnk_role_views_role_id
    ON "03_iam"."46_lnk_role_views" (role_id);

CREATE INDEX IF NOT EXISTS idx_lnk_role_views_view_id
    ON "03_iam"."46_lnk_role_views" (view_id);

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."46_lnk_role_views";
DROP TABLE IF EXISTS "03_iam"."08_dim_portal_views";
