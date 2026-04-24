// Envelope
export type ApiEnvelope<T> = { ok: true; data: T } | { ok: false; error: { code: string; message: string } };

// Auth
export type AuthResponse = { token: string; user_id: string; email: string };

// Dim types
export type ContactStatus = "active" | "inactive" | "archived";
export type LeadStatus = "new" | "contacted" | "qualified" | "unqualified" | "converted";
export type DealStatus = "open" | "won" | "lost";
export type ActivityType = "task" | "call" | "email" | "meeting" | "note";
export type ActivityStatus = "pending" | "in_progress" | "done" | "cancelled";
export type AddressType = "home" | "office" | "billing" | "delivery" | "other";
export type EntityType = "contact" | "organization" | "lead" | "deal";

// Contacts
export type Contact = {
  id: string;
  tenant_id: string;
  organization_id: string | null;
  organization_name: string | null;
  first_name: string;
  last_name: string | null;
  full_name: string;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  job_title: string | null;
  company_name: string | null;
  website: string | null;
  linkedin_url: string | null;
  twitter_handle: string | null;
  lead_source: string | null;
  status: ContactStatus;
  notes_count: number;
  activities_count: number;
  deals_count: number;
  properties: Record<string, unknown>;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};
export type ContactCreate = {
  first_name: string;
  last_name?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  organization_id?: string;
  job_title?: string;
  company_name?: string;
  lead_source?: string;
  status?: ContactStatus;
  properties?: Record<string, unknown>;
};
export type ContactUpdate = Partial<ContactCreate>;

// Organizations
export type Organization = {
  id: string;
  tenant_id: string;
  name: string;
  slug: string;
  industry: string | null;
  website: string | null;
  phone: string | null;
  email: string | null;
  employee_count: number | null;
  annual_revenue: number | null;
  description: string | null;
  contact_count: number;
  deal_count: number;
  properties: Record<string, unknown>;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};
export type OrgCreate = {
  name: string;
  slug: string;
  industry?: string;
  website?: string;
  phone?: string;
  email?: string;
  employee_count?: number;
  annual_revenue?: number;
  description?: string;
};
export type OrgUpdate = Partial<OrgCreate>;

// Addresses
export type Address = {
  id: string;
  tenant_id: string;
  entity_type: EntityType;
  entity_id: string;
  address_type: AddressType;
  is_primary: boolean;
  street: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  postal_code: string | null;
  full_address: string | null;
  properties: Record<string, unknown>;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};
export type AddressCreate = {
  entity_type: EntityType;
  entity_id: string;
  address_type_id: number;
  is_primary?: boolean;
  street?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
};
export type AddressUpdate = Partial<Omit<AddressCreate, "entity_type" | "entity_id">>;

// Leads
export type Lead = {
  id: string;
  tenant_id: string;
  title: string;
  contact_id: string | null;
  organization_id: string | null;
  contact_name: string | null;
  organization_name: string | null;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  company: string | null;
  lead_source: string | null;
  status: LeadStatus;
  score: number;
  assigned_to: string | null;
  converted_deal_id: string | null;
  converted_at: string | null;
  properties: Record<string, unknown>;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};
export type LeadCreate = {
  title: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  company?: string;
  lead_source?: string;
  status_id?: number;
  score?: number;
  contact_id?: string;
  organization_id?: string;
};
export type LeadUpdate = Partial<LeadCreate>;

// Pipeline stages
export type PipelineStage = {
  id: string;
  tenant_id: string;
  name: string;
  order_position: number;
  probability_pct: number;
  color: string;
  is_won: boolean;
  is_lost: boolean;
  deals_count: number;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};
export type PipelineStageCreate = {
  name: string;
  order_position?: number;
  probability_pct?: number;
  color?: string;
  is_won?: boolean;
  is_lost?: boolean;
};
export type PipelineStageUpdate = Partial<PipelineStageCreate>;

// Deals
export type Deal = {
  id: string;
  tenant_id: string;
  title: string;
  contact_id: string | null;
  organization_id: string | null;
  contact_name: string | null;
  organization_name: string | null;
  stage_id: string | null;
  stage_name: string | null;
  stage_color: string | null;
  stage_order: number | null;
  status: DealStatus;
  value: number | null;
  currency: string;
  expected_close_date: string | null;
  actual_close_date: string | null;
  probability_pct: number | null;
  assigned_to: string | null;
  description: string | null;
  properties: Record<string, unknown>;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};
export type DealCreate = {
  title: string;
  contact_id?: string;
  organization_id?: string;
  stage_id?: string;
  value?: number;
  currency?: string;
  expected_close_date?: string;
  probability_pct?: number;
  description?: string;
};
export type DealUpdate = Partial<DealCreate & { status_id?: number }>;

// Activities
export type Activity = {
  id: string;
  tenant_id: string;
  activity_type: ActivityType;
  activity_type_label: string;
  activity_type_icon: string;
  status: ActivityStatus;
  title: string;
  description: string | null;
  due_at: string | null;
  completed_at: string | null;
  duration_minutes: number | null;
  entity_type: EntityType | null;
  entity_id: string | null;
  assigned_to: string | null;
  properties: Record<string, unknown>;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};
export type ActivityCreate = {
  activity_type_id: number;
  title: string;
  description?: string;
  due_at?: string;
  duration_minutes?: number;
  entity_type?: EntityType;
  entity_id?: string;
  assigned_to?: string;
};
export type ActivityUpdate = Partial<ActivityCreate & { status_id?: number; completed_at?: string }>;

// Notes
export type Note = {
  id: string;
  tenant_id: string;
  entity_type: EntityType;
  entity_id: string;
  content: string;
  is_pinned: boolean;
  deleted_at: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
};
export type NoteCreate = { entity_type: EntityType; entity_id: string; content: string; is_pinned?: boolean };
export type NoteUpdate = { content?: string; is_pinned?: boolean };

// Tags
export type Tag = {
  id: string;
  tenant_id: string;
  name: string;
  color: string;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};
export type TagCreate = { name: string; color?: string };
export type EntityTag = { entity_type: EntityType; entity_id: string; tag_id: string };

// Reports
export type PipelineSummaryStage = {
  stage_id: string | null;
  stage_name: string | null;
  stage_color: string | null;
  stage_order: number | null;
  deal_count: number;
  total_value: number;
};
export type LeadConversionRow = { status: string; lead_count: number };
export type ActivitySummaryRow = { activity_type: string; status: string; count: number };
export type ContactGrowthPoint = { week: string; new_contacts: number };
