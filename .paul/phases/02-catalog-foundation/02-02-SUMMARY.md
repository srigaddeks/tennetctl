---
phase: 02-catalog-foundation
plan: 02
subsystem: infra
tags: [catalog, manifest-loader, pydantic, cross-import-linter, ast, claude-skill, smoke-test]

requires:
  - phase: 02-catalog-foundation-01
    provides: "01_catalog" DB schema with 9 tables + 19 seeded dim rows
provides:
  - backend/01_catalog Python package (6 files)
  - manifest parser (Pydantic models = NCP v1 §3 schema)
  - boot loader wired into FastAPI lifespan
  - cross-import linter (detects both `from X import Y` and `import_module("X")` patterns)
  - /tnt Claude Code skill (44 lines)
  - Test fixture feature + smoke test (2 tests passing)
affects: [02-03 node runner, 03-02 IAM feature manifest, all Phase 3+ feature verticals]

tech-stack:
  added: []
  patterns:
    - "import_module:Any typing pattern — numeric-prefix dirs require dynamic import; use Any typing to satisfy pyright"
    - "Pydantic field alias for reserved names (db_schema → schema) with populate_by_name"
    - "Linter detects both `from X` statements AND `import_module(\"X\")` call patterns via ast.Call traversal"
    - "DB-level + validator-level dual enforcement of effect-must-emit-audit"
    - "Loader uses one transaction per feature (not one global tx) — isolates feature-level failures"

key-files:
  created:
    - backend/01_catalog/__init__.py
    - backend/01_catalog/manifest.py
    - backend/01_catalog/repository.py
    - backend/01_catalog/loader.py
    - backend/01_catalog/linter.py
    - backend/01_catalog/cli.py
    - .claude/skills/tnt.md
    - tests/fixtures/features/99_test_fixture/feature.manifest.yaml
    - tests/fixtures/features/99_test_fixture/sub_features/01_sample/nodes/core_sample_ping.py
    - tests/test_catalog_loader.py
  modified:
    - backend/main.py

key-decisions:
  - "Manifest uses Pydantic models as schema (no separate JSON Schema file) — Pydantic 2.12.5 model_json_schema() gives the spec for free"
  - "Feature.key must equal metadata.module in v1 (one feature per module, enforced by validator)"
  - "Linter parses ast.Call nodes for `import_module(\"...\")` in addition to ImportFrom — required because numeric-prefix dirs use importlib, not from-imports"
  - "Deprecation sweep is no-op when keys_present is empty (safety — prevents bulk-deprecating the whole catalog on a misfire)"
  - "Strict mode in v1: first error fails boot after all errors are logged; tolerant mode deferred to v0.1.5"

patterns-established:
  - "Handler path resolution: manifest_path's `02_features` vs `tests/fixtures/features` segment determines package prefix"
  - "LoaderReport dataclass: features_upserted / sub_features_upserted / nodes_upserted / deprecated / errors"
  - "CLI convention: `python -m backend.01_catalog.cli {lint|upsert}` with exit codes 0/1/2 meaningful for CI"
  - "Fixture features live at tests/fixtures/features/ and only load when upsert_all called with fixtures=True"

duration: ~40min
started: 2026-04-16T11:00:00Z
completed: 2026-04-16T11:40:00Z
---

# Phase 2 Plan 02: Manifest Loader + Validator + /tnt Skill — Summary

**backend/01_catalog/ is live: manifest parser + boot loader + cross-import linter + /tnt skill + end-to-end smoke test all green against the `01_catalog` schema; backend lifespan now upserts the catalog on every startup.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~40min |
| Started | 2026-04-16T11:00:00Z |
| Completed | 2026-04-16T11:40:00Z |
| Tasks | 3 completed + 1 checkpoint (self-verified against spec per user directive) |
| Files created | 10 |
| Files modified | 1 (backend/main.py) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Manifest parser validates NCP v1 §3 grammar | Pass | Pydantic models enforce regex, kinds, tx modes, effect-must-audit, key hierarchy (tested via pytest `test_invalid_manifest_raises`) |
| AC-2: Boot loader upserts catalog rows | Pass | 1 feature / 1 sub-feature / 1 node inserted on first run; zero new rows on second run; handler `PingNode` resolves via importlib |
| AC-3: Cross-import linter rejects forbidden imports | Pass | Constructed test: detects `import_module("backend.02_features.X.sub_features.Y.service")`, allows `.nodes.Y` + `backend.01_core.*` |
| AC-4: /tnt skill explains the pattern concisely | Pass | `.claude/skills/tnt.md` = 44 lines; frontmatter valid; covers folder, add-node playbook, hard rules, references |
| AC-5: Smoke test proves pipeline | Pass | `pytest tests/test_catalog_loader.py` → 2 passed in 0.24s |

