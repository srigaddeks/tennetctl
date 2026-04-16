"use client";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Input,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Label,
  Separator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui";
import {
  Activity,
  AlertCircle,
  Boxes,
  CheckCircle2,
  ChevronRight,
  Pencil,
  Plus,
  Search,
  RefreshCw,
  ExternalLink,
  ArrowRight,
  Globe,
  Loader2,
  X,
  Plug,
} from "lucide-react";
import {
  listConnectors,
  testConnector,
  listConnectorCategories,
  listConnectorTypes,
  listAssetVersions,
  getConnectorConfigSchema,
  preflightTestConnector,
  createConnector,
  listAssets,
} from "@/lib/api/sandbox";
import type {
  ConnectorInstanceResponse,
  DimensionResponse,
  AssetVersionResponse,
  ConnectorTestResult,
  ConnectorConfigField,
  ConnectorConfigSchemaResponse,
  AssetResponse,
} from "@/lib/api/sandbox";
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext";
import { CreateConnectorDialog } from "@/components/connectors/CreateConnectorDialog";
import { EditConnectorDialog } from "@/components/connectors/EditConnectorDialog";
import { ConnectorIcon, getConnectorLabel } from "@/components/common/ConnectorIcon";
import { GlobalLibraryDialog } from "@/components/grc/GlobalLibraryDialog";

// ── Types ─────────────────────────────────────────────────────────────────────

type ToastMsg = { id: number; message: string; type: "success" | "error" };

interface CatalogIntegration extends DimensionResponse {
  categoryCode: string;
  categoryName: string;
}

// ── Toast ─────────────────────────────────────────────────────────────────────

