# Folder and File Naming Standards

tennetctl keeps numbered prefixes because they make large documentation trees stable and readable.

## The Rule

```text
{nn}_{name}/
{nn}_{name}.md
```

Keep numbering. Keep names short and clear.

## Top-Level Documentation Areas

```text
02_contributing_guidelines/
03_docs/
├── 00_main/
├── features/
└── nodes/
```

## Feature Layout

```text
03_docs/features/{nn}_{feature}/
├── 00_overview.md
├── 01_sub_features.md
├── feature.manifest.yaml
├── 04_architecture/
│   └── 01_architecture.md
└── 05_sub_features/
    └── {nn}_{sub_feature}/
        ├── 01_scope.md
        ├── 02_design.md
        ├── sub_feature.manifest.yaml
        └── 05_api_contract.yaml    # optional
```

## Node Layout

```text
03_docs/nodes/{nn}_{node}/
├── 00_overview.md
└── node.manifest.yaml
```

Use `03_docs/nodes/` only for intentionally shared reusable nodes.

## Manifest Shapes

### Feature manifest

```yaml
title: "IAM"
feature: "03_iam"
status: ACTIVE
owner: "owner"
created_at: "2026-04-10"
description: |
  Identity and access management.
sub_features:
  - number: 1
    name: users
    status: ACTIVE
```

### Sub-feature manifest

```yaml
title: "Create User"
sub_feature: "01_create_user"
feature: "03_iam"
status: PLANNED
owner: "owner"
created_at: "2026-04-10"
description: |
  Create platform users.
```

### Node manifest

```yaml
title: "Rate Limit"
node: "03_rate_limit"
status: ACTIVE
owner: "owner"
kind: request
description: |
  Request-path rate limiting node.
```

## Status Values

**Feature manifest** (`feature.manifest.yaml`):
- `PLANNED` — Defined, not started
- `ACTIVE` — In progress (has at least one sub-feature building)
- `DONE` — All sub-features shipped

**Sub-feature manifest** (`sub_feature.manifest.yaml`):
- `PLANNED` — Listed, no work started
- `SCOPED` — `01_scope.md` written, GitHub issue open
- `DESIGNED` — `02_design.md` + migrations written, docs-first PR merged
- `BUILDING` — Implementation in progress
- `DONE` — PR merged, contracts verified

## Naming Guidance

- feature names: domain nouns such as `iam`, `audit`, `monitoring`
- sub-feature names: small capability names such as `users`, `sessions`, `api_keys`
- node names: reusable action or concern names such as `auth_required`, `feature_flag`, `rate_limit`

Prefer stable names over clever ones.
