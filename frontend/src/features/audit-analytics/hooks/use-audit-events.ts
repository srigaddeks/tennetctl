"use client";

/**
 * Audit Explorer — TanStack Query hooks over the Phase 10-01 backend.
 *
 * Read-only. Cursor pagination on the list endpoint; simple fetch on detail,
 * stats, and keys endpoints.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  AuditBucket,
  AuditEventFilter,
  AuditEventKeyListResponse,
  AuditEventListResponse,
  AuditEventRow,
  AuditEventStatsResponse,
  AuditFunnelRequest,
  AuditFunnelResponse,
  AuditOutboxCursorResponse,
  AuditRetentionBucket,
  AuditRetentionResponse,
  AuditSavedViewCreate,
  AuditSavedViewListResponse,
  AuditSavedViewRow,
  AuditTailResponse,
} from "@/types/api";

const qk = {
  all: ["audit-events"] as const,
  list: (f: AuditEventFilter, cursor: string | null, limit: number) =>
    ["audit-events", "list", f, cursor, limit] as const,
  detail: (id: string) => ["audit-events", "detail", id] as const,
  stats: (f: AuditEventFilter, bucket: AuditBucket) =>
    ["audit-events", "stats", f, bucket] as const,
  keys: () => ["audit-event-keys"] as const,
};

function filterParams(f: AuditEventFilter): Record<string, string | number | boolean | null | undefined> {
  return {
    event_key: f.event_key ?? undefined,
    category_code: f.category_code ?? undefined,
    outcome: f.outcome ?? undefined,
    actor_user_id: f.actor_user_id ?? undefined,
    actor_session_id: f.actor_session_id ?? undefined,
    org_id: f.org_id ?? undefined,
    workspace_id: f.workspace_id ?? undefined,
    application_id: f.application_id ?? undefined,
    trace_id: f.trace_id ?? undefined,
    since: f.since ?? undefined,
    until: f.until ?? undefined,
    q: f.q ?? undefined,
  };
}

export function useAuditEvents(
  filters: AuditEventFilter,
  opts?: { cursor?: string | null; limit?: number },
): UseQueryResult<AuditEventListResponse> {
  const cursor = opts?.cursor ?? null;
  const limit = opts?.limit ?? 50;
  return useQuery({
    queryKey: qk.list(filters, cursor, limit),
    queryFn: () =>
      apiFetch<AuditEventListResponse>(
        `/v1/audit-events${buildQuery({
          ...filterParams(filters),
          cursor: cursor ?? undefined,
          limit,
        })}`,
      ),
    placeholderData: (prev) => prev,
  });
}

export function useLoadMore(): UseMutationResult<
  AuditEventListResponse,
  Error,
  { filters: AuditEventFilter; cursor: string; limit: number }
> {
  return useMutation({
    mutationFn: ({ filters, cursor, limit }) =>
      apiFetch<AuditEventListResponse>(
        `/v1/audit-events${buildQuery({
          ...filterParams(filters),
          cursor,
          limit,
        })}`,
      ),
  });
}

export function useAuditEventDetail(
  eventId: string | null,
): UseQueryResult<AuditEventRow> {
  return useQuery({
    queryKey: qk.detail(eventId ?? ""),
    queryFn: () =>
      apiFetch<AuditEventRow>(`/v1/audit-events/${eventId}`),
    enabled: eventId !== null,
  });
}

export function useAuditEventStats(
  filters: AuditEventFilter,
  bucket: AuditBucket = "hour",
): UseQueryResult<AuditEventStatsResponse> {
  return useQuery({
    queryKey: qk.stats(filters, bucket),
    queryFn: () =>
      apiFetch<AuditEventStatsResponse>(
        `/v1/audit-events/stats${buildQuery({ ...filterParams(filters), bucket })}`,
      ),
  });
}

export function useAuditEventKeys(): UseQueryResult<AuditEventKeyListResponse> {
  return useQuery({
    queryKey: qk.keys(),
    queryFn: () => apiFetch<AuditEventKeyListResponse>("/v1/audit-event-keys"),
  });
}

export function useInvalidateAuditEvents() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: qk.all });
}

// ─── Analytics hooks (Plan 10-03) ────────────────────────────────────────────

export function useAuditFunnel(): UseMutationResult<
  AuditFunnelResponse,
  Error,
  AuditFunnelRequest
> {
  return useMutation({
    mutationFn: (body) =>
      apiFetch<AuditFunnelResponse>("/v1/audit-events/funnel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
  });
}

export function useAuditRetention(
  params: {
    anchor: string;
    return_event: string;
    bucket?: AuditRetentionBucket;
    periods?: number;
    org_id?: string | null;
  } | null,
): UseQueryResult<AuditRetentionResponse> {
  return useQuery({
    queryKey: ["audit-retention", params],
    queryFn: () => {
      if (!params) throw new Error("no params");
      return apiFetch<AuditRetentionResponse>(
        `/v1/audit-events/retention${buildQuery({
          anchor: params.anchor,
          return_event: params.return_event,
          bucket: params.bucket ?? "week",
          periods: params.periods ?? 6,
          org_id: params.org_id ?? undefined,
        })}`,
      );
    },
    enabled: params !== null && params.anchor !== "" && params.return_event !== "",
  });
}

// ─── Saved views hooks (Plan 10-03) ──────────────────────────────────────────

const svqk = {
  all: ["audit-saved-views"] as const,
};

export function useAuditSavedViews(): UseQueryResult<AuditSavedViewListResponse> {
  return useQuery({
    queryKey: svqk.all,
    queryFn: () => apiFetch<AuditSavedViewListResponse>("/v1/audit-saved-views"),
  });
}

export function useCreateSavedView(): UseMutationResult<
  AuditSavedViewRow,
  Error,
  AuditSavedViewCreate
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<AuditSavedViewRow>("/v1/audit-saved-views", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: svqk.all }),
  });
}

export function useDeleteSavedView(): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) =>
      apiFetch<void>(`/v1/audit-saved-views/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: svqk.all }),
  });
}

// ─── Live tail hooks (Plan 10-04) ────────────────────────────────────────────

export function useOutboxCursor(): UseQueryResult<AuditOutboxCursorResponse> {
  return useQuery({
    queryKey: ["audit-outbox-cursor"],
    queryFn: () => apiFetch<AuditOutboxCursorResponse>("/v1/audit-events/outbox-cursor"),
    staleTime: Infinity,
  });
}

/**
 * Live tail: polls /v1/audit-events/tail every 3s when `enabled`.
 * `sinceId` is the outbox cursor returned by the previous poll; the caller
 * must advance it via the returned `last_outbox_id`.
 */
/**
 * Poll the outbox tail. Caller manages the interval and advances since_id.
 * Use `mutateAsync({since_id, org_id})` inside a setInterval.
 */
export function useAuditTailPoll(): UseMutationResult<
  AuditTailResponse,
  Error,
  { since_id: number; org_id?: string | null }
> {
  return useMutation({
    mutationFn: ({ since_id, org_id }) =>
      apiFetch<AuditTailResponse>(
        `/v1/audit-events/tail${buildQuery({
          since_id,
          org_id: org_id ?? undefined,
          limit: 50,
        })}`,
      ),
  });
}
