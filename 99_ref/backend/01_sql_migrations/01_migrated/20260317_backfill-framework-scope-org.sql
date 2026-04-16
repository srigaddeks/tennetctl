-- Backfill scope_org_id on GRC library records created without org scoping.
-- Assigns each tenant's un-scoped frameworks to that tenant's second org
-- (first real user org, skipping the auto-created personal org).
-- Platform records (tenant_key = '__platform__') keep NULL so they stay shared.
-- Safe to re-run: WHERE scope_org_id IS NULL guard.

UPDATE "05_grc_library"."10_fct_frameworks" f
SET    scope_org_id = (
           SELECT o.id
           FROM   "03_auth_manage"."29_fct_orgs" o
           WHERE  o.tenant_key = f.tenant_key
             AND  o.is_deleted  = FALSE
           ORDER  BY o.created_at ASC
           LIMIT  1
           OFFSET 1
       )
WHERE  f.scope_org_id IS NULL
  AND  f.tenant_key   != '__platform__'
  AND  f.is_deleted   = FALSE;
