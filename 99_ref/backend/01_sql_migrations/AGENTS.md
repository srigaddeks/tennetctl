# SQL Migration AGENTS.md

Last updated: 2026-03-13

## Purpose

This folder contains all database migration SQL files for the backend.
Migrations run automatically at app startup when `APP_RUN_MIGRATIONS_ON_STARTUP=true`.

Two directories with distinct roles:

- `01_migrated/` — Deployed migration history. Scanned at runtime. **Immutable once merged to main.**
- `02_inprogress/` — Development staging area. **NOT scanned at runtime.** Used for work-in-progress SQL before promotion.

## How it works

1. The app startup runner (`database.py:apply_sql_migrations()`) scans only `01_migrated/`.
2. It checks each `.sql` file against the `01_dev_features.01_schema_migration` tracking table.
3. Already-applied migrations are skipped. New ones are executed in sorted order (CREATE SCHEMA first).
4. A PostgreSQL advisory lock ensures only one pod runs migrations at a time (HPA-safe).

## Workflow

1. Write new migration SQL in `02_inprogress/` following the naming convention.
2. Test locally.
3. When ready, move the file from `02_inprogress/` to `01_migrated/` in git.
4. Merge to main. On deployment, the migration runs automatically.

## Hard rules

1. Never modify, rename, delete, or reorder anything inside `01_migrated/` after it has been deployed.
2. Treat `01_migrated/` as immutable deployed history.
3. Do all active migration work inside `02_inprogress/`.
4. Move a file from `02_inprogress/` to `01_migrated/` only when ready for deployment.

## File naming convention

Format: `YYYYMMDD_short-explanation.sql`

- Use calendar date prefix in `YYYYMMDD` format.
- Use lowercase words separated by hyphens.
- Keep description short but specific.

Examples:

- `20260313_create-auth-core.sql`
- `20260314_add-session-audit-indexes.sql`

## Review checklist

- Does the filename follow `YYYYMMDD_short-explanation.sql`?
- Is `01_migrated/` untouched (no edits to existing files)?
- Does the SQL use `IF NOT EXISTS` / `IF EXISTS` for idempotency?
- Are cross-file FK dependencies satisfied by alphabetical sort order?
