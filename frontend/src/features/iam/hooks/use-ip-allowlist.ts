import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { IpAllowlistCreateBody, IpAllowlistEntry } from "@/types/api";

const BASE = "/v1/iam/ip-allowlist";
const QK = ["iam", "ip-allowlist"] as const;

export function useIpAllowlist(orgId: string | undefined) {
  return useQuery<IpAllowlistEntry[]>({
    queryKey: [...QK, orgId],
    enabled: !!orgId,
    queryFn: () =>
      apiFetch<IpAllowlistEntry[]>(BASE, {
        headers: { "x-org-id": orgId! },
      }),
  });
}

export function useAddIpAllowlistEntry(orgId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: IpAllowlistCreateBody) =>
      apiFetch<IpAllowlistEntry>(BASE, {
        method: "POST",
        headers: { "x-org-id": orgId! },
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}

export function useRemoveIpAllowlistEntry(orgId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (entryId: string) =>
      apiFetch<void>(`${BASE}/${entryId}`, {
        method: "DELETE",
        headers: { "x-org-id": orgId! },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  });
}
