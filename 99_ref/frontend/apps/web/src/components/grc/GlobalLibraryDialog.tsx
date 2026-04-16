"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui";
import {
  Globe,
  Zap,
  Shield,
  Download,
  CheckCircle2,
} from "lucide-react";
import {
  listGlobalControlTests,
  listDeployedGlobalTestIds,
  deployGlobalControlTest,
} from "@/lib/api/sandbox";
import type { GlobalControlTestResponse } from "@/lib/api/sandbox";
import { ConnectorIcon, getConnectorLabel } from "@/components/common/ConnectorIcon";

interface GlobalLibraryDialogProps {
  open: boolean;
  orgId: string;
  workspaceId: string | null;
  connectorInstanceId?: string | null;
  lockedConnectorType?: string | null;
  onDeployed: () => void;
  onClose: () => void;
}

export function GlobalLibraryDialog({
  open,
  orgId,
  workspaceId,
  connectorInstanceId,
  lockedConnectorType,
  onDeployed,
  onClose,
}: GlobalLibraryDialogProps) {
  const [tests, setTests] = useState<GlobalControlTestResponse[]>([]);
  const [deployedIds, setDeployedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState(lockedConnectorType || "");
  const [filterCategory, setFilterCategory] = useState("");
  const [deploying, setDeploying] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [testsRes, deployedRes] = await Promise.all([
        listGlobalControlTests({
          connector_type_code: filterType || undefined,
          category: filterCategory || undefined,
          publish_status: "published",
          limit: 200,
        }),
        listDeployedGlobalTestIds(orgId, workspaceId ?? undefined),
      ]);
      setTests(testsRes.items);
      setDeployedIds(new Set(deployedRes));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [orgId, workspaceId, filterType, filterCategory]);

  useEffect(() => {
    if (open) {
      loadData();
    }
  }, [open, loadData]);

  // Sync filter type with lockedConnectorType if it changes
  useEffect(() => {
    if (lockedConnectorType) {
      setFilterType(lockedConnectorType);
    }
  }, [lockedConnectorType]);

  const connectorTypes = useMemo(
    () => [...new Set(tests.map((t) => t.connector_type_code))].sort(),
    [tests]
  );
  const categories = useMemo(
    () => [...new Set(tests.filter((t) => t.category).map((t) => t.category!))].sort(),
    [tests]
  );

  const notDeployed = tests.filter((t) => !deployedIds.has(t.id));
  const deployed = tests.filter((t) => deployedIds.has(t.id));

  async function handleDeploy(testId: string) {
    if (!workspaceId) return;
    setDeploying(testId);
    try {
      await deployGlobalControlTest(testId, {
        org_id: orgId,
        workspace_id: workspaceId,
        connector_instance_id: connectorInstanceId || undefined,
      });
      setDeployedIds((prev) => new Set([...prev, testId]));
      setSuccessMsg("Deployed successfully");
      setTimeout(() => setSuccessMsg(null), 3000);
      onDeployed();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Deploy failed");
    } finally {
      setDeploying(null);
    }
  }

  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="sm:max-w-3xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-500/10 p-2.5">
              <Globe className="h-5 w-5 text-emerald-500" />
            </div>
            <div>
              <DialogTitle>Global Control Test Library</DialogTitle>
              <DialogDescription>
                Deploy pre-built control tests to your workspace. Tests include signals, threat types, and policies.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Filters */}
        <div className="flex items-center gap-2 pt-2">
          {!lockedConnectorType && (
            <select
              className="h-8 rounded-md border border-border bg-background px-2.5 text-sm"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="">All Connector Types</option>
              {connectorTypes.map((t) => (
                <option key={t} value={t}>
                  {getConnectorLabel(t)}
                </option>
              ))}
            </select>
          )}
          {lockedConnectorType && (
             <div className="flex items-center gap-1.5 h-8 px-2.5 rounded-md border border-border bg-muted/30 text-xs font-semibold text-muted-foreground mr-2">
                <ConnectorIcon typeCode={lockedConnectorType} className="h-3.5 w-3.5" />
                {getConnectorLabel(lockedConnectorType)}
             </div>
          )}
          
          <select
            className="h-8 rounded-md border border-border bg-background px-2.5 text-sm"
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <div className="flex-1" />
          <span className="text-[11px] text-muted-foreground">
            {notDeployed.length} available · {deployed.length} deployed
          </span>
        </div>

        {successMsg && (
          <div className="rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-1.5 text-xs text-green-600">
            {successMsg}
          </div>
        )}
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs text-red-500">
            {error}
          </div>
        )}

        {/* List */}
        <div className="flex-1 overflow-y-auto space-y-1.5 min-h-0 pr-1">
          {loading ? (
            <div className="space-y-2 py-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-16 rounded-lg bg-muted/30 animate-pulse"
                />
              ))}
            </div>
          ) : tests.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Globe className="h-8 w-8 text-muted-foreground/30 mb-2" />
              <p className="text-sm text-muted-foreground">
                No control tests in the global library.
              </p>
            </div>
          ) : (
            <>
              {/* Not deployed section */}
              {notDeployed.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground px-1 pt-1">
                    Available to Deploy ({notDeployed.length})
                  </p>
                  {notDeployed.map((t) => (
                    <div
                      key={t.id}
                      className="flex items-center gap-3 rounded-lg border border-l-[3px] border-l-emerald-500 bg-card px-3 py-2.5"
                    >
                      <div className="h-8 w-8 rounded-md bg-muted/50 flex items-center justify-center shrink-0">
                        <ConnectorIcon
                          typeCode={t.connector_type_code}
                          className="h-4 w-4 text-muted-foreground"
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold truncate">
                            {t.name || t.global_code}
                          </span>
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono">
                            {t.connector_type_code}
                          </span>
                          {t.category && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded border border-border text-muted-foreground">
                              {t.category}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5 text-[10px] text-muted-foreground">
                          <span className="flex items-center gap-0.5">
                            <Zap className="h-2.5 w-2.5" />
                            {t.signal_count} signal
                            {t.signal_count !== 1 ? "s" : ""}
                          </span>
                          {t.bundle.threat_type && (
                            <span className="flex items-center gap-0.5">
                              <Shield className="h-2.5 w-2.5" />
                              {t.bundle.threat_type.severity_code}
                            </span>
                          )}
                          {t.description && (
                            <span className="truncate max-w-[200px]">
                              {t.description}
                            </span>
                          )}
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1 shrink-0 text-emerald-600 border-emerald-500/30 hover:bg-emerald-500/10 h-7 text-xs"
                        onClick={() => handleDeploy(t.id)}
                        disabled={deploying === t.id || !workspaceId}
                      >
                        {deploying === t.id ? (
                          <span className="h-3 w-3 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
                        ) : (
                          <Download className="h-3 w-3" />
                        )}
                        Deploy
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {/* Deployed section */}
              {deployed.length > 0 && (
                <div className="space-y-1.5 pt-2">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground px-1">
                    Already Deployed ({deployed.length})
                  </p>
                  {deployed.map((t) => (
                    <div
                      key={t.id}
                      className="flex items-center gap-3 rounded-lg border border-l-[3px] border-l-muted bg-card/50 px-3 py-2.5 opacity-70"
                    >
                      <div className="h-8 w-8 rounded-md bg-muted/50 flex items-center justify-center shrink-0">
                        <ConnectorIcon
                          typeCode={t.connector_type_code}
                          className="h-4 w-4 text-muted-foreground"
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold truncate">
                            {t.name || t.global_code}
                          </span>
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono">
                            {t.connector_type_code}
                          </span>
                        </div>
                        <span className="text-[10px] text-muted-foreground">
                          {t.description}
                        </span>
                      </div>
                      <span className="flex items-center gap-1 text-xs text-green-500 shrink-0">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Deployed
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <DialogFooter className="pt-2">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
