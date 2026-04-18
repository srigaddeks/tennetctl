import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ApiSuccess, IpAllowlistCreateBody, IpAllowlistEntry } from "@/types/api";

const BASE = "/api/v1/iam/ip-allowlist";
const QK = ["iam", "ip-allowlist"] as const;

export function useIpAllowlist(orgId: string | undefined) {
  return useQuery<IpAllowlistEntry[]>({
    queryKey: [...QK, orgId],
    enabled: !!orgId,
    queryFn: async () => {
      const res = await fetch(BASE, { headers: { "x-org-id": orgId! } });
      const data: ApiSuccess<IpAllowlistEntry[]> = await res.json();
      if (!data.ok) throw new Error((data as unknown as { error: { message: string } }).error?.message);
      return data.data;
    },
  });
}

export function useAddIpAllowlistEntry(orgId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: IpAllowlistCreateBody) => {
      const res = await fetch(BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-org-id": orgId! },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as IpAllowlistEntry;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}

export function useRemoveIpAllowlistEntry(orgId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (entryId: string) => {
      const res = await fetch(`${BASE}/${entryId}`, {
        method: "DELETE",
        headers: { "x-org-id": orgId! },
      });
      if (!res.ok && res.status !== 204) {
        const data = await res.json();
        throw new Error(data.error?.message ?? "Failed to remove entry");
      }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}
