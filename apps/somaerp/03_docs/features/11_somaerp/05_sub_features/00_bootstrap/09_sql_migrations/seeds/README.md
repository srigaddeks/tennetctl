# somaerp Bootstrap Seeds

Idempotent seed data for the somaerp application. All files use fixed UUID v7-style IDs and
rely on `ON CONFLICT DO NOTHING` so they are safe to re-run.

Run with:
```bash
cd /path/to/tennetctl
.venv/bin/python -m backend.01_migrator.runner seed
```

## Files

| File | Schema / Table | What it creates |
|------|----------------|-----------------|
| `01a_somaerp_application.json` | `03_iam.15_fct_applications` | somaerp application record |
| `01b_somaerp_application_attrs.json` | `03_iam.21_dtl_attrs` | Application code, label, description attrs |
| `02a_somaerp_roles.json` | `03_iam.13_fct_roles` | 4 roles: admin, manager, operator, viewer |
| `02b_somaerp_roles_attrs.json` | `03_iam.21_dtl_attrs` | Code, label, description for each role |
| `03a_somaerp_groups.json` | `03_iam.14_fct_groups` | 4 groups: admins, kitchen-managers, delivery-riders, viewers |
| `03b_somaerp_groups_attrs.json` | `03_iam.21_dtl_attrs` | Code, label, description for each group |
| `04_somaerp_feature_flags.json` | `09_featureflags.10_fct_flags` | 16 module feature flags (15 on, 1 beta/off) |
| `05_somaerp_flag_states.json` | `09_featureflags.11_fct_flag_states` | Prod environment state for each flag |

## Key IDs

- **Application**: `019dbfc0-1001-7000-8000-000000000001`
- **Org** (existing): `019db460-92e0-7c61-968b-6c01d507511c`
- **Admin user** (existing): `019db460-90ed-7351-a97f-36d6b37584fe`

## Roles

| Code | ID |
|------|----|
| somaerp-admin | `019dbfc0-2001-7000-8000-000000000001` |
| somaerp-manager | `019dbfc0-2002-7000-8000-000000000001` |
| somaerp-operator | `019dbfc0-2003-7000-8000-000000000001` |
| somaerp-viewer | `019dbfc0-2004-7000-8000-000000000001` |

## Groups

| Code | ID |
|------|----|
| somaerp-admins | `019dbfc0-3001-7000-8000-000000000001` |
| kitchen-managers | `019dbfc0-3002-7000-8000-000000000001` |
| delivery-riders | `019dbfc0-3003-7000-8000-000000000001` |
| somaerp-viewers | `019dbfc0-3004-7000-8000-000000000001` |

## Feature Flags

All flags are application-scoped (`scope_id=3`), boolean type (`value_type_id=1`).
Flag states are set for the **prod** environment (`environment_id=3`).

| Flag Key | Default | Prod State |
|----------|---------|------------|
| somaerp_geography | true | enabled |
| somaerp_catalog | true | enabled |
| somaerp_supply | true | enabled |
| somaerp_recipes | true | enabled |
| somaerp_equipment | true | enabled |
| somaerp_quality | true | enabled |
| somaerp_procurement | true | enabled |
| somaerp_inventory | true | enabled |
| somaerp_production | true | enabled |
| somaerp_customers | true | enabled |
| somaerp_subscriptions | true | enabled |
| somaerp_delivery | true | enabled |
| somaerp_reports | true | enabled |
| somaerp_mrp_planner | **false** | **disabled** (beta) |
| somaerp_multi_kitchen | true | enabled |
| somaerp_csv_export | true | enabled |
