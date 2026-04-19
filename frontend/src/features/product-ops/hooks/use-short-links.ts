import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  CreateShortLinkBody,
  ShortLink,
  ShortLinkListResponse,
} from "@/types/api";

export function useShortLinks(workspaceId: string | undefined, opts: { includeDeleted?: boolean } = {}) {
  const params = buildQuery({
    workspace_id: workspaceId,
    include_deleted: opts.includeDeleted ?? false,
  });
  return useQuery({
    queryKey: ["short-links", workspaceId, opts.includeDeleted],
    queryFn: () => apiFetch<ShortLinkListResponse>(`/v1/short-links?${params}`),
    enabled: Boolean(workspaceId),
  });
}

export function useCreateShortLink() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateShortLinkBody) =>
      apiFetch<ShortLink>("/v1/short-links", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["short-links"] });
    },
  });
}

export function useDeleteShortLink() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/short-links/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["short-links"] });
    },
  });
}
