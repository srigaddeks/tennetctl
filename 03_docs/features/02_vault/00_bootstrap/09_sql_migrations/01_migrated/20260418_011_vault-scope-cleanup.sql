-- UP ====

-- Feature 02 (vault) — add scope model to secrets + clean up orphan soft-deleted rows.
-- Prepares vault for v0.3 scope-aware access (global / org / workspace).
-- See ADR-028 (updated) and plan 07-03.
--
-- Changes:
-- 1. New dim_scopes (3 rows: global/org/workspace) — shared by secrets + configs.
-- 2. Clean up orphan soft-deleted rows in fct_vault_entries (+ their dtl_attrs) so
--    bootstrap can re-seed deleted keys on the next boot.
-- 3. Add scope_id + org_id + workspace_id to fct_vault_entries with CHECK
--    constraints matching the scope.
-- 4. Drop the old (key, version) unique and add a scope-aware one so the same key
--    can coexist at global + org + workspace.
-- 5. Recreate v_vault_entries including the scope columns.

-- ── 1. dim_scopes ───────────────────────────────────────────────────

CREATE TABLE "02_vault"."02_dim_scopes" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_vault_dim_scopes PRIMARY KEY (id),
    CONSTRAINT uq_vault_dim_scopes_code UNIQUE (code)
);
COMMENT ON TABLE  "02_vault"."02_dim_scopes" IS 'Where a vault entry applies: global / org / workspace. Shared by fct_vault_entries and fct_vault_configs.';
COMMENT ON COLUMN "02_vault"."02_dim_scopes".id IS 'Permanent manual id. Never renumber.';
COMMENT ON COLUMN "02_vault"."02_dim_scopes".code IS 'Scope code (global, org, workspace).';
COMMENT ON COLUMN "02_vault"."02_dim_scopes".label IS 'Human-readable label.';
COMMENT ON COLUMN "02_vault"."02_dim_scopes".description IS 'Free-text description.';
COMMENT ON COLUMN "02_vault"."02_dim_scopes".deprecated_at IS 'Non-null when no longer in use.';

INSERT INTO "02_vault"."02_dim_scopes" (id, code, label, description) VALUES
    (1, 'global',    'Global',    'Platform-wide entry; no tenant context. org_id NULL, workspace_id NULL.'),
    (2, 'org',       'Org',       'Scoped to one org. org_id set, workspace_id NULL.'),
    (3, 'workspace', 'Workspace', 'Scoped to one workspace. org_id + workspace_id both set.')
ON CONFLICT (id) DO NOTHING;

-- ── 2. Clean up orphan soft-deleted rows ───────────────────────────

-- dtl_attrs first (FK from dtl_attrs.entity_id to fct_vault_entries.id is not
-- declared with CASCADE; handled explicitly).
DELETE FROM "02_vault"."21_dtl_attrs"
WHERE entity_type_id = 1
  AND entity_id IN (
      SELECT id FROM "02_vault"."10_fct_vault_entries" WHERE deleted_at IS NOT NULL
  );

-- Any row referenced by a live row's rotated_from_id is promoted to hard-delete
-- only if the pointing row is also deleted. Otherwise keep the history link.
-- In v0.2 the bootstrap keys and test rows cover the only real case: fully-deleted
-- chains. Defensive: clear rotated_from_id on live rows that point at deleted rows.
UPDATE "02_vault"."10_fct_vault_entries" live
SET rotated_from_id = NULL
WHERE live.deleted_at IS NULL
  AND live.rotated_from_id IN (
      SELECT id FROM "02_vault"."10_fct_vault_entries" WHERE deleted_at IS NOT NULL
  );

DELETE FROM "02_vault"."10_fct_vault_entries" WHERE deleted_at IS NOT NULL;

-- ── 3. Scope columns on fct_vault_entries ──────────────────────────

ALTER TABLE "02_vault"."10_fct_vault_entries"
    ADD COLUMN scope_id     SMALLINT NOT NULL DEFAULT 1,
    ADD COLUMN org_id       VARCHAR(36),
    ADD COLUMN workspace_id VARCHAR(36),
    ADD CONSTRAINT fk_fct_vault_entries_scope
        FOREIGN KEY (scope_id) REFERENCES "02_vault"."02_dim_scopes"(id),
    ADD CONSTRAINT chk_fct_vault_entries_scope_shape CHECK (
        (scope_id = 1 AND org_id IS NULL     AND workspace_id IS NULL)
     OR (scope_id = 2 AND org_id IS NOT NULL AND workspace_id IS NULL)
     OR (scope_id = 3 AND org_id IS NOT NULL AND workspace_id IS NOT NULL)
    );

COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".scope_id IS 'FK to dim_scopes. 1=global, 2=org, 3=workspace.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".org_id IS 'Required for scope=org/workspace. NULL for global.';
COMMENT ON COLUMN "02_vault"."10_fct_vault_entries".workspace_id IS 'Required for scope=workspace. NULL for global/org.';

