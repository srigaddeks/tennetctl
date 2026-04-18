"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { TosVersion } from "@/types/api";

const QK = ["iam-security", "tos-versions"] as const;

export type TosVersionCreateBody = {
  version: string;
  title: string;
  body_markdown: string;
};

export function useTosVersions() {
  return useQuery({
    queryKey: QK,
    queryFn: () =>
      apiFetch<TosVersion[]>("/v1/tos").then((r) =>
        Array.isArray(r) ? r : [],
      ),
  });
}

export function useCreateTosVersion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TosVersionCreateBody) =>
      apiFetch<TosVersion>("/v1/tos", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}

export function useMarkTosEffective() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { id: string; effective_at: string }) =>
      apiFetch<TosVersion>(`/v1/tos/${vars.id}/effective`, {
        method: "POST",
        body: JSON.stringify({ effective_at: vars.effective_at }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}
