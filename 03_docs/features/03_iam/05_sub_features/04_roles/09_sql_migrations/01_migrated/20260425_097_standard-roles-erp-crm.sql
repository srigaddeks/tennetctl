-- UP ====

-- Standard role + permission set for somaerp + somacrm.
--
-- Adds:
--   * 7 dim_feature_flags rows (41..47) — one per ERP/CRM resource family
--   * 28 dim_feature_permissions rows (139..166) — view/create/update/delete
--     for each of the 7 flags
--   * fct_applications row for somacrm (somaerp + solsocial already exist)
--   * 7 fct_roles rows + dtl_attrs (code/label/description) for the standard
--     role set:
--       somaerp.kitchen_staff   — read recipes/production, create batches
--       somaerp.rider           — read deliveries, update run status
--       somaerp.ops_manager     — full ERP except admin/configure
--       somaerp.admin           — every ERP permission
--       somacrm.viewer          — read-only across CRM
--       somacrm.sales_rep       — read + create/update contacts/deals/activities
--       somacrm.admin           — every CRM permission
--   * lnk_role_feature_permissions rows mapping each role to its permission set.
--
-- All UUIDs are deterministic (019dc400-* family) so the migration is
-- idempotent and re-runnable.

-- ── Feature flag category for SaaS apps (somacrm/somaerp/etc.) ───────────
INSERT INTO "09_featureflags"."02_dim_feature_flag_categories"
    (id, code, label, description, sort_order, deprecated_at)
VALUES (9, 'apps', 'Apps', 'SaaS apps consuming tennetctl primitives — somacrm, somaerp, etc.', 90, NULL)
ON CONFLICT (id) DO NOTHING;

-- ── Feature flags ────────────────────────────────────────────────────────
INSERT INTO "09_featureflags"."03_dim_feature_flags"
    (id, code, name, description, category_id, feature_scope, access_mode, lifecycle_state,
     env_dev, env_staging, env_prod, rollout_mode, required_license, deprecated_at)
VALUES
    (41, 'somacrm_contacts',   'somacrm — Contacts',   'CRM contact records.',
     9, 'product', 'permissioned', 'active', TRUE, TRUE, TRUE, 'simple', NULL, NULL),
    (42, 'somacrm_deals',      'somacrm — Deals',      'CRM deal pipeline.',
     9, 'product', 'permissioned', 'active', TRUE, TRUE, TRUE, 'simple', NULL, NULL),
    (43, 'somacrm_activities', 'somacrm — Activities', 'Calls, emails, meetings, notes against contacts.',
     9, 'product', 'permissioned', 'active', TRUE, TRUE, TRUE, 'simple', NULL, NULL),
    (44, 'somaerp_kitchens',   'somaerp — Kitchens',   'Production facilities (locations + service zones).',
     9, 'product', 'permissioned', 'active', TRUE, TRUE, TRUE, 'simple', NULL, NULL),
    (45, 'somaerp_recipes',    'somaerp — Recipes',    'Recipe versions + BOMs + COGS rollups.',
     9, 'product', 'permissioned', 'active', TRUE, TRUE, TRUE, 'simple', NULL, NULL),
    (46, 'somaerp_production', 'somaerp — Production', 'Production batches + inventory consumption.',
     9, 'product', 'permissioned', 'active', TRUE, TRUE, TRUE, 'simple', NULL, NULL),
    (47, 'somaerp_deliveries', 'somaerp — Deliveries', 'Delivery routes, riders, runs, customer subscriptions.',
     9, 'product', 'permissioned', 'active', TRUE, TRUE, TRUE, 'simple', NULL, NULL)
ON CONFLICT (id) DO NOTHING;

