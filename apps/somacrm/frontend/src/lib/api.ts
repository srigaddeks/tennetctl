import type {
  ApiEnvelope,
  TimelineItem,
  Contact,
  ContactCreate,
  ContactUpdate,
  Organization,
  OrgCreate,
  OrgUpdate,
  Address,
  AddressCreate,
  AddressUpdate,
  Lead,
  LeadCreate,
  LeadUpdate,
  PipelineStage,
  PipelineStageCreate,
  PipelineStageUpdate,
  Deal,
  DealCreate,
  DealUpdate,
  Activity,
  ActivityCreate,
  ActivityUpdate,
  Note,
  NoteCreate,
  NoteUpdate,
  Tag,
  TagCreate,
  EntityTag,
  PipelineSummaryStage,
  LeadConversionRow,
  ActivitySummaryRow,
  ContactGrowthPoint,
  EntityType,
  SearchResult,
} from "@/types/api";

const BASE = process.env.NEXT_PUBLIC_SOMACRM_API_URL ?? "http://localhost:51738";

function getHeaders(): HeadersInit {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("somacrm_token") : null;
  return token
    ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    : { "Content-Type": "application/json" };
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...getHeaders(), ...(init?.headers ?? {}) },
  });
  const data = (await res.json()) as ApiEnvelope<T>;
  if (!data.ok) throw new Error(data.error?.message ?? "API error");
  return data.data;
}

// ── Contacts ──────────────────────────────────────────────────────────────────

export function listContacts(params?: {
  q?: string;
  status?: string;
  organization_id?: string;
  limit?: number;
  offset?: number;
}): Promise<Contact[]> {
  const qs = params ? "?" + new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]))
  ) : "";
  return apiFetch<Contact[]>(`/v1/somacrm/contacts${qs}`);
}

