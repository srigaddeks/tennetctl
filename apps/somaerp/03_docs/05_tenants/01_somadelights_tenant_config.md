# Soma Delights — Tenant Configuration

> The first-tenant mapping. Every Soma Delights operational fact from `99_business_refs/somadelights/` translated into seedable somaerp entity instances. This doc SPECIFIES what the seed YAML files (shipping in plan 56-02 onwards) will contain. It does NOT create the YAML files.
>
> Treat this as the executable acceptance bar for "is the somaerp data model expressive enough to model Soma Delights?" If a Soma Delights workflow does not appear here, downstream plans are wrong.

## Workspace identity

| Field | Value |
| --- | --- |
| Tenant identity | tennetctl `workspace_id` (TBD at provisioning — assigned by tennetctl iam when the workspace is created) |
| Workspace name | `Soma Delights` |
| Workspace code (slug) | `soma-delights` |
| Workspace owner | The founder's tennetctl iam user_id (TBD at provisioning) |
| Default region code | `IN` |
| Default location | Hyderabad |
| Default currency code | `INR` (ISO 4217) |
| Timezone | `Asia/Kolkata` |
| Supported customer-facing languages | `["en", "hi", "te"]` per `multi-lingual-strategy.md` § 2 |
| Operator UI language | `en` only at v0.9.0 |
| FSSAI tier (Stage 1) | Basic Registration (Form A); upgrade to State License at Stage 3 per `compliance-food-safety.md` |
| Business structure (Stage 1) | Sole proprietorship per `compliance-food-safety.md` Business Structure section |

Setup-mode bootstrap audit category: `setup` per `../04_integration/02_audit_emission.md`.

Vault entries created at bootstrap (per `../04_integration/03_vault_for_secrets_and_blobs.md`):

- `somaerp.tenants.{ws}.fssai_license_number` — TBD (populated when license issues)
- `somaerp.tenants.{ws}.fssai_license_expiry` — TBD
- `somaerp.tenants.{ws}.business_address` — KPHB Colony address (TBD: confirm exact unit)
- `somaerp.tenants.{ws}.gstin` — initially empty; populated after voluntary GST registration per `compliance-food-safety.md`

## Geography seed

### Regions (`dim_regions`)

| code | name | country_iso | properties |
| --- | --- | --- | --- |
| `IN` | India | IN | `{}` |

### Locations (`fct_locations`)

| name | region_code | timezone | default_currency_code |
| --- | --- | --- | --- |
| Hyderabad | IN | Asia/Kolkata | INR |

### Kitchens (`fct_kitchens`)

Stage 1 (now): exactly one kitchen.

| name | location | timezone | stage | properties |
| --- | --- | --- | --- | --- |
| KPHB Home Kitchen | Hyderabad | Asia/Kolkata | 1 | `{"physical_type":"home","equipment_count":1,"founder_operated":true}` |

Forward staging per `brand-roadmap-vision.md` and `operations-model.md` Scale Stages:
- **Stage 2 (~Month 3-4):** upgrade KPHB Home Kitchen capacity in place (insert new `fct_kitchen_capacity` row, close prior). Same kitchen row.
- **Stage 3 (~Month 6+):** add a second kitchen `Kukatpally Production Unit` at a rented commercial space.
- **Stage 4-7+:** as the brand-roadmap-vision Stage progression demands.

Subsequent kitchens are added by the operator post-bootstrap; the seed only ships Stage 1.

### Service zones (`fct_service_zones`)

Stage 1: one zone.

| kitchen | name | area_description | sequence |
| --- | --- | --- | --- |
| KPHB Home Kitchen | KPHB Colony | Phases 1-15, KPHB Colony, Kukatpally Metro to JNTU stretch | 1 |

Per `delivery-routes.md` Cluster 1.

### Kitchen capacity (`fct_kitchen_capacity`)

Stage 1 row, per ADR-003 + `02_capacity_planning_model.md`:

| kitchen | product_line | capacity_value | capacity_unit | time_window_start | time_window_end | valid_from | valid_to |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KPHB Home Kitchen | Cold-Pressed Drinks | 30 | bottles | 04:00 | 08:00 | 2026-04-24 | NULL |

Buffer: an additional 10% per `operations-model.md` Batching Logic = produce up to 33 bottles. Capacity row is the planning ceiling, not the production cap; the buffer lives in service-layer planning rules, not the seed.

