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

const LIST_KEY = (params: ListParams) => ["iam", "sessions", "list", params] as const;

type ListParams = {
  limit?: number;
  offset?: number;
  only_valid?: boolean;
};

export function useMySessions(
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
