"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList, buildQuery } from "@/lib/api";
import type {
  Flag,
  FlagCreateBody,
  FlagState,
  FlagStateUpdateBody,
  FlagUpdateBody,
  ListResult,
} from "@/types/api";

type ListParams = {
  limit?: number;
  offset?: number;
  scope?: string | null;
  org_id?: string | null;
  application_id?: string | null;
  is_active?: boolean;
};

const key = {
  all: ["ff", "flags"] as const,
  list: (p?: ListParams) => ["ff", "flags", "list", p ?? {}] as const,
  one: (id: string) => ["ff", "flags", "one", id] as const,
  states: (flagId: string) => ["ff", "flag-states", "list", flagId] as const,
};

export function useFlags(
  params?: ListParams
): UseQueryResult<ListResult<Flag>> {
  return useQuery({
    queryKey: key.list(params),
    queryFn: () => apiList<Flag>(`/v1/flags${buildQuery(params ?? {})}`),
  });
}

export function useFlag(id: string | null): UseQueryResult<Flag | null> {
  return useQuery({
    queryKey: key.one(id ?? ""),
    queryFn: async () => (id ? apiFetch<Flag>(`/v1/flags/${id}`) : null),
    enabled: id !== null,
  });
}

export function useFlagStates(
  flagId: string | null
): UseQueryResult<ListResult<FlagState>> {
  return useQuery({
    queryKey: key.states(flagId ?? ""),
    queryFn: () =>
      apiList<FlagState>(`/v1/flag-states${buildQuery({ flag_id: flagId, limit: 100 })}`),
    enabled: flagId !== null,
  });
}

export function useCreateFlag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: FlagCreateBody) =>
      apiFetch<Flag>("/v1/flags", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useUpdateFlag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: FlagUpdateBody }) =>
      apiFetch<Flag>(`/v1/flags/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: key.all });
      qc.setQueryData(key.one(data.id), data);
    },
  });
}

export function useDeleteFlag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/flags/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useUpdateFlagState() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: FlagStateUpdateBody }) =>
      apiFetch<FlagState>(`/v1/flag-states/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: key.states(data.flag_id) });
    },
  });
}