function ToastContainer({
  toasts,
  onDismiss,
}: {
  toasts: ToastMsg[];
  onDismiss: (id: number) => void;
}) {
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-80">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg border text-sm font-medium animate-in slide-in-from-bottom-2 ${t.type === "success"
            ? "bg-green-50 border-green-500/30 text-green-800 dark:bg-green-950 dark:border-green-800 dark:text-green-200"
            : "bg-red-50 border-red-500/30 text-red-800 dark:bg-red-950 dark:border-red-800 dark:text-red-200"
            }`}
        >
          {t.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0 text-green-600" />
          ) : (
            <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
          )}
          <span className="flex-1">{t.message}</span>
          <button
            onClick={() => onDismiss(t.id)}
            className="shrink-0 opacity-60 hover:opacity-100"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}

// ── Connector Type Icon ───────────────────────────────────────────────────────


function connectorPriority(typeCode: string): number {
  const lower = typeCode.toLowerCase();
  if (lower.includes("github")) return 0;
  if (lower.includes("aws")) return 1;
  if (lower.includes("azure")) return 2;
  if (lower.includes("gcp")) return 3;
  return 10;
}

function sortConnectorTypes(types: DimensionResponse[]): DimensionResponse[] {
  return [...types].sort((a, b) => {
    const priorityDiff = connectorPriority(a.code) - connectorPriority(b.code);
    if (priorityDiff !== 0) return priorityDiff;
    return a.name.localeCompare(b.name);
  });
}

function sortConnectedIntegrations(
  connectors: ConnectorInstanceResponse[]
): ConnectorInstanceResponse[] {
  return [...connectors].sort((a, b) => {
    const priorityDiff =
      connectorPriority(a.connector_type_code) -
      connectorPriority(b.connector_type_code);
    if (priorityDiff !== 0) return priorityDiff;
    return (a.name || a.instance_code).localeCompare(b.name || b.instance_code);
  });
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ── Health Status Badge ───────────────────────────────────────────────────────

function HealthBadge({ status }: { status: string }) {
  const lower = status.toLowerCase();
  if (lower === "healthy" || lower === "connected") {
    return (
      <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20 text-[10px] font-semibold tracking-wide uppercase px-2 py-0">
        Connected
      </Badge>
    );
  }
  if (lower === "degraded" || lower === "warning") {
    return (
      <Badge className="bg-primary/10 text-primary border-primary/20 dark:bg-primary/10 dark:text-primary dark:border-primary/20 text-[10px] font-semibold tracking-wide uppercase px-2 py-0">
        Degraded
      </Badge>
    );
  }
  if (lower === "unhealthy" || lower === "error" || lower === "failed") {
    return (
      <Badge className="bg-rose-500/10 text-rose-600 border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20 text-[10px] font-semibold tracking-wide uppercase px-2 py-0">
        Error
      </Badge>
    );
  }
  if (lower === "unknown" || lower === "pending") {
    return (
      <Badge className="bg-muted text-muted-foreground border-border text-[10px] font-semibold tracking-wide uppercase px-2 py-0">
        Unknown
      </Badge>
    );
  }
  return (
    <Badge
      variant="outline"
      className="text-[10px] uppercase font-semibold px-2 py-0"
    >
      {status}
    </Badge>
  );
}

// ── Helper Components ─────────────────────────────────────────────────────────

function assetPrimaryLabel(asset: AssetResponse): string {
  const props = asset.properties ?? {};
  return (
    props.name ||
    props.display_name ||
    props.hostname ||
    props.resource_name ||
    asset.asset_external_id
  );
}

function assetSecondaryLabel(asset: AssetResponse): string {
  const props = asset.properties ?? {};
  return (
    props.account_name ||
    props.account_id ||
    props.region ||
    props.namespace ||
    props.repository ||
    asset.asset_type_code
  );
}

function formatStatus(statusCode: string): string {
  return statusCode
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function assetScopeLabel(
  asset: AssetResponse
): "Cloud" | "Identity" | "Endpoints" | "Other" {
  const provider = asset.provider_code.toLowerCase();
  const type = asset.asset_type_code.toLowerCase();

  if (
    provider.includes("okta") ||
    provider.includes("ad") ||
    provider.includes("entra") ||
    type.includes("identity")
  ) {
    return "Identity";
  }
  if (
    type.includes("endpoint") ||
    type.includes("server") ||
    type.includes("host") ||
    type.includes("device")
  ) {
    return "Endpoints";
  }
  if (
    provider.includes("aws") ||
    provider.includes("azure") ||
    provider.includes("gcp") ||
    provider.includes("cloud")
  ) {
    return "Cloud";
  }
  return "Other";
}

function assetStatusTone(statusCode: string): string {
  const lower = statusCode.toLowerCase();
  if (
    lower.includes("active") ||
    lower.includes("monitored") ||
    lower.includes("healthy")
  ) {
    return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  }
  if (
    lower.includes("partial") ||
    lower.includes("stale") ||
    lower.includes("degraded")
  ) {
    return "bg-amber-500/10 text-amber-300 border-amber-500/20";
  }
  return "bg-muted text-muted-foreground border-border";
}

function assetTypeLabel(asset: AssetResponse): string {
  return asset.asset_type_code
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function isLiveConnector(connector: ConnectorInstanceResponse): boolean {
  const status = (connector.health_status || "").toLowerCase();
  return (
    !connector.is_draft && (status === "healthy" || status === "connected")
  );
}

function isMonitoredAssetStatus(statusCode: string): boolean {
  const lower = statusCode.toLowerCase();
  return (
    lower.includes("active") ||
    lower.includes("monitored") ||
    lower.includes("healthy") ||
    lower.includes("connected")
  );
}

function isCriticalAsset(asset: AssetResponse): boolean {
  const props = asset.properties ?? {};
  const haystack = [
    asset.asset_type_code,
    asset.asset_external_id,
    props.name,
    props.display_name,
    props.hostname,
    props.resource_name,
    props.account_name,
    props.account_id,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return [
    "admin",
    "critical",
    "prod",
    "production",
    "database",
    "storage",
    "bucket",
    "repo",
    "repository",
    "secret",
    "key",
    "org",
    "cluster",
    "server",
    "vault",
  ].some((term) => haystack.includes(term));
}

function AssetOverviewCard({
  label,
  value,
  accentClass,
  borderCls,
  detail,
  description,
}: {
  label: string;
  value: string;
  accentClass: string;
  borderCls: string;
  detail?: string;
  description: string;
}) {
  return (
    <Card
      className={`rounded-xl border bg-card border-l-[3px] ${borderCls} shadow-sm`}
    >
      <CardContent className="px-5 py-5">
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
          {label}
        </p>
        <div className="mt-4 flex items-end gap-2">
          <span
            className={`text-4xl font-bold tabular-nums leading-none tracking-tight ${accentClass}`}
          >
            {value}
          </span>
          {detail && (
            <span className="pb-0.5 text-lg font-medium text-muted-foreground">
              {detail}
            </span>
          )}
        </div>
        <p className="mt-3 text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

function AssetCard({
  connector,
  onEdit,
  onTest,
  onOpenLibrary,
  isTesting,
}: {
  connector: ConnectorInstanceResponse;
  onEdit: () => void;
  onTest: () => void;
  onOpenLibrary: () => void;
  isTesting: boolean;
}) {
  const displayName = connector.name || connector.instance_code;
  const typeName =
    connector.connector_type_name ||
    getConnectorLabel(connector.connector_type_code);
  const connectedDate = connector.created_at
    ? new Date(connector.created_at).toLocaleDateString("en-US", {
      month: "short",
      year: "numeric",
    })
    : null;

  const accentBorder = connector.is_draft
    ? "border-muted"
    : "border-primary/50";
  const glowShadow =
    connector.health_status === "healthy" ? "shadow-primary/5" : "";

  return (
    <div
      className={`group relative overflow-hidden transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 hover:border-primary/50 border-l-4 ${accentBorder} bg-card/60 backdrop-blur-xl rounded-xl border border-border/50 ${glowShadow} shadow-lg`}
    >
      <div className="px-2 py-4 sm:p-5">
        <div className="flex flex-col gap-3.5">
          {/* Top Row: Identity + Status */}
          <div className="flex items-center justify-between gap-3 w-full">
            <div className="flex items-center gap-2.5 sm:gap-3.5 min-w-0 flex-1">
              <div className="h-9 w-9 sm:h-12 sm:w-12 rounded-xl bg-gradient-to-br from-muted/80 to-muted/30 flex items-center justify-center shrink-0 shadow-inner ring-1 ring-white/10">
                <ConnectorIcon
                  typeCode={connector.connector_type_code}
                  className="h-4.5 w-4.5 sm:h-6 sm:w-6 text-foreground/80"
                />
              </div>
              <div className="min-w-0">
                <h3 className="font-semibold text-sm sm:text-lg tracking-tight leading-snug text-foreground mb-1.5">
                  {displayName}
                </h3>
                <div className="flex items-center gap-1.5 opacity-80">
                  <span className="text-[9px] sm:text-[10px] font-bold text-muted-foreground/80 uppercase tracking-widest">
                    {typeName}
                  </span>
                  {connector.is_draft && (
                    <Badge
                      variant="secondary"
                      className="text-[8px] font-bold uppercase py-0 px-1 h-3.5 shrink-0"
                    >
                      Draft
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="shrink-0 flex items-center gap-3 md:pt-1 self-center mt-2 sm:mt-0">
              <HealthBadge status={connector.health_status || "unknown"} />
            </div>
          </div>

          {/* Bottom Row: Metadata + Actions */}
          <div className="flex items-center justify-between gap-4 w-full border-t border-border/10 pt-3">
            <div className="flex items-center gap-4 bg-muted/20 px-3 py-1.5 rounded-lg border border-border/5 shadow-inner">
              {connectedDate && (
                <div className="flex items-center gap-1.5 whitespace-nowrap">
                  <span className="text-[9px] uppercase font-extrabold text-muted-foreground/80">
                    Connected
                  </span>
                  <span className="text-[10px] font-bold text-foreground/90">
                    {connectedDate}
                  </span>
                </div>
              )}
              {connector.last_collected_at && (
                <>
                  <div className="h-3 w-[1px] bg-border/40" />
                  <div className="flex items-center gap-1.5 whitespace-nowrap">
                    <span className="text-[9px] uppercase font-extrabold text-primary/80">
                      Activity
                    </span>
                    <span className="text-[10px] font-bold text-foreground/90">
                      {new Date(connector.last_collected_at).toLocaleDateString(
                        "en-US",
                        { month: "short", day: "numeric" }
                      )}
                    </span>
                  </div>
                </>
              )}
            </div>

            <div className="shrink-0 flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenLibrary();
                }}
                className="flex items-center gap-1.5 h-7 px-3 rounded-md border border-emerald-500/20 bg-emerald-500/5 text-emerald-600 text-[10px] font-bold hover:bg-emerald-500/10 transition-all"
                title="Open Global Test Library"
              >
                <Globe className="h-3 w-3" />
                Library
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onTest();
                }}
                disabled={isTesting}
                className="hidden sm:flex items-center gap-1.5 h-7 px-3 rounded-md border border-border/50 bg-muted/30 text-muted-foreground text-[10px] font-semibold hover:bg-primary/10 hover:text-primary hover:border-primary/30 transition-all disabled:opacity-50"
              >
                {isTesting ? (
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                ) : (
                  <Activity className="h-3 w-3" />
                )}
                {isTesting ? "Testing..." : "Test"}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit();
                }}
                className="flex items-center gap-1.5 h-7 px-3 rounded-md border border-border/50 bg-muted/30 text-muted-foreground text-[10px] font-semibold hover:bg-primary/10 hover:text-primary hover:border-primary/30 transition-all"
              >
                <Pencil className="h-3 w-3" />
                Edit
              </button>
              <a
                href={`/tests?connector=${connector.id}`}
                onClick={(e) => e.stopPropagation()}
                className="hidden lg:flex items-center gap-1.5 h-7 px-3 rounded-md border border-primary/20 bg-primary/5 text-primary text-[10px] font-bold hover:bg-primary/10 transition-all"
              >
                View Tests
                <ArrowRight className="h-3 w-3" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
        <Plug className="h-7 w-7 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">No assets connected</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-sm">
        Connect your infrastructure to start running automated control tests and
        evidence collection.
      </p>
      <Button onClick={onAdd} className="bg-primary hover:bg-primary/90">
        <Plus className="h-4 w-4 mr-2" />
        Add Connector
      </Button>
    </div>
  );
}

export default function AssetsPage() {
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace();

  const [connectors, setConnectors] = useState<ConnectorInstanceResponse[]>([]);
  const [assets, setAssets] = useState<AssetResponse[]>([]);
  const [categories, setCategories] = useState<DimensionResponse[]>([]);
  const [connectorTypesByCategory, setConnectorTypesByCategory] = useState<
    Record<string, DimensionResponse[]>
  >({});
  const [createOpen, setCreateOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("assets");
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [selectedConnectorForLibrary, setSelectedConnectorForLibrary] = useState<{
    instanceId: string;
    typeCode: string;
  } | null>(null);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState("");
  const [createDefaults, setCreateDefaults] = useState<{
    categoryCode?: string;
    typeCode?: string;
  }>({});
  const [connectorsLoading, setConnectorsLoading] = useState(false);
  const [assetsLoading, setAssetsLoading] = useState(false);
  const [connectorsError, setConnectorsError] = useState<string | null>(null);
  const [assetsError, setAssetsError] = useState<string | null>(null);
  const [integrationSearch, setIntegrationSearch] = useState("");
  const [assetSearch, setAssetSearch] = useState("");
  const [assetCategoryFilter, setAssetCategoryFilter] = useState<
    "All" | "Cloud" | "Identity" | "Endpoints"
  >("All");
  const [toasts, setToasts] = useState<ToastMsg[]>([]);
  const [editConnector, setEditConnector] =
    useState<ConnectorInstanceResponse | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);

  // Persistence tracking to avoid duplicate loads in Strict Mode or re-mounts
  const catalogLoadedRef = useRef(false);
  const connectorsLoadedRef = useRef<string | null>(null);
  const inventoryLoadedRef = useRef<string | null>(null);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (message: string, type: "success" | "error") => {
      const id = Date.now();
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => dismissToast(id), 4000);
    },
    [dismissToast]
  );

  const ensureCatalogLoaded = useCallback(async () => {
    if (catalogLoadedRef.current || catalogLoading) return;

    setCatalogLoading(true);
    try {
      const loadedCategories = await listConnectorCategories();
      const sortedCategories = [...loadedCategories].sort(
        (a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name)
      );
      const typeEntries = await Promise.all(
        sortedCategories.map(async (category) => {
          const types = await listConnectorTypes(category.code);
          return [category.code, sortConnectorTypes(types)] as const;
        })
      );
      setCategories(sortedCategories);
      setConnectorTypesByCategory(Object.fromEntries(typeEntries));
      catalogLoadedRef.current = true;
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to load connector catalog";
      addToast(msg, "error");
    } finally {
      setCatalogLoading(false);
    }
  }, [catalogLoading, addToast]);

  const loadConnectors = useCallback(async () => {
    if (!selectedOrgId) return;
    setConnectorsLoading(true);
    setConnectorsError(null);
    try {
      const result = await listConnectors({ org_id: selectedOrgId });
      setConnectors(result.items);
      connectorsLoadedRef.current = selectedOrgId;
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to load integrations";
      setConnectorsError(msg);
      addToast(msg, "error");
    } finally {
      setConnectorsLoading(false);
    }
  }, [selectedOrgId, addToast]);

  const loadAssetInventory = useCallback(async () => {
    if (!selectedOrgId) return;
    setAssetsLoading(true);
    setAssetsError(null);
    try {
      const result = await listAssets(selectedOrgId, { limit: 500 });
      setAssets(result.items);
      inventoryLoadedRef.current = selectedOrgId;
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to load asset inventory";
      setAssetsError(msg);
      addToast(msg, "error");
    } finally {
      setAssetsLoading(false);
    }
  }, [selectedOrgId, addToast]);

  useEffect(() => {
    if (ready && selectedOrgId) {
      if (connectorsLoadedRef.current !== selectedOrgId) {
        void loadConnectors();
      }
      if (inventoryLoadedRef.current !== selectedOrgId) {
        void loadAssetInventory();
      }
      if (!catalogLoadedRef.current) {
        void ensureCatalogLoaded();
      }
    }
  }, [ready, selectedOrgId, loadConnectors, loadAssetInventory, ensureCatalogLoaded]);

  const openCreateDialog = useCallback(
    async (defaults?: { categoryCode?: string; typeCode?: string }) => {
      await ensureCatalogLoaded();
      setCreateDefaults(defaults ?? {});
      setCreateOpen(true);
    },
    [ensureCatalogLoaded]
  );

  const handleTestConnector = useCallback(
    async (connectorId: string) => {
      setTestingId(connectorId);
      try {
        const result = await testConnector(connectorId);
        if (result.health_status === "healthy") {
          addToast("Connection test passed", "success");
        } else {
          addToast(`Test: ${result.message}`, "error");
        }
        loadConnectors();
      } catch (err) {
        addToast(err instanceof Error ? err.message : "Test failed", "error");
      } finally {
        setTestingId(null);
      }
    },
    [addToast, loadConnectors]
  );

  const filtered = useMemo(() => {
    return connectors.filter((c) => {
      const name = (c.name || c.instance_code || "").toLowerCase();
      const typeCode = (c.connector_type_code || "").toLowerCase();
      const typeName = (c.connector_type_name || "").toLowerCase();
      return (
        !integrationSearch ||
        name.includes(integrationSearch.toLowerCase()) ||
        typeCode.includes(integrationSearch.toLowerCase()) ||
        typeName.includes(integrationSearch.toLowerCase())
      );
    });
  }, [connectors, integrationSearch]);

  const visibleConnectors = useMemo(() => {
    return sortConnectedIntegrations(filtered);
  }, [filtered]);

  const connectorNameById = useMemo(() => {
    return new Map(
      connectors.map((connector) => [
        connector.id,
        connector.name || connector.instance_code,
      ])
    );
  }, [connectors]);

  const visibleAssets = useMemo(() => {
    const term = assetSearch.trim().toLowerCase();
    return [...assets]
      .filter((asset) => {
        if (
          assetCategoryFilter !== "All" &&
          assetScopeLabel(asset) !== assetCategoryFilter
        )
          return false;
        if (!term) return true;
        const connectorName = (
          connectorNameById.get(asset.connector_instance_id) || ""
        ).toLowerCase();
        return [
          assetPrimaryLabel(asset).toLowerCase(),
          assetSecondaryLabel(asset).toLowerCase(),
          asset.asset_external_id.toLowerCase(),
          asset.provider_code.toLowerCase(),
          asset.asset_type_code.toLowerCase(),
          connectorName,
        ].some((value) => value.includes(term));
      })
      .sort((a, b) => {
        const priorityDiff =
          connectorPriority(a.provider_code) -
          connectorPriority(b.provider_code);
        if (priorityDiff !== 0) return priorityDiff;
        return assetPrimaryLabel(a).localeCompare(assetPrimaryLabel(b));
      });
  }, [assets, assetSearch, assetCategoryFilter, connectorNameById]);

  const groupedAssets = useMemo(() => {
    const sourceMap = new Map<
      string,
      { source: string; types: Map<string, AssetResponse[]> }
    >();

    for (const asset of visibleAssets) {
      const source = getConnectorLabel(asset.provider_code);
      const type = assetTypeLabel(asset);
      const sourceGroup = sourceMap.get(source) ?? {
        source,
        types: new Map<string, AssetResponse[]>(),
      };
      const typeAssets = sourceGroup.types.get(type) ?? [];
      typeAssets.push(asset);
      sourceGroup.types.set(type, typeAssets);
      sourceMap.set(source, sourceGroup);
    }

    return Array.from(sourceMap.values()).map((group) => ({
      source: group.source,
      typeGroups: Array.from(group.types.entries())
        .map(([type, items]) => ({ type, items }))
        .sort((a, b) => a.type.localeCompare(b.type)),
    }));
  }, [visibleAssets]);

  const availableIntegrations = useMemo<CatalogIntegration[]>(() => {
    return categories.flatMap((category) =>
      (connectorTypesByCategory[category.code] ?? []).map((type) => ({
        ...type,
        categoryCode: category.code,
        categoryName: category.name,
      }))
    );
  }, [categories, connectorTypesByCategory]);

  const matchingIntegrations = useMemo(() => {
    const term = catalogSearch.trim().toLowerCase();
    return availableIntegrations.filter((integration) => {
      if (!term) return true;
      return (
        integration.name.toLowerCase().includes(term) ||
        integration.code.toLowerCase().includes(term) ||
        integration.categoryName.toLowerCase().includes(term)
      );
    });
  }, [availableIntegrations, catalogSearch]);

  const featuredIntegrations = useMemo(() => {
    return [...matchingIntegrations]
      .sort((a, b) => {
        const priorityDiff =
          connectorPriority(a.code) - connectorPriority(b.code);
        if (priorityDiff !== 0) return priorityDiff;
        return a.name.localeCompare(b.name);
      })
      .slice(0, 4);
  }, [matchingIntegrations]);

  const featuredKeys = useMemo(() => {
    return new Set(
      featuredIntegrations.map(
        (integration) => `${integration.categoryCode}:${integration.code}`
      )
    );
  }, [featuredIntegrations]);

  const activeCount = connectors.filter((c) => !c.is_draft).length;
  const assetCount = assets.length;
  const availableCount = availableIntegrations.length;
  const liveIntegrationCount = connectors.filter(isLiveConnector).length;
  const degradedIntegrationCount = connectors.filter(
    (connector) => !connector.is_draft && !isLiveConnector(connector)
  ).length;
  const liveConnectorIds = new Set(
    connectors.filter(isLiveConnector).map((connector) => connector.id)
  );
  const monitoredAssetCount = assets.filter((asset) => {
    return (
      liveConnectorIds.has(asset.connector_instance_id) &&
      isMonitoredAssetStatus(asset.status_code)
    );
  }).length;
  const unmonitoredAssetCount = Math.max(assetCount - monitoredAssetCount, 0);
  const criticalAssetCount = assets.filter(isCriticalAsset).length;

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b border-border">
        <div className="flex items-start gap-4 min-w-0 w-full">
          <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
            <Boxes className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-semibold leading-tight">
              Asset Inventory
            </h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Discovered assets and the integrations that collect them
            </p>
          </div>
          <Button className="shrink-0" onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Connection
          </Button>
        </div>
      </div>

      <div className="flex-1 min-h-0 px-6 py-6 overflow-y-auto">
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="flex flex-col gap-5"
        >
          <div className="grid gap-4 xl:grid-cols-4 md:grid-cols-2">
            <AssetOverviewCard
              label="Total Assets"
              value={assetCount.toLocaleString()}
              accentClass="text-foreground"
              borderCls="border-l-primary"
              description={`${monitoredAssetCount.toLocaleString()} under healthy integrations`}
            />
            <AssetOverviewCard
              label="Unmonitored"
              value={unmonitoredAssetCount.toLocaleString()}
              accentClass="text-amber-500"
              borderCls="border-l-amber-500"
              description="Need healthy coverage or manual review"
            />
            <AssetOverviewCard
              label="Integrations"
              value={liveIntegrationCount.toLocaleString()}
              detail="connected"
              accentClass="text-emerald-500"
              borderCls="border-l-emerald-500"
              description={`${degradedIntegrationCount.toLocaleString()} degraded | ${availableCount.toLocaleString()} available`}
            />
            <AssetOverviewCard
              label="Critical Assets"
              value={criticalAssetCount.toLocaleString()}
              accentClass="text-rose-500"
              borderCls="border-l-rose-500"
              description="Estimated from sensitive asset types and naming"
            />
          </div>

          <div className="border-b border-border/60">
            <div className="flex min-w-max gap-1 px-1">
              <button
                type="button"
                onClick={() => setActiveTab("assets")}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${activeTab === "assets"
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
              >
                Asset Inventory
                <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  {assetCount}
                </span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("integrations")}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${activeTab === "integrations"
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
              >
                Integrations
                <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
                  {liveIntegrationCount} live
                </span>
              </button>
            </div>
          </div>

          <TabsContent value="assets" className="mt-0">
            <Card className="border-border/70 bg-card/70 shadow-sm">
              <CardContent className="p-0">
                <div className="flex items-center justify-between gap-4 border-b border-border/60 px-5 py-5">
                  <div>
                    <h2 className="text-xl font-semibold">Asset Inventory</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Discovered assets collected from your configured
                      integrations.
                    </p>
                  </div>
                  <div className="text-right text-sm text-muted-foreground">
                    <div className="font-medium text-foreground">
                      {assetCount} assets
                    </div>
                    <div>{activeCount} active integrations</div>
                  </div>
                </div>

                <div className="space-y-5 p-5">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div className="flex flex-1 flex-col gap-3 lg:flex-row lg:items-center">
                      <div className="relative w-full max-w-sm">
                        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input
                          placeholder="Search assets..."
                          value={assetSearch}
                          onChange={(e) => setAssetSearch(e.target.value)}
                          className="h-11 rounded-xl border-border/70 bg-background/80 pl-9"
                        />
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {(
                          ["All", "Cloud", "Identity", "Endpoints"] as const
                        ).map((scope) => (
                          <Button
                            key={scope}
                            variant="outline"
                            size="sm"
                            className={`rounded-full px-4 ${assetCategoryFilter === scope
                              ? "border-primary bg-primary/15 text-primary"
                              : "border-border/70 bg-background/70 text-muted-foreground"
                              }`}
                            onClick={() => setAssetCategoryFilter(scope)}
                          >
                            {scope}
                          </Button>
                        ))}
                      </div>
                    </div>
                    <Button
                      className="self-start lg:self-auto"
                      onClick={() => {
                        setActiveTab("integrations");
                        void openCreateDialog();
                      }}
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Add Integration
                    </Button>
                  </div>

                  {assetsLoading && (
                    <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
                      <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent mr-3" />
                      Loading asset inventory...
                    </div>
                  )}

                  {!assetsLoading && assetsError && assets.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                      <AlertCircle className="mb-3 h-10 w-10 text-destructive/80" />
                      <p className="mb-4 text-sm text-muted-foreground">
                        {assetsError}
                      </p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => void loadAssetInventory()}
                      >
                        Try again
                      </Button>
                    </div>
                  )}

                  {!assetsLoading && assets.length === 0 && !assetsError && (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                      <Boxes className="mb-3 h-10 w-10 text-muted-foreground/50" />
                      <p className="text-sm text-muted-foreground">
                        No assets found across your connections
                      </p>
                    </div>
                  )}

                  {!assetsLoading &&
                    assets.length > 0 &&
                    visibleAssets.length === 0 && (
                      <div className="flex flex-col items-center justify-center py-16 text-center">
                        <Search className="mb-3 h-8 w-8 text-muted-foreground/50" />
                        <p className="text-sm text-muted-foreground">
                          No assets match your search
                        </p>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="mt-3 text-xs"
                          onClick={() => setAssetSearch("")}
                        >
                          Clear search
                        </Button>
                      </div>
                    )}

                  {visibleAssets.length > 0 && (
                    <div className="overflow-hidden rounded-2xl border border-border/70">
                      {groupedAssets.map((sourceGroup, sourceIndex) => (
                        <details
                          key={sourceGroup.source}
                          className={`group ${sourceIndex > 0 ? "border-t border-border/70" : ""}`}
                        >
                          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 bg-muted/15 px-5 py-4 marker:hidden">
                            <div className="flex items-center gap-3">
                              <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-open:rotate-90" />
                              <Badge
                                variant="outline"
                                className="border-border/70 bg-background/70"
                              >
                                {sourceGroup.source}
                              </Badge>
                              <span className="text-sm text-muted-foreground">
                                {sourceGroup.typeGroups.reduce(
                                  (count, group) => count + group.items.length,
                                  0
                                )}{" "}
                                service
                              </span>
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {sourceGroup.typeGroups.length} types
                            </span>
                          </summary>

                          {sourceGroup.typeGroups.map(
                            (typeGroup, typeIndex) => (
                              <details
                                key={`${sourceGroup.source}-${typeGroup.type}`}
                                className={`group ${typeIndex > 0 ? "border-t border-border/50" : ""}`}
                              >
                                <summary className="flex cursor-pointer list-none items-center justify-between gap-3 bg-background/40 px-5 py-3 marker:hidden">
                                  <div className="flex items-center gap-3">
                                    <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-open:rotate-90" />
                                    <span className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                                      {typeGroup.type}
                                    </span>
                                  </div>
                                  <span className="text-xs text-muted-foreground">
                                    {typeGroup.items.length} service
                                  </span>
                                </summary>
                                <Table>
                                  <TableHeader>
                                    <TableRow className="bg-muted/20 hover:bg-muted/20">
                                      <TableHead className="pl-5">
                                        Asset
                                      </TableHead>
                                      <TableHead>Connector</TableHead>
                                      <TableHead className="hidden lg:table-cell">
                                        External ID
                                      </TableHead>
                                      <TableHead className="hidden xl:table-cell">
                                        Last Collected
                                      </TableHead>
                                      <TableHead>Status</TableHead>
                                    </TableRow>
                                  </TableHeader>
                                  <TableBody>
                                    {typeGroup.items.map((asset) => (
                                      <TableRow
                                        key={asset.id}
                                        className="border-border/60"
                                      >
                                        <TableCell className="pl-5">
                                          <div className="min-w-0">
                                            <div className="truncate font-medium text-foreground">
                                              {assetPrimaryLabel(asset)}
                                            </div>
                                            <div className="truncate text-xs text-muted-foreground">
                                              {assetSecondaryLabel(asset)}
                                            </div>
                                          </div>
                                        </TableCell>
                                        <TableCell className="text-muted-foreground">
                                          {connectorNameById.get(
                                            asset.connector_instance_id
                                          ) ?? "Unknown"}
                                        </TableCell>
                                        <TableCell className="hidden max-w-[220px] truncate text-muted-foreground lg:table-cell">
                                          {asset.asset_external_id}
                                        </TableCell>
                                        <TableCell className="hidden text-muted-foreground xl:table-cell">
                                          {asset.last_collected_at
                                            ? timeAgo(asset.last_collected_at)
                                            : "Not collected"}
                                        </TableCell>
                                        <TableCell>
                                          <Badge
                                            className={assetStatusTone(
                                              asset.status_code
                                            )}
                                          >
                                            {formatStatus(asset.status_code)}
                                          </Badge>
                                        </TableCell>
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                              </details>
                            )
                          )}
                        </details>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="integrations" className="mt-0">
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,0.9fr)]">
              <Card className="border-border/70 bg-card/70 shadow-sm">
                <CardContent className="p-0">
                  <div className="flex items-center justify-between gap-4 border-b border-border/60 px-5 py-5">
                    <div>
                      <h2 className="text-xl font-semibold">
                        Connected Integrations
                      </h2>
                      <p className="mt-1 text-sm text-muted-foreground">
                        All configured connectors and their latest sync status.
                      </p>
                    </div>
                    <div className="text-right text-sm text-muted-foreground">
                      <div className="font-medium text-foreground">
                        {activeCount} connected
                      </div>
                      {connectors.length !== activeCount && (
                        <div>{connectors.length - activeCount} draft</div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-5 p-5">
                    <div className="relative max-w-sm">
                      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        placeholder="Search integrations..."
                        value={integrationSearch}
                        onChange={(e) => setIntegrationSearch(e.target.value)}
                        className="h-11 rounded-xl border-border/70 bg-background/80 pl-9"
                      />
                    </div>

                    {!connectorsLoading &&
                      !connectorsError &&
                      connectors.length === 0 && (
                        <EmptyState onAdd={() => void openCreateDialog()} />
                      )}

                    {!connectorsLoading &&
                      connectors.length > 0 &&
                      filtered.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-16 text-center">
                          <Search className="h-8 w-8 text-muted-foreground mb-3 opacity-40" />
                          <p className="text-sm text-muted-foreground">
                            No integrations match your search
                          </p>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="mt-3 text-xs"
                            onClick={() => {
                              setIntegrationSearch("");
                            }}
                          >
                            Clear filters
                          </Button>
                        </div>
                      )}

                    {filtered.length > 0 && (
                      <div className="space-y-4">
                        <h2 className="text-sm font-semibold text-foreground/70 uppercase tracking-wider px-1">
                          Connected Infrastructure
                        </h2>
                        {visibleConnectors.map((connector) => (
                          <AssetCard
                            key={connector.id}
                            connector={connector}
                            onEdit={() => setEditConnector(connector)}
                            onTest={() => handleTestConnector(connector.id)}
                            onOpenLibrary={() => {
                              setSelectedConnectorForLibrary({
                                instanceId: connector.id,
                                typeCode: connector.connector_type_code,
                              });
                              setLibraryOpen(true);
                            }}
                            isTesting={testingId === connector.id}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-5">
                <Card className="border-border/70 bg-card/70 shadow-sm overflow-hidden group">
                  <div className="relative h-20 bg-gradient-to-br from-primary/20 via-primary/5 to-transparent">
                    <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
                    <div className="absolute top-4 right-6 h-12 w-12 rounded-2xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Plus className="h-6 w-6 text-primary" />
                    </div>
                  </div>
                  <CardContent className="p-6 pt-5">
                    <h3 className="font-semibold text-lg">
                      Connect New Source
                    </h3>
                    <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                      Expand your visibility by connecting more cloud providers,
                      identity systems, or security tools.
                    </p>
                    <Button
                      className="w-full mt-6 shadow-md group border-primary/20 bg-primary/10 text-primary hover:bg-primary hover:text-white transition-all shadow-primary/20"
                      onClick={() => void openCreateDialog()}
                    >
                      <Plus className="h-4 w-4 mr-2 transition-transform group-hover:rotate-90" />
                      Add Integration
                    </Button>
                  </CardContent>
                </Card>

                {availableIntegrations.length > 0 && (
                  <Card className="border-border/70 bg-card/70 shadow-sm">
                    <CardHeader className="pb-3 pt-5">
                      <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
                        Available Libraries
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 px-3 pb-5">
                      {featuredIntegrations.map((integration) => (
                        <button
                          key={`${integration.categoryCode}:${integration.code}`}
                          onClick={() => {
                            setCreateDefaults({
                              categoryCode: integration.categoryCode,
                              typeCode: integration.code,
                            });
                            setCreateOpen(true);
                          }}
                          className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 hover:bg-muted/30 transition-all text-left group"
                        >
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 rounded-lg bg-background flex items-center justify-center border border-border/50 group-hover:border-primary/30 transition-colors">
                              <ConnectorIcon
                                typeCode={integration.code}
                                className="h-4 w-4"
                              />
                            </div>
                            <span className="text-sm font-medium">
                              {integration.name}
                            </span>
                          </div>
                          <Plus className="h-3.5 w-3.5 text-muted-foreground/40 group-hover:text-primary transition-colors" />
                        </button>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {selectedOrgId && (
        <CreateConnectorDialog
          open={createOpen}
          orgId={selectedOrgId}
          defaults={createDefaults}
          initialCategories={categories}
          initialTypesByCategory={connectorTypesByCategory}
          onCreated={() => {
            loadConnectors();
            addToast("Connector created successfully", "success");
          }}
          onClose={() => {
            setCreateOpen(false);
            setCreateDefaults({});
          }}
        />
      )}

      {selectedOrgId && editConnector && (
        <EditConnectorDialog
          connector={editConnector}
          orgId={selectedOrgId}
          onSaved={() => {
            loadConnectors();
            addToast("Connector updated successfully", "success");
          }}
          onClose={() => setEditConnector(null)}
        />
      )}

      {selectedOrgId && (
        <GlobalLibraryDialog
          open={libraryOpen}
          orgId={selectedOrgId}
          workspaceId={selectedWorkspaceId}
          lockedConnectorType={selectedConnectorForLibrary?.typeCode}
          connectorInstanceId={selectedConnectorForLibrary?.instanceId}
          onDeployed={() => {
            addToast("Control tests deployed successfully", "success");
          }}
          onClose={() => {
            setLibraryOpen(false);
            setSelectedConnectorForLibrary(null);
          }}
        />
      )}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
