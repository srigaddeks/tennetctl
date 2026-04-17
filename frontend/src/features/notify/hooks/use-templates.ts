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
  NotifyTemplate,
  NotifyTemplateAnalytics,
  NotifyTemplateCreate,
  NotifyTemplateGroup,
  NotifyTemplateGroupListResponse,
  NotifyTemplateListResponse,
  NotifyTemplatePatch,
} from "@/types/api";

const qk = {
  all: (orgId: string) => ["notify-templates", orgId] as const,
  list: (orgId: string) => ["notify-templates", orgId, "list"] as const,
  one: (id: string) => ["notify-templates", "one", id] as const,
};

export function useTemplates(orgId: string | null): UseQueryResult<NotifyTemplateListResponse> {
  return useQuery({
    queryKey: qk.list(orgId ?? ""),
    queryFn: () => {
      if (!orgId) throw new Error("org_id required");
      return apiFetch<NotifyTemplateListResponse>(
        `/v1/notify/templates${buildQuery({ org_id: orgId })}`,
      );
    },
    enabled: !!orgId,
  });
}

export function useTemplate(id: string | null): UseQueryResult<NotifyTemplate> {
  return useQuery({
    queryKey: qk.one(id ?? ""),
    queryFn: () => {
      if (!id) throw new Error("id required");
      return apiFetch<NotifyTemplate>(`/v1/notify/templates/${id}`);
    },
    enabled: !!id,
  });
}

export function useCreateTemplate(
  orgId: string | null,
): UseMutationResult<NotifyTemplate, Error, NotifyTemplateCreate> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<NotifyTemplate>("/v1/notify/templates", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: qk.all(orgId) });
    },
  });
}

export function usePatchTemplate(
  orgId: string | null,
): UseMutationResult<NotifyTemplate, Error, { id: string; patch: NotifyTemplatePatch }> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }) =>
      apiFetch<NotifyTemplate>(`/v1/notify/templates/${id}`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: qk.one(data.id) });
      if (orgId) qc.invalidateQueries({ queryKey: qk.all(orgId) });
    },
  });
}

export function useUpsertBodies(
  _orgId?: string | null,
): UseMutationResult<
  NotifyTemplate,
  Error,
  { id: string; bodies: Array<{ channel_id: number; body_html: string; body_text?: string; preheader?: string }> }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, bodies }) =>
      apiFetch<NotifyTemplate>(`/v1/notify/templates/${id}/bodies`, {
        method: "PUT",
        body: JSON.stringify({ bodies }),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: qk.one(data.id) });
    },
  });
}

export function useTemplateGroups(orgId: string | null): UseQueryResult<NotifyTemplateGroupListResponse> {
  return useQuery({
    queryKey: ["notify-template-groups", orgId ?? ""],
    queryFn: () => {
      if (!orgId) throw new Error("org_id required");
      return apiFetch<NotifyTemplateGroupListResponse>(
        `/v1/notify/template-groups${buildQuery({ org_id: orgId })}`,
      );
    },
    enabled: !!orgId,
  });
}

// Exposed for external pickers — returns the raw group list.
export type { NotifyTemplateGroup };


export function useTemplateAnalytics(id: string | null): UseQueryResult<NotifyTemplateAnalytics> {
  return useQuery({
    queryKey: ["notify-template-analytics", id ?? ""],
    queryFn: () => {
      if (!id) throw new Error("id required");
      return apiFetch<NotifyTemplateAnalytics>(`/v1/notify/templates/${id}/analytics`);
    },
    enabled: !!id,
  });
}

export function useTestSend(): UseMutationResult<
  { sent_to: string },
  Error,
  { id: string; to_email: string; context?: Record<string, unknown> }
> {
  return useMutation({
    mutationFn: ({ id, to_email, context }) =>
      apiFetch<{ sent_to: string }>(`/v1/notify/templates/${id}/test-send`, {
        method: "POST",
        body: JSON.stringify({ to_email, context: context ?? {} }),
      }),
  });
}
