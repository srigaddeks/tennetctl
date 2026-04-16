-- Add default_route to portal views + unique constraint on view routes
-- Allows setting a default landing page per portal view

ALTER TABLE "03_auth_manage"."50_dim_portal_views"
    ADD COLUMN IF NOT EXISTS default_route TEXT DEFAULT NULL;

-- Add description length check (safety)
ALTER TABLE "03_auth_manage"."50_dim_portal_views"
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Update existing views with sensible defaults
UPDATE "03_auth_manage"."50_dim_portal_views" SET default_route = '/dashboard' WHERE default_route IS NULL;

-- Ensure route sort_order has a default
ALTER TABLE "03_auth_manage"."52_dtl_view_routes"
    ALTER COLUMN sort_order SET DEFAULT 0;
