# Phase 33 SUMMARY — APISIX Gateway Sync

**Status:** ✅ Complete (2026-04-18) — backend sync loop live; operator docker-compose mount step documented

## What shipped

### `apisix_writer.py` — publish layer

Two publishing paths that run together on every cycle:

1. **YAML file** (primary) — generates an APISIX standalone-mode `apisix.yaml` and writes it atomically (`.tmp` → rename, only when content actually changes). APISIX polls this file every ~1s in `config_provider: yaml` mode and hot-reloads routes.
2. **Admin API PUT** (secondary) — iterates compiled routes and PUTs each to the APISIX Admin API. Gated on `APISIX_ADMIN_ENABLED=true`; noop when off. Used when APISIX runs with etcd backend instead of YAML. Failures logged, counted, not raised.

Key APIs:
- `ApisixWriterConfig.from_env()` — reads `APISIX_YAML_PATH`, `APISIX_ADMIN_URL`, `APISIX_ADMIN_KEY`, `APISIX_ADMIN_ENABLED`
- `build_apisix_yaml(configs)` — renders compiled flag configs to YAML with `#END\n` sentinel
- `write_yaml(body, path)` — idempotent atomic write; returns `True` iff content changed
- `put_admin_routes(configs, ...)` — async HTTP client; returns `(succeeded, failed)`
- `publish(conn)` — orchestrator; returns `PublishResult` dataclass

### `apisix_worker.py` — background poll loop

`run_worker(pool, poll_seconds=30, status_holder=...)` runs forever:
1. First iteration: **boot reconcile** — immediate publish so APISIX gets current state
2. Every 30s: `publish_once(pool)` → compare content digest to last cycle
3. On content-digest change → emit `flags.apisix.synced` audit with compiled-count + digest
4. On error-state transition → emit `flags.apisix.sync_failed` with reason
5. Stores the latest `PublishResult` on `app.state.apisix_sync_status` for the admin UI

Audit emission uses category=`system` so it bypasses audit-scope user requirements.

### Status endpoints

- `GET /v1/flags/apisix/sync-status` — returns the last `PublishResult`
- `POST /v1/flags/apisix/sync` — forces an immediate publish; returns fresh result

### Lifespan wiring

`backend/main.py` — worker spawned as an `asyncio` task when `featureflags` module is enabled; cancelled cleanly on shutdown alongside the other workers.

## Operator integration

APISIX is running in YAML config provider mode at host ports **51780** (data plane) + **51718** (admin). To consume the generated `apisix.yaml`:

```yaml
# docker-compose.yml
services:
  apisix:
    volumes:
      - ${APISIX_YAML_PATH:-/tmp/tennetctl_apisix.yaml}:/usr/local/apisix/conf/apisix.yaml:ro
```

Then restart APISIX. Subsequent `tennetctl` flag mutations → backend writes `apisix.yaml` → APISIX hot-reloads. No APISIX restart needed after initial mount.

For `etcd`-backed APISIX deployments instead, set:
```
APISIX_ADMIN_ENABLED=true
APISIX_ADMIN_URL=http://apisix:9180/apisix/admin
APISIX_ADMIN_KEY=<admin-key>
```

## Existing assets reused

- `backend/02_features/09_featureflags/apisix_sync.py` — flag → plugin-config compilation (pre-existing; unchanged)
- `flag_kind` EAV lookup — already wired via `dim_attr_defs` code='kind'
- `audit.events.emit` node — called via `run_node()` for sync audits

## Verification

```
.venv/bin/python -m pytest tests/test_apisix_writer.py -v
```

Result:
```
16 passed in 0.40s
  test_build_yaml_emits_routes_and_end_sentinel        ✅
  test_build_yaml_empty_list_still_valid               ✅
  test_build_yaml_methods_present_on_every_route       ✅
  test_digest_stable_across_calls                      ✅
  test_digest_differs_for_different_content            ✅
  test_write_yaml_creates_file                         ✅
  test_write_yaml_skips_unchanged                      ✅
  test_write_yaml_rewrites_when_changed                ✅
  test_write_yaml_atomic_via_tempfile                  ✅
  test_write_yaml_creates_parent_dirs                  ✅
  test_config_from_env_defaults                        ✅
  test_config_admin_enabled_toggle                     ✅
  test_config_custom_yaml_path                         ✅
  test_publish_with_empty_flag_set                     ✅
  test_publish_idempotent_second_call                  ✅
  test_publish_records_compile_error                   ✅
```

## Deferred

- **Live integration test** — requires a flag row with `kind=request` attr seeded, then observing APISIX pick up the new route. Manual smoke test; not automated (would need fixtures + APISIX restart coordination in CI).
- **Sync status badge in admin UI** — data is already exposed at `GET /v1/flags/apisix/sync-status`; rendering the badge in the flag detail page lands in Phase 35 admin UI work.
- **Mutation-triggered sync** — instead of 30s polling, hook flag/rule/override service-layer mutations to enqueue an immediate sync. Incremental improvement; polling works correctly today.

## Files

| File | Action |
|---|---|
| `backend/02_features/09_featureflags/apisix_writer.py` | NEW — 170 lines |
| `backend/02_features/09_featureflags/apisix_worker.py` | NEW — 130 lines |
| `backend/02_features/09_featureflags/apisix_routes.py` | NEW — 45 lines |
| `backend/02_features/09_featureflags/routes.py` | include apisix_routes.router |
| `backend/main.py` | lifespan start/stop for apisix_worker_task |
| `tests/test_apisix_writer.py` | NEW — 16 tests |
