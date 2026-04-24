import type {
  ApiEnvelope,
  DashboardToday,
  YieldTrendPoint,
  CogsTrendPoint,
  InventoryAlert,
  InventoryAlertSeverity,
  ProcurementSpendPoint,
  ReportBucket,
  RevenueProjection,
  ComplianceBatchRow,
  BatchConsumptionLine,
  BatchDetail,
  BatchQcResult,
  BatchStepLog,
  BatchSummary,
  Equipment,
  EquipmentCategory,
  EquipmentStatus,
  InventoryCurrent,
  InventoryMovement,
  InventoryMovementType,
  Kitchen,
  KitchenCapacity,
  KitchenEquipmentLink,
  KitchenStatus,
  KitchenType,
  Location,
  ProcurementLine,
  ProcurementPlanDemand,
  ProcurementPlanResponse,
  ProcurementRun,
  ProcurementRunStatus,
  Product,
  ProductCategory,
  ProductLine,
  ProductLineStatus,
  ProductStatus,
  ProductTag,
  ProductionBatch,
  ProductionBatchStatus,
  ProductionBoard,
  QcCheck,
  QcCheckType,
  QcCheckpoint,
  QcCheckpointScopeKind,
  QcCheckpointStatus,
  QcOutcome,
  QcStage,
  RawMaterial,
  RawMaterialCategory,
  RawMaterialStatus,
  Recipe,
  RecipeCostSummary,
  RecipeIngredient,
  RecipeStatus,
  RecipeStep,
  Region,
  ServiceZone,
  StepEquipmentLink,
  Supplier,
  SupplierSourceType,
  SupplierStatus,
  UnitOfMeasure,
  ZoneStatus,
  Customer,
  CustomerStatus,
  SubscriptionFrequency,
  SubscriptionPlan,
  SubscriptionPlanDetail,
  SubscriptionPlanItem,
  SubscriptionPlanStatus,
  Subscription,
  SubscriptionStatus,
  SubscriptionEvent,
  RiderRole,
  Rider,
  RiderStatus,
  RouteStatus,
  DeliveryRoute,
  RouteCustomerLink,
  DeliveryRun,
  DeliveryRunStatus,
  DeliveryRunDetail,
  DeliveryStop,
  DeliveryStopStatus,
  DeliveryBoard,
} from "@/types/api";

function readToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem("somaerp_token");
  } catch {
    return null;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const base = process.env.NEXT_PUBLIC_SOMAERP_BACKEND ?? "http://localhost:51736";
  const token = readToken();
  const headers = new Headers(init?.headers);
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(`${base}${path}`, { ...init, headers });
  const json = (await res.json()) as ApiEnvelope<T>;
  if (!json.ok) {
    throw new Error(json.error?.message ?? "unknown error");
  }
  return json.data;
}

// ---------------------------------------------------------------------------
// Geography (Plan 56-03) wrappers — typed thin helpers over apiFetch.
// All geography routes are rooted at /v1/somaerp/geography per spec.
// ---------------------------------------------------------------------------

type QsScalar = string | number | boolean | undefined | null;
type QsRecord = Record<string, QsScalar>;

function qs(params?: QsRecord): string {
  if (!params) return "";
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== ""
  );
  if (entries.length === 0) return "";
  const sp = new URLSearchParams();
  for (const [k, v] of entries) sp.set(k, String(v));
  return `?${sp.toString()}`;
}

const jsonHeaders: HeadersInit = { "Content-Type": "application/json" };

// Regions (read-only) ---------------------------------------------------------

export const listRegions = (): Promise<Region[]> =>
  apiFetch<Region[]>("/v1/somaerp/geography/regions");

// Locations -------------------------------------------------------------------

export type ListLocationsParams = {
  region_id?: number;
  q?: string;
  limit?: number;
  cursor?: string;
};

export const listLocations = (params?: ListLocationsParams): Promise<Location[]> =>
  apiFetch<Location[]>(`/v1/somaerp/geography/locations${qs(params)}`);

export type CreateLocationBody = {
  region_id: number;
  name: string;
  slug: string;
  timezone: string;
  properties?: Record<string, unknown>;
};

