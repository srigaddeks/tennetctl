"use client"

import { useEffect, useState, useCallback, useMemo, useRef } from "react"
import { useRouter } from "next/navigation"
import {
  Card,
  CardContent,
  Button,
  Input,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@kcontrol/ui"
import {
  Store,
  Search,
  RefreshCw,
  AlertCircle,
  Download,
  CheckCircle2,
  ArrowUpCircle,
  Layers,
  BookOpen,
  ShieldAlert,
  ShieldCheck,
  ChevronRight,
  X,
  Plus,
  Trash2,
  TrendingUp,
  Tag,
  Zap,
  Filter,
} from "lucide-react"
import {
  listFrameworks,
  listDeployments,
  deployFramework,
  updateDeployment,
  deleteDeployment,
  listVersions,
  listDeploymentControls,
  getUpgradeDiff,
  listAllControls,
  listGlobalRisks,
  listRiskLibraryDeployments,
  deployGlobalRisks,
  removeRiskDeployment,
} from "@/lib/api/grc"
import type {
  FrameworkResponse,
  FrameworkDeploymentResponse,
} from "@/lib/types/grc"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { OrgWorkspaceSwitcher } from "@/components/layout/OrgWorkspaceSwitcher"

// ── Toast ─────────────────────────────────────────────────────────────────────

type ToastMsg = { id: number; message: string; type: "success" | "error" }

function ToastContainer({ toasts, onDismiss }: { toasts: ToastMsg[]; onDismiss: (id: number) => void }) {
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-80">
      {toasts.map(t => (
        <div key={t.id} className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg border text-sm font-medium animate-in slide-in-from-bottom-2 ${
          t.type === "success"
            ? "bg-green-50 border-green-500/30 text-green-800"
            : "bg-red-50 border-red-500/30 text-red-800"
        }`}>
          {t.type === "success"
            ? <CheckCircle2 className="h-4 w-4 shrink-0 text-green-600" />
            : <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />}
          <span className="flex-1">{t.message}</span>
          <button onClick={() => onDismiss(t.id)} className="shrink-0 opacity-60 hover:opacity-100">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function categoryBadgeClass(category: string): string {
  switch (category?.toLowerCase()) {
    case "security": return "bg-blue-500/10 text-blue-600 border-blue-500/20"
    case "privacy": return "bg-purple-500/10 text-purple-600 border-purple-500/20"
    case "compliance": return "bg-green-500/10 text-green-600 border-green-500/20"
    case "risk": return "bg-amber-500/10 text-amber-600 border-amber-500/20"
    default: return "bg-muted text-muted-foreground border-border"
  }
}

function criticalityClass(level: string | null): string {
  switch (level?.toLowerCase()) {
    case "critical": return "bg-red-500/10 text-red-700 border-red-500/20"
    case "high": return "bg-orange-500/10 text-orange-700 border-orange-500/20"
    case "medium": return "bg-amber-500/10 text-amber-700 border-amber-500/20"
    case "low": return "bg-green-500/10 text-green-700 border-green-500/20"
    default: return "bg-muted text-muted-foreground border-border"
  }
}

function riskLevelColor(level: string | null): string {
  switch (level?.toLowerCase()) {
    case "critical": return "bg-red-500/10 text-red-600 border-red-500/20"
    case "high": return "bg-orange-500/10 text-orange-600 border-orange-500/20"
    case "medium": return "bg-amber-500/10 text-amber-600 border-amber-500/20"
    case "low": return "bg-green-500/10 text-green-600 border-green-500/20"
    default: return "bg-muted text-muted-foreground border-border"
  }
}

function riskScore(score: number | null): string {
  if (score === null) return "–"
  if (score >= 20) return "Critical"
  if (score >= 12) return "High"
  if (score >= 6) return "Medium"
  return "Low"
}

// ── Filter chips ──────────────────────────────────────────────────────────────

function FilterChips({
  options,
  value,
  onChange,
  allLabel = "All",
}: {
  options: { code: string; name: string; count?: number }[]
  value: string
  onChange: (v: string) => void
  allLabel?: string
}) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <button
        onClick={() => onChange("")}
        className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
          value === ""
            ? "bg-primary text-primary-foreground border-primary"
            : "border-border text-muted-foreground hover:text-foreground hover:bg-muted"
        }`}
      >
        {allLabel}
      </button>
      {options.map(opt => (
        <button
          key={opt.code}
          onClick={() => onChange(opt.code === value ? "" : opt.code)}
          className={`px-3 py-1.5 text-xs rounded-full border transition-colors flex items-center gap-1 ${
            value === opt.code
              ? "bg-primary text-primary-foreground border-primary"
              : "border-border text-muted-foreground hover:text-foreground hover:bg-muted"
          }`}
        >
          {opt.name}
          {opt.count !== undefined && (
            <span className={`text-[9px] font-semibold ${value === opt.code ? "opacity-80" : "opacity-60"}`}>
              {opt.count}
            </span>
          )}
        </button>
      ))}
    </div>
  )
}

// ── Controls Preview Drawer ───────────────────────────────────────────────────

function ControlsDrawer({
  deployment,
  onClose,
}: {
  deployment: FrameworkDeploymentResponse
  onClose: () => void
}) {
  const [controls, setControls] = useState<Array<{id: string; control_code: string; name: string | null; category_name: string | null; criticality_name: string | null; control_type: string | null}>>([])
  const [diff, setDiff] = useState<{ added: Array<{control_code: string; name: string | null}>; removed: Array<{control_code: string; name: string | null}> } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      try {
        const [ctrlRes] = await Promise.all([
          listDeploymentControls(deployment.id),
          ...(deployment.has_update && deployment.latest_version_id
            ? [getUpgradeDiff(deployment.id, deployment.latest_version_id).then(d => { if (!cancelled) setDiff(d) })]
            : []),
        ])
        if (!cancelled) setControls(ctrlRes.controls)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [deployment.id, deployment.has_update, deployment.latest_version_id])

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[440px] bg-background border-l shadow-2xl flex flex-col">
      <div className="flex items-center justify-between px-5 py-4 border-b shrink-0">
        <div>
          <h2 className="text-sm font-semibold">{deployment.framework_name}</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            v{deployment.deployed_version_code} · {controls.length} controls
          </p>
        </div>
        <button onClick={onClose} aria-label="Close" className="p-1.5 rounded-md hover:bg-muted transition-colors">
          <X className="h-4 w-4" />
        </button>
      </div>

      {deployment.has_update && diff && (diff.added.length > 0 || diff.removed.length > 0) && (
        <div className="mx-4 mt-4 rounded-lg border border-blue-500/30 bg-blue-500/5 p-3 shrink-0">
          <p className="text-xs font-semibold text-blue-700 mb-2">Changes in v{deployment.latest_version_code}</p>
          {diff.added.length > 0 && (
            <div className="space-y-1 mb-2">
              {diff.added.map(c => (
                <div key={c.control_code} className="flex items-center gap-1.5 text-xs text-green-700">
                  <Plus className="h-3 w-3 shrink-0" />
                  <span className="font-mono text-[10px] opacity-70">{c.control_code}</span>
                  <span className="truncate">{c.name}</span>
                </div>
              ))}
            </div>
          )}
          {diff.removed.length > 0 && (
            <div className="space-y-1">
              {diff.removed.map(c => (
                <div key={c.control_code} className="flex items-center gap-1.5 text-xs text-red-600">
                  <X className="h-3 w-3 shrink-0" />
                  <span className="font-mono text-[10px] opacity-70">{c.control_code}</span>
                  <span className="truncate">{c.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-12 rounded-md bg-muted animate-pulse" />
          ))
        ) : controls.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-muted-foreground text-sm">
            <Layers className="h-8 w-8 mb-2 opacity-30" />
            No controls in this version
          </div>
        ) : (
          controls.map(c => (
            <div key={c.id} className="rounded-md border bg-card px-3 py-2.5">
              <div className="flex items-start gap-2">
                <span className="text-[10px] font-mono text-muted-foreground mt-0.5 shrink-0">{c.control_code}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate">{c.name || c.control_code}</p>
                  <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                    {c.category_name && (
                      <Badge variant="outline" className="text-[9px] px-1 py-0">{c.category_name}</Badge>
                    )}
                    {c.criticality_name && (
                      <Badge variant="outline" className={`text-[9px] px-1 py-0 ${criticalityClass(c.criticality_name)}`}>{c.criticality_name}</Badge>
                    )}
                    {c.control_type && (
                      <span className="text-[9px] text-muted-foreground">{c.control_type}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

// ── Framework Card ────────────────────────────────────────────────────────────

function FrameworkCard({
  framework,
  deployment,
  onDeploy,
  onUndeploy,
  onViewControls,
  deploying,
}: {
  framework: FrameworkResponse
  deployment: FrameworkDeploymentResponse | null
  onDeploy: (fw: FrameworkResponse) => Promise<void>
  onUndeploy: (dep: FrameworkDeploymentResponse, fw: FrameworkResponse) => void
  onViewControls: (dep: FrameworkDeploymentResponse) => void
  deploying: boolean
}) {
  const router = useRouter()
  const isDeployed = !!deployment
  const hasUpdate = deployment?.has_update ?? false

  return (
    <Card 
      className="rounded-xl hover:shadow-md cursor-pointer transition-shadow"
      onClick={() => router.push(`/framework_library/${framework.id}`)}
    >
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
            {framework.logo_url ? (
              <img src={framework.logo_url} alt={framework.name ?? ""} className="h-6 w-6 object-contain" />
            ) : (
              <BookOpen className="h-5 w-5 text-primary" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-semibold truncate" title={framework.name}>{framework.name}</h3>
              <Badge variant="outline" className={`text-[10px] font-medium ${categoryBadgeClass(framework.category_name)}`}>
                {framework.category_name || framework.framework_category_code}
              </Badge>
              {hasUpdate && (
                <Badge variant="outline" className="text-[10px] font-medium bg-blue-500/10 text-blue-600 border-blue-500/20">
                  Update available
                </Badge>
              )}
              {isDeployed && !hasUpdate && (
                <Badge variant="outline" className="text-[10px] font-medium bg-green-500/10 text-green-600 border-green-500/20">
                  <CheckCircle2 className="h-3 w-3 mr-1" />Deployed
                </Badge>
              )}
            </div>

            <p className="text-[11px] text-muted-foreground mt-0.5 font-mono">{framework.framework_code}</p>

            {framework.short_description && (
              <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2">{framework.short_description}</p>
            )}

            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground flex-wrap">
              <span className="flex items-center gap-1">
                <Layers className="h-3 w-3" />
                {framework.control_count ?? 0} controls
              </span>
              {framework.latest_version_code && (
                <span>v{framework.latest_version_code}</span>
              )}
              {framework.publisher_name && (
                <span className="truncate">by {framework.publisher_name}</span>
              )}
              {isDeployed && (
                <button
                  onClick={(e) => { e.stopPropagation(); onViewControls(deployment!); }}
                  className="flex items-center gap-0.5 text-primary hover:underline"
                >
                  View controls <ChevronRight className="h-3 w-3" />
                </button>
              )}
            </div>
          </div>

          <div className="shrink-0 mt-0.5 flex flex-col items-end gap-1">
            {hasUpdate ? (
              <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); onDeploy(framework); }} disabled={deploying}
                className="gap-1.5 text-blue-600 border-blue-500/40 hover:bg-blue-500/10">
                {deploying ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <ArrowUpCircle className="h-3.5 w-3.5" />}
                Upgrade
              </Button>
            ) : isDeployed ? (
              <Button size="sm" variant="ghost" disabled className="text-green-600 gap-1.5" onClick={(e) => e.stopPropagation()}>
                <CheckCircle2 className="h-3.5 w-3.5" />Deployed
              </Button>
            ) : (
              <Button size="sm" onClick={(e) => { e.stopPropagation(); onDeploy(framework); }}
                disabled={deploying || !framework.latest_version_code}
                title={!framework.latest_version_code ? "No published version available" : undefined}
                className="gap-1.5">
                {deploying ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
                Deploy
              </Button>
            )}
            {isDeployed && (
              <button
                onClick={(e) => { e.stopPropagation(); onUndeploy(deployment!, framework); }}
                className="text-[10px] text-muted-foreground hover:text-destructive transition-colors"
                title="Remove deployment"
              >
                Remove
              </button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ── Control Card ──────────────────────────────────────────────────────────────

type LibraryControl = {
  id: string
  control_code: string
  name: string | null
  framework_id: string
  framework_name: string | null
  framework_code: string | null
  control_category_code: string | null
  category_name: string | null
  criticality_code: string | null
  criticality_name: string | null
  control_type: string | null
  automation_potential: string | null
  short_description: string | null
}

function ControlCard({ control }: { control: LibraryControl }) {
  return (
    <Card className="rounded-xl hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10">
            <ShieldCheck className="h-4 w-4 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-0.5">
              <p className="text-xs font-semibold" title={control.name ?? control.control_code}>{control.name || control.control_code}</p>
            </div>
            <p className="text-[10px] font-mono text-muted-foreground">{control.control_code}</p>
            {control.short_description && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{control.short_description}</p>
            )}
            <div className="flex items-center gap-1.5 mt-2 flex-wrap">
              {control.criticality_name && (
                <Badge variant="outline" className={`text-[9px] font-medium ${criticalityClass(control.criticality_name)}`}>
                  {control.criticality_name}
                </Badge>
              )}
              {control.category_name && (
                <Badge variant="outline" className="text-[9px] font-medium bg-muted text-muted-foreground">
                  {control.category_name}
                </Badge>
              )}
              {control.control_type && (
                <Badge variant="outline" className="text-[9px] font-medium bg-muted text-muted-foreground">
                  {control.control_type}
                </Badge>
              )}
              {control.automation_potential && (
                <span className="text-[9px] text-muted-foreground flex items-center gap-0.5">
                  <Zap className="h-2.5 w-2.5" />{control.automation_potential}
                </span>
              )}
            </div>
            {control.framework_name && (
              <p className="text-[10px] text-muted-foreground mt-1.5 flex items-center gap-1">
                <BookOpen className="h-2.5 w-2.5 shrink-0" />
                {control.framework_name}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ── Risk Library Card ─────────────────────────────────────────────────────────

type GlobalRisk = {
  id: string; risk_code: string; title: string | null; short_description: string | null;
  risk_category_code: string; risk_category_name: string | null;
  risk_level_code: string | null; risk_level_name: string | null;
  inherent_risk_score: number | null; linked_control_count: number;
}

type RiskDeployment = {
  id: string; global_risk_id: string; risk_code: string; title: string | null;
  risk_level_name: string | null; deployment_status: string;
}

function RiskCard({
  risk,
  deployment,
  selected,
  onToggleSelect,
  onRemove,
}: {
  risk: GlobalRisk
  deployment: RiskDeployment | null
  selected: boolean
  onToggleSelect: (id: string) => void
  onRemove: (deploymentId: string, title: string) => void
}) {
  const isDeployed = !!deployment

  return (
    <Card className={`rounded-xl transition-all ${selected ? "ring-2 ring-primary" : "hover:shadow-md"}`}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {!isDeployed && (
            <button
              onClick={() => onToggleSelect(risk.id)}
              aria-label={selected ? "Deselect risk" : "Select risk"}
              className={`mt-0.5 h-4 w-4 shrink-0 rounded border-2 transition-colors flex items-center justify-center ${
                selected ? "bg-primary border-primary" : "border-muted-foreground/40 hover:border-primary"
              }`}
            >
              {selected && <CheckCircle2 className="h-3 w-3 text-primary-foreground" />}
            </button>
          )}
          {isDeployed && (
            <div className="mt-0.5 h-4 w-4 shrink-0 flex items-center justify-center">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-xs font-semibold truncate" title={risk.title ?? risk.risk_code}>{risk.title || risk.risk_code}</p>
              {risk.risk_level_name && (
                <Badge variant="outline" className={`text-[9px] font-medium ${riskLevelColor(risk.risk_level_name)}`}>
                  {risk.risk_level_name}
                </Badge>
              )}
              {risk.risk_category_name && (
                <Badge variant="outline" className="text-[9px] font-medium bg-muted text-muted-foreground">
                  {risk.risk_category_name}
                </Badge>
              )}
              {isDeployed && (
                <Badge variant="outline" className="text-[9px] font-medium bg-green-500/10 text-green-600 border-green-500/20">
                  Deployed
                </Badge>
              )}
            </div>
            <p className="text-[11px] font-mono text-muted-foreground mt-0.5">{risk.risk_code}</p>
            {risk.short_description && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{risk.short_description}</p>
            )}
            <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
              {risk.inherent_risk_score !== null && (
                <span className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  Score {risk.inherent_risk_score} ({riskScore(risk.inherent_risk_score)})
                </span>
              )}
              {risk.linked_control_count > 0 && (
                <span className="flex items-center gap-1">
                  <Layers className="h-3 w-3" />
                  {risk.linked_control_count} controls
                </span>
              )}
            </div>
          </div>

          {isDeployed && (
            <button
              onClick={() => onRemove(deployment!.id, risk.title || risk.risk_code)}
              className="shrink-0 p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors"
              title="Remove from workspace"
              aria-label="Remove risk from workspace"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function FrameworkLibraryPage() {
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace()
  const [activeTab, setActiveTab] = useState<"frameworks" | "controls" | "risks">("frameworks")

  // ── Toast ─────────────────────────────────────────────────────────────────
  const [toasts, setToasts] = useState<ToastMsg[]>([])
  const toastIdRef = useRef(0)
  const addToast = useCallback((message: string, type: "success" | "error" = "success") => {
    const id = ++toastIdRef.current
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])
  const dismissToast = useCallback((id: number) => setToasts(prev => prev.filter(t => t.id !== id)), [])

  // ── Risk removal confirm ──────────────────────────────────────────────────
  const [removeConfirm, setRemoveConfirm] = useState<{ id: string; title: string } | null>(null)

  // ── Framework undeploy confirm ────────────────────────────────────────────
  const [undeployConfirm, setUndeployConfirm] = useState<{ dep: FrameworkDeploymentResponse; fw: FrameworkResponse } | null>(null)

  // ── Frameworks state ──────────────────────────────────────────────────────
  const [frameworks, setFrameworks] = useState<FrameworkResponse[]>([])
  const [deployments, setDeployments] = useState<FrameworkDeploymentResponse[]>([])
  const [fwLoading, setFwLoading] = useState(true)
  const [fwError, setFwError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterCategory, setFilterCategory] = useState("")
  const [deployingId, setDeployingId] = useState<string | null>(null)
  const [deployError, setDeployError] = useState<string | null>(null)
  const [controlsDrawer, setControlsDrawer] = useState<FrameworkDeploymentResponse | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  // ── Control Library state ─────────────────────────────────────────────────
  const [libraryControls, setLibraryControls] = useState<LibraryControl[]>([])
  const [ctrlLoading, setCtrlLoading] = useState(false)
  const [ctrlError, setCtrlError] = useState<string | null>(null)
  const [ctrlSearch, setCtrlSearch] = useState("")
  const [ctrlFilterCategory, setCtrlFilterCategory] = useState("")
  const [ctrlFilterCriticality, setCtrlFilterCriticality] = useState("")
  const [ctrlTotal, setCtrlTotal] = useState(0)

  // ── Risk Library state ────────────────────────────────────────────────────
  const [globalRisks, setGlobalRisks] = useState<GlobalRisk[]>([])
  const [riskDeployments, setRiskDeployments] = useState<RiskDeployment[]>([])
  const [riskLoading, setRiskLoading] = useState(false)
  const [riskError, setRiskError] = useState<string | null>(null)
  const [riskSearch, setRiskSearch] = useState("")
  const [riskFilterCategory, setRiskFilterCategory] = useState("")
  const [selectedRisks, setSelectedRisks] = useState<Set<string>>(new Set())
  const [deployingRisks, setDeployingRisks] = useState(false)

  // ── Load frameworks ───────────────────────────────────────────────────────
  const loadFrameworks = useCallback(async (quiet = false) => {
    if (!selectedOrgId) return
    if (quiet) setRefreshing(true); else setFwLoading(true)
    setFwError(null)
    try {
      const [fwRes, deployRes] = await Promise.all([
        listFrameworks({
          scope_org_id: selectedOrgId,
          ...(selectedWorkspaceId ? { scope_workspace_id: selectedWorkspaceId } : {}),
          is_marketplace_visible: true,
          approval_status: "approved",
        }),
        listDeployments(selectedOrgId, selectedWorkspaceId || undefined),
      ])
      setFrameworks(fwRes.items ?? [])
      setDeployments((deployRes.items ?? []) as unknown as FrameworkDeploymentResponse[])
    } catch (e) {
      setFwError(e instanceof Error ? e.message : "Failed to load marketplace")
    } finally {
      setFwLoading(false)
      setRefreshing(false)
    }
  }, [selectedOrgId, selectedWorkspaceId])

  // ── Load control library ──────────────────────────────────────────────────
  const loadControls = useCallback(async () => {
    if (!selectedOrgId) {
      setLibraryControls([])
      setCtrlTotal(0)
      setCtrlError(null)
      setCtrlLoading(false)
      return
    }
    setCtrlLoading(true)
    setCtrlError(null)
    try {
      const res = await listAllControls({
        scope_org_id: selectedOrgId,
        ...(selectedWorkspaceId ? { scope_workspace_id: selectedWorkspaceId } : {}),
        ...(ctrlSearch ? { search: ctrlSearch } : {}),
        ...(ctrlFilterCategory ? { control_category_code: ctrlFilterCategory } : {}),
        ...(ctrlFilterCriticality ? { criticality_code: ctrlFilterCriticality } : {}),
        limit: 200,
      })
      setLibraryControls((res.items ?? []) as unknown as LibraryControl[])
      setCtrlTotal(res.total ?? 0)
    } catch (e) {
      setCtrlError(e instanceof Error ? e.message : "Failed to load control library")
    } finally {
      setCtrlLoading(false)
    }
  }, [ctrlSearch, ctrlFilterCategory, ctrlFilterCriticality, selectedOrgId, selectedWorkspaceId])

  // ── Load risk library ─────────────────────────────────────────────────────
  const loadRisks = useCallback(async () => {
    if (!selectedOrgId || !selectedWorkspaceId) return
    setRiskLoading(true)
    setRiskError(null)
    try {
      const [risksRes, riskDepRes] = await Promise.all([
        listGlobalRisks({}),
        listRiskLibraryDeployments(selectedOrgId, selectedWorkspaceId),
      ])
      setGlobalRisks((risksRes as { items?: GlobalRisk[] }).items ?? [])
      setRiskDeployments((riskDepRes.items ?? []) as unknown as RiskDeployment[])
    } catch (e) {
      setRiskError(e instanceof Error ? e.message : "Failed to load risk library")
    } finally {
      setRiskLoading(false)
    }
  }, [selectedOrgId, selectedWorkspaceId])

  useEffect(() => {
    if (ready && selectedOrgId) loadFrameworks()
  }, [loadFrameworks, ready, selectedOrgId])

  useEffect(() => {
    if (ready && selectedOrgId && activeTab === "controls") loadControls()
  }, [loadControls, ready, selectedOrgId, activeTab])

  useEffect(() => {
    if (ready && selectedOrgId && selectedWorkspaceId && activeTab === "risks") loadRisks()
  }, [loadRisks, ready, selectedOrgId, selectedWorkspaceId, activeTab])

  // Re-run control search when filters change
  useEffect(() => {
    if (activeTab === "controls" && selectedOrgId) {
      const t = setTimeout(() => loadControls(), 300)
      return () => clearTimeout(t)
    }
  }, [ctrlSearch, ctrlFilterCategory, ctrlFilterCriticality, activeTab, loadControls, selectedOrgId])

  // ── Derived ───────────────────────────────────────────────────────────────
  const deployedMap = useMemo(
    () => new Map(deployments.map(d => [d.source_framework_id || d.framework_id, d])),
    [deployments],
  )
  const riskDeployedMap = useMemo(() => new Map(riskDeployments.map(d => [d.global_risk_id, d])), [riskDeployments])
  const updatesCount = useMemo(() => deployments.filter(d => d.has_update).length, [deployments])

  const categories = useMemo(() => {
    const seen = new Set<string>()
    const counts = new Map<string, number>()
    frameworks.forEach(fw => {
      if (fw.framework_category_code) {
        if (!seen.has(fw.framework_category_code)) {
          seen.add(fw.framework_category_code)
        }
        counts.set(fw.framework_category_code, (counts.get(fw.framework_category_code) || 0) + 1)
      }
    })
    return [...seen]
      .map(code => {
        const fw = frameworks.find(f => f.framework_category_code === code)
        return { code, name: fw?.category_name || code, count: counts.get(code) || 0 }
      })
      .sort((a, b) => a.name.localeCompare(b.name))
  }, [frameworks])

  const filteredFrameworks = useMemo(() => {
    const latestByCode = new Map<string, FrameworkResponse>()
    
    frameworks.forEach(fw => {
      const existing = latestByCode.get(fw.framework_code)
      if (!existing) {
        latestByCode.set(fw.framework_code, fw)
      } else {
        const existingVer = existing.latest_version_code ?? ""
        const newVer = fw.latest_version_code ?? ""
        if (newVer > existingVer) {
          latestByCode.set(fw.framework_code, fw)
        }
      }
    })
    
    const deduped = Array.from(latestByCode.values())
    
    return deduped.filter(fw => {
      if (search && !fw.name?.toLowerCase().includes(search.toLowerCase()) && !fw.framework_code.toLowerCase().includes(search.toLowerCase())) return false
      if (filterCategory && fw.framework_category_code !== filterCategory) return false
      return true
    })
  }, [frameworks, search, filterCategory])

  // Control library derived filters
  const ctrlCategories = useMemo(() => {
    const seen = new Map<string, string>()
    libraryControls.forEach(c => { if (c.control_category_code) seen.set(c.control_category_code, c.category_name || c.control_category_code) })
    return [...seen.entries()].map(([code, name]) => ({ code, name })).sort((a, b) => a.name.localeCompare(b.name))
  }, [libraryControls])

  const ctrlCriticalities = useMemo(() => {
    const seen = new Map<string, string>()
    libraryControls.forEach(c => { if (c.criticality_code) seen.set(c.criticality_code, c.criticality_name || c.criticality_code) })
    return [...seen.entries()].map(([code, name]) => ({ code, name })).sort((a, b) => a.name.localeCompare(b.name))
  }, [libraryControls])

  // Risk derived
  const riskCategories = useMemo(() => {
    const seen = new Set<string>()
    return globalRisks
      .filter(r => r.risk_category_code && !seen.has(r.risk_category_code) && seen.add(r.risk_category_code))
      .map(r => ({ code: r.risk_category_code, name: r.risk_category_name || r.risk_category_code }))
      .sort((a, b) => a.name.localeCompare(b.name))
  }, [globalRisks])

  const filteredRisks = useMemo(() => globalRisks.filter(r => {
    if (riskFilterCategory && r.risk_category_code !== riskFilterCategory) return false
    if (!riskSearch) return true
    const q = riskSearch.toLowerCase()
    return (r.title?.toLowerCase().includes(q) || r.risk_code.toLowerCase().includes(q) || r.risk_category_name?.toLowerCase().includes(q))
  }), [globalRisks, riskSearch, riskFilterCategory])

  const selectableRisks = useMemo(() => filteredRisks.filter(r => !riskDeployedMap.has(r.id)), [filteredRisks, riskDeployedMap])
  const allSelectableSelected = selectableRisks.length > 0 && selectableRisks.every(r => selectedRisks.has(r.id))

  const toggleAllRisks = () => {
    if (allSelectableSelected) {
      setSelectedRisks(prev => { const next = new Set(prev); selectableRisks.forEach(r => next.delete(r.id)); return next })
    } else {
      setSelectedRisks(prev => { const next = new Set(prev); selectableRisks.forEach(r => next.add(r.id)); return next })
    }
  }

  // ── Actions ───────────────────────────────────────────────────────────────
  const handleDeploy = async (fw: FrameworkResponse) => {
    if (!selectedOrgId || !selectedWorkspaceId) {
      const msg = "Select an organization and workspace before deploying a framework"
      setDeployError(msg)
      addToast(msg, "error")
      return
    }
    setDeployingId(fw.id)
    setDeployError(null)
    try {
      const versionsRes = await listVersions(fw.id, {
        scope_org_id: selectedOrgId,
        scope_workspace_id: selectedWorkspaceId,
      })
      const published = versionsRes.items.filter(v => v.lifecycle_state === "published")
      const latestVersion = published[0]
      if (!latestVersion) throw new Error("No published version available to deploy")

      const existingDeployment = deployedMap.get(fw.id)
      if (existingDeployment?.has_update) {
        await updateDeployment(existingDeployment.id, { version_id: latestVersion.id })
        addToast(`${fw.name} upgraded to v${latestVersion.version_code ?? latestVersion.id}`)
      } else {
        await deployFramework({
          framework_id: fw.id,
          version_id: latestVersion.id,
          org_id: selectedOrgId,
          workspace_id: selectedWorkspaceId,
        })
        addToast(`${fw.name} deployed successfully`)
      }
      await loadFrameworks(true)
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Deployment failed"
      setDeployError(msg)
      addToast(msg, "error")
    } finally {
      setDeployingId(null)
    }
  }

  const handleUndeploy = (dep: FrameworkDeploymentResponse, fw: FrameworkResponse) => {
    setUndeployConfirm({ dep, fw })
  }

  const confirmUndeploy = async () => {
    if (!undeployConfirm) return
    const { dep, fw } = undeployConfirm
    setUndeployConfirm(null)
    try {
      await deleteDeployment(dep.id)
      await loadFrameworks(true)
      addToast(`${fw.name} removed from workspace`)
    } catch (e) {
      addToast(e instanceof Error ? e.message : "Failed to remove deployment", "error")
    }
  }

  const handleDeployRisks = async () => {
    if (!selectedOrgId || !selectedWorkspaceId || selectedRisks.size === 0) return
    setDeployingRisks(true)
    setRiskError(null)
    try {
      await deployGlobalRisks(selectedOrgId, selectedWorkspaceId, Array.from(selectedRisks))
      const count = selectedRisks.size
      setSelectedRisks(new Set())
      await loadRisks()
      addToast(`${count} risk${count > 1 ? "s" : ""} deployed to workspace`)
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to deploy risks"
      setRiskError(msg)
      addToast(msg, "error")
    } finally {
      setDeployingRisks(false)
    }
  }

  const handleRemoveRisk = (deploymentId: string, riskTitle: string) => {
    setRemoveConfirm({ id: deploymentId, title: riskTitle })
  }

  const confirmRemoveRisk = async () => {
    if (!removeConfirm) return
    const { id, title } = removeConfirm
    setRemoveConfirm(null)
    try {
      await removeRiskDeployment(id)
      await loadRisks()
      addToast(`"${title}" removed from workspace`)
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to remove risk"
      setRiskError(msg)
      addToast(msg, "error")
    }
  }

  const toggleRisk = (id: string) => {
    setSelectedRisks(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }

  if (fwLoading && activeTab === "frameworks") {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 rounded-md bg-muted animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[1,2,3,4,5,6].map(i => <div key={i} className="h-32 rounded-xl bg-muted animate-pulse" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight font-secondary">Framework Library</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Browse and deploy compliance frameworks, controls, and risks to your organization
          </p>
        </div>
        <div className="flex items-center gap-2">
          <OrgWorkspaceSwitcher />
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => {
            if (activeTab === "frameworks") loadFrameworks(true)
            else if (activeTab === "controls") loadControls()
            else loadRisks()
          }} disabled={refreshing} title="Refresh">
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b pb-0">
        {/* Framework Library */}
        <button
          onClick={() => setActiveTab("frameworks")}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
            activeTab === "frameworks" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted"
          }`}
        >
          <BookOpen className="h-4 w-4" />
          Framework Library
          {deployments.length > 0 && (
            <Badge variant="outline" className="text-[9px] px-1.5 py-0 font-semibold">{deployments.length}</Badge>
          )}
          {updatesCount > 0 && (
            <Badge className="text-[9px] px-1.5 py-0 font-semibold bg-blue-500/15 text-blue-700 border-blue-500/30">
              {updatesCount} update{updatesCount > 1 ? "s" : ""}
            </Badge>
          )}
        </button>

        {/* Control Library */}
        {/* <button
          onClick={() => setActiveTab("controls")}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
            activeTab === "controls" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted"
          }`}
        >
          <ShieldCheck className="h-4 w-4" />
          Control Library
          {ctrlTotal > 0 && (
            <Badge variant="outline" className="text-[9px] px-1.5 py-0 font-semibold">{ctrlTotal}</Badge>
          )}
        </button> */}

        {/* Risk Library */}
        {/* <button
          onClick={() => setActiveTab("risks")}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
            activeTab === "risks" ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted"
          }`}
        >
          <ShieldAlert className="h-4 w-4" />
          Risk Library
          {riskDeployments.length > 0 && (
            <Badge variant="outline" className="text-[9px] px-1.5 py-0 font-semibold">{riskDeployments.length}</Badge>
          )}
        </button> */}
      </div>

      {/* ── FRAMEWORKS TAB ─────────────────────────────────────────────────── */}
      {activeTab === "frameworks" && (
        <>
          {updatesCount > 0 && (
            <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-3 flex items-center gap-3">
              <ArrowUpCircle className="h-4 w-4 text-blue-600 shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-blue-700">
                  {updatesCount} framework update{updatesCount > 1 ? "s" : ""} available
                </p>
                <p className="text-xs text-muted-foreground">New versions are ready to deploy to your organization.</p>
              </div>
            </div>
          )}

          {fwError && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 flex items-center gap-3">
              <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
              <p className="text-sm text-destructive flex-1">{fwError}</p>
            </div>
          )}
          {deployError && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 flex items-center gap-3">
              <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
              <p className="text-sm text-destructive flex-1">{deployError}</p>
              <button className="text-xs underline text-destructive" onClick={() => setDeployError(null)}>Dismiss</button>
            </div>
          )}

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span><span className="font-semibold text-foreground">{frameworks.length}</span> available</span>
            <span><span className="font-semibold text-foreground">{deployments.length}</span> deployed to workspace</span>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input placeholder="Search frameworks..." value={search} onChange={e => setSearch(e.target.value)} className="pl-8 pr-7 h-8 text-sm" />
              {search && (
                <button onClick={() => setSearch("")} aria-label="Clear search" className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
            {categories.length > 1 && (
              <FilterChips options={categories} value={filterCategory} onChange={setFilterCategory} />
            )}
          </div>

          {filteredFrameworks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <Store className="h-12 w-12 text-muted-foreground/40" />
              <p className="text-base font-medium text-muted-foreground">
                {search || filterCategory ? "No frameworks match your filters" : "No approved frameworks in the marketplace yet"}
              </p>
              {!search && !filterCategory && (
                <p className="text-xs text-muted-foreground max-w-xs">
                  Frameworks become available here after a super admin approves them in the Library.
                </p>
              )}
              {(search || filterCategory) && (
                <Button variant="ghost" size="sm" onClick={() => { setSearch(""); setFilterCategory("") }}>
                  Clear filters
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredFrameworks.map(fw => (
                <FrameworkCard key={fw.id} framework={fw} deployment={deployedMap.get(fw.id) ?? null}
                  onDeploy={handleDeploy} onUndeploy={handleUndeploy} onViewControls={setControlsDrawer} deploying={deployingId === fw.id} />
              ))}
            </div>
          )}
        </>
      )}

      {/* ── CONTROL LIBRARY TAB ────────────────────────────────────────────── */}
      {activeTab === "controls" && (
        <>
          <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 flex items-start gap-3">
            <ShieldCheck className="h-4 w-4 text-primary shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-foreground">Enterprise Control Library</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Browse the full catalog of platform controls across all approved frameworks. Deploy frameworks from the Framework Library tab to activate controls in your organization.
              </p>
            </div>
          </div>

          {ctrlError && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 flex items-center gap-3">
              <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
              <p className="text-sm text-destructive flex-1">{ctrlError}</p>
              <button className="text-xs underline text-destructive" onClick={() => setCtrlError(null)}>Dismiss</button>
            </div>
          )}

          <div className="flex items-center gap-3 flex-wrap">
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input placeholder="Search controls by name or code..." value={ctrlSearch} onChange={e => setCtrlSearch(e.target.value)} className="pl-8 pr-7 h-8 text-sm" />
              {ctrlSearch && (
                <button onClick={() => setCtrlSearch("")} aria-label="Clear search" className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Category filter */}
          {ctrlCategories.length > 1 && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-muted-foreground flex items-center gap-1 shrink-0">
                <Tag className="h-3 w-3" />Category:
              </span>
              <FilterChips options={ctrlCategories} value={ctrlFilterCategory} onChange={setCtrlFilterCategory} />
            </div>
          )}

          {/* Criticality filter */}
          {ctrlCriticalities.length > 1 && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-muted-foreground flex items-center gap-1 shrink-0">
                <Filter className="h-3 w-3" />Criticality:
              </span>
              <FilterChips options={ctrlCriticalities} value={ctrlFilterCriticality} onChange={setCtrlFilterCriticality} />
            </div>
          )}

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span><span className="font-semibold text-foreground">{ctrlTotal}</span> controls in library</span>
            {(ctrlFilterCategory || ctrlFilterCriticality || ctrlSearch) && (
              <span><span className="font-semibold text-foreground">{libraryControls.length}</span> shown</span>
            )}
          </div>

          {ctrlLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {[1,2,3,4,5,6].map(i => <div key={i} className="h-28 rounded-xl bg-muted animate-pulse" />)}
            </div>
          ) : libraryControls.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <ShieldCheck className="h-12 w-12 text-muted-foreground/40" />
              <p className="text-base font-medium text-muted-foreground">
                {ctrlSearch || ctrlFilterCategory || ctrlFilterCriticality
                  ? "No controls match your filters"
                  : "No controls in the library yet"}
              </p>
              {(ctrlSearch || ctrlFilterCategory || ctrlFilterCriticality) && (
                <Button variant="ghost" size="sm" onClick={() => { setCtrlSearch(""); setCtrlFilterCategory(""); setCtrlFilterCriticality("") }}>
                  Clear filters
                </Button>
              )}
              {!ctrlSearch && !ctrlFilterCategory && !ctrlFilterCriticality && (
                <p className="text-xs text-muted-foreground max-w-xs">
                  Controls become available here from approved frameworks in the library.
                </p>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {libraryControls.map(ctrl => (
                <ControlCard key={ctrl.id} control={ctrl} />
              ))}
            </div>
          )}
        </>
      )}

      {/* ── RISK LIBRARY TAB ───────────────────────────────────────────────── */}
      {activeTab === "risks" && (
        <>
          {riskError && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 flex items-center gap-3">
              <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
              <p className="text-sm text-destructive flex-1">{riskError}</p>
              <button className="text-xs underline text-destructive" onClick={() => setRiskError(null)}>Dismiss</button>
            </div>
          )}

          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span><span className="font-semibold text-foreground">{globalRisks.length}</span> in library</span>
              <span><span className="font-semibold text-foreground">{riskDeployments.length}</span> deployed to workspace</span>
            </div>
            <div className="flex items-center gap-2">
              {selectableRisks.length > 0 && (
                <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={toggleAllRisks}>
                  {allSelectableSelected ? "Deselect all" : `Select all ${selectableRisks.length}`}
                </Button>
              )}
              {selectedRisks.size > 0 && (
                <Button size="sm" onClick={handleDeployRisks} disabled={deployingRisks || !selectedWorkspaceId} className="gap-1.5">
                  {deployingRisks ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
                  Deploy {selectedRisks.size} risk{selectedRisks.size > 1 ? "s" : ""}
                </Button>
              )}
            </div>
          </div>

          {!selectedWorkspaceId && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 flex items-center gap-3">
              <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />
              <p className="text-sm text-amber-700">Select a workspace to deploy risks to.</p>
            </div>
          )}

          <div className="flex items-center gap-3 flex-wrap">
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input placeholder="Search risks..." value={riskSearch} onChange={e => setRiskSearch(e.target.value)} className="pl-8 pr-7 h-8 text-sm" />
              {riskSearch && (
                <button onClick={() => setRiskSearch("")} aria-label="Clear search" className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
            {riskCategories.length > 1 && (
              <FilterChips options={riskCategories} value={riskFilterCategory} onChange={setRiskFilterCategory} />
            )}
          </div>

          {riskLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {[1,2,3,4,5,6].map(i => <div key={i} className="h-28 rounded-xl bg-muted animate-pulse" />)}
            </div>
          ) : filteredRisks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <ShieldAlert className="h-12 w-12 text-muted-foreground/40" />
              <p className="text-base font-medium text-muted-foreground">
                {riskSearch || riskFilterCategory ? "No risks match your filters" : "No risks in the global library yet"}
              </p>
              {!riskSearch && !riskFilterCategory ? (
                <p className="text-xs text-muted-foreground max-w-xs">
                  Global risks are managed by your admin team in the Risk Library.
                </p>
              ) : (
                <Button variant="ghost" size="sm" onClick={() => { setRiskSearch(""); setRiskFilterCategory("") }}>
                  Clear filters
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredRisks.map(risk => (
                <RiskCard
                  key={risk.id}
                  risk={risk}
                  deployment={riskDeployedMap.get(risk.id) ?? null}
                  selected={selectedRisks.has(risk.id)}
                  onToggleSelect={toggleRisk}
                  onRemove={handleRemoveRisk}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Controls preview drawer overlay */}
      {controlsDrawer && (
        <>
          <div className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm" onClick={() => setControlsDrawer(null)} />
          <ControlsDrawer deployment={controlsDrawer} onClose={() => setControlsDrawer(null)} />
        </>
      )}

      {/* Framework undeploy confirm dialog */}
      <Dialog open={!!undeployConfirm} onOpenChange={open => { if (!open) setUndeployConfirm(null) }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Remove framework deployment?</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">&ldquo;{undeployConfirm?.fw.name}&rdquo;</span> will be removed from your organization.
            </p>
            <p className="text-xs text-muted-foreground">
              Controls and tests linked to this framework will no longer be associated with your organization. This action does not delete existing data.
            </p>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="ghost" size="sm" onClick={() => setUndeployConfirm(null)}>Cancel</Button>
            <Button variant="destructive" size="sm" onClick={confirmUndeploy}>
              <Trash2 className="h-3.5 w-3.5 mr-1.5" />
              Remove Deployment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Risk removal confirm dialog */}
      <Dialog open={!!removeConfirm} onOpenChange={open => { if (!open) setRemoveConfirm(null) }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Remove risk from workspace?</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">&ldquo;{removeConfirm?.title}&rdquo;</span> will be removed from this workspace.
            </p>
            <p className="text-xs text-muted-foreground">
              The global risk will remain in the library and can be re-deployed at any time.
            </p>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="ghost" size="sm" onClick={() => setRemoveConfirm(null)}>Cancel</Button>
            <Button variant="destructive" size="sm" onClick={confirmRemoveRisk}>
              <Trash2 className="h-3.5 w-3.5 mr-1.5" />
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  )
}
