# Phase 32 SUMMARY — SDK vault + catalog modules

**Status:** ✅ Complete (2026-04-18, both languages in one pass)

## Shipped in both SDKs

### `client.vault.secrets`

| Method | HTTP |
|---|---|
| `secrets.list(filters?)` | `GET /v1/vault` |
| `secrets.get(key)` | `GET /v1/vault/{key}` |
| `secrets.create({key, value, description?})` | `POST /v1/vault` |
| `secrets.rotate(key, {value})` | `POST /v1/vault/{key}/rotate` |
| `secrets.delete(key)` | `DELETE /v1/vault/{key}` |

SDK never caches plaintext. Backend VaultClient has its own 60s SWR cache invalidated on rotate/delete.

### `client.vault.configs`

| Method | HTTP |
|---|---|
| `configs.list(filters?)` | `GET /v1/vault-configs` |
| `configs.get(id)` | `GET /v1/vault-configs/{id}` |
| `configs.create(body)` | `POST /v1/vault-configs` |
| `configs.update(id, patch)` | `PATCH /v1/vault-configs/{id}` |
| `configs.delete(id)` | `DELETE /v1/vault-configs/{id}` |

### `client.catalog`

| Method | HTTP | Backend status |
|---|---|---|
| `catalog.list_nodes(filters?)` / `listNodes()` | `GET /v1/catalog/nodes` | ✅ shipped |
| `catalog.list_features(filters?)` / `listFeatures()` | `GET /v1/catalog/features` | ⚠ reserved — not shipped on backend yet |
| `catalog.list_sub_features(feature?)` / `listSubFeatures(feature?)` | `GET /v1/catalog/sub-features` | ⚠ reserved — not shipped on backend yet |
| `catalog.get_flow(key)` / `getFlow(key)` | `GET /v1/catalog/flows/{key}` | ⚠ reserved — ships with Phase 42 v0.4.0 |

Aliases hit reserved paths. Callers will see `NotFoundError` until the backend surface lands; signal is explicit rather than silent drift.

## Verification

Python: 15 new tests, vault at 98% coverage, catalog at 63% (aliases not exercised — paths not live).
TypeScript: 11 new tests, vault 100%, catalog 100% statement.

## Notes

- Browser-side SDK: `vault.secrets.get(key)` returns plaintext. The ROADMAP originally called for a `get_signed_ref(key)` variant in browsers. Deferred — no backend endpoint exists to sign references yet. Revisit in v0.2.4 alongside admin UI rollout.
- APISIX gateway sync (original Phase 33) remains a backend-side task separate from the SDK — leave for a dedicated plan with APISIX running.
