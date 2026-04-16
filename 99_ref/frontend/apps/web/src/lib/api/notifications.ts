import { fetchWithAuth } from "./apiClient";

// ── Web Push ──────────────────────────────────────────────────────────────────

export interface WebPushSubscription {
  id: string;
  user_id: string;
  tenant_key: string;
  endpoint: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

export async function getVapidPublicKey(): Promise<string | null> {
  const res = await fetchWithAuth("/api/v1/notifications/web-push/vapid-public-key");
  if (!res.ok) return null;
  const data = await res.json();
  return data.vapid_public_key ?? null;
}

export async function listWebPushSubscriptions(): Promise<WebPushSubscription[]> {
  const res = await fetchWithAuth("/api/v1/notifications/web-push/subscriptions");
  if (!res.ok) return [];
  return res.json();
}

export async function subscribeWebPush(subscription: PushSubscription, userAgent?: string): Promise<WebPushSubscription> {
  const json = subscription.toJSON();
  const body = {
    endpoint: json.endpoint,
    p256dh_key: json.keys?.p256dh ?? "",
    auth_key: json.keys?.auth ?? "",
    user_agent: userAgent || navigator.userAgent,
  };
  const res = await fetchWithAuth("/api/v1/notifications/web-push/subscribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to subscribe");
  return data as WebPushSubscription;
}

export async function unsubscribeWebPush(subscriptionId: string): Promise<void> {
  await fetchWithAuth(`/api/v1/notifications/web-push/${subscriptionId}`, { method: "DELETE" });
}

export async function sendTestWebPush(deepLink = "/notifications"): Promise<{ success: boolean; message: string; sent: number }> {
  const q = new URLSearchParams({ deep_link: deepLink });
  const res = await fetchWithAuth(`/api/v1/notifications/web-push/test?${q}`, { method: "POST" });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to send test push");
  return data;
}

export interface NotificationPreference {
  id: string;
  notification_type_code: string;
  channel_code: string;
  is_enabled: boolean;
}

export interface NotificationHistoryItem {
  id: string;
  notification_type_code: string;
  channel_code: string;
  subject: string | null;
  sent_at: string;
  read_at: string | null;
  status: string;
}

export interface BroadcastItem {
  id: string;
  title: string;
  body_text: string;
  body_html: string | null;
  scope: string;
  scope_org_id: string | null;
  scope_workspace_id: string | null;
  notification_type_code: string;
  priority_code: string;
  severity: string | null;
  is_critical: boolean;
  template_code: string | null;
  scheduled_at: string | null;
  sent_at: string | null;
  total_recipients: number | null;
  is_active: boolean;
  created_at: string;
  created_by: string;
}

export interface CreateBroadcastPayload {
  title: string;
  body_text: string;
  body_html?: string | null;
  priority_code?: string;
  severity?: string | null;
  is_critical?: boolean;
  notification_type_code?: string;
  template_code?: string | null;
  scheduled_at?: string | null;
}

export interface ReleaseItem {
  id: string;
  version: string;
  title: string;
  summary: string | null;
  body_markdown: string | null;
  body_html: string | null;
  changelog_url: string | null;
  status: string;
  release_date: string | null;
  published_at: string | null;
  created_at: string;
}

export interface IncidentUpdate {
  id: string;
  incident_id: string;
  status: string;
  message: string;
  is_public: boolean;
  created_at: string;
}

export interface IncidentItem {
  id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  affected_components: string[] | null;
  started_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updates?: IncidentUpdate[];
}

export async function listMyNotificationPreferences(): Promise<NotificationPreference[]> {
  const res = await fetchWithAuth("/api/v1/notifications/preferences");
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to load preferences");
  return (data.preferences ?? data.items ?? []) as NotificationPreference[];
}

export async function setNotificationPreference(
  notificationTypeCode: string,
  channelCode: string,
  isEnabled: boolean
): Promise<void> {
  const res = await fetchWithAuth("/api/v1/notifications/preferences", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scope_level: "type",
      notification_type_code: notificationTypeCode,
      channel_code: channelCode,
      is_enabled: isEnabled,
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to update preference");
  }
}

export async function listNotificationHistory(params?: { limit?: number; offset?: number }): Promise<{ items: NotificationHistoryItem[]; total: number }> {
  const q = new URLSearchParams();
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  const res = await fetchWithAuth(`/api/v1/notifications/history${q.toString() ? `?${q}` : ""}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to load notification history");
  return { items: data.items ?? [], total: data.total ?? 0 };
}

// ---------------------------------------------------------------------------
// Org-scoped broadcast endpoints
// ---------------------------------------------------------------------------

export async function listOrgBroadcasts(orgId: string): Promise<BroadcastItem[]> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/broadcasts`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to load org broadcasts");
  return (data ?? []) as BroadcastItem[];
}

export async function createOrgBroadcast(orgId: string, payload: CreateBroadcastPayload): Promise<BroadcastItem> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/broadcasts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to create broadcast");
  return data as BroadcastItem;
}

export async function sendOrgBroadcast(orgId: string, broadcastId: string): Promise<BroadcastItem> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/broadcasts/${broadcastId}/send`, {
    method: "POST",
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to send broadcast");
  return data as BroadcastItem;
}

// ---------------------------------------------------------------------------
// Public releases/incidents — no platform permission required
// ---------------------------------------------------------------------------

export async function listPublishedReleases(params?: { limit?: number; offset?: number }): Promise<{ items: ReleaseItem[]; total: number }> {
  const q = new URLSearchParams();
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  const res = await fetchWithAuth(`/api/v1/notifications/releases/public${q.toString() ? `?${q}` : ""}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to load releases");
  return { items: data.items ?? [], total: data.total ?? 0 };
}