-- ── Permissions (flag × action) ─────────────────────────────────────────
-- 7 flags × 4 actions (view/create/update/delete) = 28 permissions.
INSERT INTO "09_featureflags"."04_dim_feature_permissions" (id, flag_id, action_id, code, name, description, deprecated_at)
VALUES
    (139, 41, 1, 'somacrm_contacts.view',     'somacrm Contacts — View',     'Read CRM contacts.', NULL),
    (140, 41, 2, 'somacrm_contacts.create',   'somacrm Contacts — Create',   'Create CRM contacts.', NULL),
    (141, 41, 3, 'somacrm_contacts.update',   'somacrm Contacts — Update',   'Edit CRM contacts.', NULL),
    (142, 41, 4, 'somacrm_contacts.delete',   'somacrm Contacts — Delete',   'Soft-delete CRM contacts.', NULL),

    (143, 42, 1, 'somacrm_deals.view',        'somacrm Deals — View',        'Read deals.', NULL),
    (144, 42, 2, 'somacrm_deals.create',      'somacrm Deals — Create',      'Create deals.', NULL),
    (145, 42, 3, 'somacrm_deals.update',      'somacrm Deals — Update',      'Edit deals (incl. stage transitions).', NULL),
    (146, 42, 4, 'somacrm_deals.delete',      'somacrm Deals — Delete',      'Soft-delete deals.', NULL),

    (147, 43, 1, 'somacrm_activities.view',   'somacrm Activities — View',   'Read activities.', NULL),
    (148, 43, 2, 'somacrm_activities.create', 'somacrm Activities — Create', 'Log activities.', NULL),
    (149, 43, 3, 'somacrm_activities.update', 'somacrm Activities — Update', 'Edit activities.', NULL),
    (150, 43, 4, 'somacrm_activities.delete', 'somacrm Activities — Delete', 'Soft-delete activities.', NULL),

    (151, 44, 1, 'somaerp_kitchens.view',     'somaerp Kitchens — View',     'Read kitchens, locations, service zones.', NULL),
    (152, 44, 2, 'somaerp_kitchens.create',   'somaerp Kitchens — Create',   'Add new kitchens, zones.', NULL),
    (153, 44, 3, 'somaerp_kitchens.update',   'somaerp Kitchens — Update',   'Edit kitchens, zones.', NULL),
    (154, 44, 4, 'somaerp_kitchens.delete',   'somaerp Kitchens — Delete',   'Soft-delete kitchens, zones.', NULL),

    (155, 45, 1, 'somaerp_recipes.view',      'somaerp Recipes — View',      'Read recipes + BOMs.', NULL),
    (156, 45, 2, 'somaerp_recipes.create',    'somaerp Recipes — Create',    'Create recipes.', NULL),
    (157, 45, 3, 'somaerp_recipes.update',    'somaerp Recipes — Update',    'Edit recipes.', NULL),
    (158, 45, 4, 'somaerp_recipes.delete',    'somaerp Recipes — Delete',    'Soft-delete recipes.', NULL),

    (159, 46, 1, 'somaerp_production.view',   'somaerp Production — View',   'Read production batches.', NULL),
    (160, 46, 2, 'somaerp_production.create', 'somaerp Production — Create', 'Plan + start batches.', NULL),
    (161, 46, 3, 'somaerp_production.update', 'somaerp Production — Update', 'Update batch status, yields.', NULL),
    (162, 46, 4, 'somaerp_production.delete', 'somaerp Production — Delete', 'Cancel batches.', NULL),

    (163, 47, 1, 'somaerp_deliveries.view',   'somaerp Deliveries — View',   'Read deliveries, routes, runs.', NULL),
    (164, 47, 2, 'somaerp_deliveries.create', 'somaerp Deliveries — Create', 'Plan deliveries, routes.', NULL),
    (165, 47, 3, 'somaerp_deliveries.update', 'somaerp Deliveries — Update', 'Update run status, rider assignments.', NULL),
    (166, 47, 4, 'somaerp_deliveries.delete', 'somaerp Deliveries — Delete', 'Cancel deliveries.', NULL)
ON CONFLICT (id) DO NOTHING;

-- ── Register somacrm application ────────────────────────────────────────
-- somaerp + solsocial already exist; this adds somacrm.
DO $$
DECLARE
    default_org_id VARCHAR(36);
    sys_user_id    VARCHAR(36);
    crm_app_id     VARCHAR(36) := '019dc400-1001-7000-8000-000000000001';
