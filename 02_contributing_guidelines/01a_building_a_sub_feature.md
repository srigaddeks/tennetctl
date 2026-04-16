# Building a Sub-Feature

Use this guide for normal day-to-day work.

A sub-feature is the smallest independently scoped capability inside a feature.

## Use a New Sub-Feature When

- the capability has its own scope
- it exposes or consumes a contract
- it can be built and reviewed independently
- it would be confusing to hide it inside an existing sub-feature

If you are only extending behavior already owned by an existing sub-feature, use [02_building_an_enhancement.md](02_building_an_enhancement.md).

## Required Sub-Feature Pack

```text
03_docs/features/{nn}_{feature}/05_sub_features/{nn}_{sub_feature}/
├── 01_scope.md
├── 02_design.md
├── sub_feature.manifest.yaml
└── 05_api_contract.yaml        # optional
```

## Sub-Feature Workflow

1. Confirm the owning feature is correct.
2. Write the scope.
3. Write the design.
4. Add the manifest.
5. Add API contract docs only if the sub-feature exposes an external interface.
6. Then implement.

## What Goes in `01_scope.md`

Keep it practical.

Answer only:

- what this sub-feature does
- what is in scope
- what is out of scope
- what it owns
- what depends on it
- what done looks like

### Minimal template

```markdown
# {Sub-Feature Name} — Scope

## Purpose
{1-2 sentences}

## In Scope
- {thing}

## Out of Scope
- {thing}

## Owns
- {thing}

## Depends On
- {contract or feature}

## Done Means
- {observable outcome}
```

## What Goes in `02_design.md`

The design doc should let implementation start without more architecture decisions.

Answer only:

- inputs
- outputs
- stored data, if any
- main runtime path
- side effects
- contracts exposed
- contracts consumed
- failure cases worth handling deliberately

If the sub-feature creates or uses reusable nodes, say so explicitly.

## What Goes in `sub_feature.manifest.yaml`

```yaml
title: "{Sub-Feature Name}"
sub_feature: "{nn}_{sub_feature}"
feature: "{nn}_{feature}"
status: PLANNED
owner: "{owner}"
created_at: "YYYY-MM-DD"
description: |
  {short description}
```

Sub-feature status follows the docs-first workflow:

- `PLANNED` — Listed in feature manifest, no work started
- `SCOPED` — GitHub issue open + `01_scope.md` written
- `DESIGNED` — `02_design.md` + migration SQL written (docs-first PR merged)
- `BUILDING` — Implementation in progress (backend + frontend + tests)
- `DONE` — Implementation PR merged, all contracts verified

## When to Add `05_api_contract.yaml`

Add it only when the sub-feature exposes a meaningful external interface such as:

- HTTP endpoints
- event contracts
- node contracts intended for reuse outside the owning feature

Do not create API contract files just to satisfy process.

## Done Criteria

The sub-feature is ready to build when:

- scope is clear
- design is concrete
- ownership and dependency boundaries are explicit
- implementation can start without inventing new structure
