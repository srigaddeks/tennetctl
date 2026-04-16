# Contributing Guidelines

This is the practical workflow for growing tennetctl without turning it into a mess.

## Core Vocabulary

- **Feature**: a bounded domain such as IAM, Audit, API Gateway, or Monitoring.
- **Sub-feature**: the smallest independently scoped capability inside a feature.
- **Node**: a reusable backend runtime block, usually a Python function with typed contracts.
- **Enhancement**: a change to an existing sub-feature.

## The Simple System

The system is intentionally small.

### Every feature must have:

- `00_overview.md`
- `01_sub_features.md`
- `04_architecture/01_architecture.md`
- `feature.manifest.yaml`

### Every sub-feature must have:

- `01_scope.md`
- `02_design.md`
- `sub_feature.manifest.yaml`

### Every shared node should have:

- `00_overview.md`
- `node.manifest.yaml`

Anything beyond that is optional unless the work genuinely needs it.

## Start Here

| Guide | Use it when |
|------|-------------|
| [01_building_a_feature.md](01_building_a_feature.md) | You are defining a new top-level feature boundary. |
| [01a_building_a_sub_feature.md](01a_building_a_sub_feature.md) | You are planning or building a new capability inside an existing feature. |
| [02_building_an_enhancement.md](02_building_an_enhancement.md) | You are extending an existing sub-feature. |
| [03_database_structure.md](03_database_structure.md) | You are designing persistence or SQL-backed contracts. |
| [04_folder_naming_standards.md](04_folder_naming_standards.md) | You need the canonical repo layout and naming rules. |

## Golden Rules

1. Make the feature boundary clear before building reusable nodes.
2. Build one sub-feature at a time.
3. Depend only on declared public contracts.
4. Keep docs short enough that people actually maintain them.
5. Keep the backend as the source of truth.

## Read Before You Start

- [Vision](../03_docs/00_main/01_vision.md)
- [Rules](../03_docs/00_main/03_rules.md)
- [Roadmap](../03_docs/00_main/04_roadmap.md)
- [Features README](../03_docs/features/README.md)
- [Nodes README](../03_docs/nodes/README.md)
