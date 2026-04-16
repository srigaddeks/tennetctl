"use client";

import { useMutation } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { EvaluateRequest, EvaluateResponse } from "@/types/api";

export function useEvaluate() {
  return useMutation({
    mutationFn: (body: EvaluateRequest) =>
      apiFetch<EvaluateResponse>("/v1/evaluate", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}
