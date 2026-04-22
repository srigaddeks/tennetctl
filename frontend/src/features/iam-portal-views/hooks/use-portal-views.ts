import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { PortalView, RoleViewAssignment } from "@/types/api";

const BASE = "/v1/iam";

// ─── Query keys ────────────────────────────────────────────────────────────────

export const portalViewsKeys = {
  all: ["iam", "portal-views"] as const,
  roleViews: (roleId: string) => ["iam", "portal-views", "role", roleId] as const,
  myViews: (orgId: string) => ["iam", "my-views", orgId] as const,
};

// ─── Queries ───────────────────────────────────────────────────────────────────

/** List all non-deprecated portal views from the global catalog. */
export function usePortalViews() {
  return useQuery<PortalView[]>({
    queryKey: portalViewsKeys.all,
    queryFn: () => apiFetch<PortalView[]>(`${BASE}/portal-views`),
  });
}

/** List views granted to a specific role. */
export function useRoleViews(roleId: string | undefined) {
  return useQuery<RoleViewAssignment[]>({
    queryKey: roleId ? portalViewsKeys.roleViews(roleId) : [],
    enabled: !!roleId,
    queryFn: () => apiFetch<RoleViewAssignment[]>(`${BASE}/roles/${roleId}/views`),
  });
}

/** Resolve the current user's granted portal views. */
export function useMyViews(orgId: string | undefined) {
  return useQuery<PortalView[]>({
    queryKey: orgId ? portalViewsKeys.myViews(orgId) : [],
    enabled: !!orgId,
    queryFn: () =>
      apiFetch<PortalView[]>(`${BASE}/my-views`, {
        headers: orgId ? { "x-org-id": orgId } : {},
      }),
  });
}

// ─── Mutations ─────────────────────────────────────────────────────────────────

/** Attach a portal view to a role. */
export function useAttachView(roleId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (viewId: number) =>
      apiFetch<RoleViewAssignment>(`${BASE}/roles/${roleId}/views`, {
        method: "POST",
        body: JSON.stringify({ view_id: viewId }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: portalViewsKeys.roleViews(roleId) });
    },
  });
}

/** Detach a portal view from a role. */
export function useDetachView(roleId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (viewId: number) =>
      apiFetch<void>(`${BASE}/roles/${roleId}/views/${viewId}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: portalViewsKeys.roleViews(roleId) });
    },
  });
}
