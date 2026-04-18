"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
} from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { NotifyDelivery, NotifyDeliveryListResponse } from "@/types/api";

export function useDeliveries(
  orgId: string | null,
  filters: { status?: string; channel?: string; recipient_user_id?: string } = {},
) {
  return useQuery({
    queryKey: ["notify-deliveries", orgId, filters],
    enabled: !!orgId,
    queryFn: () => {
      const params = new URLSearchParams({ org_id: orgId! });
      if (filters.status) params.set("status", filters.status);
      if (filters.channel) params.set("channel", filters.channel);
      if (filters.recipient_user_id) params.set("recipient_user_id", filters.recipient_user_id);
      return apiFetch<NotifyDeliveryListResponse>(`/v1/notify/deliveries?${params}`);
    },
  });
}

export function useRetryDelivery(): UseMutationResult<
  NotifyDelivery,
  Error,
  string
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) =>
      apiFetch<NotifyDelivery>(`/v1/notify/deliveries/${id}/retry`, {
        method: "POST",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notify-deliveries"] });
    },
  });
}
