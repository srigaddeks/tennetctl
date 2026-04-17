"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, apiList } from "@/lib/api";
import type { Invite, InviteCreateBody } from "@/types/api";

const keys = {
  list: (orgId: string) => ["iam", "invites", orgId] as const,
};

export function useInvites(orgId: string | null) {
  return useQuery({
    queryKey: keys.list(orgId ?? ""),
    queryFn: () =>
      apiList<Invite>(`/v1/orgs/${orgId}/invites?limit=100&offset=0`).then(
        (r) => r.items,
      ),
    enabled: !!orgId,
  });
}

export function useCreateInvite(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: InviteCreateBody) =>
      apiFetch<Invite>(`/v1/orgs/${orgId}/invites`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: keys.list(orgId) });
    },
  });
}

export function useCancelInvite(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (inviteId: string) =>
      apiFetch<void>(`/v1/orgs/${orgId}/invites/${inviteId}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: keys.list(orgId) });
    },
  });
}
