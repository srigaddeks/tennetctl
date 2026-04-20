/**
 * TanStack Query hooks for SLO CRUD, list, evaluations.
 * Plan 41-01 implementation.
 */

"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import type {
  SloResponse,
  SloCreateRequest,
  SloUpdateRequest,
  SloEvaluationResponse,
  SloBudgetSnapshot,
} from "@/types/api";

const API_BASE = "/v1/monitoring";

export function useListSlos(
  {
    status,
    windowKind,
    ownerUserId,
    q,
    limit = 100,
    offset = 0,
  }: {
    status?: string;
    windowKind?: string;
    ownerUserId?: string;
    q?: string;
    limit?: number;
    offset?: number;
  } = {}
) {
  return useQuery({
    queryKey: ["slos", { status, windowKind, ownerUserId, q, limit, offset }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.append("status", status);
      if (windowKind) params.append("window_kind", windowKind);
      if (ownerUserId) params.append("owner_user_id", ownerUserId);
      if (q) params.append("q", q);
      params.append("limit", String(limit));
      params.append("offset", String(offset));

      const res = await fetch(`${API_BASE}/slos?${params}`);
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as {
        items: SloResponse[];
        total: number;
        limit: number;
        offset: number;
      };
    },
  });
}

export function useGetSlo(sloId: string) {
  return useQuery({
    queryKey: ["slo", sloId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/slos/${sloId}`);
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as SloResponse;
    },
    enabled: !!sloId,
  });
}

export function useCreateSlo() {
  return useMutation({
    mutationFn: async (req: SloCreateRequest) => {
      const res = await fetch(`${API_BASE}/slos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as SloResponse;
    },
  });
}

export function useUpdateSlo(sloId: string) {
  return useMutation({
    mutationFn: async (req: SloUpdateRequest) => {
      const res = await fetch(`${API_BASE}/slos/${sloId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as SloResponse;
    },
  });
}

export function useDeleteSlo(sloId: string) {
  return useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/slos/${sloId}`, {
        method: "DELETE",
      });
      if (res.status !== 204) {
        const data = await res.json();
        throw new Error(data.error?.message);
      }
    },
  });
}

export function useListSloEvaluations(
  sloId: string,
  {
    fromTs,
    toTs,
    granularity = "1h",
    limit = 100,
  }: {
    fromTs?: string;
    toTs?: string;
    granularity?: string;
    limit?: number;
  } = {}
) {
  return useQuery({
    queryKey: [
      "slo-evaluations",
      sloId,
      { fromTs, toTs, granularity, limit },
    ],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (fromTs) params.append("from_ts", fromTs);
      if (toTs) params.append("to_ts", toTs);
      params.append("granularity", granularity);
      params.append("limit", String(limit));

      const res = await fetch(
        `${API_BASE}/slos/${sloId}/evaluations?${params}`
      );
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as SloEvaluationResponse[];
    },
    enabled: !!sloId,
  });
}

export function useGetSloBudget(sloId: string, at?: string) {
  return useQuery({
    queryKey: ["slo-budget", sloId, at],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (at) params.append("at", at);

      const res = await fetch(
        `${API_BASE}/slos/${sloId}/budget${params.toString() ? "?" + params : ""}`
      );
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as SloBudgetSnapshot;
    },
    enabled: !!sloId,
  });
}

export function useSloMutations(sloId: string) {
  return {
    update: useUpdateSlo(sloId),
    delete: useDeleteSlo(sloId),
  };
}
