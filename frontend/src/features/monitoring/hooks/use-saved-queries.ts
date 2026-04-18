"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  QueryTarget,
  SavedQuery,
  SavedQueryCreateRequest,
  SavedQueryListResponse,
  SavedQueryUpdateRequest,
} from "@/types/api";

const qk = {
  all: ["monitoring", "saved-queries"] as const,
  list: (target?: QueryTarget) =>
    ["monitoring", "saved-queries", "list", target ?? "all"] as const,
  detail: (id: string) =>
    ["monitoring", "saved-queries", "detail", id] as const,
};

export function useSavedQueries(
  target?: QueryTarget,
): UseQueryResult<SavedQueryListResponse> {
  return useQuery({
    queryKey: qk.list(target),
    queryFn: () =>
      apiFetch<SavedQueryListResponse>(
        `/v1/monitoring/saved-queries${buildQuery(target ? { target } : {})}`,
      ),
  });
}

export function useSavedQuery(
  id: string | null,
): UseQueryResult<SavedQuery> {
  return useQuery({
    queryKey: qk.detail(id ?? ""),
    queryFn: () =>
      apiFetch<SavedQuery>(
        `/v1/monitoring/saved-queries/${encodeURIComponent(id ?? "")}`,
      ),
    enabled: id !== null && id !== "",
  });
}

export function useCreateSavedQuery(): UseMutationResult<
  SavedQuery,
  Error,
  SavedQueryCreateRequest
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<SavedQuery>("/v1/monitoring/saved-queries", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}

export function useUpdateSavedQuery(): UseMutationResult<
  SavedQuery,
  Error,
  { id: string; body: SavedQueryUpdateRequest }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }) =>
      apiFetch<SavedQuery>(
        `/v1/monitoring/saved-queries/${encodeURIComponent(id)}`,
        { method: "PATCH", body: JSON.stringify(body) },
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}

export function useDeleteSavedQuery(): UseMutationResult<
  void,
  Error,
  string
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      await apiFetch<void>(
        `/v1/monitoring/saved-queries/${encodeURIComponent(id)}`,
        { method: "DELETE" },
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}
