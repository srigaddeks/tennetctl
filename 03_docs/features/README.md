# Features

This directory holds per-feature documentation. Every top-level feature in tennetctl (IAM, Vault, Audit, Monitoring, Notify, Ops, LLMOps, …) gets a numbered subdirectory here.

## What lives here

```
03_docs/features/{nn}_{feature}/
├── 00_overview.md                # What this feature does, scope boundaries
├── 01_sub_features.md            # Index of all sub-features and build order
├── feature.manifest.yaml         # Status, sub-feature list
├── 04_architecture/
│   ├── 01_architecture.md
│   └── 02_workflows.md
└── 05_sub_features/
    ├── 00_bootstrap/             # Schema + shared dim/dtl tables (special)
    │   ├── 01_scope.md
    │   ├── sub_feature.manifest.yaml
    │   └── 09_sql_migrations/
    │       ├── 01_migrated/
    │       └── 02_in_progress/
    │           └── YYYYMMDD_NNN_{feature}_bootstrap.sql
    └── {nn}_{sub_feature}/
        ├── 01_scope.md
        ├── 02_design.md
        ├── 03_architecture.md         # optional
        ├── 05_api_contract.yaml
        ├── 08_worklog.md              # enhancement log
        ├── sub_feature.manifest.yaml
        └── 09_sql_migrations/
            ├── 01_migrated/           # applied migrations
            └── 02_in_progress/        # pending migrations
```

**Migration runner:** SQL files live inside the sub-feature that owns them, never at the feature level. The runner walks `03_docs/features/*/05_sub_features/*/09_sql_migrations/02_in_progress/*.sql` and applies them in global `{NNN}` sequence order. The `00_bootstrap/` sub-feature exists in every feature, sorts first, and owns the schema-creation migration — so the runner needs no special-casing.

The canonical layout reference is [04_folder_naming_standards.md](../../04_contributing_guidelines/04_folder_naming_standards.md).

## How to add a new feature

Read [04_contributing_guidelines/01_building_a_feature.md](../../04_contributing_guidelines/01_building_a_feature.md). It walks you through scaffolding a feature directory, writing the feature manifest, and listing sub-features.

## How to add a sub-feature inside an existing feature

Read [04_contributing_guidelines/01a_building_a_sub_feature.md](../../04_contributing_guidelines/01a_building_a_sub_feature.md). It walks you through opening the tracking issue, writing scope/design docs, the migration, tests, and the implementation PR.

## How to enhance an existing sub-feature

Read [04_contributing_guidelines/02_building_an_enhancement.md](../../04_contributing_guidelines/02_building_an_enhancement.md).

## Currently in flight

No features have been built yet. The first one is IAM — see [11_iam_build_plan.md](../../04_contributing_guidelines/11_iam_build_plan.md).
