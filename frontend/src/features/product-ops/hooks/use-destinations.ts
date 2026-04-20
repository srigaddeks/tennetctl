import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  CreateDestinationBody,
  Destination,
  DestinationDeliveryListResponse,
  DestinationListResponse,
} from "@/types/api";

export function useDestinations(workspaceId: string | undefined, kind?: "webhook" | "slack" | "custom") {
  const params = buildQuery({ workspace_id: workspaceId, kind });
  return useQuery({
    queryKey: ["destinations", workspaceId, kind],
    queryFn: () => apiFetch<DestinationListResponse>(`/v1/destinations?${params}`),
    enabled: Boolean(workspaceId),
  });
}

export function useCreateDestination() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateDestinationBody) =>
      apiFetch<Destination>("/v1/destinations", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["destinations"] });
    },
  });
}

export function useDeleteDestination() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/v1/destinations/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["destinations"] });
    },
  });
}

export function useTestDestination() {
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<{ destination_id: string; status: string }>(
        `/v1/destinations/${id}/test`, { method: "POST", body: JSON.stringify({}) },
      ),
  });
}

export function useDeliveries(destinationId: string | null) {
  return useQuery({
    queryKey: ["destination-deliveries", destinationId],
    queryFn: () => apiFetch<DestinationDeliveryListResponse>(`/v1/destinations/${destinationId}/deliveries?limit=50`),
    enabled: Boolean(destinationId),
  });
}
