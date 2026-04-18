"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { IpAllowlistCreateBody, IpAllowlistEntry } from "@/types/api";

const QK = ["iam-security", "ip-allowlist"] as const;

export function useIpAllowlist() {
  return useQuery({
    queryKey: QK,
    queryFn: () =>
      apiFetch<IpAllowlistEntry[]>("/v1/iam/ip-allowlist").then((r) =>
        Array.isArray(r) ? r : [],
      ),
  });
}

export function useAddIpAllowlistEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: IpAllowlistCreateBody) =>
      apiFetch<IpAllowlistEntry>("/v1/iam/ip-allowlist", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}

export function useRemoveIpAllowlistEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/iam/ip-allowlist/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}