BEGIN
    SELECT id INTO default_org_id FROM "03_iam"."10_fct_orgs" ORDER BY created_at LIMIT 1;
    SELECT id INTO sys_user_id    FROM "03_iam"."12_fct_users" WHERE deleted_at IS NULL ORDER BY created_at LIMIT 1;

    -- Fresh install (no org / no user)? Skip tenant data; the dim flag/permission
    -- rows above remain so the lookup catalog is complete.
    IF default_org_id IS NULL OR sys_user_id IS NULL THEN
        RAISE NOTICE 'no org / user yet — skipping somacrm app + standard roles';
        RETURN;
    END IF;

    -- Insert somacrm app (no-op on conflict).
    INSERT INTO "03_iam"."15_fct_applications"
        (id, org_id, is_active, is_test, created_by, updated_by)
    VALUES (crm_app_id, default_org_id, TRUE, FALSE, sys_user_id, sys_user_id)
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO "03_iam"."21_dtl_attrs"
        (id, entity_type_id, entity_id, attr_def_id, key_text)
    VALUES
        ('019dc400-1011-7000-8000-000000000001', 6, crm_app_id,
         (SELECT id FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id=6 AND code='code'),
         'somacrm'),
        ('019dc400-1012-7000-8000-000000000001', 6, crm_app_id,
         (SELECT id FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id=6 AND code='label'),
         'somacrm'),
        ('019dc400-1013-7000-8000-000000000001', 6, crm_app_id,
         (SELECT id FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id=6 AND code='description'),
         'CRM app for managing contacts, organizations, leads, deals, activities, and reports.')
    ON CONFLICT (id) DO NOTHING;
END $$;

-- ── Standard roles ───────────────────────────────────────────────────────
DO $$
DECLARE
    default_org_id VARCHAR(36);
    sys_user_id    VARCHAR(36);
    crm_app_id     VARCHAR(36) := '019dc400-1001-7000-8000-000000000001';
    erp_app_id     VARCHAR(36);

    code_def      SMALLINT;
    label_def     SMALLINT;
    desc_def      SMALLINT;

    -- Role IDs
    r_kitchen     VARCHAR(36) := '019dc400-2001-7000-8000-000000000001';
    r_rider       VARCHAR(36) := '019dc400-2002-7000-8000-000000000001';
    r_ops_manager VARCHAR(36) := '019dc400-2003-7000-8000-000000000001';
    r_erp_admin   VARCHAR(36) := '019dc400-2004-7000-8000-000000000001';
    r_crm_viewer  VARCHAR(36) := '019dc400-2005-7000-8000-000000000001';
    r_crm_sales   VARCHAR(36) := '019dc400-2006-7000-8000-000000000001';
    r_crm_admin   VARCHAR(36) := '019dc400-2007-7000-8000-000000000001';