Stage transition path (the operator's expansion playbook, not seeded today):
- Stage 2: close Stage 1 row, insert row with `capacity_value=90, valid_from=<Stage2 start>`.
- Stage 3: close Stage 2 row, insert `capacity_value=250, time_window_end=09:00`.

## Catalog seed

### Product lines (`fct_product_lines`)

Per `brand-roadmap-vision.md` 8-stage roadmap:

| name | stage | status | activates_when | properties |
| --- | --- | --- | --- | --- |
| Cold-Pressed Drinks | 1 | active | NOW | `{"roadmap_stage":1,"trigger":"now"}` |
| Dehydrated Pulp Products | 2 | inactive | Stable Stage 1 ops | `{"roadmap_stage":2,"trigger":"stable_stage_1"}` |
| Fermented Drinks (Entry) | 3 | inactive | ~200 customers | `{"roadmap_stage":3,"trigger":"~200_customers"}` |
| Premium Fermented & Wellness Shots | 4 | inactive | ~300 customers | `{"roadmap_stage":4,"trigger":"~300_customers"}` |
| Premium Breakfast Kits | 5 | inactive | ~500 customers | `{"roadmap_stage":5,"trigger":"~500_customers"}` |
| Pantry Essentials | 6 | inactive | Brand maturity | `{"roadmap_stage":6,"trigger":"future"}` |
| Farm-to-Home | 7 | inactive | Farm partnerships | `{"roadmap_stage":7,"trigger":"future"}` |
| Wellness Cosmetics | 8 | inactive | Full ecosystem | `{"roadmap_stage":8,"trigger":"future"}` |

Only Cold-Pressed Drinks is `active` at v0.9.0. Inactive lines are seeded as catalog placeholders so the future stage activations are PATCHes, not creates.

### Product categories (`dim_product_categories`)

| code | name |
| --- | --- |
| `daily_staple` | Daily staple |
| `premium_upsell` | Premium upsell |
| `seasonal` | Seasonal |
| `trial` | Trial / starter |

Source: `launch-menu.md` SKU Summary Table category column.

### Product tags (`dim_product_tags`)

| code | name |
| --- | --- |
| `immunity` | Immunity |
| `energy` | Energy |
| `detox` | Detox |
| `hydration` | Hydration |
| `digestion` | Digestion |
| `anti_inflammatory` | Anti-inflammatory |

Source: distilled from `launch-menu.md` Target Benefit columns.

### Products (`fct_products`)

The Stage 1 launch SKUs. Source: `launch-menu.md` Core SKUs + `recipe-standardization.md` Launch SKUs (the recipe doc supersedes when they disagree on quantities).

| sku_code | name | product_line | category | serving_volume_ml | tags | properties |
| --- | --- | --- | --- | --- | --- | --- |
| `SD-CP-001` | Green Morning | Cold-Pressed Drinks | daily_staple | 250 | hydration, detox | `{"target_benefit":"morning hydration, micronutrient loading, gentle detox"}` |
| `SD-CP-002` | Beet Vitality (Beetroot Recharge) | Cold-Pressed Drinks | daily_staple | 250 | energy | `{"target_benefit":"iron boost, endurance, blood pressure support"}` |
| `SD-CP-003` | Citrus Immunity | Cold-Pressed Drinks | daily_staple | 250 | immunity, anti_inflammatory | `{"target_benefit":"immune support, vitamin C loading"}` |
| `SD-CP-004` | ABC Classic | Cold-Pressed Drinks | trial | 250 | digestion | `{"target_benefit":"general wellness, skin health, digestion"}` |
| `SD-CP-005` | Golden Shield (Turmeric Ginger) | Cold-Pressed Drinks | daily_staple | 250 | anti_inflammatory, immunity | `{"target_benefit":"anti-inflammatory, joint support"}` |
| `SD-CP-006` | Hydration Cooler | Cold-Pressed Drinks | daily_staple | 300 | hydration | `{"target_benefit":"hydration, electrolyte balance"}` |
| `SD-SHOT-001` | Ginger Fire Shot | Cold-Pressed Drinks | premium_upsell | 60 | immunity, digestion | `{"target_benefit":"daily immunity ritual, digestion"}`, `{"is_shot":true}` |

Note on serving_volume_ml: `recipe-standardization.md` uses 250 ml as the target per bottle (not 300 ml as in `launch-menu.md`). The seed uses 250 for the recipe-bound SKUs and 300 for Hydration Cooler (which uses the larger bottle per `launch-menu.md`). TBD: confirm with operator whether all SKUs ship at 250 ml or whether Hydration Cooler is genuinely a different SKU at 300 ml.

### Product variants (`fct_product_variants`)

Stage 1: no variants seeded; each product has exactly one default variant. Variants table seed is empty rows-wise; the table exists.

## Recipes seed

Per ADR-004, all v1 recipes ship as `status=active`, one per product. Source: `recipe-standardization.md` Launch SKUs (the canonical recipe spec).

### `fct_recipes` rows (one per SKU)

| product | version | status | yield_target_ml | yield_min_ml | yield_max_ml | properties |
| --- | --- | --- | --- | --- | --- | --- |
| Green Morning | 1 | active | 250 | 220 | 270 | `{"juicing_order":["spinach","cucumber","green_apple","celery","ginger","lemon_juice_post"]}` |
| Beet Vitality | 1 | active | 250 | 240 | 260 | `{"juicing_order":["beetroot","carrot","apple","ginger","lemon_juice_post"]}` |
| Citrus Immunity | 1 | active | 250 | 240 | 260 | `{"juicing_order":["carrot","amla","orange","ginger","lemon_juice_post","honey_post"]}` |
| ABC Classic | 1 | active | 250 | 250 | 270 | `{"juicing_order":["beetroot","carrot","apple","ginger","lemon_juice_post"]}` |
| Golden Shield | 1 | active | 250 | 230 | 260 | `{"juicing_order":["carrot","fresh_turmeric","ginger","apple","lemon_juice_post","black_pepper_post"]}` |
| Hydration Cooler | 1 | active | 300 | 280 | 310 | `{"juicing_order":["cucumber","mint","coconut_water_pre","lemon_juice_post","pink_salt_post"]}` |
| Ginger Fire Shot | 1 | active | 60 | 55 | 65 | `{"juicing_order":["ginger","fresh_turmeric","lemon_juice_post","black_pepper_post","honey_post","cayenne_post_optional"]}` |

### `dtl_recipe_ingredients` rows (per recipe, exact quantities from `recipe-standardization.md`)

#### Green Morning v1
| raw_material | quantity | unit |
| --- | --- | --- |
| Spinach (palak) | 80 | g |
| Cucumber | 120 | g |
| Green apple | 80 | g |
| Celery | 40 | g |
| Lemon juice | 15 | ml |
| Ginger (fresh) | 5 | g |

#### Beet Vitality v1
| raw_material | quantity | unit |
| --- | --- | --- |
| Beetroot | 130 | g |
| Carrot | 80 | g |
| Apple | 60 | g |
| Ginger (fresh) | 8 | g |
| Lemon juice | 10 | ml |

#### Citrus Immunity v1
| raw_material | quantity | unit |
| --- | --- | --- |
| Orange | 150 | g |
| Carrot | 60 | g |
| Amla | 30 | g |
| Lemon juice | 20 | ml |
| Ginger | 5 | g |
| Honey (raw, local) | 5 | ml (~7 g) |

#### ABC Classic v1
| raw_material | quantity | unit |
| --- | --- | --- |
| Apple | 100 | g |
| Beetroot | 80 | g |
| Carrot | 100 | g |
| Lemon juice | 10 | ml |
| Ginger | 3 | g |

#### Golden Shield v1
| raw_material | quantity | unit |
| --- | --- | --- |
| Carrot | 150 | g |
| Fresh turmeric | 15 | g |
| Ginger (fresh) | 12 | g |
| Apple | 60 | g |
| Lemon juice | 10 | ml |
| Black pepper | 0.3 | g |

#### Hydration Cooler v1
| raw_material | quantity | unit |
| --- | --- | --- |
| Cucumber | 150 | g |
| Coconut water | 100 | ml |
| Mint | 10 | g |
| Lemon juice | 20 | ml |
| Pink salt | 0.3 | g |

#### Ginger Fire Shot v1
| raw_material | quantity | unit |
| --- | --- | --- |
| Ginger (fresh) | 40 | g |
| Lemon juice | 15 | ml |
| Fresh turmeric | 5 | g |
| Black pepper | 0.3 | g |
| Honey | 3 | ml (~4 g) |
| Cayenne pepper (optional) | 0.1 | g |

### `dtl_recipe_steps` per recipe

Common shape, per `recipe-standardization.md` Prep Steps and Juicing Order. Each recipe gets ~5-7 steps:

1. Wash all produce twice (rinse + soak + drain) — duration 5 min — equipment: sink
2. Prep ingredients (peel, chop, segment) — duration 8-12 min — equipment: cutting board, knife
3. Juice ingredients in declared order — duration 10-15 min — equipment: cold-press juicer
4. Stir post-juice additions (lemon, honey, pepper, salt) — duration 1 min — equipment: spoon
5. Strain (if needed) — duration 1-2 min — equipment: fine mesh strainer
6. Bottle and cap — duration 2-3 min — equipment: funnel, bottles
7. Refrigerate immediately (target ≤ 8°C within 15 min) — duration 0-15 min — equipment: production fridge

Step kinds (dim_recipe_step_kinds): `wash`, `prep`, `juice`, `stir`, `strain`, `bottle`, `chill`.

Recipe rows are immutable once active per ADR-004; future recipe revisions ship as v2/v3 rows.

### Kitchen recipe overrides (`lnk_kitchen_recipe_overrides`)

Stage 1: empty — KPHB Home Kitchen uses the base recipe for every product. Future overrides for a Bangalore expansion or a seasonal substitution use this table.

## Quality seed

Per ADR-005 and `operations-model.md` Quality SOP + `recipe-standardization.md` Quality Control Checklist + `compliance-food-safety.md` FSSAI requirements.

### `dim_qc_stages`

| code | name | order |
| --- | --- | --- |
| `pre_production` | Pre-production | 1 |
| `in_production` | In-production | 2 |
| `post_production` | Post-production | 3 |
| `fssai` | FSSAI compliance | 4 |

### `dim_qc_check_types`

| code | name |
| --- | --- |
| `visual` | Visual inspection |
| `smell` | Smell test |
| `firmness` | Firmness / texture |
| `weight` | Weight verification |
| `temperature` | Temperature reading |
| `taste` | Taste test |
| `color` | Color match |
| `fill_level` | Fill level |
| `cap_seal` | Cap seal integrity |
| `lot_traceability` | Lot/batch traceability |
| `label_correctness` | Label correctness |

### `dim_qc_checkpoints`

Pre-production checkpoints (per batch ingredient):

| stage | check_type | scope | criteria_jsonb |
| --- | --- | --- | --- |
| pre_production | visual | per ingredient | `{"pass":"bright color, no yellowing, no mold","fail_action":"reject batch ingredient"}` |
| pre_production | smell | per ingredient | `{"pass":"fresh and clean","fail_action":"reject"}` |
| pre_production | firmness | per ingredient | `{"pass":"firm to gentle squeeze","fail_action":"trim or reject"}` |
| pre_production | weight | per ingredient | `{"pass":"within 10% of paid weight","fail_action":"flag vendor"}` |
| pre_production | temperature | per delivered ingredient | `{"target_max_c":15,"fail_action":"reject"}` |

In-production checkpoints (per batch):

| stage | check_type | scope | criteria_jsonb |
| --- | --- | --- | --- |
| in_production | taste | per batch | `{"per_recipe":"matches expected profile","fail_action":"do not deliver"}` |
| in_production | color | per batch | `{"per_recipe":"matches expected color","fail_action":"do not deliver — likely oxidation"}` |
| in_production | temperature | per batch | `{"target_max_c":10,"timing":"at bottling","fail_action":"recheck cold chain"}` |

Post-production checkpoints (per bottle in batch):

| stage | check_type | scope | criteria_jsonb |
| --- | --- | --- | --- |
| post_production | fill_level | per bottle | `{"pass":"within target serving volume ± 5%","fail_action":"discard bottle"}` |
| post_production | cap_seal | per bottle | `{"pass":"tamper-evident band intact","fail_action":"recap or discard"}` |
| post_production | label_correctness | per bottle | `{"pass":"correct SKU label, MFG date+time present, FSSAI logo+number visible","fail_action":"relabel"}` |
| post_production | temperature | per bottle | `{"target_max_c":10,"timing":"at fridge entry","fail_action":"discard"}` |

FSSAI checkpoints (per batch):

| stage | check_type | scope | criteria_jsonb |
| --- | --- | --- | --- |
| fssai | lot_traceability | per batch | `{"requires":"batch_id_ref present on every consumption movement; lot_number resolves to a procurement_line","fail_action":"do not dispatch — block batch"}` |
| fssai | label_correctness | per batch (sample one bottle) | `{"requires":"FSSAI license number, batch number, MFG/EXP, ingredient list, net qty, MRP, allergen declaration","fail_action":"halt batch dispatch"}` |
| fssai | temperature | spot-check at delivery | `{"target_max_c":12,"timing":"at customer hand-off","fail_action":"replace bottle, log cold-chain breach"}` |

Photo capture is required for every `category=compliance` checkpoint per ADR-005; photo stored via tennetctl vault per `../04_integration/03_vault_for_secrets_and_blobs.md`.

## Raw materials seed

Source: `operations-model.md` Procurement table + `supplier-vendor-directory.md`.

### `dim_raw_material_categories`

| code | name |
| --- | --- |
| `vegetable_leafy` | Leafy vegetable |
| `vegetable_root` | Root vegetable |
| `fruit` | Fruit |
| `herb` | Herb |
| `spice` | Spice |
| `sweetener` | Sweetener |
| `liquid_base` | Liquid base |
| `salt_mineral` | Salt / mineral |
| `packaging_bottle` | Bottle |
| `packaging_cap` | Cap |
| `packaging_label` | Label |
| `packaging_other` | Packaging — other |
| `cold_chain` | Cold-chain consumable |

### `dim_units_of_measure`

| code | name | base_kind |
| --- | --- | --- |
| `g` | gram | mass |
| `kg` | kilogram | mass |
| `ml` | milliliter | volume |
| `l` | liter | volume |
| `count` | count | count |
| `bottle` | bottle | count |

### `fct_raw_materials`

| name | category | default_unit | properties |
| --- | --- | --- | --- |
| Spinach (palak) | vegetable_leafy | g | `{"freshness_window_days":2,"wash_protocol":"2x rinse + 5min soak"}` |
| Cucumber | vegetable_leafy | g | `{"peel":"optional","freshness_window_days":4}` |
| Mint (pudina) | herb | g | `{"freshness_window_days":2}` |
| Celery | vegetable_leafy | g | `{"freshness_window_days":4}` |
| Coriander (dhaniya) | herb | g | `{"freshness_window_days":2}` |
| Carrot | vegetable_root | g | `{"variety_preferred":"Ooty","freshness_window_days":7}` |
| Beetroot | vegetable_root | g | `{"freshness_window_days":7}` |
| Ginger (fresh) | vegetable_root | g | `{"freshness_window_days":14}` |
| Fresh turmeric | spice | g | `{"freshness_window_days":14,"seasonal":"Dec-Mar peak"}` |
| Dry turmeric | spice | g | `{"use_when":"fresh unavailable; not for juicing"}` |
| Apple (green / Granny Smith) | fruit | g | `{"freshness_window_days":14}` |
| Apple (red / Shimla) | fruit | g | `{"seasonal":"Aug-Feb"}` |
| Orange (mosambi/malta) | fruit | g | `{"freshness_window_days":7}` |
| Amla (Indian gooseberry) | fruit | g | `{"seasonal":"Oct-Mar","freshness_window_days":10}` |
| Lemon | fruit | g | `{"freshness_window_days":7}` |
| Pineapple | fruit | g | `{"freshness_window_days":5}` |
| Mixed berries | fruit | g | `{"freshness_window_days":3}` |
| Pomegranate | fruit | g | `{"freshness_window_days":10}` |
| Aloe vera | herb | g | `{"freshness_window_days":7}` |
| Basil (tulsi) | herb | g | `{"freshness_window_days":3}` |
| Coconut water | liquid_base | ml | `{"sourcing":"packaged shelf-stable"}` |
| Honey (raw, local) | sweetener | g | `{"shelf_stable":true}` |
| Black pepper (whole) | spice | g | `{"shelf_stable":true,"grind":"fresh per use"}` |
| Pink salt | salt_mineral | g | `{"shelf_stable":true}` |
| Cayenne pepper | spice | g | `{"shelf_stable":true,"optional":true}` |
| 250 ml PET bottle | packaging_bottle | count | `{"capacity_ml":250,"food_grade":true,"bpa_free":true}` |
| 300 ml PET bottle | packaging_bottle | count | `{"capacity_ml":300,"food_grade":true,"bpa_free":true}` |
| 60 ml glass bottle (shot) | packaging_bottle | count | `{"capacity_ml":60,"material":"glass"}` |
| Tamper-evident cap | packaging_cap | count | `{}` |
| Glass shot cap | packaging_cap | count | `{}` |
| BOPP sticker label | packaging_label | count | `{"material":"BOPP","lamination":"matte","waterproof":true}` |
| Gel ice pack (300g, reusable) | cold_chain | count | `{"reuse_lifetime_uses":100}` |
| Insulated delivery bag (15L) | cold_chain | count | `{"reuse_lifetime_months":9}` |

### `dim_supplier_source_types`

| code | name |
| --- | --- |
| `wholesale_market` | Wholesale market |
| `farm` | Direct farm |
| `marketplace` | Online marketplace |
| `manufacturer` | Manufacturer (packaging) |
| `printer` | Printer (labels) |
| `medical_supply` | Medical supply store |
| `electronics_retail` | Electronics retail |

### `fct_suppliers`

Per `supplier-vendor-directory.md`:

| name | source_type | location | properties |
| --- | --- | --- | --- |
| Bowenpally Wholesale Market | wholesale_market | Hyderabad | `{"open_hours":"04:00-11:00","payment":"cash_preferred","best_for":["leafy_greens","root_vegetables","ginger","turmeric"]}` |
| Rythu Bazaar (Kukatpally) | wholesale_market | Hyderabad | `{"open_hours":"06:00-13:00","payment":"cash_or_upi","best_for":["leafy_greens","amla","fresh_turmeric","lemons"]}` |
| Erragadda Vegetable Market | wholesale_market | Hyderabad | `{"backup_role":true}` |
| Kothapet Fruit Market | wholesale_market | Hyderabad | `{"open_hours":"05:00-14:00","best_for":["apples","amla","oranges"]}` |
| Local farm (TBD) | farm | Hyderabad | `{"relationship_status":"to_establish"}`, TBD: confirm with operator which farm partnerships are active |
| BigBasket | marketplace | Hyderabad | `{"backup_only":true,"price_premium_pct":"30-50"}` |
| Jiomart | marketplace | Hyderabad | `{"backup_only":true}` |
| Amazon India | marketplace | Online | `{"used_for":"equipment, packaging, ice_packs"}` |
| IndiaMART (PET bottle supplier) | manufacturer | Hyderabad | `{"moq":"100-500","payment":"50% advance"}`, TBD: confirm exact supplier name once selected |
| Local printer (Kukatpally) | printer | Hyderabad | `{"turnaround_days":"1-3"}`, TBD: confirm shop name |
| 24 Mantra (organic store) | marketplace | Hyderabad | `{"used_for":"organic upgrade for leafy_greens","optional":true}` |

### `lnk_raw_material_suppliers`

Primary + backup mapping per `supplier-vendor-directory.md`:

| raw_material | supplier | is_primary | properties |
| --- | --- | --- | --- |
| Spinach (palak) | Bowenpally Wholesale Market | true | `{"buy_frequency":"every_2_days"}` |
| Spinach (palak) | Rythu Bazaar (Kukatpally) | false | `{"role":"backup_for_freshness"}` |
| Mint | Bowenpally Wholesale Market | true | |
| Mint | Rythu Bazaar (Kukatpally) | false | |
| Celery | Bowenpally Wholesale Market | true | |
| Carrot | Bowenpally Wholesale Market | true | `{"buy_frequency":"twice_per_week"}` |
| Carrot | Erragadda Vegetable Market | false | |
| Beetroot | Bowenpally Wholesale Market | true | |
| Ginger (fresh) | Bowenpally Wholesale Market | true | |
| Fresh turmeric | Rythu Bazaar (Kukatpally) | true | |
| Fresh turmeric | Bowenpally Wholesale Market | false | |
| Apple (green) | Kothapet Fruit Market | true | |
| Apple (red Shimla) | Kothapet Fruit Market | true | |
| Orange | Kothapet Fruit Market | true | |
| Amla | Kothapet Fruit Market | true | `{"seasonal":"Oct-Mar"}` |
| Lemon | Bowenpally Wholesale Market | true | |
| Cucumber | Bowenpally Wholesale Market | true | |
| Coconut water | BigBasket | true | `{"shelf_stable":true}` |
| Honey | 24 Mantra (organic store) | true | TBD: confirm preferred supplier |
| Black pepper | BigBasket | true | |
| Pink salt | BigBasket | true | |
| 250 ml PET bottle | IndiaMART (PET bottle supplier) | true | |
| 250 ml PET bottle | Amazon India | false | `{"role":"emergency_top_up"}` |
| Tamper-evident cap | IndiaMART (PET bottle supplier) | true | |
| BOPP sticker label | Local printer (Kukatpally) | true | |
| Gel ice pack | Amazon India | true | |

## Customers seed

### `fct_customers`

**Empty.** No real customers seeded at bootstrap. Per `customer-data-privacy.md` § 1, every customer record is created from a real signup; the seed creates only the table shape (zero rows). Anonymized "test customer" rows for QA are seeded only in dev environments, not production.

The schema shape (per `08_customers` data layer, forward reference) accepts the columns that `customer-data-privacy.md` § 2.1 enumerates: name, whatsapp_number, email (optional), location_id, address (in `properties` or `dtl_*`), preferred_language, opted_in_to_tips, allergies (in `dtl_attrs`), preferences (in `dtl_attrs`).

### `dim_subscription_plans`

Plan templates per `subscription-plans.md` Phase 1 launch (the three to ship Day 1):

| code | name | frequency | bottles_per_week | duration_kind | weekly_price_inr | monthly_price_inr | properties |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `5d_starter_reset` | 5-Day Starter Reset | one_time | 5 | one_time | 449 (one-time) | NULL | `{"role":"trial","conversion_target":true}` |
| `morning_glow_weekly` | Morning Glow Plan (weekly) | weekly | 6 | recurring | 549 | NULL | `{"sku_rotation":["Green Morning x3","Citrus Immunity x2","Beet Vitality x1"]}` |
| `morning_glow_monthly` | Morning Glow Plan (monthly) | monthly | 6 | recurring | NULL | 2099 | `{"sku_rotation":"as weekly","commitment_discount_pct":4.5}` |
| `family_wellness_weekly` | Family Wellness Starter (weekly) | weekly | 10 | recurring | 799 | NULL | `{"household_size":2,"bottles_per_delivery":2,"days_per_week":5}` |
| `family_wellness_monthly` | Family Wellness Starter (monthly) | monthly | 10 | recurring | NULL | 2999 | `{"as":"family_wellness_weekly + monthly commitment discount"}` |

Phase 2 plans (`subscription-plans.md` Month 2-3 add) are seeded as `inactive`; the operator activates them when ready:

| code | name | status |
| --- | --- | --- |
| `hydration_habit_weekly` | Hydration Habit Plan (weekly) | inactive |
| `hydration_habit_monthly` | Hydration Habit Plan (monthly) | inactive |
| `womens_wellness_weekly` | Women's Wellness Plan | inactive |

Phase 3 plans (`office_energy`, `20_day_routine_builder`) similarly inactive.

### `dtl_subscription_plan_items`

Per the `properties.sku_rotation` specification on each active plan. For example for `morning_glow_weekly`:

| plan | product_sku | qty_per_week |
| --- | --- | --- |
| morning_glow_weekly | SD-CP-001 (Green Morning) | 3 |
| morning_glow_weekly | SD-CP-003 (Citrus Immunity) | 2 |
| morning_glow_weekly | SD-CP-002 (Beet Vitality) | 1 |

Pause and cancellation policy per `subscription-plans.md` Pause & Cancellation section:
- Up to 2 days/month free pause: enforced in service-layer (`somaerp.customers.compute_pause_window_validity` node referenced in `../04_integration/05_flows_for_workflows.md`).
- 3-7 days pause: weekly pricing reverts.
- > 7 days: treated as cancellation.
- Cancellation: no penalty; mandatory 1-question reason survey captured into `evt_subscription_pauses.reason`.

## Delivery seed

Per `delivery-routes.md`.

### `fct_delivery_routes`

Stage 1: one route.

| name | kitchen | service_zone | sequence_jsonb | properties |
| --- | --- | --- | --- | --- |
| Cluster 1 — KPHB Colony | KPHB Home Kitchen | KPHB Colony | `[]` (populated as customers join) | `{"target_subscribers_year_1":"50-80","route_time_min":"45-60","loop_distance_km":"8-12","delivery_window":"06:00-07:00"}` |

Future routes (added when density triggers fire — `delivery-routes.md` Cluster Expansion Sequence):
- Cluster 2 — Miyapur (added Month 2-3 if Cluster 1 ≥ 15 subscribers)
- Cluster 3 — Chandanagar (added Month 4+ if Cluster 2 ≥ 15 subscribers)

These are NOT seeded; the operator inserts them when the trigger fires.

### `lnk_route_customers`

Empty at bootstrap (no customers).

### `dim_rider_roles`

| code | name |
| --- | --- |
| `founder_rider` | Founder (self-delivery) |
| `part_time_rider` | Part-time rider |
| `full_time_rider` | Full-time rider |
| `route_lead` | Route lead (multi-rider tier) |

### `fct_riders`

Stage 1: one rider — the founder.

| name | role | linked_iam_user_id | properties |
| --- | --- | --- | --- |
| Founder (self) | founder_rider | <founder's tennetctl iam user_id, TBD> | `{"vehicle":"personal_scooter","compensation":"Rs 0 — founder time"}` |

Compensation structure per `delivery-routes.md` Rider Hiring section ships in plan 56-11 alongside the operator UI to add riders.

## Plan-to-feature mapping

Every Soma Delights workflow named anywhere in `99_business_refs/somadelights/` is delivered by a specific downstream plan in Phase 56:

| Soma Delights workflow | somaerp plan |
| --- | --- |
| Daily production tracker (4 AM batch log) | 56-09 |
| Tomorrow's delivery dispatch sheet | 56-11 |
| Procurement planner (next 3 days) | 56-08 |
| Subscription mgmt + customer profile | 56-10 |
| Recipe definitions for 6 SKUs | 56-05 |
| QC checkpoints + FSSAI compliance | 56-06 |
| Raw materials + supplier matrix | 56-07 |
| Kitchen + capacity setup | 56-03 |
| Product line + product catalog | 56-04 |
| Yield / COGS / spoilage reporting | 56-12 |

Plan numbering matches the data-model layer numbering so the build sequence respects FK dependencies (geography before catalog before recipes before quality, etc.). Plan 56-02 ships the foundational scaffolding (proxy client implementation, schema bootstrap, tenant config seed loader) before layer plans begin.

## TBDs to confirm with operator before seed YAML lands

These are non-fabricated unknowns. Each must be confirmed before the bootstrap runs in production; the seed YAML in plan 56-02 will read each from a tenant-config file the operator fills.

- KPHB Home Kitchen exact unit/floor address (for `business_address` vault entry)
- FSSAI license number (vault key `fssai_license_number`) — populated when license issues
- Founder's tennetctl iam user_id (for `fct_riders` and `workspace.owner_user_id`)
- Specific local farm partnerships (currently TBD per `supplier-vendor-directory.md`)
- Specific IndiaMART PET bottle supplier name (TBD; depends on operator's first vendor choice)
- Specific Kukatpally print shop (TBD)
- Whether Hydration Cooler genuinely uses 300 ml (per `launch-menu.md`) vs 250 ml (consistency with other SKUs in `recipe-standardization.md`)
- Honey supplier (`24 Mantra` is one option; operator may prefer another)

## Related documents

- `../00_main/00_overview.md` — somaerp scope
- `../00_main/02_tenant_model.md` — tenant_id = workspace_id
- `../03_scaling/01_multi_region_kitchen_topology.md` — multi-kitchen path
- `../03_scaling/02_capacity_planning_model.md` — capacity row shape
- `../03_scaling/03_data_residency_compliance.md` — FSSAI + DPDP posture
- `../04_integration/02_audit_emission.md` — bootstrap audit category
- `../04_integration/03_vault_for_secrets_and_blobs.md` — tenant-secret keyspace
- `../04_integration/04_notify_integration.md` — Soma-Delights-specific notification triggers
- `../04_integration/05_flows_for_workflows.md` — flow keys this tenant exercises
- `../01_data_model/*` (forward references — Task 2)
- `99_business_refs/somadelights/01-foundation/brand-roadmap-vision.md`
- `99_business_refs/somadelights/03-product/launch-menu.md`
- `99_business_refs/somadelights/03-product/recipe-standardization.md`
- `99_business_refs/somadelights/03-product/subscription-plans.md`
- `99_business_refs/somadelights/05-operations/operations-model.md`
- `99_business_refs/somadelights/05-operations/delivery-routes.md`
- `99_business_refs/somadelights/05-operations/supplier-vendor-directory.md`
- `99_business_refs/somadelights/09-execution/multi-lingual-strategy.md`
- `99_business_refs/somadelights/09-execution/customer-data-privacy.md`
- `99_business_refs/somadelights/09-execution/compliance-food-safety.md`
