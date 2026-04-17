"use client";

/**
 * Hooks for notification preferences.
 *
 * GET  /v1/notify/preferences  — returns all 16 channel×category combos
 * PATCH /v1/notify/preferences — upsert one or more preference items
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type {
  NotifyPreference,
  NotifyPreferencePatchItem,
} from "@/types/api";

const qk = {
  all: ["notify-preferences"] as const,
  list: (userId: string | null, orgId: string | null) =>
    ["notify-preferences", "list", userId, orgId] as const,
};

/** Fetch all 16 preference rows for the current user. */
export function useNotifyPreferences(
  userId: string | null,
  orgId: string | null,
): UseQueryResult<NotifyPreference[]> {
  return useQuery({
    queryKey: qk.list(userId, orgId),
    queryFn: () => {
      if (!userId || !orgId) throw new Error("not authenticated");
      return apiFetch<NotifyPreference[]>("/v1/notify/preferences");
    },
    enabled: !!userId && !!orgId,
  });
}

/** Upsert one or more preference items. */
export function useUpdatePreferences(
  userId: string | null,
  orgId: string | null,
): UseMutationResult<NotifyPreference[], Error, NotifyPreferencePatchItem[]> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (preferences) =>
      apiFetch<NotifyPreference[]>("/v1/notify/preferences", {
        method: "PATCH",
        body: JSON.stringify({ preferences }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.list(userId, orgId) });
    },
  });
}
