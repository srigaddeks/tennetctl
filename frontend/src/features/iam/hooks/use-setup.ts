"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import type { InitialAdminBody, InitialAdminResult, SetupStatus } from "@/types/api";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:51734";

async function fetchSetupStatus(): Promise<SetupStatus> {
  const res = await fetch(`${BASE}/v1/setup/status`, { cache: "no-store" });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error?.message ?? "Failed to fetch setup status");
  return data.data as SetupStatus;
}

async function postInitialAdmin(body: InitialAdminBody): Promise<InitialAdminResult> {
  const res = await fetch(`${BASE}/v1/setup/initial-admin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error?.message ?? "Setup failed");
  return data.data as InitialAdminResult;
}

export function useSetupStatus() {
  return useQuery({
    queryKey: ["setup-status"],
    queryFn: fetchSetupStatus,
    retry: false,
    staleTime: 0,
  });
}

export function useCreateInitialAdmin() {
  return useMutation({
    mutationFn: postInitialAdmin,
  });
}
