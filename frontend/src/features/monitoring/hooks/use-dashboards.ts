"use client";

/**
 * Dashboard CRUD + panel CRUD hooks.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type {
  Dashboard,
  DashboardCreateRequest,
  DashboardDetail,
  DashboardListResponse,
  DashboardUpdateRequest,
  Panel,
  PanelCreateRequest,
  PanelUpdateRequest,
} from "@/types/api";

const qk = {
  all: ["monitoring", "dashboards"] as const,
  list: () => ["monitoring", "dashboards", "list"] as const,
  detail: (id: string) => ["monitoring", "dashboards", "detail", id] as const,
};

export function useDashboards(): UseQueryResult<DashboardListResponse> {
  return useQuery({
    queryKey: qk.list(),
    queryFn: () =>
      apiFetch<DashboardListResponse>("/v1/monitoring/dashboards"),
  });
}

export function useDashboard(
  id: string | null,
): UseQueryResult<DashboardDetail> {
  return useQuery({
    queryKey: qk.detail(id ?? ""),
    queryFn: () =>
      apiFetch<DashboardDetail>(
        `/v1/monitoring/dashboards/${encodeURIComponent(id ?? "")}`,
      ),
    enabled: id !== null && id !== "",
  });
}

export function useCreateDashboard(): UseMutationResult<
  Dashboard,
  Error,
  DashboardCreateRequest
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<Dashboard>("/v1/monitoring/dashboards", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.all }),
  });
}

export function useUpdateDashboard(): UseMutationResult<
  Dashboard,
  Error,
  { id: string; body: DashboardUpdateRequest }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }) =>
      apiFetch<Dashboard>(
        `/v1/monitoring/dashboards/${encodeURIComponent(id)}`,
        {
          method: "PATCH",
          body: JSON.stringify(body),
        },
      ),
    onSuccess: (_, v) => {
      void qc.invalidateQueries({ queryKey: qk.all });
      void qc.invalidateQueries({ queryKey: qk.detail(v.id) });
    },
  });
}

export function useDeleteDashboard(): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) =>
      apiFetch<void>(`/v1/monitoring/dashboards/${encodeURIComponent(id)}`, {
        method: "DELETE",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.all }),
  });
}

export function useCreatePanel(): UseMutationResult<
  Panel,
  Error,
  { dashboardId: string; body: PanelCreateRequest }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, body }) =>
      apiFetch<Panel>(
        `/v1/monitoring/dashboards/${encodeURIComponent(dashboardId)}/panels`,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),
    onSuccess: (_, v) =>
      qc.invalidateQueries({ queryKey: qk.detail(v.dashboardId) }),
  });
}

export function useUpdatePanel(): UseMutationResult<
  Panel,
  Error,
  { dashboardId: string; panelId: string; body: PanelUpdateRequest }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, panelId, body }) =>
      apiFetch<Panel>(
        `/v1/monitoring/dashboards/${encodeURIComponent(
          dashboardId,
        )}/panels/${encodeURIComponent(panelId)}`,
        {
          method: "PATCH",
          body: JSON.stringify(body),
        },
      ),
    onSuccess: (_, v) =>
      qc.invalidateQueries({ queryKey: qk.detail(v.dashboardId) }),
  });
}

export function useDeletePanel(): UseMutationResult<
  void,
  Error,
  { dashboardId: string; panelId: string }
> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, panelId }) =>
      apiFetch<void>(
        `/v1/monitoring/dashboards/${encodeURIComponent(
          dashboardId,
        )}/panels/${encodeURIComponent(panelId)}`,
        { method: "DELETE" },
      ),
    onSuccess: (_, v) =>
      qc.invalidateQueries({ queryKey: qk.detail(v.dashboardId) }),
  });
}
