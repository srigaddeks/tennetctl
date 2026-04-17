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
  OtpRequestBody,
  OtpVerifyBody,
  PasskeyAuthBeginResponse,
  PasskeyListResponse,
  PasskeyRegisterBeginResponse,
  PasswordResetCompleteBody,
  PasswordResetRequestBody,
  SigninBody,
  SignupBody,
  TotpListResponse,
  TotpSetupBody,
  TotpSetupResponse,
  TotpVerifyBody,
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

export function useMagicLinkRequest() {
  return useMutation({
    mutationFn: (body: { email: string; redirect_url?: string }) =>
      apiFetch<{ sent: boolean; message: string }>("/v1/auth/magic-link/request", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

export function useOtpRequest() {
  return useMutation({
    mutationFn: (body: OtpRequestBody) =>
      apiFetch<{ sent: boolean; message: string }>("/v1/auth/otp/request", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

export function useOtpVerify() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: OtpVerifyBody) =>
      apiFetch<AuthResponseBody>("/v1/auth/otp/verify", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ME_KEY });
    },
  });
}

export function useTotpSetup() {
  return useMutation({
    mutationFn: (body: TotpSetupBody) =>
      apiFetch<TotpSetupResponse>("/v1/auth/totp/setup", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

export function useTotpVerify() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TotpVerifyBody) =>
      apiFetch<AuthResponseBody>("/v1/auth/totp/verify", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ME_KEY });
    },
  });
}

export function useTotpList() {
  return useQuery<TotpListResponse>({
    queryKey: ["auth", "totp"],
    queryFn: () => apiFetch<TotpListResponse>("/v1/auth/totp"),
    staleTime: 30_000,
  });
}

export function useTotpDelete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (credentialId: string) =>
      apiFetch<void>(`/v1/auth/totp/${credentialId}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["auth", "totp"] });
    },
  });
}

export function usePasskeyRegisterBegin() {
  return useMutation({
    mutationFn: (body: { device_name?: string }) =>
      apiFetch<PasskeyRegisterBeginResponse>("/v1/auth/passkeys/register/begin", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

export function usePasskeyRegisterComplete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { challenge_id: string; credential_json: string }) =>
      apiFetch<{ id: string; device_name: string }>("/v1/auth/passkeys/register/complete", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["auth", "passkeys"] });
    },
  });
}

export function usePasskeyAuthBegin() {
  return useMutation({
    mutationFn: (body: { email: string }) =>
      apiFetch<PasskeyAuthBeginResponse>("/v1/auth/passkeys/auth/begin", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

export function usePasskeyAuthComplete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { challenge_id: string; credential_json: string }) =>
      apiFetch<AuthResponseBody>("/v1/auth/passkeys/auth/complete", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ME_KEY });
    },
  });
}

export function usePasskeyList() {
  return useQuery<PasskeyListResponse>({
    queryKey: ["auth", "passkeys"],
    queryFn: () => apiFetch<PasskeyListResponse>("/v1/auth/passkeys"),
    staleTime: 30_000,
  });
}

export function usePasskeyDelete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (credId: string) =>
      apiFetch<void>(`/v1/auth/passkeys/${credId}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["auth", "passkeys"] });
    },
  });
}

export function usePasswordResetRequest() {
  return useMutation({
    mutationFn: (body: PasswordResetRequestBody) =>
      apiFetch<{ sent: boolean; message: string }>("/v1/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

export function usePasswordResetComplete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PasswordResetCompleteBody) =>
      apiFetch<AuthResponseBody>("/v1/auth/password-reset/complete", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ME_KEY });
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
