"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList, buildQuery } from "@/lib/api";
import type {
  Application,
  ApplicationCreateBody,
  ApplicationUpdateBody,
  ListResult,
} from "@/types/api";

type ListParams = {
  limit?: number;
  offset?: number;
  org_id?: string | null;
  is_active?: boolean;
};

const key = {
  all: ["iam", "applications"] as const,
  list: (p?: ListParams) =>
    ["iam", "applications", "list", p ?? {}] as const,
  one: (id: string) => ["iam", "applications", "one", id] as const,
};

export function useApplications(
  params?: ListParams
): UseQueryResult<ListResult<Application>> {
  return useQuery({
    queryKey: key.list(params),
    queryFn: () =>
      apiList<Application>(`/v1/applications${buildQuery(params ?? {})}`),
  });
}

export function useApplication(
  id: string | null
): UseQueryResult<Application | null> {
  return useQuery({
    queryKey: key.one(id ?? ""),
    queryFn: async () =>
      id ? apiFetch<Application>(`/v1/applications/${id}`) : null,
    enabled: id !== null,
  });
}

export function useCreateApplication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ApplicationCreateBody) =>
      apiFetch<Application>("/v1/applications", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useUpdateApplication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: ApplicationUpdateBody }) =>
      apiFetch<Application>(`/v1/applications/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: key.all });
      qc.setQueryData(key.one(data.id), data);
    },
  });
}

export function useDeleteApplication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/applications/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}
