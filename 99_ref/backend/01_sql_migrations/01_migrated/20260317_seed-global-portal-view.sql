-- ============================================================================
-- Seed the "Global" portal view — unrestricted access to all routes
-- ============================================================================
-- A special view that grants access to every route (/*). Useful for super
-- admins and platform operators who need full visibility across all modules.
-- ============================================================================

-- ── Insert the global view ────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."50_dim_portal_views" (code, name, description, color, icon, sort_order)
VALUES
    ('global', 'Global', 'Unrestricted access — all routes and modules visible', '#ef4444', 'Globe', 1)
ON CONFLICT (code) DO NOTHING;

-- ── Single wildcard route: /* ─────────────────────────────────────────────

INSERT INTO "03_auth_manage"."52_dtl_view_routes" (view_code, route_prefix, is_read_only, sort_order, sidebar_label, sidebar_icon, sidebar_section) VALUES
    ('global', '/*', FALSE, 0, NULL, NULL, NULL)
ON CONFLICT (view_code, route_prefix) DO NOTHING;

-- ── Assign global view to platform admin role ─────────────────────────────

INSERT INTO "03_auth_manage"."51_lnk_role_views" (role_id, view_code)
VALUES ('00000000-0000-0000-0000-000000000601'::UUID, 'global')
ON CONFLICT (role_id, view_code) DO NOTHING;