-- ── 4. Swap uniqueness constraint to include scope ─────────────────

ALTER TABLE "02_vault"."10_fct_vault_entries"
    DROP CONSTRAINT IF EXISTS uq_fct_vault_entries_key_version;

-- COALESCE with the zero UUID so the unique index treats NULL identically
-- across rows at the same scope level.
CREATE UNIQUE INDEX uq_fct_vault_entries_scope_key_version
    ON "02_vault"."10_fct_vault_entries" (
        scope_id,
        COALESCE(org_id,       '00000000-0000-0000-0000-000000000000'),
        COALESCE(workspace_id, '00000000-0000-0000-0000-000000000000'),
        key,
        version
    );

-- Keep the latest-version partial index; scope column adds no selectivity beyond
-- the existing (key, version DESC) ordering for single-scope lookups. Leave as-is.

-- ── 5. Recreate v_vault_entries with scope ─────────────────────────

DROP VIEW IF EXISTS "02_vault"."v_vault_entries";

CREATE VIEW "02_vault"."v_vault_entries" AS
SELECT
    latest.id,
    latest.key,
    latest.version,
    MAX(da.key_text) FILTER (WHERE ad.code = 'description') AS description,
    latest.scope_id,
    ds.code AS scope,
    latest.org_id,
    latest.workspace_id,
    latest.is_active,
    latest.is_test,
    latest.deleted_at,
    latest.rotated_from_id,
    latest.created_by,
    latest.updated_by,
    latest.created_at,
    latest.updated_at
FROM (
    SELECT DISTINCT ON (scope_id, org_id, workspace_id, key)
        id, key, version, scope_id, org_id, workspace_id,
        is_active, is_test, deleted_at, rotated_from_id,
        created_by, updated_by, created_at, updated_at
    FROM "02_vault"."10_fct_vault_entries"
    WHERE deleted_at IS NULL
    ORDER BY scope_id, org_id, workspace_id, key, version DESC
) latest
JOIN "02_vault"."02_dim_scopes" ds ON ds.id = latest.scope_id
LEFT JOIN "02_vault"."21_dtl_attrs" da
    ON da.entity_type_id = 1 AND da.entity_id = latest.id
LEFT JOIN "02_vault"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    latest.id, latest.key, latest.version, latest.scope_id, ds.code,
    latest.org_id, latest.workspace_id, latest.is_active, latest.is_test,
    latest.deleted_at, latest.rotated_from_id, latest.created_by,
    latest.updated_by, latest.created_at, latest.updated_at;

COMMENT ON VIEW "02_vault"."v_vault_entries" IS 'Flat read shape for secrets — latest non-deleted per (scope, key), description pivoted from dtl_attrs, scope code joined. Metadata only.';

-- DOWN ====

DROP VIEW IF EXISTS "02_vault"."v_vault_entries";

-- Restore the prior view shape (no scope columns).
CREATE VIEW "02_vault"."v_vault_entries" AS
SELECT
    latest.id,
    latest.key,
    latest.version,
    MAX(da.key_text) FILTER (WHERE ad.code = 'description') AS description,
    latest.is_active,
    latest.is_test,
    latest.deleted_at,
    latest.rotated_from_id,
    latest.created_by,
    latest.updated_by,
    latest.created_at,
    latest.updated_at
FROM (
    SELECT DISTINCT ON (key)
        id, key, version, is_active, is_test, deleted_at, rotated_from_id,
        created_by, updated_by, created_at, updated_at
    FROM "02_vault"."10_fct_vault_entries"
    WHERE deleted_at IS NULL
    ORDER BY key, version DESC
) latest
LEFT JOIN "02_vault"."21_dtl_attrs" da
    ON da.entity_type_id = 1 AND da.entity_id = latest.id
LEFT JOIN "02_vault"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    latest.id, latest.key, latest.version, latest.is_active, latest.is_test,
    latest.deleted_at, latest.rotated_from_id, latest.created_by,
    latest.updated_by, latest.created_at, latest.updated_at;

DROP INDEX IF EXISTS "02_vault".uq_fct_vault_entries_scope_key_version;

ALTER TABLE "02_vault"."10_fct_vault_entries"
    DROP CONSTRAINT IF EXISTS chk_fct_vault_entries_scope_shape,
    DROP CONSTRAINT IF EXISTS fk_fct_vault_entries_scope,
    DROP COLUMN IF EXISTS workspace_id,
    DROP COLUMN IF EXISTS org_id,
    DROP COLUMN IF EXISTS scope_id;

-- Restore the old (key, version) uniqueness.
ALTER TABLE "02_vault"."10_fct_vault_entries"
    ADD CONSTRAINT uq_fct_vault_entries_key_version UNIQUE (key, version);

DROP TABLE IF EXISTS "02_vault"."02_dim_scopes";