export function createContact(data: ContactCreate): Promise<Contact> {
  return apiFetch<Contact>("/v1/somacrm/contacts", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getContact(id: string): Promise<Contact> {
  return apiFetch<Contact>(`/v1/somacrm/contacts/${id}`);
}

export function updateContact(id: string, data: ContactUpdate): Promise<Contact> {
  return apiFetch<Contact>(`/v1/somacrm/contacts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteContact(id: string): Promise<void> {
  return apiFetch<void>(`/v1/somacrm/contacts/${id}`, { method: "DELETE" });
}

export function getContactTimeline(id: string, limit = 200): Promise<TimelineItem[]> {
  return apiFetch<TimelineItem[]>(`/v1/somacrm/contacts/${id}/timeline?limit=${limit}`);
}

export function createErpCustomer(
  contactId: string,
  data: { delivery_notes?: string; acquisition_source?: string },
): Promise<{ erp_customer_id: string; already_existed: boolean }> {
  return apiFetch(`/v1/somacrm/contacts/${contactId}/create-erp-customer`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ── Organizations ─────────────────────────────────────────────────────────────

export function listOrganizations(params?: {
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<Organization[]> {
  const qs = params ? "?" + new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]))
  ) : "";
  return apiFetch<Organization[]>(`/v1/somacrm/organizations${qs}`);
}

export function createOrganization(data: OrgCreate): Promise<Organization> {
  return apiFetch<Organization>("/v1/somacrm/organizations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getOrganization(id: string): Promise<Organization> {
  return apiFetch<Organization>(`/v1/somacrm/organizations/${id}`);
}

export function updateOrganization(id: string, data: OrgUpdate): Promise<Organization> {
  return apiFetch<Organization>(`/v1/somacrm/organizations/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteOrganization(id: string): Promise<void> {
  return apiFetch<void>(`/v1/somacrm/organizations/${id}`, { method: "DELETE" });
}

// ── Addresses ─────────────────────────────────────────────────────────────────

export function listAddresses(params: {
  entity_type: EntityType;
  entity_id: string;
}): Promise<Address[]> {
  const qs = "?" + new URLSearchParams({ entity_type: params.entity_type, entity_id: params.entity_id });
  return apiFetch<Address[]>(`/v1/somacrm/addresses${qs}`);
}

export function createAddress(data: AddressCreate): Promise<Address> {
  return apiFetch<Address>("/v1/somacrm/addresses", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateAddress(id: string, data: AddressUpdate): Promise<Address> {
  return apiFetch<Address>(`/v1/somacrm/addresses/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteAddress(id: string): Promise<void> {
  return apiFetch<void>(`/v1/somacrm/addresses/${id}`, { method: "DELETE" });
}

// ── Leads ─────────────────────────────────────────────────────────────────────

export function listLeads(params?: {
  q?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<Lead[]> {
  const qs = params ? "?" + new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]))
  ) : "";
  return apiFetch<Lead[]>(`/v1/somacrm/leads${qs}`);
}

export function createLead(data: LeadCreate): Promise<Lead> {
  return apiFetch<Lead>("/v1/somacrm/leads", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getLead(id: string): Promise<Lead> {
  return apiFetch<Lead>(`/v1/somacrm/leads/${id}`);
}

export function updateLead(id: string, data: LeadUpdate): Promise<Lead> {
  return apiFetch<Lead>(`/v1/somacrm/leads/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteLead(id: string): Promise<void> {
  return apiFetch<void>(`/v1/somacrm/leads/${id}`, { method: "DELETE" });
}

// ── Pipeline Stages ───────────────────────────────────────────────────────────

export function listPipelineStages(): Promise<PipelineStage[]> {
  return apiFetch<PipelineStage[]>("/v1/somacrm/pipeline-stages");
}

export function createPipelineStage(data: PipelineStageCreate): Promise<PipelineStage> {
  return apiFetch<PipelineStage>("/v1/somacrm/pipeline-stages", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updatePipelineStage(id: string, data: PipelineStageUpdate): Promise<PipelineStage> {
  return apiFetch<PipelineStage>(`/v1/somacrm/pipeline-stages/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deletePipelineStage(id: string): Promise<void> {
  return apiFetch<void>(`/v1/somacrm/pipeline-stages/${id}`, { method: "DELETE" });
}

// ── Deals ─────────────────────────────────────────────────────────────────────

export function listDeals(params?: {
  q?: string;
  status?: string;
  stage_id?: string;
  contact_id?: string;
  organization_id?: string;
  limit?: number;
  offset?: number;
}): Promise<Deal[]> {
  const qs = params ? "?" + new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]))
  ) : "";
  return apiFetch<Deal[]>(`/v1/somacrm/deals${qs}`);
}

export function createDeal(data: DealCreate): Promise<Deal> {
  return apiFetch<Deal>("/v1/somacrm/deals", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getDeal(id: string): Promise<Deal> {
  return apiFetch<Deal>(`/v1/somacrm/deals/${id}`);
}

export function updateDeal(id: string, data: DealUpdate): Promise<Deal> {
  return apiFetch<Deal>(`/v1/somacrm/deals/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteDeal(id: string): Promise<void> {
  return apiFetch<void>(`/v1/somacrm/deals/${id}`, { method: "DELETE" });
}

// ── Activities ────────────────────────────────────────────────────────────────

export function listActivities(params?: {
  activity_type?: string;
  status?: string;
  entity_type?: EntityType;
  entity_id?: string;
  limit?: number;
  offset?: number;
}): Promise<Activity[]> {
  const qs = params ? "?" + new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]))
  ) : "";
  return apiFetch<Activity[]>(`/v1/somacrm/activities${qs}`);
}

export function createActivity(data: ActivityCreate): Promise<Activity> {
  return apiFetch<Activity>("/v1/somacrm/activities", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateActivity(id: string, data: ActivityUpdate): Promise<Activity> {
  return apiFetch<Activity>(`/v1/somacrm/activities/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteActivity(id: string): Promise<void> {
  return apiFetch<void>(`/v1/somacrm/activities/${id}`, { method: "DELETE" });
}

// ── Notes ─────────────────────────────────────────────────────────────────────

export function listNotes(params: {
  entity_type: EntityType;
  entity_id: string;
}): Promise<Note[]> {
  const qs = "?" + new URLSearchParams({ entity_type: params.entity_type, entity_id: params.entity_id });
  return apiFetch<Note[]>(`/v1/somacrm/notes${qs}`);
}

export function createNote(data: NoteCreate): Promise<Note> {
  return apiFetch<Note>("/v1/somacrm/notes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateNote(id: string, data: NoteUpdate): Promise<Note> {
  return apiFetch<Note>(`/v1/somacrm/notes/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteNote(id: string): Promise<void> {
  return apiFetch<void>(`/v1/somacrm/notes/${id}`, { method: "DELETE" });
}

// ── Tags ──────────────────────────────────────────────────────────────────────

export function listTags(): Promise<Tag[]> {
  return apiFetch<Tag[]>("/v1/somacrm/tags");
}

export function createTag(data: TagCreate): Promise<Tag> {
  return apiFetch<Tag>("/v1/somacrm/tags", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteTag(id: string): Promise<void> {
  return apiFetch<void>(`/v1/somacrm/tags/${id}`, { method: "DELETE" });
}

export function addEntityTag(data: EntityTag): Promise<void> {
  return apiFetch<void>("/v1/somacrm/entity-tags", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteEntityTag(id: string): Promise<void> {
  return apiFetch<void>(`/v1/somacrm/entity-tags/${id}`, { method: "DELETE" });
}

// ── Search ────────────────────────────────────────────────────────────────────

export async function globalSearch(q: string): Promise<SearchResult[]> {
  const d = await apiFetch<{ results: SearchResult[] }>(
    `/v1/somacrm/search?q=${encodeURIComponent(q)}`,
  );
  return d.results;
}

// ── Reports ───────────────────────────────────────────────────────────────────

export async function getPipelineSummary(): Promise<PipelineSummaryStage[]> {
  const d = await apiFetch<{ stages: PipelineSummaryStage[] }>("/v1/somacrm/reports/pipeline-summary");
  return d.stages ?? [];
}

export async function getLeadConversion(): Promise<LeadConversionRow[]> {
  const d = await apiFetch<{ by_status: LeadConversionRow[] }>("/v1/somacrm/reports/lead-conversion");
  return d.by_status ?? [];
}

export async function getActivitySummary(): Promise<ActivitySummaryRow[]> {
  const d = await apiFetch<{ rows: ActivitySummaryRow[] }>("/v1/somacrm/reports/activity-summary");
  return d.rows ?? [];
}

export async function getContactGrowth(): Promise<ContactGrowthPoint[]> {
  const d = await apiFetch<{ weeks: ContactGrowthPoint[] }>("/v1/somacrm/reports/contact-growth");
  return d.weeks ?? [];
}
