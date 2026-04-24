// All shared TS types for the somaerp frontend live here.
// Per project rule: ONE types file, no scattering.

export type ApiEnvelope<T> =
  | { ok: true; data: T }
  | { ok: false; error: { code: string; message: string } };

// ---------------------------------------------------------------------------
// Auth — tennetctl IAM
// ---------------------------------------------------------------------------

export type AuthUser = {
  id: string;
  email: string;
  display_name: string | null;
};

export type AuthSession = {
  id: string;
  expires_at: string;
};

export type AuthResponse = {
  token: string;
  user: AuthUser;
  session: AuthSession;
};

export type TennetctlProxyStatus = {
  ok: boolean;
  base_url: string;
  latency_ms: number;
  last_error: string | null;
};

export type HealthData = {
  somaerp_version: string;
  somaerp_uptime_s: number;
  tennetctl_proxy: TennetctlProxyStatus;
};

// ---------------------------------------------------------------------------
// Geography (Plan 56-03) — regions (read-only), locations, kitchens, zones.
// Shape mirrors the v_* view payloads from the backend.
// ---------------------------------------------------------------------------

export type Region = {
  id: number;
  code: string;
  country_code: string;
  state_name: string;
  regulatory_body: string | null;
  default_currency_code: string;
  default_timezone: string;
};

