import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { CapabilityCatalog, RoleGrants } from "@/types/api";

export const capabilityKeys = {
  catalog: ["capabilities", "catalog"] as const,
  roleGrants: (roleId: string) => ["capabilities", "role-grants", roleId] as const,
};

export function useCapabilityCatalog() {
  return useQuery<CapabilityCatalog>({
    queryKey: capabilityKeys.catalog,
    queryFn: () => apiFetch<CapabilityCatalog>("/v1/capabilities"),
    staleTime: 60_000,
  });
}

export function useRoleGrants(roleId: string | undefined) {
  return useQuery<RoleGrants>({
    queryKey: roleId ? capabilityKeys.roleGrants(roleId) : [],
    enabled: !!roleId,
    queryFn: () => apiFetch<RoleGrants>(`/v1/roles/${roleId}/grants`),
  });
}

export function useGrantPermissions(roleId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (permissionCodes: string[]) =>
      apiFetch<RoleGrants>(`/v1/roles/${roleId}/grants`, {
        method: "POST",
        body: JSON.stringify({ permission_codes: permissionCodes }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: capabilityKeys.roleGrants(roleId) });
    },
  });
}

export function useRevokePermission(roleId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (permissionCode: string) =>
      apiFetch<void>(
        `/v1/roles/${roleId}/grants/${encodeURIComponent(permissionCode)}`,
        { method: "DELETE" },
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: capabilityKeys.roleGrants(roleId) });
    },
  });
}
