"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type {
  NotifyTemplateVariable,
  NotifyTemplateVariableCreate,
  NotifyTemplateVariableListResponse,
} from "@/types/api";

const qk = {
  all: (templateId: string) => ["notify-template-vars", templateId] as const,
  list: (templateId: string) => ["notify-template-vars", templateId, "list"] as const,
};

export function useTemplateVariables(
  templateId: string | null,
): UseQueryResult<NotifyTemplateVariableListResponse> {
  return useQuery({
    queryKey: qk.list(templateId ?? ""),
    queryFn: () => {
      if (!templateId) throw new Error("template_id required");
      return apiFetch<NotifyTemplateVariableListResponse>(
        `/v1/notify/templates/${templateId}/variables`,
      );
    },
    enabled: !!templateId,
  });
}

export function useCreateTemplateVariable(
  templateId: string | null,
): UseMutationResult<NotifyTemplateVariable, Error, NotifyTemplateVariableCreate> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<NotifyTemplateVariable>(
        `/v1/notify/templates/${templateId}/variables`,
        { method: "POST", body: JSON.stringify(body) },
      ),
    onSuccess: () => {
      if (templateId) qc.invalidateQueries({ queryKey: qk.all(templateId) });
    },
  });
}

export function useResolveVariables(): UseMutationResult<
  Record<string, string>,
  Error,
  { templateId: string; context?: Record<string, unknown> }
> {
  return useMutation({
    mutationFn: ({ templateId, context }) =>
      apiFetch<Record<string, string>>(
        `/v1/notify/templates/${templateId}/variables/resolve`,
        { method: "POST", body: JSON.stringify({ context: context ?? {} }) },
      ),
  });
}