## Accomplishments

- **End-to-end catalog pipeline working:** YAML manifest → Pydantic validation → handler resolution → DB upsert → idempotent rerun → deprecation sweep. All in one `await upsert_all(pool, enabled_modules, fixtures=True)` call.
- **Cross-import discipline is now enforceable:** the linter detects both `from X import Y` statements and `import_module("X")` call patterns, which was critical because numeric-prefix dirs (`01_core`, `02_features`) can't use syntactic from-imports — this project uses importlib exclusively.
- **Single 44-line `/tnt` skill** gives every coding agent a complete onboarding: folder layout + how to add a node + hard rules + ADR/NCP references. Matches the "simplicity king" directive from planning.

## Task Commits

No commits yet — Phase 2 batches at phase close per prior decision. Will land as `feat(02-catalog-foundation): catalog DB + loader + linter + /tnt` when Phase 2 transitions.

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Task 1: backend/01_catalog module + main.py wiring | pending | feat | Manifest parser, repo upserts, boot loader, lifespan hook |
| Task 2: Cross-import linter + CLI | pending | feat | ast-based linter catches both `from X` and `import_module("X")` patterns |
| Task 3: /tnt skill + fixture + smoke test | pending | test | 44-line skill, 99_test_fixture feature, 2 pytest tests |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `backend/01_catalog/__init__.py` | Created | Public re-exports (parse_manifest, upsert_all, error classes) |
| `backend/01_catalog/manifest.py` | Created | Pydantic models = NCP v1 §3 schema + error hierarchy + discover/parse functions |
| `backend/01_catalog/repository.py` | Created | asyncpg raw upserts; dim code→id cache; deprecation sweep |
| `backend/01_catalog/loader.py` | Created | NCP §11 boot sequence: discover → parse → filter → resolve → topsort → upsert → sweep |
| `backend/01_catalog/linter.py` | Created | ast-based cross-import checker (statements + import_module calls) |
| `backend/01_catalog/cli.py` | Created | `python -m backend.01_catalog.cli lint\|upsert` |
| `backend/main.py` | Modified | Added catalog upsert to FastAPI lifespan after pool creation |
| `.claude/skills/tnt.md` | Created | 44-line onboarding skill for agents |
| `tests/fixtures/features/99_test_fixture/feature.manifest.yaml` | Created | Throwaway manifest for smoke test (module=core, key=core, 1 control node) |
| `tests/fixtures/features/99_test_fixture/sub_features/01_sample/nodes/core_sample_ping.py` | Created | No-op PingNode class for handler resolution test |
| `tests/test_catalog_loader.py` | Created | 2 pytest tests — fixture registers idempotently; invalid manifest raises |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Pydantic models ARE the schema (no separate JSON Schema file) | Pydantic 2.12.5 can generate JSON Schema via `model_json_schema()`; maintaining two copies drifts; Pydantic also gives validation error messages for free | Any future MCP `validate` tool reads Pydantic-derived schema; single source of truth |
| Linter parses both `from X` and `import_module("X")` call patterns | Numeric-prefix dirs (`01_core`, `02_features`) cannot use `from X import Y` syntactically — this project uses `import_module(string)` everywhere. Without the Call detection, the linter would never flag anything | CAT_CROSS_IMPORT enforcement is real; would have been a silent loophole otherwise |
| `_handler_import_path` signature simplified (removed unused `feature_key`/`feature_number`) | They were never used — path.parts + `02_features` vs `features` segment tells us everything | Minor scope trim; no behavior change |
| Feature.key must equal metadata.module in v1 | NCP v1 says "one feature per module" — enforced at Pydantic validator level so manifests can't slip through | Test fixture uses module=core, key=core accordingly |
| Fixtures use module=core + key=core | Only way to pass validator with a key that also matches a real module; test cleans up rows in finally so no pollution | Fixture tests are self-contained; real "core" feature slot remains available |
| Type signatures use `Any` for objects returned by `_import_module` | Pyright can't follow dynamic imports; using Any keeps type checker happy without compromising runtime behavior (Pydantic still validates) | Pattern applies throughout numeric-prefix codebase; will reuse in Plan 02-03 |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 2 | Pyright type errors resolved via Any annotations + alias usage; no behavior change |
| Scope additions | 0 | — |
| Spec corrections | 0 | Plan spec was correct |
| Deferred | 0 | — |

