"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type {
  AlertEvent,
  AlertEventListResponse,
  AlertRule,
  AlertRuleCreateRequest,
  AlertRuleListResponse,
  AlertRuleUpdateRequest,
  Silence,
  SilenceCreateRequest,
  SilenceListResponse,
} from "@/types/api";

const qk = {
  rules: ["monitoring", "alert-rules"] as const,
  rulesList: () => ["monitoring", "alert-rules", "list"] as const,
  ruleDetail: (id: string) => ["monitoring", "alert-rules", id] as const,
  events: ["monitoring", "alerts"] as const,
  eventsList: (state?: string) =>
    ["monitoring", "alerts", "list", state ?? "all"] as const,
  silences: ["monitoring", "silences"] as const,
  silencesList: () => ["monitoring", "silences", "list"] as const,
};

// ── Rules ──────────────────────────────────────────────────────────────────

export function useAlertRules(): UseQueryResult<AlertRuleListResponse> {
  return useQuery({
    queryKey: qk.rulesList(),
    queryFn: () =>
      apiFetch<AlertRuleListResponse>("/v1/monitoring/alert-rules"),
  });
}

export function useAlertRule(
  id: string | null,
): UseQueryResult<AlertRule> {
  return useQuery({
    queryKey: qk.ruleDetail(id ?? ""),
    queryFn: () =>
      apiFetch<AlertRule>(
        `/v1/monitoring/alert-rules/${encodeURIComponent(id ?? "")}`,
      ),
    enabled: id !== null && id !== "",
  });
}

export function useCreateAlertRule(): UseMutationResult<
  AlertRule,
  Error,
  AlertRuleCreateRequest
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<AlertRule>("/v1/monitoring/alert-rules", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.rules }),
  });
}

export function useUpdateAlertRule(): UseMutationResult<
  AlertRule,
  Error,
  { id: string; body: AlertRuleUpdateRequest }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }) =>
      apiFetch<AlertRule>(
        `/v1/monitoring/alert-rules/${encodeURIComponent(id)}`,
        { method: "PATCH", body: JSON.stringify(body) },
      ),
    onSuccess: (_r, v) => {
      void qc.invalidateQueries({ queryKey: qk.rules });
      void qc.invalidateQueries({ queryKey: qk.ruleDetail(v.id) });
    },
  });
}

export function useDeleteAlertRule(): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) =>
      apiFetch<void>(
        `/v1/monitoring/alert-rules/${encodeURIComponent(id)}`,
        { method: "DELETE" },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.rules }),
  });
}

export function usePauseAlertRule(): UseMutationResult<
  AlertRule,
  Error,
  { id: string; paused_until: string }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, paused_until }) =>
      apiFetch<AlertRule>(
        `/v1/monitoring/alert-rules/${encodeURIComponent(id)}/pause`,
        { method: "POST", body: JSON.stringify({ paused_until }) },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.rules }),
  });
}

export function useUnpauseAlertRule(): UseMutationResult<
  AlertRule,
  Error,
  string
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) =>
      apiFetch<AlertRule>(
        `/v1/monitoring/alert-rules/${encodeURIComponent(id)}/unpause`,
        { method: "POST" },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.rules }),
  });
}

// ── Events ─────────────────────────────────────────────────────────────────

export function useAlertEvents(
  state?: "firing" | "resolved",
): UseQueryResult<AlertEventListResponse> {
  return useQuery({
    queryKey: qk.eventsList(state),
    queryFn: () => {
      const q = state ? `?state=${state}` : "";
      return apiFetch<AlertEventListResponse>(`/v1/monitoring/alerts${q}`);
    },
    refetchInterval: 15_000,
  });
}

export function useAlertEvent(
  id: string | null,
  startedAt: string | null = null,
): UseQueryResult<AlertEvent> {
  return useQuery({
    queryKey: ["monitoring", "alerts", id ?? "", startedAt ?? ""],
    queryFn: () => {
      const qs = startedAt
        ? `?started_at=${encodeURIComponent(startedAt)}`
        : "";
      return apiFetch<AlertEvent>(
        `/v1/monitoring/alerts/${encodeURIComponent(id ?? "")}${qs}`,
      );
    },
    enabled: id !== null && id !== "" && startedAt !== null && startedAt !== "",
  });
}

// ── Silences ───────────────────────────────────────────────────────────────

export function useSilences(): UseQueryResult<SilenceListResponse> {
  return useQuery({
    queryKey: qk.silencesList(),
    queryFn: () => apiFetch<SilenceListResponse>("/v1/monitoring/silences"),
  });
}

export function useCreateSilence(): UseMutationResult<
  Silence,
  Error,
  SilenceCreateRequest
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<Silence>("/v1/monitoring/silences", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: qk.silences });
      void qc.invalidateQueries({ queryKey: qk.events });
    },
  });
}

export function useDeleteSilence(): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) =>
      apiFetch<void>(`/v1/monitoring/silences/${encodeURIComponent(id)}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: qk.silences });
      void qc.invalidateQueries({ queryKey: qk.events });
    },
  });
}

export function useSilenceFromEvent(): UseMutationResult<
  Silence,
  Error,
  { alertId: string; ends_at: string; reason: string; started_at?: string }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ alertId, ends_at, reason, started_at }) => {
      const qs = started_at
        ? `?started_at=${encodeURIComponent(started_at)}`
        : "";
      const starts_at = new Date().toISOString();
      return apiFetch<Silence>(
        `/v1/monitoring/alerts/${encodeURIComponent(alertId)}/silence${qs}`,
        {
          method: "POST",
          body: JSON.stringify({
            matcher: {},
            starts_at,
            ends_at,
            reason,
          }),
        },
      );
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: qk.silences });
      void qc.invalidateQueries({ queryKey: qk.events });
    },
  });
}