BEGIN
    SELECT id INTO default_org_id FROM "03_iam"."10_fct_orgs" ORDER BY created_at LIMIT 1;
    SELECT id INTO sys_user_id    FROM "03_iam"."12_fct_users" WHERE deleted_at IS NULL ORDER BY created_at LIMIT 1;

    IF default_org_id IS NULL OR sys_user_id IS NULL THEN
        RAISE NOTICE 'no org / user yet — skipping standard roles';
        RETURN;
    END IF;

    SELECT a.id INTO erp_app_id   FROM "03_iam"."15_fct_applications" a
        JOIN "03_iam"."21_dtl_attrs" att ON att.entity_id = a.id
        JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = att.attr_def_id
        WHERE d.entity_type_id = 6 AND d.code = 'code' AND att.key_text = 'somaerp';

    SELECT id INTO code_def  FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id=4 AND code='code';
    SELECT id INTO label_def FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id=4 AND code='label';
    SELECT id INTO desc_def  FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id=4 AND code='description';

    -- Insert all 7 roles (custom type, application-scoped).
    INSERT INTO "03_iam"."13_fct_roles" (id, org_id, role_type_id, application_id, is_active, is_test, created_by, updated_by)
    VALUES
        (r_kitchen,     default_org_id, 2, erp_app_id, TRUE, FALSE, sys_user_id, sys_user_id),
        (r_rider,       default_org_id, 2, erp_app_id, TRUE, FALSE, sys_user_id, sys_user_id),
        (r_ops_manager, default_org_id, 2, erp_app_id, TRUE, FALSE, sys_user_id, sys_user_id),
        (r_erp_admin,   default_org_id, 2, erp_app_id, TRUE, FALSE, sys_user_id, sys_user_id),
        (r_crm_viewer,  default_org_id, 2, crm_app_id, TRUE, FALSE, sys_user_id, sys_user_id),
        (r_crm_sales,   default_org_id, 2, crm_app_id, TRUE, FALSE, sys_user_id, sys_user_id),
        (r_crm_admin,   default_org_id, 2, crm_app_id, TRUE, FALSE, sys_user_id, sys_user_id)
    ON CONFLICT (id) DO NOTHING;

    -- Role attrs (code, label, description for each).
    INSERT INTO "03_iam"."21_dtl_attrs" (id, entity_type_id, entity_id, attr_def_id, key_text)
    VALUES
        ('019dc400-3001-7000-8000-000000000001', 4, r_kitchen,     code_def,  'somaerp_kitchen_staff'),
        ('019dc400-3002-7000-8000-000000000001', 4, r_kitchen,     label_def, 'Kitchen Staff'),
        ('019dc400-3003-7000-8000-000000000001', 4, r_kitchen,     desc_def,  'Daily production crew. Reads recipes; creates + updates production batches.'),

        ('019dc400-3004-7000-8000-000000000001', 4, r_rider,       code_def,  'somaerp_rider'),
        ('019dc400-3005-7000-8000-000000000001', 4, r_rider,       label_def, 'Rider'),
        ('019dc400-3006-7000-8000-000000000001', 4, r_rider,       desc_def,  'Delivery rider. Reads delivery runs assigned to them; updates stop status.'),

        ('019dc400-3007-7000-8000-000000000001', 4, r_ops_manager, code_def,  'somaerp_ops_manager'),
        ('019dc400-3008-7000-8000-000000000001', 4, r_ops_manager, label_def, 'Ops Manager'),
        ('019dc400-3009-7000-8000-000000000001', 4, r_ops_manager, desc_def,  'Full ERP read/write across kitchens, recipes, production, deliveries. No admin/configure.'),

        ('019dc400-3010-7000-8000-000000000001', 4, r_erp_admin,   code_def,  'somaerp_admin'),
        ('019dc400-3011-7000-8000-000000000001', 4, r_erp_admin,   label_def, 'somaerp Admin'),
        ('019dc400-3012-7000-8000-000000000001', 4, r_erp_admin,   desc_def,  'Every ERP permission including delete + configure.'),

        ('019dc400-3013-7000-8000-000000000001', 4, r_crm_viewer,  code_def,  'somacrm_viewer'),
        ('019dc400-3014-7000-8000-000000000001', 4, r_crm_viewer,  label_def, 'CRM Viewer'),
        ('019dc400-3015-7000-8000-000000000001', 4, r_crm_viewer,  desc_def,  'Read-only across CRM contacts, deals, activities.'),

        ('019dc400-3016-7000-8000-000000000001', 4, r_crm_sales,   code_def,  'somacrm_sales_rep'),
        ('019dc400-3017-7000-8000-000000000001', 4, r_crm_sales,   label_def, 'Sales Rep'),
        ('019dc400-3018-7000-8000-000000000001', 4, r_crm_sales,   desc_def,  'Read + create/update across contacts, deals, activities. No delete.'),

        ('019dc400-3019-7000-8000-000000000001', 4, r_crm_admin,   code_def,  'somacrm_admin'),
        ('019dc400-3020-7000-8000-000000000001', 4, r_crm_admin,   label_def, 'somacrm Admin'),
        ('019dc400-3021-7000-8000-000000000001', 4, r_crm_admin,   desc_def,  'Every CRM permission including delete.')
    ON CONFLICT (id) DO NOTHING;

    -- ── Link roles to permissions ────────────────────────────────────
    -- Helper: insert (role, perm_id) skipping duplicates.
    INSERT INTO "09_featureflags"."40_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, created_by)
    VALUES
        -- Kitchen staff: read recipes + create/update production
        ('019dc400-4001-7000-8000-000000000001', r_kitchen, 155, sys_user_id), -- recipes.view
        ('019dc400-4002-7000-8000-000000000001', r_kitchen, 159, sys_user_id), -- production.view
        ('019dc400-4003-7000-8000-000000000001', r_kitchen, 160, sys_user_id), -- production.create
        ('019dc400-4004-7000-8000-000000000001', r_kitchen, 161, sys_user_id), -- production.update
        ('019dc400-4005-7000-8000-000000000001', r_kitchen, 151, sys_user_id), -- kitchens.view

        -- Rider: read deliveries + update run status
        ('019dc400-4006-7000-8000-000000000001', r_rider, 163, sys_user_id), -- deliveries.view
        ('019dc400-4007-7000-8000-000000000001', r_rider, 165, sys_user_id), -- deliveries.update

        -- Ops Manager: full read + create/update across all ERP
        ('019dc400-4008-7000-8000-000000000001', r_ops_manager, 151, sys_user_id),
        ('019dc400-4009-7000-8000-000000000001', r_ops_manager, 152, sys_user_id),
        ('019dc400-4010-7000-8000-000000000001', r_ops_manager, 153, sys_user_id),
        ('019dc400-4011-7000-8000-000000000001', r_ops_manager, 155, sys_user_id),
        ('019dc400-4012-7000-8000-000000000001', r_ops_manager, 156, sys_user_id),
        ('019dc400-4013-7000-8000-000000000001', r_ops_manager, 157, sys_user_id),
        ('019dc400-4014-7000-8000-000000000001', r_ops_manager, 159, sys_user_id),
        ('019dc400-4015-7000-8000-000000000001', r_ops_manager, 160, sys_user_id),
        ('019dc400-4016-7000-8000-000000000001', r_ops_manager, 161, sys_user_id),
        ('019dc400-4017-7000-8000-000000000001', r_ops_manager, 163, sys_user_id),
        ('019dc400-4018-7000-8000-000000000001', r_ops_manager, 164, sys_user_id),
        ('019dc400-4019-7000-8000-000000000001', r_ops_manager, 165, sys_user_id),

        -- ERP Admin: every ERP permission (151..166)
        ('019dc400-5001-7000-8000-000000000001', r_erp_admin, 151, sys_user_id),
        ('019dc400-5002-7000-8000-000000000001', r_erp_admin, 152, sys_user_id),
        ('019dc400-5003-7000-8000-000000000001', r_erp_admin, 153, sys_user_id),
        ('019dc400-5004-7000-8000-000000000001', r_erp_admin, 154, sys_user_id),
        ('019dc400-5005-7000-8000-000000000001', r_erp_admin, 155, sys_user_id),
        ('019dc400-5006-7000-8000-000000000001', r_erp_admin, 156, sys_user_id),
        ('019dc400-5007-7000-8000-000000000001', r_erp_admin, 157, sys_user_id),
        ('019dc400-5008-7000-8000-000000000001', r_erp_admin, 158, sys_user_id),
        ('019dc400-5009-7000-8000-000000000001', r_erp_admin, 159, sys_user_id),
        ('019dc400-5010-7000-8000-000000000001', r_erp_admin, 160, sys_user_id),
        ('019dc400-5011-7000-8000-000000000001', r_erp_admin, 161, sys_user_id),
        ('019dc400-5012-7000-8000-000000000001', r_erp_admin, 162, sys_user_id),
        ('019dc400-5013-7000-8000-000000000001', r_erp_admin, 163, sys_user_id),
        ('019dc400-5014-7000-8000-000000000001', r_erp_admin, 164, sys_user_id),
        ('019dc400-5015-7000-8000-000000000001', r_erp_admin, 165, sys_user_id),
        ('019dc400-5016-7000-8000-000000000001', r_erp_admin, 166, sys_user_id),

        -- CRM Viewer: read-only
        ('019dc400-6001-7000-8000-000000000001', r_crm_viewer, 139, sys_user_id),
        ('019dc400-6002-7000-8000-000000000001', r_crm_viewer, 143, sys_user_id),
        ('019dc400-6003-7000-8000-000000000001', r_crm_viewer, 147, sys_user_id),

        -- CRM Sales Rep: read + create/update (no delete)
        ('019dc400-6004-7000-8000-000000000001', r_crm_sales, 139, sys_user_id),
        ('019dc400-6005-7000-8000-000000000001', r_crm_sales, 140, sys_user_id),
        ('019dc400-6006-7000-8000-000000000001', r_crm_sales, 141, sys_user_id),
        ('019dc400-6007-7000-8000-000000000001', r_crm_sales, 143, sys_user_id),
        ('019dc400-6008-7000-8000-000000000001', r_crm_sales, 144, sys_user_id),
        ('019dc400-6009-7000-8000-000000000001', r_crm_sales, 145, sys_user_id),
        ('019dc400-6010-7000-8000-000000000001', r_crm_sales, 147, sys_user_id),
        ('019dc400-6011-7000-8000-000000000001', r_crm_sales, 148, sys_user_id),
        ('019dc400-6012-7000-8000-000000000001', r_crm_sales, 149, sys_user_id),

        -- CRM Admin: every CRM permission (139..150)
        ('019dc400-7001-7000-8000-000000000001', r_crm_admin, 139, sys_user_id),
        ('019dc400-7002-7000-8000-000000000001', r_crm_admin, 140, sys_user_id),
        ('019dc400-7003-7000-8000-000000000001', r_crm_admin, 141, sys_user_id),
        ('019dc400-7004-7000-8000-000000000001', r_crm_admin, 142, sys_user_id),
        ('019dc400-7005-7000-8000-000000000001', r_crm_admin, 143, sys_user_id),
        ('019dc400-7006-7000-8000-000000000001', r_crm_admin, 144, sys_user_id),
        ('019dc400-7007-7000-8000-000000000001', r_crm_admin, 145, sys_user_id),
        ('019dc400-7008-7000-8000-000000000001', r_crm_admin, 146, sys_user_id),
        ('019dc400-7009-7000-8000-000000000001', r_crm_admin, 147, sys_user_id),
        ('019dc400-7010-7000-8000-000000000001', r_crm_admin, 148, sys_user_id),
        ('019dc400-7011-7000-8000-000000000001', r_crm_admin, 149, sys_user_id),
        ('019dc400-7012-7000-8000-000000000001', r_crm_admin, 150, sys_user_id)
    ON CONFLICT (id) DO NOTHING;
END $$;

-- DOWN ====

DELETE FROM "09_featureflags"."40_lnk_role_feature_permissions"
 WHERE id LIKE '019dc400-%';
DELETE FROM "03_iam"."21_dtl_attrs"
 WHERE id LIKE '019dc400-%';
DELETE FROM "03_iam"."13_fct_roles"
 WHERE id LIKE '019dc400-2%';
DELETE FROM "03_iam"."15_fct_applications"
 WHERE id = '019dc400-1001-7000-8000-000000000001';
DELETE FROM "09_featureflags"."04_dim_feature_permissions"
 WHERE id BETWEEN 139 AND 166;
DELETE FROM "09_featureflags"."03_dim_feature_flags"
 WHERE id BETWEEN 41 AND 47;
DELETE FROM "09_featureflags"."02_dim_feature_flag_categories"
 WHERE id = 9;
