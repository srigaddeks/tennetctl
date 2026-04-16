---
name: tnt
description: How to work in the tennetctl node catalog. Read this first for any catalog, node, manifest, feature, or sub-feature work. Covers the NCP v1 pattern (feature → sub-feature → node), folder layout, and the "add a node" playbook.
---

# tennetctl — Node Catalog Pattern (NCP v1)

## What this is
A feature contains sub-features. A sub-feature contains nodes.
All declared in one `feature.manifest.yaml` per feature. On boot, the loader
parses every manifest and upserts into the `"01_catalog"` DB schema. Code is
the source of truth; the catalog is a mirror.

**Hard rule:** sub-features communicate with each other ONLY via
`run_node("other.sub.action", ctx, inputs)`. Direct imports across sub-features
are rejected by the linter.

## Folder
```
backend/02_features/{nn}_{feature}/
  feature.manifest.yaml              ← the contract
  sub_features/{nn}_{sub}/
    __init__.py, schemas.py, repository.py, service.py, routes.py
    nodes/{node_key}.py              ← file name = node.key
```

## To add a node
1. Search first — grep `backend/02_features/*/feature.manifest.yaml` for similar keys. If one fits with config, use it.
2. Copy an existing `nodes/*.py` file; rename to `{new_key}.py`. Class must set `key = "{new_key}"` and `kind = "request"|"effect"|"control"`.
3. Add an entry in the parent `feature.manifest.yaml` under the right `sub_features[].nodes:` list.
4. Run `.venv/bin/python -m backend.01_catalog.cli lint` — must exit 0.
5. Restart backend (uvicorn reload re-runs the catalog upsert).

## Hard rules
- Node file name MUST equal `{node.key}.py`. No aliasing.
- Effect nodes MUST have `emits_audit: true` (Pydantic validator + DB CHECK both enforce).
- Never import from another sub-feature's non-`nodes/` modules. Use `run_node`.
- Never add business columns to `fct_*`. Use `dtl_attrs` via EAV.
- Nodes are for **cross-cutting platform concerns**. Feature-internal logic stays in `service.py`.

## References
- NCP v1 spec: `03_docs/00_main/protocols/001_node_catalog_protocol_v1.md`
- ADR-027 (catalog + runner): `03_docs/00_main/08_decisions/027_node_catalog_and_runner.md`
- Minimum surface (ADR-026): `03_docs/00_main/08_decisions/026_minimum_surface_principle.md`
