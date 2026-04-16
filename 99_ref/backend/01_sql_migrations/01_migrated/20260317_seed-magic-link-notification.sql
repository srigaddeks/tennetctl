-- Migration: Seed magic link login notification type
-- Adds magic_link_login to 04_dim_notification_types so the dispatcher can
-- queue transactional emails for passwordless auth.

INSERT INTO "03_notifications"."04_dim_notification_types" (
    id, code, name, description,
    category_code, is_mandatory, is_user_triggered,
    default_enabled, cooldown_seconds, sort_order,
    created_at, updated_at
) VALUES (
    'c0000000-0000-0000-0000-000000000020',
    'magic_link_login',
    'Magic Link Login',
    'Passwordless login link sent to user email',
    'security',
    TRUE,
    TRUE,
    TRUE,
    NULL,
    20,
    NOW(),
    NOW()
)
ON CONFLICT (code) DO NOTHING;
