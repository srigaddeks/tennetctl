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
  Workspace,
  WorkspaceCreateBody,
  WorkspaceUpdateBody,
} from "@/types/api";

type ListParams = {
  limit?: number;
  offset?: number;
  org_id?: string | null;
  is_active?: boolean;
};

const key = {
  all: ["iam", "workspaces"] as const,
  list: (p?: ListParams) => ["iam", "workspaces", "list", p ?? {}] as const,
  one: (id: string) => ["iam", "workspaces", "one", id] as const,
};

export function useWorkspaces(
  params?: ListParams
): UseQueryResult<ListResult<Workspace>> {
  return useQuery({
    queryKey: key.list(params),
    queryFn: () =>
      apiList<Workspace>(`/v1/workspaces${buildQuery(params ?? {})}`),
  });
}

export function useWorkspace(
  id: string | null
): UseQueryResult<Workspace | null> {
  return useQuery({
    queryKey: key.one(id ?? ""),
    queryFn: async () => {
      if (!id) return null;
      return apiFetch<Workspace>(`/v1/workspaces/${id}`);
    },
    enabled: id !== null,
  });
}

export function useCreateWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: WorkspaceCreateBody) =>
      apiFetch<Workspace>("/v1/workspaces", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key.all });
    },
  });
}

export function useUpdateWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: WorkspaceUpdateBody }) =>
      apiFetch<Workspace>(`/v1/workspaces/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: key.all });
      qc.setQueryData(key.one(data.id), data);
    },
  });
}

export function useDeleteWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/workspaces/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key.all });
    },
  });
}
