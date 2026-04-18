"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { SiemDestination, SiemDestinationCreateBody } from "@/types/api";

const QK = ["iam-security", "siem-destinations"] as const;

export function useSiemDestinations() {
  return useQuery({
    queryKey: QK,
    queryFn: () =>
      apiFetch<SiemDestination[]>("/v1/iam/siem-destinations").then((r) =>
        Array.isArray(r) ? r : [],
      ),
  });
}

export function useCreateSiemDestination() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SiemDestinationCreateBody) =>
      apiFetch<SiemDestination>("/v1/iam/siem-destinations", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}

export function useDeleteSiemDestination() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/iam/siem-destinations/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}