export const createLocation = (body: CreateLocationBody): Promise<Location> =>
  apiFetch<Location>("/v1/somaerp/geography/locations", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

// Kitchens --------------------------------------------------------------------

export type ListKitchensParams = {
  location_id?: string;
  status?: KitchenStatus;
  q?: string;
  limit?: number;
  cursor?: string;
};

export const listKitchens = (params?: ListKitchensParams): Promise<Kitchen[]> =>
  apiFetch<Kitchen[]>(`/v1/somaerp/geography/kitchens${qs(params)}`);

export const getKitchen = (id: string): Promise<Kitchen> =>
  apiFetch<Kitchen>(`/v1/somaerp/geography/kitchens/${id}`);

export type CreateKitchenBody = {
  location_id: string;
  name: string;
  slug: string;
  kitchen_type: KitchenType;
  address_jsonb?: Record<string, unknown>;
  geo_lat?: number;
  geo_lng?: number;
  status?: KitchenStatus;
  properties?: Record<string, unknown>;
};

export const createKitchen = (body: CreateKitchenBody): Promise<Kitchen> =>
  apiFetch<Kitchen>("/v1/somaerp/geography/kitchens", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

// Kitchen capacity -----------------------------------------------------------

export type ListKitchenCapacityParams = {
  product_line_id?: string;
  valid_on?: string;
  include_history?: boolean;
  include_deleted?: boolean;
  limit?: number;
  offset?: number;
};

export const listKitchenCapacity = (
  kitchenId: string,
  params?: ListKitchenCapacityParams
): Promise<KitchenCapacity[]> =>
  apiFetch<KitchenCapacity[]>(
    `/v1/somaerp/geography/kitchens/${kitchenId}/capacity${qs(
      params as QsRecord | undefined
    )}`
  );

export type CreateKitchenCapacityBody = {
  product_line_id: string;
  capacity_value: number;
  capacity_unit_id: number;
  time_window_start: string;
  time_window_end: string;
  valid_from: string;
  valid_to?: string | null;
  properties?: Record<string, unknown>;
};

export const createKitchenCapacity = (
  kitchenId: string,
  body: CreateKitchenCapacityBody
): Promise<KitchenCapacity> =>
  apiFetch<KitchenCapacity>(
    `/v1/somaerp/geography/kitchens/${kitchenId}/capacity`,
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    }
  );

export const closeKitchenCapacity = (
  kitchenId: string,
  capacityId: string,
  validTo: string
): Promise<KitchenCapacity> =>
  apiFetch<KitchenCapacity>(
    `/v1/somaerp/geography/kitchens/${kitchenId}/capacity/${capacityId}`,
    {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify({ valid_to: validTo }),
    }
  );

// Service zones --------------------------------------------------------------

export type ListServiceZonesParams = {
  kitchen_id?: string;
  status?: ZoneStatus;
  limit?: number;
  cursor?: string;
};

export const listServiceZones = (
  params?: ListServiceZonesParams
): Promise<ServiceZone[]> =>
  apiFetch<ServiceZone[]>(`/v1/somaerp/geography/service-zones${qs(params)}`);

export type CreateServiceZoneBody = {
  kitchen_id: string;
  name: string;
  polygon_jsonb: Record<string, unknown>;
  status?: ZoneStatus;
  properties?: Record<string, unknown>;
};

export const createServiceZone = (
  body: CreateServiceZoneBody
): Promise<ServiceZone> =>
  apiFetch<ServiceZone>("/v1/somaerp/geography/service-zones", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

// ---------------------------------------------------------------------------
// Catalog (Plan 56-04) wrappers
// ---------------------------------------------------------------------------

export const listCategories = (): Promise<ProductCategory[]> =>
  apiFetch<ProductCategory[]>("/v1/somaerp/catalog/categories");

export const listTags = (): Promise<ProductTag[]> =>
  apiFetch<ProductTag[]>("/v1/somaerp/catalog/tags");

export type ListProductLinesParams = {
  category_id?: number;
  status?: ProductLineStatus;
  q?: string;
  limit?: number;
  cursor?: string;
};

export const listProductLines = (
  params?: ListProductLinesParams
): Promise<ProductLine[]> =>
  apiFetch<ProductLine[]>(`/v1/somaerp/catalog/product-lines${qs(params)}`);

export type CreateProductLineBody = {
  category_id: number;
  name: string;
  slug: string;
  status?: ProductLineStatus;
  properties?: Record<string, unknown>;
};

export const createProductLine = (
  body: CreateProductLineBody
): Promise<ProductLine> =>
  apiFetch<ProductLine>("/v1/somaerp/catalog/product-lines", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export type ListProductsParams = {
  product_line_id?: string;
  tag_code?: string;
  status?: ProductStatus;
  currency_code?: string;
  q?: string;
  limit?: number;
  cursor?: string;
};

export const listProducts = (
  params?: ListProductsParams
): Promise<Product[]> =>
  apiFetch<Product[]>(`/v1/somaerp/catalog/products${qs(params)}`);

export type CreateProductBody = {
  product_line_id: string;
  name: string;
  slug: string;
  description?: string;
  target_benefit?: string;
  default_serving_size_ml?: number;
  default_shelf_life_hours?: number;
  target_cogs_amount?: number;
  default_selling_price?: number;
  currency_code: string;
  status?: ProductStatus;
  tag_codes?: string[];
  properties?: Record<string, unknown>;
};

export const createProduct = (body: CreateProductBody): Promise<Product> =>
  apiFetch<Product>("/v1/somaerp/catalog/products", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

// ---------------------------------------------------------------------------
// Supply (Plan 56-05) wrappers — raw materials + suppliers.
// All supply routes rooted at /v1/somaerp/supply per spec.
// ---------------------------------------------------------------------------

export const listRawMaterialCategories = (): Promise<RawMaterialCategory[]> =>
  apiFetch<RawMaterialCategory[]>(
    "/v1/somaerp/supply/raw-material-categories"
  );

export const listUnitsOfMeasure = (): Promise<UnitOfMeasure[]> =>
  apiFetch<UnitOfMeasure[]>("/v1/somaerp/supply/units-of-measure");

export const listSupplierSourceTypes = (): Promise<SupplierSourceType[]> =>
  apiFetch<SupplierSourceType[]>(
    "/v1/somaerp/supply/supplier-source-types"
  );

export type ListRawMaterialsParams = {
  category_id?: number;
  status?: RawMaterialStatus;
  q?: string;
  limit?: number;
  cursor?: string;
};

export const listRawMaterials = (
  params?: ListRawMaterialsParams
): Promise<RawMaterial[]> =>
  apiFetch<RawMaterial[]>(`/v1/somaerp/supply/raw-materials${qs(params)}`);

export type CreateRawMaterialBody = {
  category_id: number;
  name: string;
  slug: string;
  default_unit_id: number;
  default_shelf_life_hours?: number;
  requires_lot_tracking?: boolean;
  target_unit_cost?: number;
  currency_code: string;
  status?: RawMaterialStatus;
  properties?: Record<string, unknown>;
};

export const createRawMaterial = (
  body: CreateRawMaterialBody
): Promise<RawMaterial> =>
  apiFetch<RawMaterial>("/v1/somaerp/supply/raw-materials", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export type ListSuppliersParams = {
  source_type_id?: number;
  status?: SupplierStatus;
  location_id?: string;
  q?: string;
  limit?: number;
  cursor?: string;
};

export const listSuppliers = (
  params?: ListSuppliersParams
): Promise<Supplier[]> =>
  apiFetch<Supplier[]>(`/v1/somaerp/supply/suppliers${qs(params)}`);

export type CreateSupplierBody = {
  source_type_id: number;
  name: string;
  slug: string;
  location_id?: string;
  contact_jsonb?: Record<string, unknown>;
  payment_terms?: string;
  default_currency_code: string;
  quality_rating?: number;
  status?: SupplierStatus;
  properties?: Record<string, unknown>;
};

export const createSupplier = (body: CreateSupplierBody): Promise<Supplier> =>
  apiFetch<Supplier>("/v1/somaerp/supply/suppliers", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

// ---------------------------------------------------------------------------
// Recipes (Plan 56-07)
// ---------------------------------------------------------------------------

export type ListRecipesParams = {
  product_id?: string;
  status?: RecipeStatus;
  q?: string;
  limit?: number;
  offset?: number;
};

export const listRecipes = (params?: ListRecipesParams): Promise<Recipe[]> =>
  apiFetch<Recipe[]>(`/v1/somaerp/recipes${qs(params)}`);

export const getRecipe = (id: string): Promise<Recipe> =>
  apiFetch<Recipe>(`/v1/somaerp/recipes/${id}`);

export type CreateRecipeBody = {
  product_id: string;
  version?: number;
  status?: RecipeStatus;
  effective_from?: string | null;
  notes?: string | null;
  properties?: Record<string, unknown>;
};

export const createRecipe = (body: CreateRecipeBody): Promise<Recipe> =>
  apiFetch<Recipe>("/v1/somaerp/recipes", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export type UpdateRecipeBody = {
  version?: number;
  status?: RecipeStatus;
  effective_from?: string | null;
  notes?: string | null;
  properties?: Record<string, unknown>;
};

export const updateRecipe = (id: string, body: UpdateRecipeBody): Promise<Recipe> =>
  apiFetch<Recipe>(`/v1/somaerp/recipes/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteRecipe = (id: string): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/recipes/${id}`, { method: "DELETE" });

// Recipe ingredients -----------------------------------------------------

export const listRecipeIngredients = (
  recipeId: string
): Promise<RecipeIngredient[]> =>
  apiFetch<RecipeIngredient[]>(`/v1/somaerp/recipes/${recipeId}/ingredients`);

export type CreateRecipeIngredientBody = {
  raw_material_id: string;
  quantity: number;
  unit_id: number;
  position?: number;
  notes?: string | null;
};

export const createRecipeIngredient = (
  recipeId: string,
  body: CreateRecipeIngredientBody
): Promise<RecipeIngredient> =>
  apiFetch<RecipeIngredient>(`/v1/somaerp/recipes/${recipeId}/ingredients`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export type PatchRecipeIngredientBody = {
  raw_material_id?: string;
  quantity?: number;
  unit_id?: number;
  position?: number;
  notes?: string | null;
};

export const patchRecipeIngredient = (
  recipeId: string,
  ingredientId: string,
  body: PatchRecipeIngredientBody
): Promise<RecipeIngredient> =>
  apiFetch<RecipeIngredient>(
    `/v1/somaerp/recipes/${recipeId}/ingredients/${ingredientId}`,
    {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    }
  );

export const deleteRecipeIngredient = (
  recipeId: string,
  ingredientId: string
): Promise<void> =>
  apiFetch<void>(
    `/v1/somaerp/recipes/${recipeId}/ingredients/${ingredientId}`,
    { method: "DELETE" }
  );

// Recipe steps -----------------------------------------------------------

export const listRecipeSteps = (recipeId: string): Promise<RecipeStep[]> =>
  apiFetch<RecipeStep[]>(`/v1/somaerp/recipes/${recipeId}/steps`);

export type CreateRecipeStepBody = {
  step_number: number;
  name: string;
  duration_min?: number | null;
  equipment_notes?: string | null;
  instructions?: string | null;
};

export const createRecipeStep = (
  recipeId: string,
  body: CreateRecipeStepBody
): Promise<RecipeStep> =>
  apiFetch<RecipeStep>(`/v1/somaerp/recipes/${recipeId}/steps`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteRecipeStep = (
  recipeId: string,
  stepId: string
): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/recipes/${recipeId}/steps/${stepId}`, {
    method: "DELETE",
  });

// Recipe cost rollup -----------------------------------------------------

export const getRecipeCost = (recipeId: string): Promise<RecipeCostSummary> =>
  apiFetch<RecipeCostSummary>(`/v1/somaerp/recipes/${recipeId}/cost`);

// Step <-> equipment -----------------------------------------------------

export const listStepEquipment = (
  recipeId: string,
  stepId: string
): Promise<StepEquipmentLink[]> =>
  apiFetch<StepEquipmentLink[]>(
    `/v1/somaerp/recipes/${recipeId}/steps/${stepId}/equipment`
  );

export const attachStepEquipment = (
  recipeId: string,
  stepId: string,
  equipmentId: string
): Promise<StepEquipmentLink> =>
  apiFetch<StepEquipmentLink>(
    `/v1/somaerp/recipes/${recipeId}/steps/${stepId}/equipment`,
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ equipment_id: equipmentId }),
    }
  );

export const detachStepEquipment = (
  recipeId: string,
  stepId: string,
  equipmentId: string
): Promise<void> =>
  apiFetch<void>(
    `/v1/somaerp/recipes/${recipeId}/steps/${stepId}/equipment/${equipmentId}`,
    { method: "DELETE" }
  );

// ---------------------------------------------------------------------------
// Equipment (Plan 56-07)
// ---------------------------------------------------------------------------

export const listEquipmentCategories = (): Promise<EquipmentCategory[]> =>
  apiFetch<EquipmentCategory[]>("/v1/somaerp/equipment/categories");

export type ListEquipmentParams = {
  category_id?: number;
  status?: EquipmentStatus;
  q?: string;
  limit?: number;
  offset?: number;
};

export const listEquipment = (
  params?: ListEquipmentParams
): Promise<Equipment[]> =>
  apiFetch<Equipment[]>(`/v1/somaerp/equipment${qs(params)}`);

export type CreateEquipmentBody = {
  category_id: number;
  name: string;
  slug: string;
  status?: EquipmentStatus;
  purchase_cost?: number;
  currency_code?: string;
  purchase_date?: string | null;
  expected_lifespan_months?: number;
  properties?: Record<string, unknown>;
};

export const createEquipment = (body: CreateEquipmentBody): Promise<Equipment> =>
  apiFetch<Equipment>("/v1/somaerp/equipment", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const getEquipment = (id: string): Promise<Equipment> =>
  apiFetch<Equipment>(`/v1/somaerp/equipment/${id}`);

export type UpdateEquipmentBody = {
  name?: string;
  slug?: string;
  category_id?: number;
  status?: EquipmentStatus;
  purchase_cost?: number | null;
  currency_code?: string | null;
  purchase_date?: string | null;
  expected_lifespan_months?: number | null;
  properties?: Record<string, unknown>;
};

export const updateEquipment = (
  id: string,
  body: UpdateEquipmentBody
): Promise<Equipment> =>
  apiFetch<Equipment>(`/v1/somaerp/equipment/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

// Kitchen <-> Equipment link --------------------------------------------

export const listKitchenEquipment = (
  kitchenId: string
): Promise<KitchenEquipmentLink[]> =>
  apiFetch<KitchenEquipmentLink[]>(
    `/v1/somaerp/geography/kitchens/${kitchenId}/equipment`
  );

export type AttachKitchenEquipmentBody = {
  equipment_id: string;
  quantity?: number;
  notes?: string | null;
};

export const attachKitchenEquipment = (
  kitchenId: string,
  body: AttachKitchenEquipmentBody
): Promise<KitchenEquipmentLink> =>
  apiFetch<KitchenEquipmentLink>(
    `/v1/somaerp/geography/kitchens/${kitchenId}/equipment`,
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    }
  );

export const detachKitchenEquipment = (
  kitchenId: string,
  equipmentId: string
): Promise<void> =>
  apiFetch<void>(
    `/v1/somaerp/geography/kitchens/${kitchenId}/equipment/${equipmentId}`,
    { method: "DELETE" }
  );

// ---------------------------------------------------------------------------
// Quality (Plan 56-08)
// ---------------------------------------------------------------------------

export const listQcCheckTypes = (): Promise<QcCheckType[]> =>
  apiFetch<QcCheckType[]>("/v1/somaerp/quality/check-types");

export const listQcStages = (): Promise<QcStage[]> =>
  apiFetch<QcStage[]>("/v1/somaerp/quality/stages");

export const listQcOutcomes = (): Promise<QcOutcome[]> =>
  apiFetch<QcOutcome[]>("/v1/somaerp/quality/outcomes");

export type ListQcCheckpointsParams = {
  scope_kind?: QcCheckpointScopeKind;
  scope_ref_id?: string;
  stage_id?: number;
  check_type_id?: number;
  status?: QcCheckpointStatus;
  q?: string;
  limit?: number;
  offset?: number;
  include_deleted?: boolean;
};

export const listQcCheckpoints = (
  params?: ListQcCheckpointsParams
): Promise<QcCheckpoint[]> =>
  apiFetch<QcCheckpoint[]>(`/v1/somaerp/quality/checkpoints${qs(params)}`);

export const getQcCheckpoint = (id: string): Promise<QcCheckpoint> =>
  apiFetch<QcCheckpoint>(`/v1/somaerp/quality/checkpoints/${id}`);

export type CreateQcCheckpointBody = {
  stage_id: number;
  check_type_id: number;
  scope_kind: QcCheckpointScopeKind;
  scope_ref_id?: string | null;
  name: string;
  criteria_jsonb?: Record<string, unknown>;
  required?: boolean;
  status?: QcCheckpointStatus;
  properties?: Record<string, unknown>;
};

export const createQcCheckpoint = (
  body: CreateQcCheckpointBody
): Promise<QcCheckpoint> =>
  apiFetch<QcCheckpoint>("/v1/somaerp/quality/checkpoints", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export type UpdateQcCheckpointBody = {
  stage_id?: number;
  check_type_id?: number;
  scope_kind?: QcCheckpointScopeKind;
  scope_ref_id?: string | null;
  name?: string;
  criteria_jsonb?: Record<string, unknown>;
  required?: boolean;
  status?: QcCheckpointStatus;
  properties?: Record<string, unknown>;
};

export const updateQcCheckpoint = (
  id: string,
  body: UpdateQcCheckpointBody
): Promise<QcCheckpoint> =>
  apiFetch<QcCheckpoint>(`/v1/somaerp/quality/checkpoints/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteQcCheckpoint = (id: string): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/quality/checkpoints/${id}`, {
    method: "DELETE",
  });

export type ListQcChecksParams = {
  checkpoint_id?: string;
  batch_id?: string;
  outcome_id?: number;
  kitchen_id?: string;
  raw_material_lot?: string;
  performed_by_user_id?: string;
  ts_after?: string;
  ts_before?: string;
  limit?: number;
  offset?: number;
};

export const listQcChecks = (
  params?: ListQcChecksParams
): Promise<QcCheck[]> =>
  apiFetch<QcCheck[]>(`/v1/somaerp/quality/checks${qs(params)}`);

export type RecordQcCheckBody = {
  checkpoint_id: string;
  batch_id?: string | null;
  raw_material_lot?: string | null;
  kitchen_id?: string | null;
  outcome_id: number;
  measured_value?: number | null;
  measured_unit_id?: number | null;
  notes?: string | null;
  photo_vault_key?: string | null;
  metadata?: Record<string, unknown>;
};

export const recordQcCheck = (body: RecordQcCheckBody): Promise<QcCheck> =>
  apiFetch<QcCheck>("/v1/somaerp/quality/checks", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

// ---------------------------------------------------------------------------
// Procurement + Inventory + MRP-lite planner (Plan 56-09)
// ---------------------------------------------------------------------------

export type ListProcurementRunsParams = {
  kitchen_id?: string;
  supplier_id?: string;
  status?: ProcurementRunStatus;
  run_date_from?: string;
  run_date_to?: string;
  limit?: number;
  offset?: number;
  include_deleted?: boolean;
};

export const listProcurementRuns = (
  params?: ListProcurementRunsParams
): Promise<ProcurementRun[]> =>
  apiFetch<ProcurementRun[]>(`/v1/somaerp/procurement/runs${qs(params)}`);

export const getProcurementRun = (id: string): Promise<ProcurementRun> =>
  apiFetch<ProcurementRun>(`/v1/somaerp/procurement/runs/${id}`);

export type CreateProcurementRunBody = {
  kitchen_id: string;
  supplier_id: string;
  run_date: string;
  currency_code: string;
  notes?: string | null;
  properties?: Record<string, unknown>;
};

export const createProcurementRun = (
  body: CreateProcurementRunBody
): Promise<ProcurementRun> =>
  apiFetch<ProcurementRun>("/v1/somaerp/procurement/runs", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export type UpdateProcurementRunBody = {
  status?: ProcurementRunStatus;
  notes?: string | null;
  properties?: Record<string, unknown>;
};

export const updateProcurementRun = (
  id: string,
  body: UpdateProcurementRunBody
): Promise<ProcurementRun> =>
  apiFetch<ProcurementRun>(`/v1/somaerp/procurement/runs/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteProcurementRun = (id: string): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/procurement/runs/${id}`, { method: "DELETE" });

// Lines (nested) ---------------------------------------------------------

export const listProcurementLines = (
  runId: string
): Promise<ProcurementLine[]> =>
  apiFetch<ProcurementLine[]>(
    `/v1/somaerp/procurement/runs/${runId}/lines`
  );

export type AddProcurementLineBody = {
  raw_material_id: string;
  quantity: number;
  unit_id: number;
  unit_cost: number;
  lot_number?: string | null;
  quality_grade?: number | null;
  received_at?: string | null;
};

export const addProcurementLine = (
  runId: string,
  body: AddProcurementLineBody
): Promise<ProcurementLine> =>
  apiFetch<ProcurementLine>(`/v1/somaerp/procurement/runs/${runId}/lines`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export type PatchProcurementLineBody = {
  quantity?: number;
  unit_id?: number;
  unit_cost?: number;
  lot_number?: string | null;
  quality_grade?: number | null;
  received_at?: string | null;
};

export const patchProcurementLine = (
  runId: string,
  lineId: string,
  body: PatchProcurementLineBody
): Promise<ProcurementLine> =>
  apiFetch<ProcurementLine>(
    `/v1/somaerp/procurement/runs/${runId}/lines/${lineId}`,
    {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    }
  );

export const deleteProcurementLine = (
  runId: string,
  lineId: string
): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/procurement/runs/${runId}/lines/${lineId}`, {
    method: "DELETE",
  });

// Inventory --------------------------------------------------------------

export type ListInventoryCurrentParams = {
  kitchen_id?: string;
  raw_material_id?: string;
  category_id?: number;
  limit?: number;
  offset?: number;
};

export const listInventoryCurrent = (
  params?: ListInventoryCurrentParams
): Promise<InventoryCurrent[]> =>
  apiFetch<InventoryCurrent[]>(`/v1/somaerp/inventory/current${qs(params)}`);

export type ListInventoryMovementsParams = {
  kitchen_id?: string;
  raw_material_id?: string;
  movement_type?: InventoryMovementType;
  ts_after?: string;
  ts_before?: string;
  limit?: number;
  offset?: number;
};

export const listInventoryMovements = (
  params?: ListInventoryMovementsParams
): Promise<InventoryMovement[]> =>
  apiFetch<InventoryMovement[]>(
    `/v1/somaerp/inventory/movements${qs(params)}`
  );

export type RecordInventoryMovementBody = {
  kitchen_id: string;
  raw_material_id: string;
  movement_type: InventoryMovementType;
  quantity: number;
  unit_id: number;
  lot_number?: string | null;
  reason?: string | null;
  metadata?: Record<string, unknown>;
};

export const recordInventoryMovement = (
  body: RecordInventoryMovementBody
): Promise<InventoryMovement> =>
  apiFetch<InventoryMovement>("/v1/somaerp/inventory/movements", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

// MRP-lite planner -------------------------------------------------------

export type ComputeProcurementPlanBody = {
  kitchen_id: string;
  demand: ProcurementPlanDemand[];
};

export const computeProcurementPlan = (
  body: ComputeProcurementPlanBody
): Promise<ProcurementPlanResponse> =>
  apiFetch<ProcurementPlanResponse>("/v1/somaerp/inventory/plan", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

// ---------------------------------------------------------------------------
// Production Batches (Plan 56-10) — the 4 AM tracker.
// ---------------------------------------------------------------------------

export type ListBatchesParams = {
  kitchen_id?: string;
  product_id?: string;
  recipe_id?: string;
  status?: ProductionBatchStatus;
  run_date_from?: string;
  run_date_to?: string;
  lead_user_id?: string;
  limit?: number;
  offset?: number;
};

export const listBatches = (
  params?: ListBatchesParams
): Promise<ProductionBatch[]> =>
  apiFetch<ProductionBatch[]>(`/v1/somaerp/production/batches${qs(params)}`);

export type CreateBatchBody = {
  kitchen_id: string;
  product_id: string;
  recipe_id?: string | null;
  run_date?: string;
  shift_start?: string | null;
  planned_qty: number;
  lead_user_id?: string | null;
  notes?: string | null;
  properties?: Record<string, unknown>;
};

export const createBatch = (body: CreateBatchBody): Promise<ProductionBatch> =>
  apiFetch<ProductionBatch>("/v1/somaerp/production/batches", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const getBatch = (id: string): Promise<BatchDetail> =>
  apiFetch<BatchDetail>(`/v1/somaerp/production/batches/${id}`);

export type PatchBatchBody = {
  status?: ProductionBatchStatus;
  actual_qty?: number | null;
  cancel_reason?: string | null;
  notes?: string | null;
  lead_user_id?: string | null;
  properties?: Record<string, unknown>;
};

export const patchBatch = (
  id: string,
  body: PatchBatchBody
): Promise<ProductionBatch> =>
  apiFetch<ProductionBatch>(`/v1/somaerp/production/batches/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteBatch = (id: string): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/production/batches/${id}`, { method: "DELETE" });

export const getBatchSummary = (id: string): Promise<BatchSummary> =>
  apiFetch<BatchSummary>(`/v1/somaerp/production/batches/${id}/summary`);

// Steps ---------------------------------------------------------------------

export const listBatchSteps = (batchId: string): Promise<BatchStepLog[]> =>
  apiFetch<BatchStepLog[]>(`/v1/somaerp/production/batches/${batchId}/steps`);

export type PatchBatchStepBody = {
  started_at?: string | null;
  completed_at?: string | null;
  notes?: string | null;
};

export const patchBatchStep = (
  batchId: string,
  stepId: string,
  body: PatchBatchStepBody
): Promise<BatchStepLog> =>
  apiFetch<BatchStepLog>(
    `/v1/somaerp/production/batches/${batchId}/steps/${stepId}`,
    {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    }
  );

// Consumption ---------------------------------------------------------------

export const listBatchConsumption = (
  batchId: string
): Promise<BatchConsumptionLine[]> =>
  apiFetch<BatchConsumptionLine[]>(
    `/v1/somaerp/production/batches/${batchId}/consumption`
  );

export type PatchBatchConsumptionBody = {
  actual_qty?: number | null;
  lot_number?: string | null;
  unit_cost_snapshot?: number | null;
};

export const patchBatchConsumption = (
  batchId: string,
  lineId: string,
  body: PatchBatchConsumptionBody
): Promise<BatchConsumptionLine> =>
  apiFetch<BatchConsumptionLine>(
    `/v1/somaerp/production/batches/${batchId}/consumption/${lineId}`,
    {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    }
  );

// QC ------------------------------------------------------------------------

export const listBatchQc = (batchId: string): Promise<BatchQcResult[]> =>
  apiFetch<BatchQcResult[]>(`/v1/somaerp/production/batches/${batchId}/qc`);

export type RecordBatchQcBody = {
  checkpoint_id: string;
  outcome_id: number;
  measured_value?: number | null;
  measured_unit_id?: number | null;
  notes?: string | null;
  photo_vault_key?: string | null;
  metadata?: Record<string, unknown>;
};

export const recordBatchQc = (
  batchId: string,
  body: RecordBatchQcBody
): Promise<BatchQcResult> =>
  apiFetch<BatchQcResult>(
    `/v1/somaerp/production/batches/${batchId}/qc`,
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    }
  );

// Today's board -------------------------------------------------------------

export const getTodaysBoard = (dateIso?: string): Promise<ProductionBoard> =>
  apiFetch<ProductionBoard>(
    `/v1/somaerp/production/board${qs(dateIso ? { date: dateIso } : undefined)}`
  );

// ---------------------------------------------------------------------------
// Customers + Subscriptions (Plan 56-11)
// ---------------------------------------------------------------------------

// Customers ------------------------------------------------------------------

export type ListCustomersParams = {
  status?: CustomerStatus;
  location_id?: string;
  q?: string;
  limit?: number;
  offset?: number;
  include_deleted?: boolean;
};

export const listCustomers = (
  params?: ListCustomersParams
): Promise<Customer[]> =>
  apiFetch<Customer[]>(`/v1/somaerp/customers${qs(params)}`);

export type CreateCustomerBody = {
  location_id?: string | null;
  name: string;
  slug: string;
  email?: string | null;
  phone?: string | null;
  address_jsonb?: Record<string, unknown>;
  delivery_notes?: string | null;
  acquisition_source?: string | null;
  status?: CustomerStatus;
  properties?: Record<string, unknown>;
};

export const createCustomer = (body: CreateCustomerBody): Promise<Customer> =>
  apiFetch<Customer>("/v1/somaerp/customers", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const getCustomer = (id: string): Promise<Customer> =>
  apiFetch<Customer>(`/v1/somaerp/customers/${id}`);

export type UpdateCustomerBody = Partial<CreateCustomerBody>;

export const updateCustomer = (
  id: string,
  body: UpdateCustomerBody
): Promise<Customer> =>
  apiFetch<Customer>(`/v1/somaerp/customers/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteCustomer = (id: string): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/customers/${id}`, { method: "DELETE" });

// Subscription Frequencies (read-only) ---------------------------------------

export const listSubscriptionFrequencies = (): Promise<SubscriptionFrequency[]> =>
  apiFetch<SubscriptionFrequency[]>("/v1/somaerp/subscriptions/frequencies");

// Subscription Plans ---------------------------------------------------------

export type ListSubscriptionPlansParams = {
  status?: SubscriptionPlanStatus;
  frequency_id?: number;
  q?: string;
  limit?: number;
  offset?: number;
  include_deleted?: boolean;
};

export const listSubscriptionPlans = (
  params?: ListSubscriptionPlansParams
): Promise<SubscriptionPlan[]> =>
  apiFetch<SubscriptionPlan[]>(`/v1/somaerp/subscriptions/plans${qs(params)}`);

export type CreateSubscriptionPlanBody = {
  name: string;
  slug: string;
  description?: string | null;
  frequency_id: number;
  price_per_delivery?: number | null;
  currency_code: string;
  status?: SubscriptionPlanStatus;
  properties?: Record<string, unknown>;
};

export const createSubscriptionPlan = (
  body: CreateSubscriptionPlanBody
): Promise<SubscriptionPlan> =>
  apiFetch<SubscriptionPlan>("/v1/somaerp/subscriptions/plans", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const getSubscriptionPlan = (id: string): Promise<SubscriptionPlanDetail> =>
  apiFetch<SubscriptionPlanDetail>(`/v1/somaerp/subscriptions/plans/${id}`);

export type UpdateSubscriptionPlanBody = Partial<CreateSubscriptionPlanBody>;

export const updateSubscriptionPlan = (
  id: string,
  body: UpdateSubscriptionPlanBody
): Promise<SubscriptionPlan> =>
  apiFetch<SubscriptionPlan>(`/v1/somaerp/subscriptions/plans/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteSubscriptionPlan = (id: string): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/subscriptions/plans/${id}`, { method: "DELETE" });

// Plan items -----------------------------------------------------------------

export const listSubscriptionPlanItems = (
  planId: string
): Promise<SubscriptionPlanItem[]> =>
  apiFetch<SubscriptionPlanItem[]>(
    `/v1/somaerp/subscriptions/plans/${planId}/items`
  );

export type AddSubscriptionPlanItemBody = {
  product_id: string;
  variant_id?: string | null;
  qty_per_delivery: number;
  position?: number;
  notes?: string | null;
};

export const addSubscriptionPlanItem = (
  planId: string,
  body: AddSubscriptionPlanItemBody
): Promise<SubscriptionPlanItem> =>
  apiFetch<SubscriptionPlanItem>(
    `/v1/somaerp/subscriptions/plans/${planId}/items`,
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    }
  );

export type UpdateSubscriptionPlanItemBody = Partial<AddSubscriptionPlanItemBody>;

export const updateSubscriptionPlanItem = (
  planId: string,
  itemId: string,
  body: UpdateSubscriptionPlanItemBody
): Promise<SubscriptionPlanItem> =>
  apiFetch<SubscriptionPlanItem>(
    `/v1/somaerp/subscriptions/plans/${planId}/items/${itemId}`,
    {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    }
  );

export const deleteSubscriptionPlanItem = (
  planId: string,
  itemId: string
): Promise<void> =>
  apiFetch<void>(
    `/v1/somaerp/subscriptions/plans/${planId}/items/${itemId}`,
    { method: "DELETE" }
  );

// Subscriptions --------------------------------------------------------------

export type ListSubscriptionsParams = {
  customer_id?: string;
  plan_id?: string;
  status?: SubscriptionStatus;
  start_date_from?: string;
  start_date_to?: string;
  limit?: number;
  offset?: number;
  include_deleted?: boolean;
};

export const listSubscriptions = (
  params?: ListSubscriptionsParams
): Promise<Subscription[]> =>
  apiFetch<Subscription[]>(`/v1/somaerp/subscriptions${qs(params)}`);

export type CreateSubscriptionBody = {
  customer_id: string;
  plan_id: string;
  service_zone_id?: string | null;
  start_date: string;
  end_date?: string | null;
  billing_cycle?: string | null;
  properties?: Record<string, unknown>;
};

export const createSubscription = (
  body: CreateSubscriptionBody
): Promise<Subscription> =>
  apiFetch<Subscription>("/v1/somaerp/subscriptions", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const getSubscription = (id: string): Promise<Subscription> =>
  apiFetch<Subscription>(`/v1/somaerp/subscriptions/${id}`);

export type UpdateSubscriptionBody = {
  service_zone_id?: string | null;
  end_date?: string | null;
  status?: SubscriptionStatus;
  paused_from?: string | null;
  paused_to?: string | null;
  reason?: string | null;
  billing_cycle?: string | null;
  properties?: Record<string, unknown>;
};

export const updateSubscription = (
  id: string,
  body: UpdateSubscriptionBody
): Promise<Subscription> =>
  apiFetch<Subscription>(`/v1/somaerp/subscriptions/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteSubscription = (id: string): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/subscriptions/${id}`, { method: "DELETE" });

export const listSubscriptionEvents = (
  subscriptionId: string
): Promise<SubscriptionEvent[]> =>
  apiFetch<SubscriptionEvent[]>(
    `/v1/somaerp/subscriptions/${subscriptionId}/events`
  );

// ---------------------------------------------------------------------------
// Delivery (Plan 56-12) — routes, riders, runs, stops, board.
// ---------------------------------------------------------------------------

// Rider roles (read-only) ----------------------------------------------------

export const listRiderRoles = (): Promise<RiderRole[]> =>
  apiFetch<RiderRole[]>("/v1/somaerp/delivery/rider-roles");

// Riders ---------------------------------------------------------------------

export type ListRidersParams = {
  status?: RiderStatus;
  role_id?: number;
  q?: string;
  limit?: number;
  offset?: number;
  include_deleted?: boolean;
};

export const listRiders = (params?: ListRidersParams): Promise<Rider[]> =>
  apiFetch<Rider[]>(`/v1/somaerp/delivery/riders${qs(params)}`);

export type CreateRiderBody = {
  name: string;
  phone?: string | null;
  role_id: number;
  vehicle_type?: string | null;
  license_number?: string | null;
  user_id?: string | null;
  status?: RiderStatus;
  properties?: Record<string, unknown>;
};

export const createRider = (body: CreateRiderBody): Promise<Rider> =>
  apiFetch<Rider>("/v1/somaerp/delivery/riders", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const getRider = (id: string): Promise<Rider> =>
  apiFetch<Rider>(`/v1/somaerp/delivery/riders/${id}`);

export type UpdateRiderBody = Partial<CreateRiderBody>;

export const updateRider = (
  id: string,
  body: UpdateRiderBody,
): Promise<Rider> =>
  apiFetch<Rider>(`/v1/somaerp/delivery/riders/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteRider = (id: string): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/delivery/riders/${id}`, { method: "DELETE" });

// Delivery routes ------------------------------------------------------------

export type ListDeliveryRoutesParams = {
  kitchen_id?: string;
  status?: RouteStatus;
  q?: string;
  limit?: number;
  offset?: number;
  include_deleted?: boolean;
};

export const listDeliveryRoutes = (
  params?: ListDeliveryRoutesParams,
): Promise<DeliveryRoute[]> =>
  apiFetch<DeliveryRoute[]>(`/v1/somaerp/delivery/routes${qs(params)}`);

export type CreateDeliveryRouteBody = {
  kitchen_id: string;
  name: string;
  slug: string;
  area?: string | null;
  target_window_start?: string | null;
  target_window_end?: string | null;
  status?: RouteStatus;
  properties?: Record<string, unknown>;
};

export const createDeliveryRoute = (
  body: CreateDeliveryRouteBody,
): Promise<DeliveryRoute> =>
  apiFetch<DeliveryRoute>("/v1/somaerp/delivery/routes", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const getDeliveryRoute = (id: string): Promise<DeliveryRoute> =>
  apiFetch<DeliveryRoute>(`/v1/somaerp/delivery/routes/${id}`);

export type UpdateDeliveryRouteBody = Partial<CreateDeliveryRouteBody>;

export const updateDeliveryRoute = (
  id: string,
  body: UpdateDeliveryRouteBody,
): Promise<DeliveryRoute> =>
  apiFetch<DeliveryRoute>(`/v1/somaerp/delivery/routes/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteDeliveryRoute = (id: string): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/delivery/routes/${id}`, { method: "DELETE" });

// Route <-> customer links ---------------------------------------------------

export const listRouteCustomers = (
  routeId: string,
): Promise<RouteCustomerLink[]> =>
  apiFetch<RouteCustomerLink[]>(
    `/v1/somaerp/delivery/routes/${routeId}/customers`,
  );

export type AttachRouteCustomerBody = {
  customer_id: string;
  sequence_position?: number | null;
};

export const attachRouteCustomer = (
  routeId: string,
  body: AttachRouteCustomerBody,
): Promise<RouteCustomerLink> =>
  apiFetch<RouteCustomerLink>(
    `/v1/somaerp/delivery/routes/${routeId}/customers`,
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    },
  );

export const detachRouteCustomer = (
  routeId: string,
  customerId: string,
): Promise<void> =>
  apiFetch<void>(
    `/v1/somaerp/delivery/routes/${routeId}/customers/${customerId}`,
    { method: "DELETE" },
  );

export const reorderRouteCustomers = (
  routeId: string,
  customerIds: string[],
): Promise<RouteCustomerLink[]> =>
  apiFetch<RouteCustomerLink[]>(
    `/v1/somaerp/delivery/routes/${routeId}/customers/reorder`,
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ customer_ids: customerIds }),
    },
  );

// Delivery runs --------------------------------------------------------------

export type ListDeliveryRunsParams = {
  route_id?: string;
  rider_id?: string;
  status?: DeliveryRunStatus;
  run_date_from?: string;
  run_date_to?: string;
  limit?: number;
  offset?: number;
  include_deleted?: boolean;
};

export const listDeliveryRuns = (
  params?: ListDeliveryRunsParams,
): Promise<DeliveryRun[]> =>
  apiFetch<DeliveryRun[]>(`/v1/somaerp/delivery/runs${qs(params)}`);

export type CreateDeliveryRunBody = {
  route_id: string;
  rider_id: string;
  run_date: string;
  notes?: string | null;
  properties?: Record<string, unknown>;
};

export const createDeliveryRun = (
  body: CreateDeliveryRunBody,
): Promise<DeliveryRun> =>
  apiFetch<DeliveryRun>("/v1/somaerp/delivery/runs", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const getDeliveryRun = (id: string): Promise<DeliveryRunDetail> =>
  apiFetch<DeliveryRunDetail>(`/v1/somaerp/delivery/runs/${id}`);

export type UpdateDeliveryRunBody = {
  status?: DeliveryRunStatus;
  rider_id?: string;
  notes?: string | null;
  properties?: Record<string, unknown>;
  allow_incomplete_completion?: boolean;
};

export const updateDeliveryRun = (
  id: string,
  body: UpdateDeliveryRunBody,
): Promise<DeliveryRun> =>
  apiFetch<DeliveryRun>(`/v1/somaerp/delivery/runs/${id}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  });

export const deleteDeliveryRun = (id: string): Promise<void> =>
  apiFetch<void>(`/v1/somaerp/delivery/runs/${id}`, { method: "DELETE" });

export type GenerateRunStopsResult = {
  run: DeliveryRun;
  stops: DeliveryStop[];
  count: number;
};

export const generateRunStops = (
  runId: string,
): Promise<GenerateRunStopsResult> =>
  apiFetch<GenerateRunStopsResult>(
    `/v1/somaerp/delivery/runs/${runId}/generate-stops`,
    { method: "POST" },
  );

export const listRunStops = (runId: string): Promise<DeliveryStop[]> =>
  apiFetch<DeliveryStop[]>(`/v1/somaerp/delivery/runs/${runId}/stops`);

export type PatchRunStopBody = {
  status?: DeliveryStopStatus;
  notes?: string | null;
  photo_vault_key?: string | null;
  signature_vault_key?: string | null;
  actual_at?: string | null;
};

export const patchRunStop = (
  runId: string,
  stopId: string,
  body: PatchRunStopBody,
): Promise<DeliveryStop> =>
  apiFetch<DeliveryStop>(
    `/v1/somaerp/delivery/runs/${runId}/stops/${stopId}`,
    {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(body),
    },
  );

export const getDeliveryBoard = (dateIso?: string): Promise<DeliveryBoard> =>
  apiFetch<DeliveryBoard>(
    `/v1/somaerp/delivery/board${qs({ date: dateIso })}`,
  );

// ---------------------------------------------------------------------------
// Reports (Plan 56-13) — read-only cross-layer rollups.
// ---------------------------------------------------------------------------

export const getDashboardToday = (dateIso?: string): Promise<DashboardToday> =>
  apiFetch<DashboardToday>(
    `/v1/somaerp/reports/dashboard/today${qs(dateIso ? { date: dateIso } : undefined)}`,
  );

export type ListYieldTrendsParams = {
  from: string;
  to: string;
  kitchen_id?: string;
  product_id?: string;
  bucket?: ReportBucket;
};

export const listYieldTrends = (
  params: ListYieldTrendsParams,
): Promise<YieldTrendPoint[]> =>
  apiFetch<YieldTrendPoint[]>(
    `/v1/somaerp/reports/yield/trends${qs(params as QsRecord)}`,
  );

export type ListCogsTrendsParams = ListYieldTrendsParams;

export const listCogsTrends = (
  params: ListCogsTrendsParams,
): Promise<CogsTrendPoint[]> =>
  apiFetch<CogsTrendPoint[]>(
    `/v1/somaerp/reports/cogs/trends${qs(params as QsRecord)}`,
  );

export type ListInventoryAlertsParams = {
  kitchen_id?: string;
  severity?: InventoryAlertSeverity;
};

export const listInventoryAlerts = (
  params?: ListInventoryAlertsParams,
): Promise<InventoryAlert[]> =>
  apiFetch<InventoryAlert[]>(
    `/v1/somaerp/reports/inventory/alerts${qs(params as QsRecord | undefined)}`,
  );

export type ListProcurementSpendParams = {
  from: string;
  to: string;
  kitchen_id?: string;
  supplier_id?: string;
  bucket?: "monthly";
};

export const listProcurementSpend = (
  params: ListProcurementSpendParams,
): Promise<ProcurementSpendPoint[]> =>
  apiFetch<ProcurementSpendPoint[]>(
    `/v1/somaerp/reports/procurement/spend${qs(params as QsRecord)}`,
  );

export type ListRevenueProjectionParams = {
  status?: string;
  as_of?: string;
};

export const listRevenueProjection = (
  params?: ListRevenueProjectionParams,
): Promise<RevenueProjection[]> =>
  apiFetch<RevenueProjection[]>(
    `/v1/somaerp/reports/revenue/projection${qs(params as QsRecord | undefined)}`,
  );

export type ListComplianceBatchesParams = {
  from: string;
  to: string;
  product_id?: string;
};

export const listComplianceBatches = (
  params: ListComplianceBatchesParams,
): Promise<ComplianceBatchRow[]> =>
  apiFetch<ComplianceBatchRow[]>(
    `/v1/somaerp/reports/compliance/batches${qs({ ...params, format: "json" } as QsRecord)}`,
  );

/**
 * Download the FSSAI compliance CSV as a Blob. Raw CSV is returned by the
 * backend (no ApiEnvelope), so we bypass apiFetch and handle auth + errors
 * directly. The caller is responsible for triggering the browser download.
 */
export const downloadComplianceCsv = async (
  params: ListComplianceBatchesParams,
): Promise<Blob> => {
  const base = process.env.NEXT_PUBLIC_SOMAERP_BACKEND ?? "http://localhost:51736";
  const query = qs({ ...params, format: "csv" } as QsRecord);
  const headers = new Headers();
  if (typeof window !== "undefined") {
    try {
      const token = window.localStorage.getItem("somaerp_token");
      if (token) headers.set("Authorization", `Bearer ${token}`);
    } catch {
      // swallow; CSV will 401 if missing.
    }
  }
  const res = await fetch(
    `${base}/v1/somaerp/reports/compliance/batches${query}`,
    { headers },
  );
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `CSV download failed (${res.status})`);
  }
  return res.blob();
};
