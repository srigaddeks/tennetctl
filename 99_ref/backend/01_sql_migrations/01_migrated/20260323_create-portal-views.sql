-- ============================================================================
-- Portal Views — dimension table + role-view mapping
-- ============================================================================
-- Views define which subset of the UI a user sees. A role can be associated
-- with one or more views. When a user has multiple roles each granting
-- different views, they see a view switcher.
-- ============================================================================

-- ── Dimension: portal views ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."50_dim_portal_views" (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    description     TEXT,
    color           TEXT,           -- hex color for UI pill
    icon            TEXT,           -- lucide icon name
    sort_order      INT NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Seed the 5 standard views ───────────────────────────────────────────────

INSERT INTO "03_auth_manage"."50_dim_portal_views" (code, name, description, color, icon, sort_order)
VALUES
    ('grc',         'GRC Practitioner',   'Full compliance management — frameworks, controls, risks, tasks, tests',                     '#2878ff', 'ShieldCheck',    10),
    ('auditor',     'External Auditor',   'Read-only compliance view — evidence requests, control testing, findings',                    '#6366f1', 'Search',         20),
    ('engineering', 'Engineering',        'Task-focused view — my tasks, evidence to submit, owned controls, test results',              '#10b981', 'Wrench',         30),
    ('executive',   'CISO / Executive',   'Board-level read-only view — security posture, risk summary, framework status',               '#f59e0b', 'BarChart3',      40),
    ('vendor',      'Vendor',             'Vendor portal — questionnaire, document upload, review status',                               '#06b6d4', 'Building2',      50)
ON CONFLICT (code) DO NOTHING;

-- ── Link: role → views ──────────────────────────────────────────────────────
-- A role can grant access to multiple views.
-- When evaluating a user's available views, we union all views from all roles
-- the user inherits through group membership.

CREATE TABLE IF NOT EXISTS "03_auth_manage"."51_lnk_role_views" (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id         UUID NOT NULL REFERENCES "03_auth_manage"."16_fct_roles"(id),
    view_code       TEXT NOT NULL REFERENCES "03_auth_manage"."50_dim_portal_views"(code),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      UUID,
    UNIQUE (role_id, view_code)
);

CREATE INDEX IF NOT EXISTS idx_role_views_role ON "03_auth_manage"."51_lnk_role_views"(role_id);
CREATE INDEX IF NOT EXISTS idx_role_views_view ON "03_auth_manage"."51_lnk_role_views"(view_code);

-- ── View route definitions ──────────────────────────────────────────────────
-- Stores which frontend routes each view is allowed to access.
-- This is the source of truth for both sidebar filtering and ViewGuard.

CREATE TABLE IF NOT EXISTS "03_auth_manage"."52_dtl_view_routes" (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    view_code       TEXT NOT NULL REFERENCES "03_auth_manage"."50_dim_portal_views"(code),
    route_prefix    TEXT NOT NULL,       -- e.g. '/dashboard', '/risks'
    is_read_only    BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order      INT NOT NULL DEFAULT 0,
    sidebar_label   TEXT,                -- label in sidebar nav (null = don't show in sidebar)
    sidebar_icon    TEXT,                -- lucide icon name
    sidebar_section TEXT,                -- sidebar group label
    UNIQUE (view_code, route_prefix)
);

-- ── Seed view routes ────────────────────────────────────────────────────────

-- GRC Practitioner (full access)
INSERT INTO "03_auth_manage"."52_dtl_view_routes" (view_code, route_prefix, is_read_only, sort_order, sidebar_label, sidebar_icon, sidebar_section) VALUES
    ('grc', '/dashboard',   FALSE, 10, 'Dashboard',      'LayoutDashboard', 'Navigate'),
    ('grc', '/frameworks',  FALSE, 20, 'Frameworks',     'Library',         'GRC Platform'),
    ('grc', '/controls',    FALSE, 30, 'Controls',       'ShieldCheck',     'GRC Platform'),
    ('grc', '/tests',       FALSE, 40, 'Control Tests',  'FlaskConical',    'GRC Platform'),
    ('grc', '/risks',       FALSE, 50, 'Risk Registry',  'ShieldAlert',     'GRC Platform'),
    ('grc', '/tasks',       FALSE, 60, 'Tasks',          'CheckSquare',     'GRC Platform'),
    ('grc', '/workspaces',  FALSE, 70, 'Workspaces',     'Layers',          'Administration')
ON CONFLICT (view_code, route_prefix) DO NOTHING;

-- External Auditor (read-only compliance)
INSERT INTO "03_auth_manage"."52_dtl_view_routes" (view_code, route_prefix, is_read_only, sort_order, sidebar_label, sidebar_icon, sidebar_section) VALUES
    ('auditor', '/dashboard',   TRUE,  10, 'Dashboard',      'LayoutDashboard', 'Audit'),
    ('auditor', '/frameworks',  TRUE,  20, 'Frameworks',     'Library',         'Compliance'),
    ('auditor', '/controls',    TRUE,  30, 'Controls',       'ShieldCheck',     'Compliance'),
    ('auditor', '/tests',       TRUE,  40, 'Tests',          'FlaskConical',    'Compliance')
ON CONFLICT (view_code, route_prefix) DO NOTHING;

-- Engineering (task-focused)
INSERT INTO "03_auth_manage"."52_dtl_view_routes" (view_code, route_prefix, is_read_only, sort_order, sidebar_label, sidebar_icon, sidebar_section) VALUES
    ('engineering', '/dashboard',  FALSE, 10, 'Dashboard',    'LayoutDashboard', 'My Work'),
    ('engineering', '/tasks',      FALSE, 20, 'Tasks',        'CheckSquare',     'My Work'),
    ('engineering', '/controls',   TRUE,  30, 'Controls',     'ShieldCheck',     'Controls I Own'),
    ('engineering', '/tests',      TRUE,  40, 'Test Results', 'FlaskConical',    'Controls I Own')
ON CONFLICT (view_code, route_prefix) DO NOTHING;

-- Executive (read-only board view)
INSERT INTO "03_auth_manage"."52_dtl_view_routes" (view_code, route_prefix, is_read_only, sort_order, sidebar_label, sidebar_icon, sidebar_section) VALUES
    ('executive', '/dashboard',   TRUE,  10, 'Security Posture', 'LayoutDashboard', 'Board View'),
    ('executive', '/risks',       TRUE,  20, 'Risk Summary',     'ShieldAlert',     'Board View'),
    ('executive', '/frameworks',  TRUE,  30, 'Frameworks',       'Library',         'Board View')
ON CONFLICT (view_code, route_prefix) DO NOTHING;

-- Vendor (portal)
INSERT INTO "03_auth_manage"."52_dtl_view_routes" (view_code, route_prefix, is_read_only, sort_order, sidebar_label, sidebar_icon, sidebar_section) VALUES
    ('vendor', '/dashboard',  FALSE, 10, 'Dashboard', 'LayoutDashboard', 'My Assessment'),
    ('vendor', '/tasks',      FALSE, 20, 'Tasks',     'CheckSquare',     'My Assessment')
ON CONFLICT (view_code, route_prefix) DO NOTHING;

-- ── Seed default role-view assignments ──────────────────────────────────────
-- Assign the GRC Practitioner view to all existing system roles so current
-- users see no change.  Admins can refine assignments later via the Portal
-- Views admin page.

INSERT INTO "03_auth_manage"."51_lnk_role_views" (role_id, view_code)
SELECT r.id, 'grc'
FROM "03_auth_manage"."16_fct_roles" r
WHERE r.is_active = TRUE
  AND r.is_deleted = FALSE
ON CONFLICT (role_id, view_code) DO NOTHING;
