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
  NotifySMTPConfig,
  NotifySMTPConfigCreate,
  NotifySMTPConfigListResponse,
  NotifySMTPConfigUpdate,
  NotifySubscription,
  NotifySubscriptionCreate,
  NotifySubscriptionListResponse,
  NotifySubscriptionUpdate,
  NotifyTemplateGroup,
  NotifyTemplateGroupCreate,
  NotifyTemplateGroupListResponse,
  NotifyTemplateGroupUpdate,
} from "@/types/api";

const smtpQk = {
  list: (orgId: string) => ["notify-smtp-configs", orgId] as const,
};

const groupsQk = {
  list: (orgId: string) => ["notify-template-groups", orgId] as const,
};

// ── SMTP Configs ──────────────────────────────────────────────────

export function useSMTPConfigs(
  orgId: string | null,
): UseQueryResult<NotifySMTPConfigListResponse> {
  return useQuery({
    queryKey: smtpQk.list(orgId ?? ""),
    queryFn: () => {
      if (!orgId) throw new Error("org_id required");
      return apiFetch<NotifySMTPConfigListResponse>(
        `/v1/notify/smtp-configs${buildQuery({ org_id: orgId })}`,
      );
    },
    enabled: !!orgId,
  });
}

export function useCreateSMTPConfig(
  orgId: string | null,
): UseMutationResult<NotifySMTPConfig, Error, NotifySMTPConfigCreate> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<NotifySMTPConfig>("/v1/notify/smtp-configs", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: smtpQk.list(orgId) });
    },
  });
}

export function useDeleteSMTPConfig(
  orgId: string | null,
): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      await apiFetch<void>(`/v1/notify/smtp-configs/${id}`, { method: "DELETE" });
    },
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: smtpQk.list(orgId) });
    },
  });
}

export function useUpdateSMTPConfig(
  orgId: string | null,
): UseMutationResult<
  NotifySMTPConfig,
  Error,
  { id: string; body: NotifySMTPConfigUpdate }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }) =>
      apiFetch<NotifySMTPConfig>(`/v1/notify/smtp-configs/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: smtpQk.list(orgId) });
    },
  });
}

// ── Template Groups ───────────────────────────────────────────────

export function useCreateTemplateGroup(
  orgId: string | null,
): UseMutationResult<NotifyTemplateGroup, Error, NotifyTemplateGroupCreate> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<NotifyTemplateGroup>("/v1/notify/template-groups", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: groupsQk.list(orgId) });
    },
  });
}

export function useDeleteTemplateGroup(
  orgId: string | null,
): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      await apiFetch<void>(`/v1/notify/template-groups/${id}`, { method: "DELETE" });
    },
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: groupsQk.list(orgId) });
    },
  });
}

export function useUpdateTemplateGroup(
  orgId: string | null,
): UseMutationResult<
  NotifyTemplateGroup,
  Error,
  { id: string; body: NotifyTemplateGroupUpdate }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }) =>
      apiFetch<NotifyTemplateGroup>(`/v1/notify/template-groups/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: groupsQk.list(orgId) });
    },
  });
}

export function useTemplateGroupList(
  orgId: string | null,
): UseQueryResult<NotifyTemplateGroupListResponse> {
  return useQuery({
    queryKey: groupsQk.list(orgId ?? ""),
    queryFn: () => {
      if (!orgId) throw new Error("org_id required");
      return apiFetch<NotifyTemplateGroupListResponse>(
        `/v1/notify/template-groups${buildQuery({ org_id: orgId })}`,
      );
    },
    enabled: !!orgId,
  });
}

// ── Subscriptions ─────────────────────────────────────────────────

const subsQk = {
  list: (orgId: string) => ["notify-subscriptions", orgId] as const,
};

export function useSubscriptionList(
  orgId: string | null,
): UseQueryResult<NotifySubscriptionListResponse> {
  return useQuery({
    queryKey: subsQk.list(orgId ?? ""),
    queryFn: () => {
      if (!orgId) throw new Error("org_id required");
      return apiFetch<NotifySubscriptionListResponse>(
        `/v1/notify/subscriptions${buildQuery({ org_id: orgId })}`,
      );
    },
    enabled: !!orgId,
  });
}

export function useCreateSubscription(
  orgId: string | null,
): UseMutationResult<NotifySubscription, Error, NotifySubscriptionCreate> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<NotifySubscription>("/v1/notify/subscriptions", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: subsQk.list(orgId) });
    },
  });
}

export function useDeleteSubscription(
  orgId: string | null,
): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      await apiFetch<void>(`/v1/notify/subscriptions/${id}`, { method: "DELETE" });
    },
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: subsQk.list(orgId) });
    },
  });
}

export function useUpdateSubscription(
  orgId: string | null,
): UseMutationResult<
  NotifySubscription,
  Error,
  { id: string; body: NotifySubscriptionUpdate }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }) =>
      apiFetch<NotifySubscription>(`/v1/notify/subscriptions/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: subsQk.list(orgId) });
    },
  });
}
