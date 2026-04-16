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
  Org,
  OrgCreateBody,
  OrgUpdateBody,
} from "@/types/api";

type ListParams = {
  limit?: number;
  offset?: number;
  is_active?: boolean;
};

const key = {
  all: ["iam", "orgs"] as const,
  list: (p?: ListParams) => ["iam", "orgs", "list", p ?? {}] as const,
  one: (id: string) => ["iam", "orgs", "one", id] as const,
};

export function useOrgs(
  params?: ListParams
): UseQueryResult<ListResult<Org>> {
  return useQuery({
    queryKey: key.list(params),
    queryFn: () =>
      apiList<Org>(`/v1/orgs${buildQuery(params ?? {})}`),
  });
}

export function useOrg(id: string | null): UseQueryResult<Org | null> {
  return useQuery({
    queryKey: key.one(id ?? ""),
    queryFn: async () => {
      if (!id) return null;
      return apiFetch<Org>(`/v1/orgs/${id}`);
    },
    enabled: id !== null,
  });
}

export function useCreateOrg() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: OrgCreateBody) =>
      apiFetch<Org>("/v1/orgs", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key.all });
    },
  });
}

export function useUpdateOrg() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: OrgUpdateBody }) =>
      apiFetch<Org>(`/v1/orgs/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: key.all });
      qc.setQueryData(key.one(data.id), data);
    },
  });
}

export function useDeleteOrg() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/orgs/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key.all });
    },
  });
}