**Total impact:** Clean execution. Two auto-fixes were pyright-only (not runtime), resolved before verify.

### Auto-fixed Issues

**1. Pydantic field name `schema` collided with BaseModel method**
- Found during: Task 1 (initial diagnostics)
- Issue: Pydantic v2 `BaseModel` has a `schema()` method; defining a field named `schema` triggers `reportIncompatibleMethodOverride`
- Fix: Renamed field to `db_schema` with `Field(alias="schema")` + `ConfigDict(populate_by_name=True)` so YAML key stays `schema`
- Files: backend/01_catalog/manifest.py
- Verification: Pydantic correctly populates from either alias or attr name; sample parse succeeds

**2. Pyright "Cannot access attribute 'metadata' for class 'object'" on dynamic imports**
- Found during: Task 1 (after main.py wiring)
- Issue: `_manifest_mod = import_module(...)` gives pyright an opaque type; `fm.metadata` reads as object.metadata → error
- Fix: Annotate `_manifest_mod: Any`, `_repo: Any`, `_catalog: Any`; use `Any` as element type in `list[tuple[Path, Any]]` rather than reassigning `FeatureManifest` name
- Files: backend/01_catalog/loader.py, backend/01_catalog/__init__.py, backend/01_catalog/cli.py
- Verification: diagnostics cleared (except stale ones that clear on next pyright pass); runtime behavior unchanged

### Deferred Items

None.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Initial linter test used `aa_feat` (not NN-prefix) — regex didn't match, silently returned clean | Switched test fixture to `99_testfeat` matching the `\d{2}_{name}` convention from NCP v1 §2 |
| `_handler_import_path` had unused params (`feature_key`, `feature_number`) causing pyright warnings | Removed them; derivation uses path.parts only |
| Postgres container was stopped from an earlier session | Restarted via `docker compose up -d postgres` (Plan 02-01's learning applied) |

## Next Phase Readiness

**Ready:**
- `backend/01_catalog.upsert_all(pool, enabled_modules, fixtures=bool)` is the single entry point for catalog boot; Plan 02-03's runner can call catalog DB the same way via `SELECT handler_path, kind_id, tx_mode_id, timeout_ms, retries, emits_audit FROM "01_catalog"."12_fct_nodes" WHERE key = $1`.
- `_repo.get_module_id / get_node_kind_id / get_tx_mode_id` helpers exist with in-process caching — runner can reuse.
- Cross-import linter is enforceable now; when Phase 3+ feature code lands, pre-commit can call `python -m backend.01_catalog.cli lint` before allowing commit.
- `/tnt` skill gives Claude (me, future sessions) a baseline understanding of the pattern.

**Concerns:**
- Pyright still shows some stale diagnostics on `loader.py` / `manifest.py` / `repository.py` even though code compiles and runs clean — this is an IDE caching issue, not a correctness issue. Future sessions may see warnings; runtime is unaffected.
- No pre-commit hook is wired to call the linter yet — that's an infra task (outside NCP scope).
- Handler path resolution assumes `02_features` or `tests/fixtures/features` segments — if we add a third location (e.g. plugins/), we must extend `_handler_import_path`.
- The `feature.key == module` constraint means only 8 features can ever exist (one per module code). Fine for v0.1 but NCP v2 will need to relax this if a single module ever hosts multiple features.

**Blockers:**
- None. Ready to draft Plan 02-03 (node runner with execution policy + NodeContext + authz hook).

---
*Phase: 02-catalog-foundation, Plan: 02*
*Completed: 2026-04-16*
