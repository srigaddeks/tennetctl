"use client";

import { useState } from "react";

import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  Skeleton,
} from "@/components/ui";
import {
  useFlagPermissions,
  useGrantPermission,
  useRevokePermission,
} from "@/features/featureflags/hooks/use-permissions";
import { useRoles } from "@/features/iam-roles/hooks/use-roles";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Flag, FlagPermission, RoleFlagPermission } from "@/types/api";

const PERMS: { code: FlagPermission; rank: number; description: string }[] = [
  { code: "view", rank: 1, description: "See the flag" },
  { code: "toggle", rank: 2, description: "Enable/disable per env" },
  { code: "write", rank: 3, description: "Edit rules, overrides, default" },
  { code: "admin", rank: 4, description: "Manage permissions + delete" },
];

export function FlagPermissionsPanel({ flag }: { flag: Flag }) {
  const { toast } = useToast();
  const { data: grants, isLoading } = useFlagPermissions(flag.id);
  const { data: roles } = useRoles({ limit: 500 });
  const grant = useGrantPermission();
  const revoke = useRevokePermission();
  const [pendingCell, setPendingCell] = useState<string | null>(null);

  if (isLoading) return <Skeleton className="h-12 w-full" />;
  if (!roles || roles.items.length === 0) {
    return (
      <EmptyState
        title="No roles yet"
        description="Create roles under IAM → Roles before granting per-flag permissions."
      />
    );
  }

  const grantMap = new Map<string, RoleFlagPermission>();
  for (const g of grants?.items ?? []) {
    grantMap.set(`${g.role_id}:${g.permission}`, g);
  }

  async function onToggle(
    roleId: string,
    perm: FlagPermission,
    grantId: string | undefined
  ) {
    const cell = `${roleId}:${perm}`;
    setPendingCell(cell);
    try {
      if (grantId) {
        await revoke.mutateAsync(grantId);
        toast(`Revoked ${perm}`, "success");
      } else {
        await grant.mutateAsync({
          role_id: roleId,
          flag_id: flag.id,
          permission: perm,
        });
        toast(`Granted ${perm}`, "success");
      }
    } catch (err) {
      const m = err instanceof ApiClientError ? err.message : String(err);
      toast(m, "error");
    } finally {
      setPendingCell(null);
    }
  }

  return (
    <>
      <div className="mb-4 max-w-3xl rounded-lg border border-zinc-200 bg-white p-4 text-xs text-zinc-600 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-400">
        <div className="mb-2 font-medium text-zinc-900 dark:text-zinc-50">
          Permission hierarchy
        </div>
        <div className="grid grid-cols-4 gap-2">
          {PERMS.map((p) => (
            <div key={p.code} className="rounded-md bg-zinc-50 p-2 dark:bg-zinc-900">
              <div className="mb-0.5 flex items-center gap-1.5">
                <Badge tone="zinc">#{p.rank}</Badge>
                <span className="font-mono text-[11px] font-medium">{p.code}</span>
              </div>
              <p className="text-[10px] leading-snug">{p.description}</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[11px]">
          A role with a higher-rank permission implicitly covers all lower-rank capabilities. A
          global IAM scope <code>flags:admin:all</code> bypasses this matrix entirely.
        </p>
      </div>
      <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <table className="w-full text-sm">
          <thead className="border-b border-zinc-200 bg-zinc-50 text-left text-xs font-medium uppercase tracking-wider text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
            <tr>
              <th className="px-4 py-2 font-medium">Role</th>
              {PERMS.map((p) => (
                <th key={p.code} className="px-4 py-2 text-center font-medium">
                  {p.code}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-900">
            {roles.items.map((r) => (
              <tr key={r.id}>
                <td className="px-4 py-2.5">
                  <div className="flex flex-col">
                    <span className="font-mono text-xs">{r.code ?? "—"}</span>
                    <span className="text-[10px] text-zinc-500">
                      {r.label ?? ""}{" "}
                      {!r.org_id && <Badge tone="amber">global</Badge>}
                    </span>
                  </div>
                </td>
                {PERMS.map((p) => {
                  const g = grantMap.get(`${r.id}:${p.code}`);
                  const cell = `${r.id}:${p.code}`;
                  const isLoadingCell = pendingCell === cell;
                  return (
                    <td key={p.code} className="px-4 py-2.5 text-center">
                      <button
                        onClick={() => onToggle(r.id, p.code, g?.id)}
                        disabled={isLoadingCell}
                        data-testid={`perm-${r.code ?? r.id}-${p.code}`}
                        className={cn(
                          "mx-auto flex h-7 w-7 items-center justify-center rounded-full border transition",
                          g
                            ? "border-emerald-400 bg-emerald-100 text-emerald-700 hover:border-emerald-600 dark:border-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                            : "border-zinc-200 bg-white text-zinc-400 hover:border-zinc-900 hover:text-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-500 dark:hover:border-zinc-100 dark:hover:text-zinc-50",
                          isLoadingCell && "opacity-50"
                        )}
                      >
                        {g ? "✓" : ""}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
