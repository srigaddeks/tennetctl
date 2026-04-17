"use client";

/**
 * In-app notification hooks.
 *
 * Fetches in-app deliveries for the current user and provides a mark-read
 * mutation. Polls every 30s when the user is logged in.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  InAppDelivery,
  InAppDeliveryListResponse,
  UnreadCountResponse,
} from "@/types/api";

const qk = {
  all: ["in-app-notifications"] as const,
  list: (userId: string, orgId: string | null) =>
    ["in-app-notifications", "list", userId, orgId] as const,
  unread: (userId: string, orgId: string | null) =>
    ["in-app-notifications", "unread", userId, orgId] as const,
};

/**
 * Server-computed unread count across all channels for the current user.
 * Cheaper than fetching the full list just to count — use this for the badge.
 */
export function useUnreadCountServer(
  userId: string | null,
  orgId: string | null,
): UseQueryResult<UnreadCountResponse> {
  return useQuery({
    queryKey: qk.unread(userId ?? "", orgId),
    queryFn: () => {
      if (!userId || !orgId) throw new Error("not authenticated");
      return apiFetch<UnreadCountResponse>(
        `/v1/notify/unread-count${buildQuery({ org_id: orgId, recipient_user_id: userId })}`,
      );
    },
    enabled: !!userId && !!orgId,
    refetchInterval: 30_000,
  });
}

/** Fetch in-app deliveries for the current user. Polls every 30s. */
export function useInAppNotifications(
  userId: string | null,
  orgId: string | null,
): UseQueryResult<InAppDeliveryListResponse> {
  return useQuery({
    queryKey: qk.list(userId ?? "", orgId),
    queryFn: () => {
      if (!userId || !orgId) throw new Error("not authenticated");
      return apiFetch<InAppDeliveryListResponse>(
        `/v1/notify/deliveries${buildQuery({
          org_id: orgId,
          channel: "in_app",
          recipient_user_id: userId,
          limit: 50,
        })}`,
      );
    },
    enabled: !!userId && !!orgId,
    refetchInterval: 30_000, // 30s polling for new notifications
    select: (data) => data,
  });
}

/** Count unread in-app notifications (status not yet opened/clicked). */
export function useUnreadCount(
  userId: string | null,
  orgId: string | null,
): number {
  const q = useInAppNotifications(userId, orgId);
  if (!q.data) return 0;
  return q.data.items.filter(
    (d) => !["opened", "clicked", "failed", "unsubscribed"].includes(d.status_code),
  ).length;
}

/** Mark an in-app delivery as read. */
export function useMarkRead(): UseMutationResult<
  InAppDelivery,
  Error,
  string
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (deliveryId) =>
      apiFetch<InAppDelivery>(`/v1/notify/deliveries/${deliveryId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: "opened" }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}

/** Mark all unread in-app notifications as read. */
export function useMarkAllRead(
  userId: string | null,
  orgId: string | null,
): UseMutationResult<void, Error, InAppDelivery[]> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (unread) => {
      await Promise.allSettled(
        unread.map((d) =>
          apiFetch<InAppDelivery>(`/v1/notify/deliveries/${d.id}`, {
            method: "PATCH",
            body: JSON.stringify({ status: "opened" }),
          }),
        ),
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.list(userId ?? "", orgId) });
    },
  });
}
