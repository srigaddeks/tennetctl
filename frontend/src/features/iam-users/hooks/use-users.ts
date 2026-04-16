"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList, buildQuery } from "@/lib/api";
import type {
  ListResult,
  User,
  UserCreateBody,
  UserUpdateBody,
} from "@/types/api";

type ListParams = {
  limit?: number;
  offset?: number;
  account_type?: string | null;
  is_active?: boolean;
};

const key = {
  all: ["iam", "users"] as const,
  list: (p?: ListParams) => ["iam", "users", "list", p ?? {}] as const,
  one: (id: string) => ["iam", "users", "one", id] as const,
};

export function useUsers(
  params?: ListParams
): UseQueryResult<ListResult<User>> {
  return useQuery({
    queryKey: key.list(params),
    queryFn: () => apiList<User>(`/v1/users${buildQuery(params ?? {})}`),
  });
}

export function useUser(id: string | null): UseQueryResult<User | null> {
  return useQuery({
    queryKey: key.one(id ?? ""),
    queryFn: async () => {
      if (!id) return null;
      return apiFetch<User>(`/v1/users/${id}`);
    },
    enabled: id !== null,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: UserCreateBody) =>
      apiFetch<User>("/v1/users", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key.all });
    },
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UserUpdateBody }) =>
      apiFetch<User>(`/v1/users/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: key.all });
      qc.setQueryData(key.one(data.id), data);
    },
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/users/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key.all });
    },
  });
}
