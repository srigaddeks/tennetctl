"use client";

import { useMemo, useState } from "react";

import { Button, Skeleton } from "@/components/ui";
import { useToast } from "@/components/toast";
import {
  useCapabilityCatalog,
  useGrantPermissions,
  useRevokePermission,
  useRoleGrants,
} from "@/features/capabilities/hooks/use-capabilities";
import type { Capability } from "@/types/api";

type Props = {
  roleId: string;
  roleCode: string | null;
  readOnly?: boolean;
};

export function CapabilityGrid({ roleId, roleCode, readOnly }: Props) {
  const { toast } = useToast();
  const { data: catalog, isLoading: catalogLoading } = useCapabilityCatalog();
  const { data: grants, isLoading: grantsLoading } = useRoleGrants(roleId);
  const grant = useGrantPermissions(roleId);
  const revoke = useRevokePermission(roleId);

  const [pending, setPending] = useState<Set<string>>(new Set());

  const grantedSet = useMemo(
    () => new Set((grants?.grants ?? []).map((g) => g.permission_code)),
    [grants],
  );

  const byCategory = useMemo(() => {
    const result: Record<string, Capability[]> = {};
    if (!catalog) return result;
    for (const cap of catalog.capabilities) {
      (result[cap.category_code] ??= []).push(cap);
    }
    return result;
  }, [catalog]);

  if (catalogLoading || grantsLoading) {
    return <Skeleton className="h-48 w-full" />;
  }
  if (!catalog) return null;

  async function toggle(permissionCode: string, granted: boolean) {
    if (readOnly) return;
    setPending((prev) => new Set(prev).add(permissionCode));
    try {
      if (granted) {
        await revoke.mutateAsync(permissionCode);
        toast(`Revoked ${permissionCode}`, "success");
      } else {
        await grant.mutateAsync([permissionCode]);
        toast(`Granted ${permissionCode}`, "success");
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    } finally {
      setPending((prev) => {
        const next = new Set(prev);
        next.delete(permissionCode);
        return next;
      });
    }
  }

  async function toggleRow(cap: Capability) {
    if (readOnly) return;
    const codes = cap.permissions.map((p) => p.code);
    const allGranted = codes.every((c) => grantedSet.has(c));
    try {
      if (allGranted) {
        await Promise.all(codes.map((c) => revoke.mutateAsync(c)));
        toast(`Revoked all on ${cap.code}`, "success");
      } else {
        const toGrant = codes.filter((c) => !grantedSet.has(c));
        await grant.mutateAsync(toGrant);
        toast(`Granted all on ${cap.code}`, "success");
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm text-zinc-500 dark:text-zinc-400">
            Role <span className="font-mono text-zinc-900 dark:text-zinc-100">{roleCode ?? roleId.slice(0, 8)}</span> grants
          </div>
          <div className="text-2xl font-semibold">
            {grantedSet.size} / {catalog.capabilities.reduce((a, c) => a + c.permissions.length, 0)}
            <span className="ml-2 text-sm font-normal text-zinc-500">permissions</span>
          </div>
        </div>
      </div>

      {catalog.categories.map((cat) => {
        const caps = byCategory[cat.code] ?? [];
        if (caps.length === 0) return null;
        const catActions = catalog.actions;
        const catGrantedCount = caps.reduce(
          (acc, c) => acc + c.permissions.filter((p) => grantedSet.has(p.code)).length,
          0,
        );
        const catTotal = caps.reduce((a, c) => a + c.permissions.length, 0);

        return (
          <div
            key={cat.code}
            className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800"
          >
            <div className="flex items-center justify-between border-b border-zinc-200 bg-zinc-50 px-4 py-2 dark:border-zinc-800 dark:bg-zinc-900/50">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold uppercase tracking-wide text-zinc-700 dark:text-zinc-300">
                  {cat.label}
                </span>
                <span className="text-xs text-zinc-500">
                  {catGrantedCount} / {catTotal} granted
                </span>
              </div>
              <span className="text-xs text-zinc-400">{cat.description}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-white text-xs uppercase text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
                  <tr>
                    <th className="sticky left-0 z-10 bg-white px-4 py-2 text-left font-medium dark:bg-zinc-950">
                      Capability
                    </th>
                    {catActions.map((a) => (
                      <th key={a.code} className="px-2 py-2 text-center font-medium">
                        {a.label}
                      </th>
                    ))}
                    {!readOnly && <th className="px-4 py-2 text-right font-medium">Row</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                  {caps.map((cap) => {
                    const codes = cap.permissions.map((p) => p.code);
                    const rowGranted = codes.every((c) => grantedSet.has(c));
                    const rowSome = codes.some((c) => grantedSet.has(c));
                    return (
                      <tr
                        key={cap.code}
                        className="hover:bg-zinc-50 dark:hover:bg-zinc-900/30"
                        data-testid={`capability-row-${cap.code}`}
                      >
                        <td className="sticky left-0 z-10 bg-white px-4 py-2 dark:bg-zinc-950">
                          <div className="flex flex-col gap-0.5">
                            <span className="font-medium text-zinc-900 dark:text-zinc-100">
                              {cap.name}
                            </span>
                            <span className="font-mono text-[10px] text-zinc-400">
                              {cap.code} · {cap.feature_scope} · {cap.access_mode}
                            </span>
                          </div>
                        </td>
                        {catActions.map((a) => {
                          const perm = cap.permissions.find(
                            (p) => p.action_code === a.code,
                          );
                          if (!perm) {
                            return (
                              <td
                                key={a.code}
                                className="px-2 py-2 text-center text-zinc-300 dark:text-zinc-700"
                              >
                                —
                              </td>
                            );
                          }
                          const isGranted = grantedSet.has(perm.code);
                          const isPending = pending.has(perm.code);
                          return (
                            <td key={a.code} className="px-2 py-2 text-center">
                              <input
                                type="checkbox"
                                checked={isGranted}
                                disabled={readOnly || isPending}
                                onChange={() => toggle(perm.code, isGranted)}
                                className="h-4 w-4 cursor-pointer rounded border-zinc-300 text-emerald-600 focus:ring-emerald-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900"
                                aria-label={`Toggle ${perm.code}`}
                                data-testid={`capability-checkbox-${perm.code}`}
                                title={perm.description ?? perm.code}
                              />
                            </td>
                          );
                        })}
                        {!readOnly && (
                          <td className="px-4 py-2 text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleRow(cap)}
                              data-testid={`capability-row-toggle-${cap.code}`}
                            >
                              {rowGranted ? "Clear row" : rowSome ? "Complete row" : "Grant all"}
                            </Button>
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}
