import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { ApiSuccess, CapabilityCatalog, RoleGrants } from "@/types/api";

const BASE = "/api/v1";

export const capabilityKeys = {
  catalog: ["capabilities", "catalog"] as const,
  roleGrants: (roleId: string) => ["capabilities", "role-grants", roleId] as const,
};

export function useCapabilityCatalog() {
  return useQuery<CapabilityCatalog>({
    queryKey: capabilityKeys.catalog,
    queryFn: async () => {
      const res = await fetch(`${BASE}/capabilities`);
      const data: ApiSuccess<CapabilityCatalog> = await res.json();
      if (!data.ok) throw new Error((data as unknown as { error: { message: string } }).error?.message);
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useRoleGrants(roleId: string | undefined) {
  return useQuery<RoleGrants>({
    queryKey: roleId ? capabilityKeys.roleGrants(roleId) : [],
    enabled: !!roleId,
    queryFn: async () => {
      const res = await fetch(`${BASE}/roles/${roleId}/grants`);
      const data: ApiSuccess<RoleGrants> = await res.json();
      if (!data.ok) throw new Error((data as unknown as { error: { message: string } }).error?.message);
      return data.data;
    },
  });
}

export function useGrantPermissions(roleId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (permissionCodes: string[]) => {
      const res = await fetch(`${BASE}/roles/${roleId}/grants`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ permission_codes: permissionCodes }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message ?? "Failed to grant");
      return data.data as RoleGrants;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: capabilityKeys.roleGrants(roleId) });
    },
  });
}

export function useRevokePermission(roleId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (permissionCode: string) => {
      const res = await fetch(
        `${BASE}/roles/${roleId}/grants/${encodeURIComponent(permissionCode)}`,
        { method: "DELETE" },
      );
      if (res.status !== 204) {
        const data = await res.json();
        throw new Error(data.error?.message ?? "Failed to revoke");
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: capabilityKeys.roleGrants(roleId) });
    },
  });
}
