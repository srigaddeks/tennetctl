---
paths:
  - "**/*.sql"
  - "**/*.py"
  - "**/*.ts"
---

# Database Conventions

Project-specific DB rules. Claude knows SQL and PostgreSQL — this file covers our deviations.

## Table Type System

| Prefix | # Range | Purpose | PK | Mandatory columns |
| --- | --- | --- | --- | --- |
| `dim_*` | 01–09 | Lookup enums — seeded, never mutated | SMALLINT | id, code, label, description, deprecated_at |
| `fct_*` | 10–19 | Entity identity — UUIDs + FK IDs only. No strings. No JSONB. | VARCHAR(36) UUID v7 | id, is_active, is_test, deleted_at, created_by, updated_by, created_at, updated_at |
| `dtl_*` | 20–29 | EAV attributes or fixed detail schema | UUID v7 | varies |
| `lnk_*` | 40–59 | Many-to-many — immutable rows | UUID v7 | id, org_id, created_by, created_at. **NO updated_at** |
| `evt_*` | 60–79 | Append-only events | UUID v7 | id, org_id, actor_id, metadata JSONB, created_at. **NO updated_at, NO deleted_at** |

## Critical Rules

- **NEVER add business columns to existing `fct_*` tables.** Use EAV `dtl_*` layer instead.
- **NEVER use Postgres ENUMs.** Use `dim_*` tables (INSERT-only, extend without DDL).
- **NEVER put JSONB or strings in `fct_*`.** Strings go in `dtl_*`, JSONB in `dtl_*` or `evt_*`.
- **dim_* IDs are permanent.** Never renumber. Never DELETE rows. Use `deprecated_at`.
- **`updated_at` is set by the application** — explicitly in every UPDATE statement. No triggers exist. `lnk_*` and `evt_*` have no `updated_at`.
- Use `TIMESTAMP` not `TIMESTAMPTZ` — app always passes UTC.
- Use `CURRENT_TIMESTAMP` not `now()`.
- `deleted_at TIMESTAMP` not `is_deleted BOOLEAN`.
- No `NULLS NOT DISTINCT` — use partial unique index instead.

## EAV Pattern

- `dtl_*` stores attributes as rows: `(entity_type_id, entity_id, attr_def_id, key_text|key_jsonb|key_smallint)`
- Register every attribute in `dim_attr_defs` before use.
- `key_text` for strings/PII, `key_jsonb` for objects/arrays, `key_smallint` for FK to dim tables.
- One value column non-NULL per row.

## Read/Write Split

- Reads → `v_{entity}` view (resolves dim codes, derives is_deleted, coalesces nulls)
- Writes → raw `{nn}_fct_{entity}` + dtl tables

**Drop views in dependency order** when modifying — drop dependents first, then recreate bottom-up.

## Migrations

File: `YYYYMMDD_{NNN}_{description}.sql` (NNN = **global** 3-digit sequence — unique across all sub-features)

Every file has `-- UP ====` and `-- DOWN ====` sections. DOWN must completely revert UP. COMMENT ON every table and column. All constraints explicitly named (`pk_`, `fk_`, `uq_`, `chk_`, `idx_`, `trg_`).

**Location (feature-distributed):**
```
03_docs/features/{nn}_{feature}/05_sub_features/{nn}_{sub}/09_sql_migrations/
  02_in_progress/   ← write new migrations here
  01_migrated/      ← migrator moves files here after apply
  seeds/            ← YAML or JSON seed files for dim_* tables
```

The migrator discovers all `02_in_progress/*.sql` files recursively and sorts globally by filename. After applying, each file is moved to `01_migrated/`. Rollback moves it back to `02_in_progress/`.

Schema-creation migrations (CREATE SCHEMA + shared dim/dtl tables) live in `00_bootstrap/` sub-feature, which sorts first by NNN convention.

**Seed files** (`seeds/*.yaml` or `seeds/*.json`) populate `dim_*` tables and are idempotent (ON CONFLICT DO NOTHING). Run with:
```bash
python -m backend.01_migrator.runner seed
```

Seed YAML format:
```yaml
schema: "03_iam"
table: "01_dim_account_types"
rows:
  - id: 1
    code: email_password
    label: Email + Password
    description: Standard email and password authentication
    deprecated_at: null
```

**Scaffold a new migration:**
```bash
python -m backend.01_migrator.runner new --name create-iam-schema --feature 03_iam --sub 00_bootstrap
```
