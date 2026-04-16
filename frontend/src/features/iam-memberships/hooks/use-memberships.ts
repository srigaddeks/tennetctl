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
  OrgMembership,
  OrgMembershipCreateBody,
  WorkspaceMembership,
  WorkspaceMembershipCreateBody,
} from "@/types/api";

// ─── Org memberships ────────────────────────────────────────────

const orgKey = {
  all: ["iam", "org-members"] as const,
  list: (p?: Record<string, unknown>) =>
    ["iam", "org-members", "list", p ?? {}] as const,
};

export function useOrgMemberships(params?: {
  user_id?: string;
  org_id?: string;
}): UseQueryResult<ListResult<OrgMembership>> {
  return useQuery({
    queryKey: orgKey.list(params),
    queryFn: () =>
      apiList<OrgMembership>(
        `/v1/org-members${buildQuery({ limit: 200, ...params })}`
      ),
  });
}

export function useCreateOrgMembership() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: OrgMembershipCreateBody) =>
      apiFetch<OrgMembership>("/v1/org-members", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: orgKey.all });
    },
  });
}

export function useDeleteOrgMembership() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/org-members/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: orgKey.all });
    },
  });
}

// ─── Workspace memberships ──────────────────────────────────────

const wsKey = {
  all: ["iam", "workspace-members"] as const,
  list: (p?: Record<string, unknown>) =>
    ["iam", "workspace-members", "list", p ?? {}] as const,
};

export function useWorkspaceMemberships(params?: {
  user_id?: string;
  workspace_id?: string;
  org_id?: string;
}): UseQueryResult<ListResult<WorkspaceMembership>> {
  return useQuery({
    queryKey: wsKey.list(params),
    queryFn: () =>
      apiList<WorkspaceMembership>(
        `/v1/workspace-members${buildQuery({ limit: 200, ...params })}`
      ),
  });
}

export function useCreateWorkspaceMembership() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: WorkspaceMembershipCreateBody) =>
      apiFetch<WorkspaceMembership>("/v1/workspace-members", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: wsKey.all });
    },
  });
}

export function useDeleteWorkspaceMembership() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/workspace-members/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: wsKey.all });
    },
  });
}
