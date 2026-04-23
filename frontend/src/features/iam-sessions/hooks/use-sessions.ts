"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList, buildQuery } from "@/lib/api";
import type {
  ListResult,
  SessionPatchBody,
  SessionReadShape,
} from "@/types/api";

type ListParams = {
  limit?: number;
  offset?: number;
  only_valid?: boolean;
  user_id?: string;
};

const LIST_KEY = (params: ListParams) => ["iam", "sessions", "list", params] as const;

export function useMySessions(
  params: ListParams = {},
): UseQueryResult<ListResult<SessionReadShape>> {
  return useQuery<ListResult<SessionReadShape>>({
    queryKey: LIST_KEY(params),
    queryFn: () => apiList<SessionReadShape>(`/v1/sessions${buildQuery(params)}`),
  });
}

/**
 * useSessions — fetch sessions, optionally filtered by user_id.
 * When user_id is provided the query targets the same /v1/sessions endpoint;
 * admin-scoped per-user listing will be supported once the backend adds that
 * filter. Until then results reflect the caller's own sessions.
 */
export function useSessions(
  params: ListParams = {},
): UseQueryResult<ListResult<SessionReadShape>> {
  return useQuery<ListResult<SessionReadShape>>({
    queryKey: LIST_KEY(params),
    queryFn: () => apiList<SessionReadShape>(`/v1/sessions${buildQuery(params)}`),
  });
}

export function useExtendSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, body }: { sessionId: string; body: SessionPatchBody }) =>
      apiFetch<SessionReadShape>(`/v1/sessions/${sessionId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["iam", "sessions"] });
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}

export function useRevokeSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) =>
      apiFetch<void>(`/v1/sessions/${sessionId}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["iam", "sessions"] });
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}
