import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ScimToken, ScimTokenCreateBody } from "@/types/api";

const BASE = "/v1/iam/scim-tokens";

async function fetchTokens(): Promise<ScimToken[]> {
  const res = await fetch(BASE, { credentials: "include" });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error?.message ?? "Failed to fetch SCIM tokens");
  return data.data;
}

async function createToken(body: ScimTokenCreateBody): Promise<ScimToken & { token: string }> {
  const res = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error?.message ?? "Failed to create SCIM token");
  return data.data;
}

async function revokeToken(id: string): Promise<void> {
  const res = await fetch(`${BASE}/${id}`, { method: "DELETE", credentials: "include" });
  if (!res.ok && res.status !== 204) throw new Error("Failed to revoke SCIM token");
}

export function useScimTokens() {
  return useQuery({ queryKey: ["scim-tokens"], queryFn: fetchTokens });
}

export function useCreateScimToken() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createToken,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scim-tokens"] }),
  });
}

export function useRevokeScimToken() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: revokeToken,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scim-tokens"] }),
  });
}
