"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { ApiClientError, apiFetch } from "@/lib/api";
import type {
  AuthMeResponse,
  AuthResponseBody,
  OAuthCallbackBody,
  SigninBody,
  SignupBody,
} from "@/types/api";

const ME_KEY = ["auth", "me"] as const;

export function useMe(): UseQueryResult<AuthMeResponse | null> {
  return useQuery<AuthMeResponse | null>({
    queryKey: ME_KEY,
    queryFn: async () => {
      try {
        return await apiFetch<AuthMeResponse>("/v1/auth/me");
      } catch (err) {
        if (err instanceof ApiClientError && err.statusCode === 401) {
          return null;
        }
        throw err;
      }
    },
    staleTime: 30_000,
  });
}

export function useSignup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SignupBody) =>
      apiFetch<AuthResponseBody>("/v1/auth/signup", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ME_KEY });
    },
  });
}

export function useSignin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SigninBody) =>
      apiFetch<AuthResponseBody>("/v1/auth/signin", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ME_KEY });
    },
  });
}

export function useSignout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<{ signed_out: boolean }>("/v1/auth/signout", {
        method: "POST",
      }),
    onSuccess: () => {
      qc.setQueryData(ME_KEY, null);
      qc.invalidateQueries();
    },
  });
}

export function useOAuthExchange(provider: "google" | "github") {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: OAuthCallbackBody) =>
      apiFetch<AuthResponseBody>(`/v1/auth/${provider}`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ME_KEY });
    },
  });
}
