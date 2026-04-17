"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { PasswordChangeBody, PasswordChangeResult } from "@/types/api";

export function useChangePassword() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PasswordChangeBody) =>
      apiFetch<PasswordChangeResult>("/v1/credentials/me", {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      // other sessions are revoked server-side; refresh both keys
      qc.invalidateQueries({ queryKey: ["iam", "sessions"] });
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}
