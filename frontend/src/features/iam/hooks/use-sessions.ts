"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList } from "@/lib/api";
import type { SessionReadShape } from "@/types/api";

const key = {
  all: ["iam", "sessions"] as const,
  list: () => ["iam", "sessions", "list"] as const,
};

export type SessionsListResult = {
  items: SessionReadShape[];
  total: number;
};

export function useSessions(): UseQueryResult<SessionsListResult> {
  return useQuery({
    queryKey: key.list(),
    queryFn: async () => {
      const res = await apiList<SessionReadShape>("/v1/sessions?only_valid=true&limit=50");
      return { items: res.items, total: res.pagination.total };
    },
    refetchInterval: 15_000,
  });
}

export function useRevokeSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) =>
      apiFetch<void>(`/v1/sessions/${encodeURIComponent(sessionId)}`, {
        method: "DELETE",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useRevokeAllOtherSessions() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (currentSessionId: string) => {
      // Fetch all sessions, then revoke all that are not the current one
      const res = await apiList<SessionReadShape>("/v1/sessions?only_valid=true&limit=50");
      const others = res.items.filter((s) => s.id !== currentSessionId);
      await Promise.all(
        others.map((s) =>
          apiFetch<void>(`/v1/sessions/${encodeURIComponent(s.id)}`, {
            method: "DELETE",
          }),
        ),
      );
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}