export type Location = {
  id: string;
  tenant_id: string;
  region_id: number;
  region_code: string;
  country_code: string;
  name: string;
  slug: string;
  timezone: string;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type KitchenType = "home" | "commissary" | "satellite";
export type KitchenStatus = "active" | "paused" | "decommissioned";

export type Kitchen = {
  id: string;
  tenant_id: string;
  location_id: string;
  location_name: string;
  name: string;
  slug: string;
  kitchen_type: KitchenType;
  address_jsonb: Record<string, unknown>;
  geo_lat: number | null;
  geo_lng: number | null;
  status: KitchenStatus;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ZoneStatus = "active" | "paused";

export type ServiceZone = {
  id: string;
  tenant_id: string;
  kitchen_id: string;
  kitchen_name: string;
  name: string;
  polygon_jsonb: Record<string, unknown>;
  status: ZoneStatus;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

// ---------------------------------------------------------------------------
// Catalog (Plan 56-04) — categories, tags, product lines, products, variants.
// Decimal fields typed as `string | null` because Pydantic v2 serializes
// Decimal as string in JSON.
// ---------------------------------------------------------------------------

export type ProductCategory = { id: number; code: string; name: string };

export type ProductTag = { id: number; code: string; name: string };

export type ProductLineStatus = "active" | "paused" | "discontinued";

export type ProductLine = {
  id: string;
  tenant_id: string;
  category_id: number;
  category_code: string;
  category_name: string;
  name: string;
  slug: string;
  status: ProductLineStatus;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ProductStatus = "active" | "paused" | "discontinued";

export type Product = {
  id: string;
  tenant_id: string;
  product_line_id: string;
  product_line_name: string;
  category_code: string;
  category_name: string;
  name: string;
  slug: string;
  description: string | null;
  target_benefit: string | null;
  default_serving_size_ml: string | null;
  default_shelf_life_hours: number | null;
  target_cogs_amount: string | null;
  default_selling_price: string | null;
  currency_code: string;
  status: ProductStatus;
  tag_codes: string[];
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type VariantStatus = "active" | "paused";

export type ProductVariant = {
  id: string;
  tenant_id: string;
  product_id: string;
  product_name: string;
  name: string;
  slug: string;
  serving_size_ml: string | null;
  selling_price: string;
  currency_code: string;
  is_default: boolean;
  status: VariantStatus;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

// ---------------------------------------------------------------------------
// Supply (Plan 56-05) — raw material categories, units of measure, supplier
// source types, raw materials, raw material variants, suppliers, and the
// mutable raw_material <-> supplier link (with is_primary toggle).
// Decimal fields as `string | null` (Pydantic v2 Decimal -> JSON string).
// ---------------------------------------------------------------------------

export type RawMaterialCategory = {
  id: number;
  code: string;
  name: string;
  deprecated_at: string | null;
};

export type UnitDimension = "mass" | "volume" | "count";

export type UnitOfMeasure = {
  id: number;
  code: string;
  name: string;
  dimension: UnitDimension;
  base_unit_id: number | null;
  to_base_factor: string;
};

export type SupplierSourceType = {
  id: number;
  code: string;
  name: string;
  deprecated_at: string | null;
};

export type RawMaterialStatus = "active" | "paused" | "discontinued";

export type RawMaterial = {
  id: string;
  tenant_id: string;
  category_id: number;
  category_code: string;
  category_name: string;
  name: string;
  slug: string;
  default_unit_id: number;
  default_unit_code: string;
  default_shelf_life_hours: number | null;
  requires_lot_tracking: boolean;
  target_unit_cost: string | null;
  currency_code: string;
  status: RawMaterialStatus;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type RawMaterialVariantStatus = "active" | "paused";

export type RawMaterialVariant = {
  id: string;
  tenant_id: string;
  raw_material_id: string;
  raw_material_name: string;
  name: string;
  slug: string;
  target_unit_cost: string | null;
  currency_code: string;
  is_default: boolean;
  status: RawMaterialVariantStatus;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type SupplierStatus = "active" | "paused" | "blacklisted";

export type Supplier = {
  id: string;
  tenant_id: string;
  name: string;
  slug: string;
  source_type_id: number;
  source_type_code: string;
  source_type_name: string;
  location_id: string | null;
  location_name: string | null;
  contact_jsonb: Record<string, unknown>;
  payment_terms: string | null;
  default_currency_code: string;
  quality_rating: number | null;
  status: SupplierStatus;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

// ---------------------------------------------------------------------------
// Kitchen Capacity (Plan 56-06) — fct_kitchen_capacity + v_kitchen_current_capacity.
// Decimal fields serialized as string by Pydantic v2. Times are "HH:MM:SS".
// ---------------------------------------------------------------------------

export type KitchenCapacity = {
  id: string;
  tenant_id: string;
  kitchen_id: string;
  kitchen_name: string;
  product_line_id: string;
  product_line_name: string;
  capacity_value: string;
  capacity_unit_id: number;
  capacity_unit_code: string;
  time_window_start: string;
  time_window_end: string;
  valid_from: string;
  valid_to: string | null;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type SupplierMaterialLink = {
  id: string;
  tenant_id: string;
  raw_material_id: string;
  raw_material_name: string;
  supplier_id: string;
  supplier_name: string;
  is_primary: boolean;
  last_known_unit_cost: string | null;
  currency_code: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

// ---------------------------------------------------------------------------
// Recipes (Plan 56-07) — fct_recipes + dtl_recipe_ingredients + dtl_recipe_steps
// + step-equipment links + cost rollup. Decimals as string (Pydantic JSON).
// ---------------------------------------------------------------------------

export type RecipeStatus = "draft" | "active" | "archived";

export type Recipe = {
  id: string;
  tenant_id: string;
  product_id: string;
  product_name: string | null;
  product_slug: string | null;
  product_category_code: string | null;
  version: number;
  status: RecipeStatus;
  effective_from: string | null;
  notes: string | null;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type RecipeIngredient = {
  id: string;
  tenant_id: string;
  recipe_id: string;
  raw_material_id: string;
  raw_material_name: string | null;
  raw_material_slug: string | null;
  raw_material_target_unit_cost: string | null;
  raw_material_currency_code: string | null;
  quantity: string;
  unit_id: number;
  unit_code: string | null;
  unit_dimension: string | null;
  position: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type RecipeStep = {
  id: string;
  tenant_id: string;
  recipe_id: string;
  step_number: number;
  name: string;
  duration_min: number | null;
  equipment_notes: string | null;
  instructions: string | null;
  created_at: string;
  updated_at: string;
};

export type RecipeCostLine = {
  ingredient_id: string;
  raw_material_id: string;
  raw_material_name: string | null;
  quantity: string;
  unit_code: string | null;
  unit_cost: string | null;
  line_cost: string | null;
  is_unconvertible: boolean;
};

export type RecipeCostSummary = {
  recipe_id: string;
  product_name: string | null;
  total_cost: string;
  currency_code: string;
  ingredient_count: number;
  has_unconvertible_units: boolean;
  lines: RecipeCostLine[];
};

export type StepEquipmentLink = {
  id: string;
  tenant_id: string;
  step_id: string;
  equipment_id: string;
  equipment_name: string | null;
  equipment_slug: string | null;
  equipment_category_code: string | null;
  equipment_category_name: string | null;
  created_at: string;
  created_by: string;
};

// ---------------------------------------------------------------------------
// Equipment (Plan 56-07)
// ---------------------------------------------------------------------------

export type EquipmentStatus = "active" | "maintenance" | "retired";

export type EquipmentCategory = {
  id: number;
  code: string;
  name: string;
  deprecated_at: string | null;
};

export type Equipment = {
  id: string;
  tenant_id: string;
  category_id: number;
  category_code: string | null;
  category_name: string | null;
  name: string;
  slug: string;
  status: EquipmentStatus;
  purchase_cost: string | null;
  currency_code: string | null;
  purchase_date: string | null;
  expected_lifespan_months: number | null;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type KitchenEquipmentLink = {
  id: string;
  tenant_id: string;
  kitchen_id: string;
  kitchen_name: string | null;
  equipment_id: string;
  equipment_name: string | null;
  equipment_slug: string | null;
  equipment_status: string | null;
  equipment_category_code: string | null;
  equipment_category_name: string | null;
  quantity: number;
  notes: string | null;
  created_at: string;
  created_by: string;
};

// ---------------------------------------------------------------------------
// Quality (Plan 56-08) — dim_qc_check_types / dim_qc_stages / dim_qc_outcomes
// (universal seeded lookups), dim_qc_checkpoints (tenant-scoped catalog),
// evt_qc_checks (append-only events).
// Decimal fields as string (Pydantic v2 Decimal -> JSON string).
// ---------------------------------------------------------------------------

export type QcCheckType = {
  id: number;
  code: string;
  name: string;
  deprecated_at: string | null;
};

export type QcStage = {
  id: number;
  code: string;
  name: string;
  deprecated_at: string | null;
};

export type QcOutcome = {
  id: number;
  code: string;
  name: string;
  deprecated_at: string | null;
};

export type QcCheckpointScopeKind =
  | "recipe_step"
  | "raw_material"
  | "kitchen"
  | "product"
  | "universal";

export type QcCheckpointStatus = "active" | "paused" | "archived";

export type QcCheckpoint = {
  id: string;
  tenant_id: string;
  stage_id: number;
  stage_code: string | null;
  stage_name: string | null;
  check_type_id: number;
  check_type_code: string | null;
  check_type_name: string | null;
  scope_kind: QcCheckpointScopeKind;
  scope_ref_id: string | null;
  name: string;
  criteria_jsonb: Record<string, unknown>;
  required: boolean;
  status: QcCheckpointStatus;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

// ---------------------------------------------------------------------------
// Procurement + Inventory (Plan 56-09) — fct_procurement_runs, dtl_procurement_lines,
// evt_inventory_movements, v_inventory_current, MRP-lite planner.
// Decimals as string (Pydantic v2 Decimal -> JSON string).
// ---------------------------------------------------------------------------

export type ProcurementRunStatus = "active" | "reconciled" | "cancelled";

export type ProcurementRun = {
  id: string;
  tenant_id: string;
  kitchen_id: string;
  kitchen_name: string | null;
  supplier_id: string;
  supplier_name: string | null;
  supplier_slug: string | null;
  run_date: string;
  performed_by_user_id: string;
  total_cost: string;
  computed_total: string | null;
  line_count: number;
  currency_code: string;
  notes: string | null;
  status: ProcurementRunStatus;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ProcurementLine = {
  id: string;
  tenant_id: string;
  procurement_run_id: string;
  raw_material_id: string;
  raw_material_name: string | null;
  raw_material_slug: string | null;
  quantity: string;
  unit_id: number;
  unit_code: string | null;
  unit_cost: string;
  line_cost: string;
  lot_number: string | null;
  quality_grade: number | null;
  received_at: string | null;
  created_at: string;
  updated_at: string;
};

export type InventoryMovementType =
  | "received"
  | "consumed"
  | "wasted"
  | "adjusted"
  | "expired";

export type InventoryCurrent = {
  tenant_id: string;
  kitchen_id: string;
  kitchen_name: string | null;
  raw_material_id: string;
  raw_material_name: string | null;
  raw_material_slug: string | null;
  category_id: number | null;
  category_code: string | null;
  category_name: string | null;
  default_unit_id: number;
  default_unit_code: string | null;
  default_unit_dimension: string | null;
  target_unit_cost: string | null;
  currency_code: string;
  qty_in_base_unit: string;
  qty_in_default_unit: string | null;
};

export type InventoryMovement = {
  id: string;
  tenant_id: string;
  kitchen_id: string;
  kitchen_name: string | null;
  raw_material_id: string;
  raw_material_name: string | null;
  raw_material_slug: string | null;
  raw_material_category_id: number | null;
  raw_material_category_code: string | null;
  raw_material_category_name: string | null;
  movement_type: InventoryMovementType;
  quantity: string;
  unit_id: number;
  unit_code: string | null;
  unit_dimension: string | null;
  lot_number: string | null;
  batch_id_ref: string | null;
  procurement_run_id: string | null;
  reason: string | null;
  ts: string;
  performed_by_user_id: string;
  metadata: Record<string, unknown>;
};

export type ProcurementPlanDemand = {
  product_id: string;
  planned_qty: number;
  target_date: string;
};

export type ProcurementPlanRequest = {
  kitchen_id: string;
  demand: ProcurementPlanDemand[];
};

export type ProcurementPlanRequirement = {
  raw_material_id: string;
  raw_material_name: string | null;
  raw_material_slug: string | null;
  category_name: string | null;
  required_qty: string;
  required_unit_code: string | null;
  in_stock_qty: string;
  gap_qty: string;
  primary_supplier_id: string | null;
  primary_supplier_name: string | null;
  last_known_unit_cost: string | null;
  target_unit_cost: string | null;
  estimated_cost: string;
  currency_code: string;
};

export type ProcurementPlanError = {
  code: string;
  product_id: string | null;
  raw_material_id: string | null;
  message: string;
};

export type ProcurementPlanResponse = {
  kitchen_id: string;
  horizon_start: string;
  horizon_end: string;
  requirements: ProcurementPlanRequirement[];
  unconvertible_units: Record<string, unknown>[];
  errors: ProcurementPlanError[];
  total_estimated_cost: string;
  currency_code: string;
};

// ---------------------------------------------------------------------------
// Production Batches (Plan 56-10) — the 4 AM tracker.
// Decimals as string (Pydantic v2 Decimal -> JSON string).
// ---------------------------------------------------------------------------

export type ProductionBatchStatus =
  | "planned"
  | "in_progress"
  | "completed"
  | "cancelled";

export type ProductionBatch = {
  id: string;
  tenant_id: string;
  kitchen_id: string;
  kitchen_name: string | null;
  product_id: string;
  product_name: string | null;
  product_slug: string | null;
  default_selling_price: string | null;
  recipe_id: string;
  recipe_version: number | null;
  recipe_status: string | null;
  run_date: string;
  planned_qty: string;
  actual_qty: string | null;
  status: ProductionBatchStatus;
  shift_start: string | null;
  shift_end: string | null;
  cancel_reason: string | null;
  currency_code: string;
  lead_user_id: string | null;
  notes: string | null;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type BatchStepLog = {
  id: string;
  tenant_id: string;
  batch_id: string;
  recipe_step_id: string | null;
  step_number: number;
  name: string;
  started_at: string | null;
  completed_at: string | null;
  performed_by_user_id: string | null;
  notes: string | null;
  duration_min: string | null;
  created_at: string;
  updated_at: string;
};

export type BatchConsumptionLine = {
  id: string;
  tenant_id: string;
  batch_id: string;
  raw_material_id: string;
  raw_material_name: string | null;
  raw_material_slug: string | null;
  recipe_ingredient_id: string | null;
  planned_qty: string;
  actual_qty: string | null;
  unit_id: number;
  unit_code: string | null;
  unit_dimension: string | null;
  unit_cost_snapshot: string;
  currency_code: string;
  lot_number: string | null;
  line_cost_actual: string | null;
  created_at: string;
  updated_at: string;
};

export type BatchQcResult = {
  id: string;
  tenant_id: string;
  batch_id: string;
  checkpoint_id: string;
  checkpoint_name: string | null;
  checkpoint_scope_kind: string | null;
  outcome_id: number;
  outcome_code: string | null;
  outcome_name: string | null;
  measured_value: string | null;
  measured_unit_id: number | null;
  measured_unit_code: string | null;
  notes: string | null;
  photo_vault_key: string | null;
  performed_by_user_id: string | null;
  last_event_id: string | null;
  events_count: number;
  created_at: string;
  updated_at: string;
};

export type BatchSummary = {
  batch_id: string;
  tenant_id: string;
  kitchen_id: string;
  product_id: string;
  recipe_id: string;
  run_date: string;
  status: ProductionBatchStatus;
  planned_qty: string;
  actual_qty: string | null;
  yield_pct: string | null;
  total_cogs: string;
  cogs_per_unit: string | null;
  gross_margin_pct: string | null;
  duration_min: string | null;
  ingredient_count: number;
  has_unconvertible_units: boolean;
  step_count_total: number;
  step_count_completed: number;
  currency_code: string;
  default_selling_price: string | null;
};

export type BatchDetail = {
  batch: ProductionBatch;
  steps: BatchStepLog[];
  consumption: BatchConsumptionLine[];
  qc_results: BatchQcResult[];
  summary: BatchSummary | null;
};

export type ProductionBoardKitchen = {
  kitchen_id: string;
  kitchen_name: string | null;
  batches: { batch: ProductionBatch; summary: BatchSummary | null }[];
};

export type ProductionBoard = {
  date: string;
  kitchens: ProductionBoardKitchen[];
};

export type QcCheck = {
  id: string;
  tenant_id: string;
  checkpoint_id: string;
  checkpoint_name: string | null;
  checkpoint_scope_kind: QcCheckpointScopeKind | null;
  checkpoint_scope_ref_id: string | null;
  stage_id: number | null;
  stage_code: string | null;
  stage_name: string | null;
  check_type_id: number | null;
  check_type_code: string | null;
  check_type_name: string | null;
  batch_id: string | null;
  raw_material_lot: string | null;
  kitchen_id: string | null;
  kitchen_name: string | null;
  outcome_id: number;
  outcome_code: string | null;
  outcome_name: string | null;
  measured_value: string | null;
  measured_unit_id: number | null;
  measured_unit_code: string | null;
  notes: string | null;
  photo_vault_key: string | null;
  performed_by_user_id: string;
  ts: string;
  metadata: Record<string, unknown>;
};

// ---------------------------------------------------------------------------
// Customers + Subscriptions (Plan 56-11)
// Decimals as string (Pydantic v2 Decimal -> JSON string).
// ---------------------------------------------------------------------------

export type CustomerStatus =
  | "prospect"
  | "active"
  | "paused"
  | "churned"
  | "blocked";

export type Customer = {
  id: string;
  tenant_id: string;
  location_id: string | null;
  location_name: string | null;
  name: string;
  slug: string;
  email: string | null;
  phone: string | null;
  address_jsonb: Record<string, unknown>;
  delivery_notes: string | null;
  acquisition_source: string | null;
  status: CustomerStatus;
  lifetime_value: string;
  properties: Record<string, unknown>;
  active_subscription_count: number;
  created_at: string;
  updated_at: string;
};

export type SubscriptionFrequency = {
  id: number;
  code: string;
  name: string;
  deliveries_per_week: string;
  deprecated_at: string | null;
};

export type SubscriptionPlanStatus = "draft" | "active" | "archived";

export type SubscriptionPlan = {
  id: string;
  tenant_id: string;
  name: string;
  slug: string;
  description: string | null;
  frequency_id: number;
  frequency_code: string | null;
  frequency_name: string | null;
  deliveries_per_week: string | null;
  price_per_delivery: string | null;
  currency_code: string;
  status: SubscriptionPlanStatus;
  properties: Record<string, unknown>;
  item_count: number;
  created_at: string;
  updated_at: string;
};

export type SubscriptionPlanItem = {
  id: string;
  tenant_id: string;
  plan_id: string;
  product_id: string;
  product_name: string | null;
  product_slug: string | null;
  variant_id: string | null;
  variant_name: string | null;
  qty_per_delivery: string;
  position: number;
  notes: string | null;
  line_price: string | null;
  currency_code: string | null;
  created_at: string;
  updated_at: string;
};

export type SubscriptionPlanDetail = {
  plan: SubscriptionPlan;
  items: SubscriptionPlanItem[];
};

export type SubscriptionStatus = "active" | "paused" | "cancelled" | "ended";

export type Subscription = {
  id: string;
  tenant_id: string;
  customer_id: string;
  customer_name: string | null;
  customer_slug: string | null;
  plan_id: string;
  plan_name: string | null;
  plan_slug: string | null;
  frequency_id: number | null;
  frequency_code: string | null;
  frequency_name: string | null;
  price_per_delivery: string | null;
  service_zone_id: string | null;
  service_zone_name: string | null;
  start_date: string;
  end_date: string | null;
  status: SubscriptionStatus;
  paused_from: string | null;
  paused_to: string | null;
  billing_cycle: string | null;
  currency_code: string | null;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type SubscriptionEventType =
  | "started"
  | "paused"
  | "resumed"
  | "cancelled"
  | "ended"
  | "plan_changed"
  | "frequency_changed";

export type SubscriptionEvent = {
  id: string;
  tenant_id: string;
  subscription_id: string;
  event_type: SubscriptionEventType;
  from_date: string | null;
  to_date: string | null;
  reason: string | null;
  metadata: Record<string, unknown>;
  ts: string;
  performed_by_user_id: string;
  created_at: string;
};

// ---------------------------------------------------------------------------
// Delivery (Plan 56-12) — routes, riders, runs, stops.
// ---------------------------------------------------------------------------

export type RiderRole = {
  id: number;
  code: string;
  name: string;
  deprecated_at: string | null;
};

export type RiderStatus = "active" | "inactive" | "suspended";

export type Rider = {
  id: string;
  tenant_id: string;
  user_id: string | null;
  name: string;
  phone: string | null;
  role_id: number;
  role_name: string | null;
  role_code: string | null;
  vehicle_type: string | null;
  license_number: string | null;
  status: RiderStatus;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type RouteStatus = "active" | "paused" | "decommissioned";

export type DeliveryRoute = {
  id: string;
  tenant_id: string;
  kitchen_id: string;
  kitchen_name: string | null;
  name: string;
  slug: string;
  area: string | null;
  target_window_start: string | null;
  target_window_end: string | null;
  status: RouteStatus;
  properties: Record<string, unknown>;
  customer_count: number;
  created_at: string;
  updated_at: string;
};

export type RouteCustomerLink = {
  id: string;
  tenant_id: string;
  route_id: string;
  customer_id: string;
  customer_name: string | null;
  customer_phone: string | null;
  customer_address: Record<string, unknown> | null;
  sequence_position: number;
  created_at: string;
  created_by: string;
};

export type DeliveryRunStatus =
  | "planned"
  | "in_transit"
  | "completed"
  | "cancelled";

export type DeliveryRun = {
  id: string;
  tenant_id: string;
  route_id: string;
  route_name: string | null;
  route_slug: string | null;
  kitchen_id: string | null;
  kitchen_name: string | null;
  rider_id: string;
  rider_name: string | null;
  rider_phone: string | null;
  run_date: string;
  status: DeliveryRunStatus;
  started_at: string | null;
  completed_at: string | null;
  total_stops: number;
  completed_stops: number;
  missed_stops: number;
  completion_pct: number | null;
  notes: string | null;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type DeliveryStopStatus =
  | "pending"
  | "delivered"
  | "missed"
  | "customer_unavailable"
  | "cancelled"
  | "rescheduled";

export type DeliveryStop = {
  id: string;
  tenant_id: string;
  delivery_run_id: string;
  customer_id: string;
  customer_name: string | null;
  customer_phone: string | null;
  customer_address: Record<string, unknown> | null;
  sequence_position: number;
  scheduled_at: string | null;
  actual_at: string | null;
  status: DeliveryStopStatus;
  photo_vault_key: string | null;
  signature_vault_key: string | null;
  notes: string | null;
  properties: Record<string, unknown>;
  delay_sec: number | null;
  created_at: string;
  updated_at: string;
};

export type DeliveryRunDetail = {
  run: DeliveryRun;
  stops: DeliveryStop[];
};

export type DeliveryBoardKitchen = {
  kitchen_id: string;
  kitchen_name: string | null;
  runs: DeliveryRun[];
};

export type DeliveryBoard = {
  date: string;
  kitchens: DeliveryBoardKitchen[];
};

// ---------------------------------------------------------------------------
// Reports (Plan 56-13) — read-only rollup views over prior layers.
// Decimals as string (Pydantic v2 Decimal -> JSON string).
// ---------------------------------------------------------------------------

export type ReportBucket = "daily" | "weekly" | "monthly";
export type InventoryAlertLevel = "critical" | "low" | "ok";
export type InventoryAlertSeverity = "critical" | "low" | "all";

export type DashboardToday = {
  tenant_id: string;
  date: string;
  active_batches: number;
  completed_batches: number;
  in_transit_runs: number;
  completed_runs: number;
  scheduled_deliveries: number;
  completed_deliveries: number;
  active_subscriptions: number;
};

export type YieldTrendPoint = {
  date: string;
  kitchen_id: string;
  kitchen_name: string | null;
  product_id: string;
  product_name: string | null;
  planned_qty: string;
  actual_qty: string;
  yield_pct: string | null;
  batch_count: number;
};

export type CogsTrendPoint = {
  date: string;
  kitchen_id: string;
  kitchen_name: string | null;
  product_id: string;
  product_name: string | null;
  total_cogs: string;
  cogs_per_unit: string | null;
  batch_count: number;
  currency_code: string | null;
};

export type InventoryAlert = {
  kitchen_id: string;
  kitchen_name: string | null;
  raw_material_id: string;
  raw_material_name: string | null;
  category_name: string | null;
  current_qty: string;
  unit_code: string | null;
  reorder_point_qty: string | null;
  alert_level: InventoryAlertLevel;
  primary_supplier_id: string | null;
  primary_supplier_name: string | null;
};

export type ProcurementSpendPoint = {
  year_month: string;
  kitchen_id: string;
  kitchen_name: string | null;
  supplier_id: string;
  supplier_name: string | null;
  total_spend: string;
  currency_code: string | null;
  run_count: number;
  line_count: number;
};

export type RevenueProjection = {
  subscription_id: string;
  customer_name: string | null;
  plan_name: string | null;
  frequency_code: string | null;
  price_per_delivery: string | null;
  deliveries_per_week: string | null;
  weekly_projected: string | null;
  daily_projected: string | null;
  monthly_projected: string | null;
  currency_code: string | null;
};

export type ComplianceBatchRow = {
  batch_id: string;
  run_date: string;
  product_name: string | null;
  recipe_version: number | null;
  kitchen_name: string | null;
  planned_qty: string;
  actual_qty: string | null;
  lot_numbers: string[];
  qc_results: Record<string, unknown>[];
  completed_by: string | null;
};
