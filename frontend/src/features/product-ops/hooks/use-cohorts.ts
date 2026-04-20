import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  Cohort,
  CohortListResponse,
  CohortRefreshResponse,
  CreateCohortBody,
} from "@/types/api";

export function useCohorts(workspaceId: string | undefined, kind?: "dynamic" | "static") {
  const params = buildQuery({ workspace_id: workspaceId, kind });
  return useQuery({
    queryKey: ["cohorts", workspaceId, kind],
    queryFn: () => apiFetch<CohortListResponse>(`/v1/cohorts?${params}`),
    enabled: Boolean(workspaceId),
  });
}

export function useCreateCohort() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateCohortBody) =>
      apiFetch<Cohort>("/v1/cohorts", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["cohorts"] });
    },
  });
}

export function useRefreshCohort() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<CohortRefreshResponse>(`/v1/cohorts/${id}/refresh`, { method: "POST" }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["cohorts"] });
    },
  });
}

export function useDeleteCohort() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/v1/cohorts/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["cohorts"] });
    },
  });
}