export async function listActiveIncidents(params?: { limit?: number; offset?: number }): Promise<{ items: IncidentItem[]; total: number }> {
  const q = new URLSearchParams();
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  const res = await fetchWithAuth(`/api/v1/notifications/incidents/active${q.toString() ? `?${q}` : ""}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to load incidents");
  return { items: data.items ?? [], total: data.total ?? 0 };
}

// ---------------------------------------------------------------------------
// User notification inbox
// ---------------------------------------------------------------------------

export interface InboxNotificationItem {
  id: string;
  notification_type_code: string;
  category_code: string | null;
  channel_code: string;
  status_code: string;
  priority_code: string;
  rendered_subject: string | null;
  rendered_body: string | null;
  rendered_body_html: string | null;
  is_read: boolean;
  read_at: string | null;
  scheduled_at: string;
  completed_at: string | null;
  created_at: string;
}

export interface InboxResponse {
  items: InboxNotificationItem[];
  total: number;
  unread_count: number;
}

export async function getInbox(params?: {
  is_read?: boolean;
  category_code?: string;
  channel_code?: string;
  limit?: number;
  offset?: number;
}): Promise<InboxResponse> {
  const q = new URLSearchParams();
  if (params?.is_read !== undefined) q.set("is_read", String(params.is_read));
  if (params?.category_code) q.set("category_code", params.category_code);
  if (params?.channel_code) q.set("channel_code", params.channel_code);
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  const res = await fetchWithAuth(`/api/v1/notifications/inbox${q.toString() ? `?${q}` : ""}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to load inbox");
  return data as InboxResponse;
}

export async function markInboxRead(notificationIds: string[]): Promise<void> {
  const res = await fetchWithAuth("/api/v1/notifications/inbox/mark-read", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notification_ids: notificationIds }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to mark as read");
  }
}

export async function getUnreadNotificationCount(): Promise<number> {
  try {
    const res = await fetchWithAuth("/api/v1/notifications/inbox/unread-count");
    if (!res.ok) return 0;
    const data = await res.json();
    return data.unread_count ?? 0;
  } catch {
    return 0;
  }
}
