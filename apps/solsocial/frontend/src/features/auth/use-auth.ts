"use client";
import { useQuery } from "@tanstack/react-query";
import { tc, getToken } from "@/lib/api";
import type { Me } from "@/types/api";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => tc.get<Me>("/v1/auth/me"),
    enabled: !!getToken(),
  });
}
