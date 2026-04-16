"use client";

import { useEffect, useState, useMemo, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Input,
  Label,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@kcontrol/ui";
import {
  ShieldAlert,
  Plus,
  Search,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  AlertTriangle,
  Target,
  Pencil,
  Trash2,
  ClipboardCheck,
  FileText,
  Link2,
  MessageSquare,
  X,
  Clock,
  TrendingUp,
  TrendingDown,
  ArrowUpDown,
  User2,
  Users,
  CalendarCheck,
  CheckCircle2,
  Check,
  Circle,
  ExternalLink,
  Wrench,
  GitMerge,
  Sparkles,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  Play,
  LayoutList,
  Table2,
  ListChecks,
  Save,
  Send,
  Zap,
  TriangleAlert,
  ArrowRight,
} from "lucide-react";
import {
  listRisks,
  listRiskCategories,
  listRiskLevels,
  listTreatmentTypes,
  createRisk,
  updateRisk,
  deleteRisk,
  listAssessments,
  createAssessment,
  getTreatmentPlan,
  createTreatmentPlan,
  updateTreatmentPlan,
  listRiskControls,
  addRiskControl,
  removeRiskControl,
  listReviewEvents,
  addReviewEvent,
  listAllControls,
  getRiskSummary,
  listRiskGroups,
  assignRiskGroup,
  unassignRiskGroup,
  getReviewSchedule,
  upsertReviewSchedule,
  completeReview,
  listOverdueReviews,
  listTasks,
  getRiskHeatMap,
} from "@/lib/api/grc";
import { RiskHeatmap } from "@/components/grc/RiskHeatmap";
import { RiskQuestionnaireModal } from "@/components/grc/RiskQuestionnaireModal";
import { CommentsSection } from "@/components/comments/CommentsSection";
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection";
import { getCommentCount } from "@/lib/api/comments";
import { getAttachmentCount } from "@/lib/api/attachments";
import type {
  RiskResponse,
  RiskListResponse,
  DimensionResponse,
  RiskLevelResponse,
  RiskAssessmentResponse,
  TreatmentPlanResponse,
  RiskControlMappingResponse,
  RiskReviewEventResponse,
  RiskGroupAssignmentResponse,
  ReviewScheduleResponse,
  OverdueReviewResponse,
  RiskSummaryResponse,
  CreateRiskRequest,
  UpdateRiskRequest,
  ControlResponse,
  TaskResponse,
  HeatMapResponse,
} from "@/lib/types/grc";
import type { OrgMemberResponse } from "@/lib/types/orgs";
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext";
import { OrgWorkspaceSwitcher } from "@/components/layout/OrgWorkspaceSwitcher";
import { ReadOnlyBanner } from "@/components/layout/ReadOnlyBanner";
import { useAccess } from "@/components/providers/AccessProvider";
import { TaskCreateSlideOver } from "@/components/tasks/TaskCreateSlideOver";
import { FormFillChat } from "@/components/ai/FormFillChat";
import { EntitySpreadsheet } from "@/components/spreadsheet/EntitySpreadsheet";
import { ExportImportToolbar } from "@/components/spreadsheet/ExportImportToolbar";
import { ImportResultDialog } from "@/components/spreadsheet/ImportResultDialog";
import type { ImportResult } from "@/components/spreadsheet/ImportResultDialog";
import { risksColumns } from "@/components/spreadsheet/risksConfig";
import type { RiskSpreadsheetRow } from "@/components/spreadsheet/risksConfig";
import {
  exportRisks,
  importRisks,
  getRisksImportTemplate,
} from "@/lib/api/grc";
import { listFrameworks } from "@/lib/api/grc";
import type { FrameworkResponse } from "@/lib/types/grc";
import {
  enqueueBulkLink,
  getRiskAdvisorJobStatus,
  listPendingMappings,
  bulkApproveMappings,
  bulkRejectMappings,
} from "@/lib/api/riskAdvisor";
import type { PendingMapping, JobStatusResponse } from "@/lib/api/riskAdvisor";

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const RISK_STATUS_META: Record<string, { label: string; cls: string }> = {
  identified: {
    label: "Identified",
    cls: "text-muted-foreground bg-muted border-border",
  },
  assessed: {
    label: "Assessed",
    cls: "text-blue-600 bg-blue-500/10 border-blue-500/20",
  },
  treating: {
    label: "Treating",
    cls: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20",
  },
  accepted: {
    label: "Accepted",
    cls: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20",
  },
  closed: {
    label: "Closed",
    cls: "text-slate-500 bg-slate-500/10 border-slate-500/20",
  },
};

const TREATMENT_PLAN_STATUS_META: Record<
  string,
  { label: string; cls: string }
> = {
  draft: { label: "Draft", cls: "text-muted-foreground" },
  active: { label: "Active", cls: "text-blue-500" },
  completed: { label: "Completed", cls: "text-emerald-500" },
  cancelled: { label: "Cancelled", cls: "text-amber-500" },
};

const LEVEL_COLORS: Record<string, { label: string; border: string; badge: string; icon: string }> = {
  critical: { label: "Critical", border: "border-l-red-500",    badge: "bg-red-500/15 text-red-400 border-red-500/30",    icon: "text-red-400" },
  high:     { label: "High",     border: "border-l-orange-500", badge: "bg-orange-500/15 text-orange-400 border-orange-500/30", icon: "text-orange-400" },
  medium:   { label: "Medium",   border: "border-l-amber-500",  badge: "bg-amber-500/15 text-amber-400 border-amber-500/30",  icon: "text-amber-400" },
  low:      { label: "Low",      border: "border-l-green-500",  badge: "bg-green-500/15 text-green-400 border-green-500/30",  icon: "text-green-400" },
}

const LEVEL_ORDER: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};
const STATUS_ORDER: Record<string, number> = {
  identified: 1,
  assessed: 2,
  treating: 3,
  accepted: 4,
  closed: 5,
};

const TASK_PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/10 text-red-500 border-red-500/30",
  high: "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium: "bg-amber-500/10 text-amber-500 border-amber-500/30",
  low: "bg-green-500/10 text-green-500 border-green-500/30",
};

const TASK_STATUS_STYLES: Record<string, string> = {
  open: "text-muted-foreground",
  in_progress: "text-blue-500",
  completed: "text-green-500",
  blocked: "text-red-500",
};

function TaskStatusIcon({ status }: { status: string }) {
  if (status === "completed")
    return <CheckCircle2 className="w-3 h-3 text-green-500" />;
  if (status === "in_progress")
    return <Clock className="w-3 h-3 text-blue-500" />;
  if (status === "blocked")
    return <AlertTriangle className="w-3 h-3 text-red-500" />;
  return <Circle className="w-3 h-3 text-muted-foreground" />;
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function getJwtSubject(): string | null {
  try {
    const token = localStorage.getItem("access_token");
    if (!token) return null;
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub || null;
  } catch {
    return null;
  }
}

function StatusBadge({ status }: { status: string }) {
  const meta = RISK_STATUS_META[status] ?? {
    label: status,
    cls: "text-muted-foreground bg-muted border-border",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold ${meta.cls}`}
    >
      {meta.label}
    </span>
  );
}

function LevelBadge({ name, color }: { name: string; color?: string | null }) {
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold"
      style={{
        color: color ?? undefined,
        backgroundColor: color ? `${color}10` : undefined,
        borderColor: color ? `${color}40` : undefined,
      }}
    >
      {name}
    </span>
  );
}

function ScoreBar({ score, max = 25 }: { score: number | null; max?: number }) {
  if (score == null)
    return <span className="text-xs text-muted-foreground">--</span>;
  const pct = Math.min((score / max) * 100, 100);
  const color =
    score >= 16
      ? "#ef4444"
      : score >= 11
        ? "#f97316"
        : score >= 6
          ? "#f59e0b"
          : "#10b981";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-medium" style={{ color }}>
        {score}
      </span>
    </div>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// ─────────────────────────────────────────────────────────────────────────────
// Searchable Combobox
// ─────────────────────────────────────────────────────────────────────────────

function SearchCombobox<T>({
  placeholder,
  value,
  options,
  getId,
  getLabel,
  onSelect,
}: {
  placeholder: string;
  value: string;
  options: T[];
  getId: (o: T) => string;
  getLabel: (o: T) => string;
  onSelect: (id: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);

  const selected = options.find((o) => getId(o) === value);
  const displayValue = selected ? getLabel(selected) : "";
  const filtered =
    query === ""
      ? options
      : options.filter((o) =>
          getLabel(o).toLowerCase().includes(query.toLowerCase())
        );

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          className="w-full h-8 rounded-md border border-input bg-background text-sm px-2 pr-6"
          placeholder={open ? "Search…" : displayValue || placeholder}
          value={open ? query : displayValue}
          onFocus={() => {
            setOpen(true);
            setQuery("");
          }}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
        {value && (
          <button
            type="button"
            className="absolute right-1.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground text-xs"
            onMouseDown={(e) => {
              e.preventDefault();
              onSelect("");
            }}
          >
            ×
          </button>
        )}
      </div>
      {open && filtered.length > 0 && (
        <div className="absolute z-50 top-full left-0 right-0 mt-0.5 bg-popover border border-border rounded-md shadow-md max-h-48 overflow-y-auto">
          {filtered.map((o) => (
            <button
              key={getId(o)}
              type="button"
              className={`w-full text-left px-3 py-1.5 text-sm hover:bg-accent ${getId(o) === value ? "bg-accent/50 font-medium" : ""}`}
              onMouseDown={(e) => {
                e.preventDefault();
                onSelect(getId(o));
                setOpen(false);
                setQuery("");
              }}
            >
              {getLabel(o)}
            </button>
          ))}
        </div>
      )}
      {open && filtered.length === 0 && (
        <div className="absolute z-50 top-full left-0 right-0 mt-0.5 bg-popover border border-border rounded-md shadow-md px-3 py-2 text-sm text-muted-foreground">
          No results
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Risk Dashboard KPI Bar
// ─────────────────────────────────────────────────────────────────────────────

const KPI_STATS = [
  {
    key: "total_risks",
    label: "Total Risks",
    icon: ShieldAlert,
    iconCls: "text-primary",
    borderCls: "border-l-primary",
    numCls: "text-foreground",
  },
  {
    key: "open_count",
    label: "Open",
    icon: TrendingUp,
    iconCls: "text-blue-500",
    borderCls: "border-l-blue-500",
    numCls: "text-blue-600",
  },
  {
    key: "critical_count",
    label: "Critical",
    icon: AlertTriangle,
    iconCls: "text-red-500",
    borderCls: "border-l-red-500",
    numCls: "text-red-600",
  },
  {
    key: "high_count",
    label: "High",
    icon: TrendingUp,
    iconCls: "text-orange-500",
    borderCls: "border-l-orange-500",
    numCls: "text-orange-600",
  },
  {
    key: "medium_count",
    label: "Medium",
    icon: TrendingDown,
    iconCls: "text-amber-500",
    borderCls: "border-l-amber-500",
    numCls: "text-amber-600",
  },
  {
    key: "low_count",
    label: "Low",
    icon: CheckCircle2,
    iconCls: "text-green-500",
    borderCls: "border-l-green-500",
    numCls: "text-green-600",
  },
  {
    key: "closed_this_week",
    label: "Closed This Week",
    icon: CalendarCheck,
    iconCls: "text-emerald-500",
    borderCls: "border-l-emerald-500",
    numCls: "text-emerald-600",
  },
] as const;

function RiskDashboardBar({
  orgId,
  workspaceId,
}: {
  orgId?: string;
  workspaceId?: string;
}) {
  const [summary, setSummary] = useState<RiskSummaryResponse | null>(null);

  useEffect(() => {
    getRiskSummary(orgId, workspaceId)
      .then(setSummary)
      .catch(() => {});
  }, [orgId, workspaceId]);

  if (!summary) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
      {KPI_STATS.map(
        ({ key, label, icon: Icon, iconCls, borderCls, numCls }) => {
          const val =
            (summary[key as keyof RiskSummaryResponse] as number) ?? 0;
          return (
            <div
              key={key}
              className={`relative rounded-xl border bg-card border-l-[3px] ${borderCls} px-4 py-3 flex items-center gap-3`}
            >
              <div className={`shrink-0 rounded-lg p-2 bg-muted`}>
                <Icon className={`w-4 h-4 ${iconCls}`} />
              </div>
              <div className="min-w-0">
                <div
                  className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}
                >
                  {val}
                </div>
                <div className="text-[11px] text-muted-foreground mt-0.5 truncate">
                  {label}
                </div>
              </div>
              {key === "critical_count" && val > 0 && (
                <div className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              )}
            </div>
          );
        }
      )}
    </div>
  );
}

// ── Overdue Reviews Banner ─────────────────────────────────────────────────

function OverdueReviewsBanner({ orgId }: { orgId?: string }) {
  const [items, setItems] = useState<OverdueReviewResponse[]>([]);
  useEffect(() => {
    if (!orgId) return;
    listOverdueReviews(orgId)
      .then(setItems)
      .catch(() => {});
  }, [orgId]);
  if (items.length === 0) return null;
  return (
    <div className="rounded-xl border border-amber-500/40 bg-gradient-to-r from-amber-500/10 to-orange-500/5 px-4 py-3">
      <div className="flex items-center gap-2 mb-3">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/20">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
        </div>
        <div>
          <span className="text-sm font-semibold text-amber-700 dark:text-amber-400">
            {items.length} Risk Review{items.length !== 1 ? "s" : ""} Overdue
          </span>
          <span className="text-xs text-muted-foreground ml-2">
            Immediate attention required
          </span>
        </div>
        <div className="ml-auto">
          <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-700 dark:text-amber-400 text-[10px] font-bold border border-amber-500/30 animate-pulse">
            ACTION NEEDED
          </span>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1.5">
        {items.slice(0, 6).map((r) => (
          <div
            key={r.id}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background/60 border border-amber-500/20 text-xs"
          >
            <Clock className="w-3 h-3 text-amber-500 shrink-0" />
            <span className="font-medium text-foreground truncate flex-1">
              {r.risk_title || r.risk_id}
            </span>
            <span className="text-amber-600 font-semibold shrink-0">
              {r.next_review_date?.split("T")[0]}
            </span>
          </div>
        ))}
        {items.length > 6 && (
          <div className="flex items-center justify-center px-3 py-2 rounded-lg bg-background/60 border border-amber-500/20 text-xs text-muted-foreground">
            +{items.length - 6} more overdue
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Assign Group Dialog
// ─────────────────────────────────────────────────────────────────────────────

function AssignGroupDialog({
  riskId,
  onAssigned,
  onClose,
}: {
  riskId: string;
  onAssigned: () => void;
  onClose: () => void;
}) {
  const { selectedOrgId } = useOrgWorkspace();
  const [groups, setGroups] = useState<
    { id: string; code: string; name: string }[]
  >([]);
  const [groupId, setGroupId] = useState("");
  const [role, setRole] = useState("responsible");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    import("@/lib/api/admin").then(({ listGroups }) =>
      listGroups(selectedOrgId ? { scope_org_id: selectedOrgId } : undefined)
        .then((res) =>
          setGroups(
            (res.groups ?? []).map((g) => ({
              id: g.id,
              code: g.code,
              name: g.name,
            }))
          )
        )
        .catch(() => {})
    );
  }, [selectedOrgId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId) {
      setError("Select a group");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await assignRiskGroup(riskId, { group_id: groupId, role });
      onAssigned();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Assign Group</DialogTitle>
          <DialogDescription>
            Assign a responsible group to this risk.
          </DialogDescription>
        </DialogHeader>
        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Group <span className="text-destructive">*</span>
            </Label>
            <select
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
              required
            >
              <option value="">-- Select group --</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name} ({g.code})
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Role
            </Label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
            >
              <option value="responsible">Responsible</option>
              <option value="accountable">Accountable</option>
              <option value="consulted">Consulted</option>
              <option value="informed">Informed</option>
            </select>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="h-9 px-4"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Assigning..." : "Assign Group"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Review Schedule Dialog
// ─────────────────────────────────────────────────────────────────────────────

function ReviewScheduleDialog({
  riskId,
  existing,
  onSaved,
  onClose,
}: {
  riskId: string;
  existing: ReviewScheduleResponse | null;
  onSaved: () => void;
  onClose: () => void;
}) {
  const [frequency, setFrequency] = useState(
    existing?.review_frequency ?? "quarterly"
  );
  const [nextDate, setNextDate] = useState(
    existing?.next_review_date?.split("T")[0] ?? ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nextDate) {
      setError("Next review date is required");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await upsertReviewSchedule(riskId, {
        review_frequency: frequency,
        next_review_date: nextDate,
      });
      onSaved();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>
            {existing ? "Edit Review Schedule" : "Set Review Schedule"}
          </DialogTitle>
          <DialogDescription>
            Configure the review schedule for this risk.
          </DialogDescription>
        </DialogHeader>
        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Frequency <span className="text-destructive">*</span>
            </Label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
            >
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="semi_annual">Semi-Annual</option>
              <option value="annual">Annual</option>
            </select>
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Next Review Date <span className="text-destructive">*</span>
            </Label>
            <Input
              type="date"
              value={nextDate}
              onChange={(e) => setNextDate(e.target.value)}
              required
              className="h-8 text-sm"
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="h-9 px-4"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Saving..." : "Save Schedule"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Create Risk Dialog
// ─────────────────────────────────────────────────────────────────────────────

function slugifyRisk(text: string): string {
  return (
    text
      .toUpperCase()
      .replace(/\s+/g, "_")
      .replace(/[^A-Z0-9_]/g, "")
      .replace(/^[^A-Z0-9]+/, "")
      .replace(/[^A-Z0-9]+$/, "")
      .slice(0, 32) || ""
  );
}

function CreateRiskDialog({
  categories,
  levels,
  treatmentTypes,
  defaultOrgId,
  defaultWorkspaceId,
  onCreated,
  onClose,
}: {
  categories: DimensionResponse[];
  levels: RiskLevelResponse[];
  treatmentTypes: DimensionResponse[];
  defaultOrgId?: string;
  defaultWorkspaceId?: string;
  onCreated: () => void;
  onClose: () => void;
}) {
  const currentUserId = getJwtSubject();
  const [title, setTitle] = useState("");
  const [code, setCode] = useState("");
  const [codeEdited, setCodeEdited] = useState(false);
  const [desc, setDesc] = useState("");
  const [categoryCode, setCategoryCode] = useState(categories[0]?.code ?? "");
  const [levelCode, setLevelCode] = useState(levels[0]?.code ?? "");
  const [treatmentCode, setTreatmentCode] = useState(
    treatmentTypes[0]?.code ?? ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleTitleChange(v: string) {
    setTitle(v);
    if (!codeEdited) setCode(slugifyRisk(v));
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Title is required");
      return;
    }
    if (!defaultOrgId) {
      setError("No organisation selected — use the org switcher at the top");
      return;
    }
    if (!defaultWorkspaceId) {
      setError("No workspace selected — use the workspace switcher at the top");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createRisk({
        risk_code: code.trim() || slugifyRisk(title),
        title,
        description: desc || undefined,
        risk_category_code: categoryCode,
        risk_level_code: levelCode,
        treatment_type_code: treatmentCode,
        source_type: "manual",
        org_id: defaultOrgId,
        workspace_id: defaultWorkspaceId,
        owner_user_id: currentUserId || undefined,
      });
      onCreated();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  function handleAIFilled(fields: Record<string, string>) {
    if (fields.title) {
      setTitle(fields.title);
      if (!codeEdited) setCode(slugifyRisk(fields.title));
    }
    if (fields.description) setDesc(fields.description);
    if (
      fields.risk_category_code &&
      categories.some((c) => c.code === fields.risk_category_code)
    )
      setCategoryCode(fields.risk_category_code);
    if (
      fields.risk_level_code &&
      levels.some((l) => l.code === fields.risk_level_code)
    )
      setLevelCode(fields.risk_level_code);
    if (
      fields.treatment_type_code &&
      treatmentTypes.some((t) => t.code === fields.treatment_type_code)
    )
      setTreatmentCode(fields.treatment_type_code);
  }

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div>
              <DialogTitle>Create Risk</DialogTitle>
              <DialogDescription>
                Register a new risk in the risk registry.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <FormFillChat
          entityType="risk"
          orgId={defaultOrgId}
          workspaceId={defaultWorkspaceId}
          pageContext={{
            org_id: defaultOrgId,
            workspace_id: defaultWorkspaceId,
          }}
          getFormValues={() => ({
            title,
            description: desc,
            risk_category_code: categoryCode,
            risk_level_code: levelCode,
            treatment_type_code: treatmentCode,
          })}
          onFilled={handleAIFilled}
          placeholder="e.g. unauthorized access to patient records via compromised credentials"
        />

        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">
              Title <span className="text-destructive">*</span>
            </Label>
            <Input
              value={title}
              onChange={(e) => handleTitleChange(e.target.value)}
              placeholder="Unauthorized ePHI Access"
              required
              className="h-9 text-sm"
              autoFocus
            />
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">
              Code{" "}
              <span className="text-muted-foreground text-[10px]">
                auto-generated · editable
              </span>
            </Label>
            <Input
              value={code}
              onChange={(e) => {
                setCode(
                  e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, "_")
                );
                setCodeEdited(true);
              }}
              placeholder="UNAUTHORIZED_EPHI_ACCESS"
              className="h-9 text-sm font-mono"
            />
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">
              Description{" "}
              <span className="text-muted-foreground text-[10px]">
                optional
              </span>
            </Label>
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              placeholder="Describe the risk scenario..."
              className="w-full min-h-[60px] px-3 py-2 rounded-md border border-input bg-background text-sm resize-y focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Category</Label>
              <select
                value={categoryCode}
                onChange={(e) => setCategoryCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
              >
                {categories.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">
                Risk Level
              </Label>
              <select
                value={levelCode}
                onChange={(e) => setLevelCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
              >
                {levels.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Treatment</Label>
              <select
                value={treatmentCode}
                onChange={(e) => setTreatmentCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
              >
                {treatmentTypes.map((t) => (
                  <option key={t.code} value={t.code}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="h-9 px-4"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Creating..." : "Create Risk"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Edit Risk Dialog
// ─────────────────────────────────────────────────────────────────────────────

function EditRiskDialog({
  risk,
  categories,
  levels,
  treatmentTypes,
  members,
  onUpdated,
  onClose,
}: {
  risk: RiskResponse;
  categories: DimensionResponse[];
  levels: RiskLevelResponse[];
  treatmentTypes: DimensionResponse[];
  members: OrgMemberResponse[];
  onUpdated: () => void;
  onClose: () => void;
}) {
  const currentUserId = getJwtSubject();
  const [title, setTitle] = useState(risk.title ?? "");
  const [desc, setDesc] = useState(risk.description ?? "");
  const [categoryCode, setCategoryCode] = useState(risk.risk_category_code);
  const [levelCode, setLevelCode] = useState(risk.risk_level_code);
  const [treatmentCode, setTreatmentCode] = useState(risk.treatment_type_code);
  const [status, setStatus] = useState(risk.risk_status);
  const [notes, setNotes] = useState(risk.notes ?? "");
  const [ownerUserId, setOwnerUserId] = useState(risk.owner_user_id ?? "");
  const [businessImpact, setBusinessImpact] = useState(
    risk.business_impact ?? ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload: UpdateRiskRequest = {
        title,
        description: desc || undefined,
        risk_category_code: categoryCode,
        risk_level_code: levelCode,
        treatment_type_code: treatmentCode,
        risk_status: status,
        notes: notes || undefined,
        owner_user_id: ownerUserId || undefined,
        business_impact: businessImpact || undefined,
      };
      await updateRisk(risk.id, payload);
      onUpdated();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  function handleAIFilled(fields: Record<string, string>) {
    if (fields.title) setTitle(fields.title);
    if (fields.description) setDesc(fields.description);
    if (
      fields.risk_category_code &&
      categories.some((c) => c.code === fields.risk_category_code)
    )
      setCategoryCode(fields.risk_category_code);
    if (
      fields.risk_level_code &&
      levels.some((l) => l.code === fields.risk_level_code)
    )
      setLevelCode(fields.risk_level_code);
    if (
      fields.treatment_type_code &&
      treatmentTypes.some((t) => t.code === fields.treatment_type_code)
    )
      setTreatmentCode(fields.treatment_type_code);
    if (
      fields.risk_status &&
      Object.keys(RISK_STATUS_META).includes(fields.risk_status)
    )
      setStatus(fields.risk_status);
    if (fields.notes) setNotes(fields.notes);
    if (fields.business_impact) setBusinessImpact(fields.business_impact);
  }

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Risk</DialogTitle>
          <DialogDescription>
            Update risk details for {risk.risk_code}.
          </DialogDescription>
        </DialogHeader>

        <FormFillChat
          entityType="risk"
          orgId={null}
          workspaceId={null}
          pageContext={{ risk_id: risk.id, risk_title: risk.title }}
          getFormValues={() => ({
            title,
            description: desc,
            risk_category_code: categoryCode,
            risk_level_code: levelCode,
            treatment_type_code: treatmentCode,
            risk_status: status,
            notes,
            business_impact: businessImpact,
          })}
          onFilled={handleAIFilled}
        />

        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Title <span className="text-destructive">*</span>
            </Label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="h-8 text-sm"
            />
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Description
            </Label>
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              className="w-full min-h-[60px] px-3 py-2 rounded-md border border-input bg-background text-sm resize-y focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Category
              </Label>
              <select
                value={categoryCode}
                onChange={(e) => setCategoryCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
              >
                {categories.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Risk Level
              </Label>
              <select
                value={levelCode}
                onChange={(e) => setLevelCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
              >
                {levels.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Treatment Type
              </Label>
              <select
                value={treatmentCode}
                onChange={(e) => setTreatmentCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
              >
                {treatmentTypes.map((t) => (
                  <option key={t.code} value={t.code}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Status
              </Label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
              >
                {Object.entries(RISK_STATUS_META).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Notes
            </Label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Additional notes..."
              className="w-full min-h-[50px] px-3 py-2 rounded-md border border-input bg-background text-sm resize-y focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Owner
              </Label>
              <SearchCombobox<OrgMemberResponse>
                placeholder="Search by name or email…"
                value={ownerUserId}
                options={members}
                getId={(m) => m.user_id}
                getLabel={(m) => {
                  const name = m.display_name || "";
                  const email = m.email || "";
                  const you = m.user_id === currentUserId ? " (you)" : "";
                  return name && email
                    ? `${name} — ${email}${you}`
                    : (email || m.user_id) + you;
                }}
                onSelect={(id) => setOwnerUserId(id)}
              />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Business Impact
              </Label>
              <Input
                value={businessImpact}
                onChange={(e) => setBusinessImpact(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="h-9 px-4"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Delete Confirmation Dialog
// ─────────────────────────────────────────────────────────────────────────────

function DeleteRiskDialog({
  risk,
  onDeleted,
  onClose,
}: {
  risk: RiskResponse;
  onDeleted: () => void;
  onClose: () => void;
}) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    setDeleting(true);
    setError(null);
    try {
      await deleteRisk(risk.id);
      onDeleted();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Risk</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete <strong>{risk.risk_code}</strong> (
            {risk.title})? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
        <DialogFooter>
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            className="h-9 px-4"
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={deleting}
            className="h-9"
          >
            {deleting ? "Deleting..." : "Delete Risk"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Assessment Dialog
// ─────────────────────────────────────────────────────────────────────────────

function AssessmentDialog({
  riskId,
  orgId,
  workspaceId,
  onCreated,
  onClose,
}: {
  riskId: string;
  orgId?: string | null;
  workspaceId?: string | null;
  onCreated: () => void;
  onClose: () => void;
}) {
  const [assessmentType, setAssessmentType] = useState<string>("inherent");
  const [likelihood, setLikelihood] = useState(3);
  const [impact, setImpact] = useState(3);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const computedScore = likelihood * impact;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createAssessment(riskId, {
        assessment_type: assessmentType,
        likelihood_score: likelihood,
        impact_score: impact,
        assessment_notes: notes || undefined,
      });
      onCreated();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>New Assessment</DialogTitle>
          <DialogDescription>
            Create a risk assessment with likelihood and impact scores.
          </DialogDescription>
        </DialogHeader>

        <FormFillChat
          entityType="assessment"
          orgId={orgId}
          workspaceId={workspaceId}
          pageContext={{
            risk_id: riskId,
            org_id: orgId,
            workspace_id: workspaceId,
          }}
          getFormValues={() => ({
            assessment_type: assessmentType,
            likelihood_score: likelihood,
            impact_score: impact,
            assessment_notes: notes,
          })}
          onFilled={(fields) => {
            if (fields.assessment_type)
              setAssessmentType(fields.assessment_type);
            if (fields.likelihood_score)
              setLikelihood(Number(fields.likelihood_score));
            if (fields.impact_score) setImpact(Number(fields.impact_score));
            if (fields.assessment_notes) setNotes(fields.assessment_notes);
          }}
          placeholder="e.g. high likelihood due to weak access controls, significant data breach impact"
        />

        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Assessment Type <span className="text-destructive">*</span>
            </Label>
            <select
              value={assessmentType}
              onChange={(e) => setAssessmentType(e.target.value)}
              className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
            >
              <option value="inherent">Inherent</option>
              <option value="residual">Residual</option>
            </select>
          </div>

          {(() => {
            const SCORE_LABELS = [
              "",
              "Very Low",
              "Low",
              "Medium",
              "High",
              "Very High",
            ];
            return (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">
                    Likelihood <span className="text-destructive">*</span>
                  </Label>
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="range"
                      min={1}
                      max={5}
                      value={likelihood}
                      onChange={(e) => setLikelihood(Number(e.target.value))}
                      className="flex-1 h-2 accent-primary"
                    />
                    <span className="text-sm font-semibold tabular-nums w-4 text-center">
                      {likelihood}
                    </span>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {SCORE_LABELS[likelihood]}
                  </p>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">
                    Impact <span className="text-destructive">*</span>
                  </Label>
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="range"
                      min={1}
                      max={5}
                      value={impact}
                      onChange={(e) => setImpact(Number(e.target.value))}
                      className="flex-1 h-2 accent-primary"
                    />
                    <span className="text-sm font-semibold tabular-nums w-4 text-center">
                      {impact}
                    </span>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {SCORE_LABELS[impact]}
                  </p>
                </div>
              </div>
            );
          })()}

          <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50 border border-border">
            <span className="text-xs text-muted-foreground">
              Computed Risk Score:
            </span>
            <span className="text-lg font-bold">{computedScore}</span>
            <span className="text-xs text-muted-foreground">/ 25</span>
            <div className="flex-1" />
            <ScoreBar score={computedScore} />
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Assessment Notes
            </Label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Notes about this assessment..."
              className="w-full min-h-[50px] px-3 py-2 rounded-md border border-input bg-background text-sm resize-y focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="h-9 px-4"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Saving..." : "Create Assessment"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Treatment Plan Dialog
// ─────────────────────────────────────────────────────────────────────────────

function TreatmentPlanDialog({
  riskId,
  orgId,
  workspaceId,
  existing,
  members,
  onSaved,
  onClose,
}: {
  riskId: string;
  orgId?: string | null;
  workspaceId?: string | null;
  existing: TreatmentPlanResponse | null;
  members: OrgMemberResponse[];
  onSaved: () => void;
  onClose: () => void;
}) {
  const currentUserId = getJwtSubject();
  const [description, setDescription] = useState(
    existing?.properties?.plan_description ?? ""
  );
  const [actionItems, setActionItems] = useState(
    existing?.properties?.action_items ?? ""
  );
  const [planStatus, setPlanStatus] = useState(
    existing?.plan_status ?? "draft"
  );
  const [targetDate, setTargetDate] = useState(
    existing?.target_date?.split("T")[0] ?? ""
  );
  const [ownerUserId, setOwnerUserId] = useState(
    existing?.properties?.approver_user_id ?? ""
  );
  const [reviewFrequency, setReviewFrequency] = useState(
    existing?.properties?.review_frequency ?? ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = {
        plan_description: description || undefined,
        action_items: actionItems || undefined,
        plan_status: planStatus,
        target_date: targetDate || undefined,
        approver_user_id: ownerUserId || undefined,
        review_frequency: reviewFrequency || undefined,
      };
      if (existing) {
        await updateTreatmentPlan(riskId, payload);
      } else {
        await createTreatmentPlan(riskId, payload);
      }
      onSaved();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>
            {existing ? "Edit Treatment Plan" : "Create Treatment Plan"}
          </DialogTitle>
          <DialogDescription>
            Define how this risk will be treated.
          </DialogDescription>
        </DialogHeader>

        <FormFillChat
          entityType="treatment_plan"
          orgId={orgId}
          workspaceId={workspaceId}
          pageContext={{
            risk_id: riskId,
            org_id: orgId,
            workspace_id: workspaceId,
            _is_edit: !!existing,
          }}
          getFormValues={() => ({
            plan_description: description,
            action_items: actionItems,
            plan_status: planStatus,
            target_date: targetDate,
            review_frequency: reviewFrequency,
          })}
          onFilled={(fields) => {
            if (fields.plan_description)
              setDescription(fields.plan_description);
            if (fields.action_items) setActionItems(fields.action_items);
            if (fields.plan_status) setPlanStatus(fields.plan_status);
            if (fields.target_date) setTargetDate(fields.target_date);
            if (fields.review_frequency)
              setReviewFrequency(fields.review_frequency);
          }}
          placeholder="e.g. mitigate the risk by implementing MFA and rotating credentials quarterly"
        />

        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Description <span className="text-destructive">*</span>
            </Label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the treatment plan..."
              required
              className="w-full min-h-[60px] px-3 py-2 rounded-md border border-input bg-background text-sm resize-y focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Action Items
            </Label>
            <textarea
              value={actionItems}
              onChange={(e) => setActionItems(e.target.value)}
              placeholder="List specific actions to implement this plan..."
              className="w-full min-h-[50px] px-3 py-2 rounded-md border border-input bg-background text-sm resize-y focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Status
              </Label>
              <select
                value={planStatus}
                onChange={(e) => setPlanStatus(e.target.value)}
                className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
              >
                {Object.entries(TREATMENT_PLAN_STATUS_META).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Target Date
              </Label>
              <Input
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Approver
              </Label>
              <SearchCombobox<OrgMemberResponse>
                placeholder="Search by name or email…"
                value={ownerUserId}
                options={members}
                getId={(m) => m.user_id}
                getLabel={(m) => {
                  const name = m.display_name || "";
                  const email = m.email || "";
                  const you = m.user_id === currentUserId ? " (you)" : "";
                  return name && email
                    ? `${name} — ${email}${you}`
                    : (email || m.user_id) + you;
                }}
                onSelect={(id) => setOwnerUserId(id)}
              />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Review Frequency
              </Label>
              <select
                value={reviewFrequency}
                onChange={(e) => setReviewFrequency(e.target.value)}
                className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
              >
                <option value="">— Not set —</option>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="semi_annual">Semi-Annual</option>
                <option value="annual">Annual</option>
              </select>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="h-9 px-4"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Saving..." : existing ? "Update Plan" : "Create Plan"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Add Control Mapping Dialog
// ─────────────────────────────────────────────────────────────────────────────

function AddControlDialog({
  riskId,
  orgId,
  workspaceId,
  onAdded,
  onClose,
}: {
  riskId: string;
  orgId?: string;
  workspaceId?: string;
  onAdded: () => void;
  onClose: () => void;
}) {
  const [controlId, setControlId] = useState("");
  const [linkType, setLinkType] = useState("mitigating");
  const [allControls, setAllControls] = useState<ControlResponse[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAllControls({
      scope_org_id: orgId,
      ...(workspaceId ? { scope_workspace_id: workspaceId } : {}),
      limit: 500,
    })
      .then((r) => setAllControls(r.items ?? []))
      .catch(() => setAllControls([]));
  }, [orgId, workspaceId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!controlId) {
      setError("Select a control");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await addRiskControl(riskId, {
        control_id: controlId,
        link_type: linkType,
      });
      onAdded();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Link Control</DialogTitle>
          <DialogDescription>
            Map a mitigating control to this risk.
          </DialogDescription>
        </DialogHeader>
        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Control <span className="text-destructive">*</span>
            </Label>
            <SearchCombobox<ControlResponse>
              placeholder="Search controls…"
              value={controlId}
              options={allControls}
              getId={(c) => c.id}
              getLabel={(c) =>
                c.name ? `${c.control_code} — ${c.name}` : c.control_code
              }
              onSelect={(id) => setControlId(id)}
            />
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Link Type
            </Label>
            <select
              value={linkType}
              onChange={(e) => setLinkType(e.target.value)}
              className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
            >
              <option value="mitigating">Mitigating</option>
              <option value="compensating">Compensating</option>
              <option value="related">Related</option>
            </select>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="h-9 px-4"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Linking..." : "Link Control"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Add Review Event Dialog
// ─────────────────────────────────────────────────────────────────────────────

function AddReviewDialog({
  riskId,
  onAdded,
  onClose,
}: {
  riskId: string;
  onAdded: () => void;
  onClose: () => void;
}) {
  const [eventType, setEventType] = useState("comment_added");
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await addReviewEvent(riskId, {
        event_type: eventType,
        comment: comment || undefined,
      });
      onAdded();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Add Review Event</DialogTitle>
          <DialogDescription>
            Record a review comment or event.
          </DialogDescription>
        </DialogHeader>
        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Event Type
            </Label>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="w-full h-8 px-2 rounded border border-input bg-background text-sm"
            >
              <option value="comment_added">Comment</option>
              <option value="reviewed">Review</option>
              <option value="assessed">Assessment Note</option>
              <option value="treatment_updated">Treatment Update</option>
            </select>
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Comment
            </Label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Write your comment..."
              className="w-full min-h-[60px] px-3 py-2 rounded-md border border-input bg-background text-sm resize-y focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="h-9 px-4"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Adding..." : "Add Event"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Expanded Risk Detail (inline)
// ─────────────────────────────────────────────────────────────────────────────

function RiskDetail({
  risk,
  members,
  onReload,
  onEdit,
  onDelete,
}: {
  risk: RiskResponse;
  members: OrgMemberResponse[];
  onReload: () => void;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [assessments, setAssessments] = useState<RiskAssessmentResponse[]>([]);
  const [treatmentPlan, setTreatmentPlan] =
    useState<TreatmentPlanResponse | null>(null);
  const [controls, setControls] = useState<RiskControlMappingResponse[]>([]);
  const [events, setEvents] = useState<RiskReviewEventResponse[]>([]);
  const [riskGroups, setRiskGroups] = useState<RiskGroupAssignmentResponse[]>(
    []
  );
  const [reviewSchedule, setReviewSchedule] =
    useState<ReviewScheduleResponse | null>(null);
  const [riskTasks, setRiskTasks] = useState<TaskResponse[]>([]);
  const [loadingDetail, setLoadingDetail] = useState(true);
  const { isWorkspaceAdmin } = useAccess();
  const { selectedOrgId, selectedWorkspaceId } = useOrgWorkspace();

  const [showAssessment, setShowAssessment] = useState(false);
  const [showTreatment, setShowTreatment] = useState(false);
  const [showAddControl, setShowAddControl] = useState(false);
  const [showAutoLinkPanel, setShowAutoLinkPanel] = useState(false);
  const [showAddReview, setShowAddReview] = useState(false);
  const [showAssignGroup, setShowAssignGroup] = useState(false);
  const [showReviewSchedule, setShowReviewSchedule] = useState(false);
  const [showTaskSlideOver, setShowTaskSlideOver] = useState(false);
  const [riskTab, setRiskTab] = useState<
    | "details"
    | "assessments"
    | "treatment"
    | "controls"
    | "tasks"
    | "reviews"
    | "groups"
    | "schedule"
    | "comments"
    | "attachments"
  >("details");
  const [commentCount, setCommentCount] = useState<number | null>(null);
  const [attachmentCount, setAttachmentCount] = useState<number | null>(null);

  const loadDetail = useCallback(async () => {
    setLoadingDetail(true);
    try {
      const [aRes, cRes, eRes, gRes, rsRes, ccnt, acnt, tRes] =
        await Promise.all([
          listAssessments(risk.id),
          listRiskControls(risk.id),
          listReviewEvents(risk.id),
          listRiskGroups(risk.id).catch(() => []),
          getReviewSchedule(risk.id).catch(() => null),
          getCommentCount("risk", risk.id).catch(() => null),
          getAttachmentCount("risk", risk.id).catch(() => null),
          listTasks({
            orgId: risk.org_id ?? undefined,
            workspaceId: risk.workspace_id ?? undefined,
            entity_type: "risk",
            entity_id: risk.id,
            limit: 50,
          }).catch(() => ({ items: [] })),
        ]);
      setAssessments(Array.isArray(aRes) ? aRes : []);
      setControls(Array.isArray(cRes) ? cRes : []);
      setEvents(Array.isArray(eRes) ? eRes : []);
      setRiskGroups(Array.isArray(gRes) ? gRes : []);
      setReviewSchedule(rsRes);
      setRiskTasks(tRes?.items ?? []);
      if (ccnt !== null) setCommentCount(ccnt);
      if (acnt !== null) setAttachmentCount(acnt);
      try {
        const tRes = await getTreatmentPlan(risk.id);
        setTreatmentPlan(tRes);
      } catch {
        setTreatmentPlan(null);
      }
    } catch {
      // graceful
    } finally {
      setLoadingDetail(false);
    }
  }, [risk.id]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  const handleRemoveControl = async (mappingId: string) => {
    try {
      await removeRiskControl(risk.id, mappingId);
      loadDetail();
    } catch {
      // graceful
    }
  };

  return (
    <div className="mt-1 mb-2 rounded-xl border border-border bg-card overflow-hidden">
      {/* Tab bar */}
      <div
        className="flex border-b border-border px-4 bg-muted/20 overflow-x-auto"
        role="tablist"
      >
        {(
          [
            "details",
            "assessments",
            "treatment",
            "controls",
            "tasks",
            "groups",
            "schedule",
            "reviews",
            "comments",
            "attachments",
          ] as const
        ).map((tab) => {
          const baseLabels: Record<typeof tab, string> = {
            details: "Details",
            assessments: "Assessments",
            treatment: "Treatment Plan",
            controls: `Controls (${controls.length})`,
            tasks: `Tasks (${riskTasks.length})`,
            groups: `Groups (${riskGroups.length})`,
            schedule: reviewSchedule
              ? reviewSchedule.is_overdue
                ? "Schedule (!)"
                : "Schedule"
              : "Schedule",
            reviews: `Reviews (${events.length})`,
            comments:
              commentCount !== null ? `Comments (${commentCount})` : "Comments",
            attachments:
              attachmentCount !== null
                ? `Attachments (${attachmentCount})`
                : "Attachments",
          };
          return (
            <button
              key={tab}
              role="tab"
              aria-selected={riskTab === tab}
              onClick={() => setRiskTab(tab)}
              className={`px-3 py-2.5 text-xs font-medium border-b-2 transition-colors whitespace-nowrap
                ${
                  riskTab === tab
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
            >
              {baseLabels[tab]}
            </button>
          );
        })}
      </div>

      <div className="px-4 py-3 space-y-4">
        {/* Comments tab */}
        {riskTab === "comments" && (
          <CommentsSection
            entityType="risk"
            entityId={risk.id}
            currentUserId={getJwtSubject() ?? ""}
            isWorkspaceAdmin={isWorkspaceAdmin}
            orgId={risk.org_id ?? null}
            workspaceId={risk.workspace_id ?? null}
          />
        )}

        {/* Attachments tab */}
        {riskTab === "attachments" && (
          <AttachmentsSection
            entityType="risk"
            entityId={risk.id}
            currentUserId={getJwtSubject() ?? ""}
            canUpload={true}
            isWorkspaceAdmin={isWorkspaceAdmin}
          />
        )}

        {/* Assessments tab */}
        {riskTab === "assessments" && (
          <div className="text-xs space-y-3">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-foreground">
                Assessment History ({assessments.length})
              </p>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => setShowAssessment(true)}
              >
                <ClipboardCheck className="w-3 h-3" /> Add Assessment
              </Button>
            </div>
            {loadingDetail ? (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div
                    key={i}
                    className="h-16 bg-muted rounded-lg animate-pulse"
                  />
                ))}
              </div>
            ) : assessments.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
                <ClipboardCheck className="w-8 h-8 opacity-30" />
                <p>No assessments recorded yet.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {assessments.map((a) => {
                  const score =
                    a.risk_score ?? a.likelihood_score * a.impact_score;
                  const scorePct = Math.min((score / 25) * 100, 100);
                  const scoreColor =
                    score >= 16
                      ? "#ef4444"
                      : score >= 11
                        ? "#f97316"
                        : score >= 6
                          ? "#f59e0b"
                          : "#10b981";
                  const scoreLabel =
                    score >= 16
                      ? "Critical"
                      : score >= 11
                        ? "High"
                        : score >= 6
                          ? "Medium"
                          : "Low";
                  const typeCls =
                    a.assessment_type === "inherent"
                      ? "text-orange-600 bg-orange-500/10 border-orange-500/20"
                      : "text-blue-600 bg-blue-500/10 border-blue-500/20";
                  return (
                    <div
                      key={a.id}
                      className="rounded-lg bg-muted/30 border border-border overflow-hidden"
                    >
                      <div className="px-3 py-2 flex items-center gap-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold capitalize ${typeCls}`}
                        >
                          {a.assessment_type}
                        </span>
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <span className="font-mono">
                            L={a.likelihood_score}
                          </span>
                          <span>×</span>
                          <span className="font-mono">I={a.impact_score}</span>
                          <span>=</span>
                          <span
                            className="font-bold text-sm"
                            style={{ color: scoreColor }}
                          >
                            {score}
                          </span>
                          <span
                            className="text-[10px] font-semibold"
                            style={{ color: scoreColor }}
                          >
                            ({scoreLabel})
                          </span>
                        </div>
                        <span className="text-muted-foreground ml-auto text-[11px]">
                          {formatDate(a.assessed_at)}
                        </span>
                      </div>
                      <div className="px-3 pb-2">
                        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${scorePct}%`,
                              backgroundColor: scoreColor,
                            }}
                          />
                        </div>
                      </div>
                      {a.assessment_notes && (
                        <div className="px-3 pb-2 text-muted-foreground italic">
                          {a.assessment_notes}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Treatment Plan tab */}
        {riskTab === "treatment" && (
          <div className="text-xs space-y-3">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-foreground">Treatment Plan</p>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => setShowTreatment(true)}
              >
                <FileText className="w-3 h-3" />{" "}
                {treatmentPlan ? "Edit Plan" : "Add Plan"}
              </Button>
            </div>
            {treatmentPlan ? (
              <div className="px-3 py-3 rounded-lg bg-muted/30 border border-border space-y-2">
                {/* Progress bar */}
                {(() => {
                  const pct =
                    treatmentPlan.plan_status === "completed"
                      ? 100
                      : treatmentPlan.plan_status === "active"
                        ? 50
                        : treatmentPlan.plan_status === "cancelled"
                          ? 0
                          : 10;
                  const color =
                    treatmentPlan.plan_status === "completed"
                      ? "bg-green-500"
                      : treatmentPlan.plan_status === "active"
                        ? "bg-blue-500"
                        : treatmentPlan.plan_status === "cancelled"
                          ? "bg-muted-foreground"
                          : "bg-amber-400";
                  return (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span
                          className={`font-medium ${TREATMENT_PLAN_STATUS_META[treatmentPlan.plan_status]?.cls ?? ""}`}
                        >
                          {TREATMENT_PLAN_STATUS_META[treatmentPlan.plan_status]
                            ?.label ?? treatmentPlan.plan_status}
                        </span>
                        <span className="text-muted-foreground">{pct}%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full transition-all ${color}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })()}
                <div className="flex items-center gap-3">
                  {treatmentPlan.target_date && (
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Target:{" "}
                      {formatDate(treatmentPlan.target_date)}
                      {new Date(treatmentPlan.target_date) < new Date() &&
                        treatmentPlan.plan_status !== "completed" && (
                          <span className="text-red-500 ml-1">— overdue</span>
                        )}
                    </span>
                  )}
                </div>
                {treatmentPlan.properties?.plan_description && (
                  <div>
                    <p className="text-muted-foreground mb-0.5">Description</p>
                    <p className="text-foreground">
                      {treatmentPlan.properties.plan_description}
                    </p>
                  </div>
                )}
                {treatmentPlan.properties?.action_items && (
                  <div>
                    <p className="text-muted-foreground mb-0.5">Action Items</p>
                    <p className="text-foreground whitespace-pre-wrap">
                      {treatmentPlan.properties.action_items}
                    </p>
                  </div>
                )}
                {treatmentPlan.properties?.approver_user_id && (
                  <div>
                    <p className="text-muted-foreground mb-0.5">Approver</p>
                    <p className="text-foreground">
                      {(() => {
                        const m = members.find(
                          (x) =>
                            x.user_id ===
                            treatmentPlan.properties?.approver_user_id
                        );
                        return m
                          ? m.display_name || m.email || m.user_id
                          : treatmentPlan.properties?.approver_user_id;
                      })()}
                    </p>
                  </div>
                )}
                {treatmentPlan.properties?.review_frequency && (
                  <div>
                    <p className="text-muted-foreground mb-0.5">
                      Review Frequency
                    </p>
                    <p className="text-foreground capitalize">
                      {treatmentPlan.properties.review_frequency.replace(
                        /_/g,
                        " "
                      )}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-muted-foreground">
                No treatment plan defined yet.
              </p>
            )}
          </div>
        )}

        {/* Controls tab */}
        {riskTab === "controls" && (
          <div className="text-xs space-y-2">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-foreground">
                Linked Controls ({controls.length})
              </p>
              <div className="flex items-center gap-1.5">
                {selectedOrgId && selectedWorkspaceId && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs gap-1 border-primary/40 text-primary hover:bg-primary/5"
                    onClick={() => setShowAutoLinkPanel(true)}
                  >
                    <GitMerge className="w-3 h-3" /> Auto-Link with AI
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs gap-1"
                  onClick={() => setShowAddControl(true)}
                >
                  <Link2 className="w-3 h-3" /> Link Control
                </Button>
              </div>
            </div>
            {showAutoLinkPanel && selectedOrgId && selectedWorkspaceId && (
              <AutoLinkModal
                orgId={selectedOrgId}
                workspaceId={selectedWorkspaceId}
                riskId={risk.id}
                onClose={() => { setShowAutoLinkPanel(false); loadDetail(); }}
              />
            )}
            {loadingDetail ? (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div
                    key={i}
                    className="h-12 bg-muted rounded-lg animate-pulse"
                  />
                ))}
              </div>
            ) : controls.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
                <Link2 className="w-8 h-8 opacity-30" />
                <p>No controls linked yet.</p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {controls.map((c) => {
                  const linkMeta: Record<
                    string,
                    { label: string; cls: string }
                  > = {
                    mitigating: {
                      label: "Mitigating",
                      cls: "text-green-600 bg-green-500/10 border-green-500/20",
                    },
                    compensating: {
                      label: "Compensating",
                      cls: "text-blue-600 bg-blue-500/10 border-blue-500/20",
                    },
                    related: {
                      label: "Related",
                      cls: "text-muted-foreground bg-muted border-border",
                    },
                  };
                  const lm = linkMeta[c.link_type] ?? {
                    label: c.link_type,
                    cls: "text-muted-foreground bg-muted border-border",
                  };
                  return (
                    <div
                      key={c.id}
                      className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-muted/30 border border-border hover:bg-muted/50 transition-colors"
                    >
                      <div className="shrink-0 rounded p-1 bg-muted">
                        <Wrench className="w-3 h-3 text-muted-foreground" />
                      </div>
                      <span className="font-mono text-[11px] text-muted-foreground shrink-0">
                        {c.control_code}
                      </span>
                      <span className="flex-1 text-sm font-medium truncate">
                        {c.control_name ?? "—"}
                      </span>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold ${lm.cls}`}
                      >
                        {lm.label}
                      </span>
                      <button
                        className="text-muted-foreground hover:text-destructive transition-colors"
                        onClick={() => handleRemoveControl(c.id)}
                        title="Unlink control"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Reviews tab */}
        {riskTab === "reviews" && (
          <div className="text-xs space-y-2">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-foreground">
                Review History ({events.length})
              </p>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => setShowAddReview(true)}
              >
                <MessageSquare className="w-3 h-3" /> Add Review
              </Button>
            </div>
            {loadingDetail ? (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div
                    key={i}
                    className="h-12 bg-muted rounded-lg animate-pulse"
                  />
                ))}
              </div>
            ) : events.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
                <MessageSquare className="w-8 h-8 opacity-30" />
                <p>No review events recorded yet.</p>
              </div>
            ) : (
              <div className="relative pl-4 space-y-0">
                <div className="absolute left-0 top-2 bottom-2 w-[2px] bg-border rounded-full" />
                {[...events]
                  .sort((a, b) => b.occurred_at.localeCompare(a.occurred_at))
                  .map((ev) => {
                    const actor = members.find(
                      (m) => m.user_id === ev.actor_id
                    );
                    const actorName = actor
                      ? actor.display_name || actor.email || ev.actor_id
                      : ev.actor_id;
                    const evTypeMeta: Record<string, { cls: string }> = {
                      comment_added: { cls: "bg-blue-500" },
                      reviewed: { cls: "bg-green-500" },
                      assessed: { cls: "bg-purple-500" },
                      treatment_updated: { cls: "bg-amber-500" },
                    };
                    const dotCls =
                      evTypeMeta[ev.event_type]?.cls ?? "bg-muted-foreground";
                    return (
                      <div key={ev.id} className="relative pb-3">
                        <div
                          className={`absolute -left-[5px] top-2 w-2.5 h-2.5 rounded-full border-2 border-background ${dotCls}`}
                        />
                        <div className="ml-3 rounded-lg bg-muted/30 border border-border px-3 py-2 space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-foreground capitalize">
                              {ev.event_type.replace(/_/g, " ")}
                            </span>
                            {ev.old_status && ev.new_status && (
                              <span className="inline-flex items-center gap-1 text-muted-foreground">
                                <span className="px-1.5 py-0 rounded bg-muted text-[10px]">
                                  {ev.old_status}
                                </span>
                                →
                                <span className="px-1.5 py-0 rounded bg-muted text-[10px]">
                                  {ev.new_status}
                                </span>
                              </span>
                            )}
                            <span className="ml-auto text-muted-foreground flex items-center gap-1 shrink-0">
                              <User2 className="w-3 h-3" />
                              {actorName}
                            </span>
                            <span className="text-muted-foreground shrink-0">
                              {formatDate(ev.occurred_at)}
                            </span>
                          </div>
                          {ev.comment && (
                            <p className="text-muted-foreground italic">
                              {ev.comment}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        )}

        {/* Tasks tab */}
        {riskTab === "tasks" && (
          <div className="text-xs space-y-3">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-foreground">
                Remediation Tasks ({riskTasks.length})
              </p>
            </div>
            {loadingDetail ? (
              <div className="space-y-1">
                {[1, 2].map((i) => (
                  <div key={i} className="h-9 bg-muted rounded animate-pulse" />
                ))}
              </div>
            ) : riskTasks.length === 0 ? (
              <p className="text-muted-foreground">No remediation tasks yet.</p>
            ) : (
              <div className="space-y-1">
                {riskTasks.map((task) => {
                  const today = new Date().toISOString().split("T")[0];
                  const isOverdue =
                    task.due_date && task.due_date < today && !task.is_terminal;
                  return (
                    <div
                      key={task.id}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/30 border border-border group hover:bg-muted/50 transition-colors"
                    >
                      <TaskStatusIcon status={task.status_code} />
                      <span
                        className={`inline-flex items-center rounded border px-1.5 py-0 text-[10px] font-semibold uppercase ${TASK_PRIORITY_COLORS[task.priority_code] ?? "bg-muted text-muted-foreground border-border"}`}
                      >
                        {task.priority_code}
                      </span>
                      <span className="truncate font-medium">{task.title}</span>
                      <span
                        className={`ml-auto shrink-0 capitalize ${TASK_STATUS_STYLES[task.status_code] ?? ""}`}
                      >
                        {task.status_name}
                      </span>
                      {task.due_date && (
                        <span
                          className={`shrink-0 ${isOverdue ? "text-red-500 font-semibold" : "text-muted-foreground"}`}
                        >
                          {new Date(task.due_date).toLocaleDateString()}
                          {isOverdue && " ⚠"}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Add task button */}
            <div className="pt-2 border-t border-border/30">
              <button
                type="button"
                onClick={() => setShowTaskSlideOver(true)}
                className="flex items-center gap-1.5 text-[11px] text-orange-600 hover:text-orange-500 transition-colors"
              >
                <Plus className="w-3 h-3" /> Add Remediation Task
              </button>
            </div>

            {/* Task create slide-over */}
            {selectedOrgId && (
              <TaskCreateSlideOver
                open={showTaskSlideOver}
                onClose={() => setShowTaskSlideOver(false)}
                onCreated={() => {
                  loadDetail();
                  onReload();
                  setShowTaskSlideOver(false);
                }}
                taskTypeCode="risk_mitigation"
                taskTypeName="Risk Mitigation"
                entityType="risk"
                entityId={risk.id}
                entityTitle={risk.title}
                orgId={selectedOrgId}
                workspaceId={selectedWorkspaceId || ""}
              />
            )}
          </div>
        )}

        {/* Groups tab */}
        {riskTab === "groups" && (
          <div className="text-xs space-y-2">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-foreground">
                Responsible Groups ({riskGroups.length})
              </p>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => setShowAssignGroup(true)}
              >
                <Users className="w-3 h-3" /> Assign Group
              </Button>
            </div>
            {loadingDetail ? (
              <div className="space-y-1">
                {[1, 2].map((i) => (
                  <div key={i} className="h-9 bg-muted rounded animate-pulse" />
                ))}
              </div>
            ) : riskGroups.length === 0 ? (
              <p className="text-muted-foreground">No groups assigned yet.</p>
            ) : (
              <div className="space-y-1">
                {riskGroups.map((g) => {
                  const roleMeta: Record<
                    string,
                    { label: string; cls: string }
                  > = {
                    responsible: {
                      label: "Responsible",
                      cls: "text-blue-600 bg-blue-500/10 border-blue-500/20",
                    },
                    accountable: {
                      label: "Accountable",
                      cls: "text-purple-600 bg-purple-500/10 border-purple-500/20",
                    },
                    consulted: {
                      label: "Consulted",
                      cls: "text-amber-600 bg-amber-500/10 border-amber-500/20",
                    },
                    informed: {
                      label: "Informed",
                      cls: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20",
                    },
                  };
                  const rm = roleMeta[g.role] ?? {
                    label: g.role,
                    cls: "text-muted-foreground bg-muted border-border",
                  };
                  return (
                    <div
                      key={g.id}
                      className="flex items-center gap-3 px-3 py-2 rounded-lg bg-muted/30 border border-border"
                    >
                      <Users className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                      <span className="font-medium flex-1">
                        {g.group_name ?? g.group_id}
                      </span>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold ${rm.cls}`}
                      >
                        {rm.label}
                      </span>
                      <span className="text-muted-foreground">
                        {formatDate(g.assigned_at)}
                      </span>
                      <button
                        className="text-muted-foreground hover:text-destructive transition-colors"
                        onClick={async () => {
                          try {
                            await unassignRiskGroup(risk.id, g.id);
                            loadDetail();
                          } catch {}
                        }}
                        title="Remove group"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Review Schedule tab */}
        {riskTab === "schedule" && (
          <div className="text-xs space-y-3">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-foreground">Review Schedule</p>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => setShowReviewSchedule(true)}
              >
                <CalendarCheck className="w-3 h-3" />{" "}
                {reviewSchedule ? "Edit Schedule" : "Set Schedule"}
              </Button>
            </div>
            {reviewSchedule ? (
              <div className="px-3 py-3 rounded-lg bg-muted/30 border border-border space-y-2">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="font-medium capitalize">
                    {reviewSchedule.review_frequency.replace(/_/g, " ")}
                  </span>
                  <span className="text-muted-foreground flex items-center gap-1">
                    <CalendarCheck className="w-3 h-3" /> Next:{" "}
                    {formatDate(reviewSchedule.next_review_date)}
                  </span>
                  {reviewSchedule.is_overdue && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold text-red-600 bg-red-500/10 border-red-500/20">
                      Overdue
                    </span>
                  )}
                </div>
                {reviewSchedule.last_reviewed_at && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Clock className="w-3 h-3" /> Last reviewed:{" "}
                    {formatDate(reviewSchedule.last_reviewed_at)}
                    {reviewSchedule.last_reviewed_by &&
                      (() => {
                        const reviewer = members.find(
                          (m) => m.user_id === reviewSchedule.last_reviewed_by
                        );
                        return reviewer
                          ? ` by ${reviewer.display_name || reviewer.email || reviewer.user_id}`
                          : "";
                      })()}
                  </div>
                )}
                <div className="pt-1">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs gap-1"
                    onClick={async () => {
                      // Default next date: add frequency interval from today
                      const now = new Date();
                      const freq = reviewSchedule.review_frequency;
                      if (freq === "monthly") now.setMonth(now.getMonth() + 1);
                      else if (freq === "quarterly")
                        now.setMonth(now.getMonth() + 3);
                      else if (freq === "semi_annual")
                        now.setMonth(now.getMonth() + 6);
                      else now.setFullYear(now.getFullYear() + 1);
                      const nextDate = now.toISOString().split("T")[0];
                      try {
                        await completeReview(risk.id, nextDate);
                        loadDetail();
                      } catch {}
                    }}
                  >
                    <ClipboardCheck className="w-3 h-3" /> Complete Review
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">
                No review schedule configured yet.
              </p>
            )}
          </div>
        )}

        {/* Details tab */}
        {riskTab === "details" && (
          <>
            {/* Info grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                {
                  label: "Risk Code",
                  value: (
                    <span className="font-mono text-xs">{risk.risk_code}</span>
                  ),
                },
                { label: "Category", value: risk.category_name },
                {
                  label: "Source",
                  value: (
                    <span className="capitalize">
                      {risk.source_type?.replace(/_/g, " ")}
                    </span>
                  ),
                },
                { label: "Created", value: formatDate(risk.created_at) },
              ].map(({ label, value }) => (
                <div
                  key={label}
                  className="rounded-lg bg-muted/40 border border-border px-3 py-2"
                >
                  <div className="text-[10px] text-muted-foreground mb-0.5">
                    {label}
                  </div>
                  <div className="text-xs font-medium text-foreground">
                    {value}
                  </div>
                </div>
              ))}
            </div>

            {/* Score cards */}
            <div className="grid grid-cols-2 gap-2">
              {[
                {
                  label: "Inherent Risk Score",
                  icon: TrendingUp,
                  score: risk.inherent_risk_score,
                  cls: "text-orange-500",
                },
                {
                  label: "Residual Risk Score",
                  icon: TrendingDown,
                  score: risk.residual_risk_score,
                  cls: "text-blue-500",
                },
              ].map(({ label, icon: Icon, score, cls }) => (
                <div
                  key={label}
                  className="rounded-lg bg-muted/40 border border-border px-3 py-2 flex items-center gap-3"
                >
                  <Icon className={`w-4 h-4 shrink-0 ${cls}`} />
                  <div>
                    <div className="text-[10px] text-muted-foreground">
                      {label}
                    </div>
                    <div className="mt-1">
                      <ScoreBar score={score} />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {(risk.description || risk.business_impact || risk.notes) && (
              <div className="space-y-2">
                {risk.description && (
                  <div className="rounded-lg bg-muted/40 border border-border px-3 py-2 text-xs">
                    <div className="text-[10px] text-muted-foreground mb-1">
                      Description
                    </div>
                    <p className="text-foreground leading-relaxed">
                      {risk.description}
                    </p>
                  </div>
                )}
                {risk.business_impact && (
                  <div className="rounded-lg bg-amber-500/5 border border-amber-500/20 px-3 py-2 text-xs">
                    <div className="text-[10px] text-amber-600 mb-1 font-semibold">
                      Business Impact
                    </div>
                    <p className="text-foreground leading-relaxed">
                      {risk.business_impact}
                    </p>
                  </div>
                )}
                {risk.notes && (
                  <div className="rounded-lg bg-muted/40 border border-border px-3 py-2 text-xs">
                    <div className="text-[10px] text-muted-foreground mb-1">
                      Notes
                    </div>
                    <p className="text-foreground leading-relaxed">
                      {risk.notes}
                    </p>
                  </div>
                )}
              </div>
            )}

            {risk.owner_user_id &&
              (() => {
                const m = members.find((x) => x.user_id === risk.owner_user_id);
                const ownerName =
                  risk.owner_display_name || m?.display_name || m?.email;
                return ownerName ? (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <User2 className="w-3.5 h-3.5" />
                    <span>
                      Owned by{" "}
                      <span className="text-foreground font-medium">
                        {ownerName}
                      </span>
                    </span>
                  </div>
                ) : null;
              })()}

            {/* Actions */}
            <div className="pt-1 border-t border-border/50 flex items-center gap-2 flex-wrap">
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={onEdit}
              >
                <Pencil className="w-3 h-3" /> Edit
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => setShowAssessment(true)}
              >
                <ClipboardCheck className="w-3 h-3" /> Assess
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => setShowTreatment(true)}
              >
                <FileText className="w-3 h-3" />{" "}
                {treatmentPlan ? "Edit Plan" : "Add Plan"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => setShowAddControl(true)}
              >
                <Link2 className="w-3 h-3" /> Link Control
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => setShowAddReview(true)}
              >
                <MessageSquare className="w-3 h-3" /> Add Review
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() => {
                  setRiskTab("tasks");
                  setShowTaskSlideOver(true);
                }}
              >
                <Wrench className="w-3 h-3" /> Add Task
              </Button>
              <div className="flex-1" />
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs gap-1 text-destructive hover:text-destructive"
                onClick={onDelete}
              >
                <Trash2 className="w-3 h-3" /> Delete
              </Button>
            </div>
          </>
        )}
      </div>

      {/* Dialogs */}
      {showAssessment && (
        <AssessmentDialog
          riskId={risk.id}
          orgId={selectedOrgId}
          workspaceId={selectedWorkspaceId}
          onCreated={() => {
            loadDetail();
            onReload();
          }}
          onClose={() => setShowAssessment(false)}
        />
      )}
      {showTreatment && (
        <TreatmentPlanDialog
          riskId={risk.id}
          orgId={selectedOrgId}
          workspaceId={selectedWorkspaceId}
          existing={treatmentPlan}
          members={members}
          onSaved={() => {
            loadDetail();
            onReload();
          }}
          onClose={() => setShowTreatment(false)}
        />
      )}
      {showAddControl && (
        <AddControlDialog
          riskId={risk.id}
          orgId={selectedOrgId}
          workspaceId={selectedWorkspaceId}
          onAdded={() => {
            loadDetail();
            onReload();
          }}
          onClose={() => setShowAddControl(false)}
        />
      )}
      {showAddReview && (
        <AddReviewDialog
          riskId={risk.id}
          onAdded={() => loadDetail()}
          onClose={() => setShowAddReview(false)}
        />
      )}
      {showAssignGroup && (
        <AssignGroupDialog
          riskId={risk.id}
          onAssigned={() => loadDetail()}
          onClose={() => setShowAssignGroup(false)}
        />
      )}
      {showReviewSchedule && (
        <ReviewScheduleDialog
          riskId={risk.id}
          existing={reviewSchedule}
          onSaved={() => loadDetail()}
          onClose={() => setShowReviewSchedule(false)}
        />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Auto-Link with AI — Approval Modal
// ─────────────────────────────────────────────────────────────────────────────

const LINK_TYPE_COLORS: Record<string, string> = {
  mitigating:   "bg-green-500/10 text-green-600 border-green-500/30",
  compensating: "bg-blue-500/10 text-blue-600 border-blue-500/30",
  related:      "bg-purple-500/10 text-purple-600 border-purple-500/30",
}

function AutoLinkModal({
  orgId,
  workspaceId,
  riskId,
  onClose,
}: {
  orgId: string
  workspaceId: string
  riskId?: string   // when set, scopes the job to this single risk
  onClose: () => void
}) {
  // Step: "configure" | "running" | "review"
  const [step, setStep] = useState<"configure" | "running" | "review">("configure")
  const [frameworks, setFrameworks] = useState<FrameworkResponse[]>([])
  const [loadingFw, setLoadingFw] = useState(true)
  const [selectedFrameworkId, setSelectedFrameworkId] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [jobError, setJobError] = useState<string | null>(null)
  const [job, setJob] = useState<JobStatusResponse | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Review step state
  const [pendingItems, setPendingItems] = useState<PendingMapping[]>([])
  const [loadingPending, setLoadingPending] = useState(false)
  const [decisions, setDecisions] = useState<Record<string, "approve" | "reject" | null>>({})
  const [processing, setProcessing] = useState(false)
  const [processError, setProcessError] = useState<string | null>(null)
  const [doneCount, setDoneCount] = useState<{ approved: number; rejected: number } | null>(null)
  const [rejectReason, setRejectReason] = useState("")

  // Load frameworks
  useEffect(() => {
    listFrameworks({ deployed_org_id: orgId })
      .then(res => setFrameworks(res.items ?? []))
      .catch(() => {})
      .finally(() => setLoadingFw(false))
  }, [orgId])

  // Poll job
  const stopPolling = useCallback(() => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
  }, [])

  useEffect(() => {
    if (!job) return
    if (["completed", "failed", "cancelled"].includes(job.status_code)) {
      stopPolling()
      if (job.status_code === "completed") {
        // Load pending mappings for review
        setStep("review")
        setLoadingPending(true)
        listPendingMappings({ org_id: orgId, workspace_id: workspaceId })
          .then(res => {
            setPendingItems(res.items)
            // Default: approve all
            const d: Record<string, "approve" | "reject" | null> = {}
            res.items.forEach(i => { d[i.id] = "approve" })
            setDecisions(d)
          })
          .catch(() => {})
          .finally(() => setLoadingPending(false))
      }
      return
    }
    if (!pollRef.current) {
      pollRef.current = setInterval(async () => {
        try {
          const updated = await getRiskAdvisorJobStatus(job.job_id)
          setJob(updated)
          // Progressive: fetch pending proposals while job is still running
          if (updated.status_code === "running") {
            listPendingMappings({ org_id: orgId, workspace_id: workspaceId })
              .then(res => {
                setPendingItems(res.items)
                setDecisions(prev => {
                  const next = { ...prev }
                  res.items.forEach(i => { if (next[i.id] === undefined) next[i.id] = "approve" })
                  return next
                })
              })
              .catch(() => {})
          }
        } catch { /* ignore */ }
      }, 2000)
    }
    return stopPolling
  }, [job, stopPolling, orgId, workspaceId])

  const handleRun = useCallback(async () => {
    setSubmitting(true)
    setJobError(null)
    try {
      const res = await enqueueBulkLink({
        framework_id: selectedFrameworkId || null,  // null = all frameworks
        risk_id: riskId || null,                    // null = all risks in workspace
        org_id: orgId,
        workspace_id: workspaceId,
        dry_run: false,
      })
      setJob({
        job_id: res.job_id,
        status_code: res.status,
        job_type: "risk_advisor_bulk_link",
        progress_pct: 0,
        output_json: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      setStep("running")
    } catch (e) {
      setJobError(e instanceof Error ? e.message : "Failed to start job")
    } finally {
      setSubmitting(false)
    }
  }, [selectedFrameworkId, orgId, workspaceId])  // selectedFrameworkId optional

  const handleSubmitDecisions = useCallback(async () => {
    const toApprove = pendingItems.filter(i => decisions[i.id] === "approve").map(i => ({ id: i.id, risk_id: i.risk_id }))
    const toReject  = pendingItems.filter(i => decisions[i.id] === "reject").map(i => ({ id: i.id, risk_id: i.risk_id }))
    setProcessing(true)
    setProcessError(null)
    try {
      let approved = 0, rejected = 0
      if (toApprove.length > 0) {
        const res = await bulkApproveMappings(orgId, toApprove.map(i => i.id))
        approved = res.approved
      }
      if (toReject.length > 0) {
        const res = await bulkRejectMappings(orgId, toReject.map(i => i.id), rejectReason || undefined)
        rejected = res.rejected
      }
      setDoneCount({ approved, rejected })
    } catch (e) {
      setProcessError(e instanceof Error ? e.message : "Failed to process decisions")
    } finally {
      setProcessing(false)
    }
  }, [pendingItems, decisions, orgId, rejectReason])

  const setAllDecisions = (value: "approve" | "reject") => {
    const d: Record<string, "approve" | "reject" | null> = {}
    pendingItems.forEach(i => { d[i.id] = value })
    setDecisions(d)
  }

  const jobOutput = job?.output_json as {
    total_controls?: number; mappings_created?: number; mappings_skipped?: number
    errors?: number; log?: string[]; current_control?: string | null; idx?: number
  } | null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-background border border-border rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <GitMerge className="w-4 h-4 text-primary" />
            </div>
            <div>
              <h2 className="text-base font-semibold">Auto-Link Controls with AI</h2>
              <p className="text-xs text-muted-foreground">
                {step === "configure" && (riskId ? "AI will propose controls for this risk only" : "Optionally filter by framework — AI will propose risk-control links for your review")}
                {step === "running" && (riskId ? "Matching controls to this risk…" : "Analysing controls and matching to risks…")}
                {step === "review" && "Review AI proposals before they are applied"}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">

          {/* ── Configure ── */}
          {step === "configure" && (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <label className="text-xs font-medium text-muted-foreground">Framework</label>
                  <span className="text-[10px] text-muted-foreground/60 bg-muted/50 px-1.5 py-0.5 rounded">optional</span>
                </div>
                {loadingFw ? (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="w-3 h-3 animate-spin" /> Loading frameworks…
                  </div>
                ) : (
                  <select
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    value={selectedFrameworkId}
                    onChange={e => setSelectedFrameworkId(e.target.value)}
                  >
                    <option value="">All frameworks (evaluate every control)</option>
                    {frameworks.map(f => (
                      <option key={f.id} value={f.id}>
                        {f.framework_code} — {f.name} ({f.control_count} controls)
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="p-3 bg-primary/5 border border-primary/20 rounded-lg text-xs text-muted-foreground space-y-1">
                <p className="font-medium text-primary flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" /> How it works
                </p>
                <ul className="space-y-0.5 list-disc list-inside">
                  <li>AI evaluates every control (all frameworks, or just the selected one) against all risks in this workspace</li>
                  <li>Proposed links land in a review queue — nothing is created yet</li>
                  <li>You approve or reject each proposal before it takes effect</li>
                  <li>Only approved links are written to the risk registry</li>
                </ul>
              </div>

              {jobError && <p className="text-xs text-red-400 bg-red-500/10 rounded px-3 py-2">{jobError}</p>}
            </div>
          )}

          {/* ── Running ── */}
          {step === "running" && job && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                {["completed", "failed"].includes(job.status_code)
                  ? job.status_code === "completed"
                    ? <CheckCircle2 className="w-5 h-5 text-green-500" />
                    : <AlertTriangle className="w-5 h-5 text-red-500" />
                  : <Loader2 className="w-5 h-5 text-primary animate-spin" />
                }
                <span className="text-sm font-medium capitalize">
                  {job.status_code === "queued" ? "Queued — waiting for worker…"
                    : job.status_code === "running" ? "Running analysis…"
                    : job.status_code === "completed" ? "Analysis complete — loading proposals…"
                    : `Job ${job.status_code}`}
                </span>
              </div>

              {job.progress_pct !== null && (
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Progress</span><span>{job.progress_pct}%</span>
                  </div>
                  <div className="w-full bg-muted/50 rounded-full h-1.5">
                    <div className="bg-primary h-1.5 rounded-full transition-all" style={{ width: `${job.progress_pct}%` }} />
                  </div>
                </div>
              )}

              {jobOutput?.current_control && job.status_code === "running" && (
                <div className="text-xs text-muted-foreground">
                  Analysing <span className="font-mono text-foreground">{jobOutput.current_control}</span>
                  {jobOutput.idx && jobOutput.total_controls && ` (${jobOutput.idx}/${jobOutput.total_controls})`}
                  {" · "}{jobOutput.mappings_created ?? 0} proposals so far
                </div>
              )}

              {pendingItems.length > 0 && job.status_code === "running" && (
                <div className="border border-border rounded-lg p-2 space-y-1 max-h-40 overflow-y-auto">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wide font-medium px-1">
                    Proposals so far ({pendingItems.length})
                  </p>
                  {pendingItems.slice(-10).reverse().map(item => (
                    <div key={item.id} className="text-xs flex items-center gap-2 px-1 py-0.5">
                      <Sparkles className="w-3 h-3 text-primary shrink-0" />
                      <span className="font-mono text-muted-foreground truncate">{item.control_code}</span>
                      <span className="text-muted-foreground">→</span>
                      <span className="truncate">{item.risk_title || item.risk_code}</span>
                    </div>
                  ))}
                </div>
              )}

              {jobOutput?.log && jobOutput.log.length > 0 && (
                <div className="bg-black/80 text-green-400 font-mono text-[10px] rounded p-2 max-h-40 overflow-y-auto space-y-0.5">
                  {jobOutput.log.slice(-30).map((line, i) => (
                    <div key={i}>{line}</div>
                  ))}
                </div>
              )}

              {jobOutput && job.status_code === "completed" && (
                <div className="grid grid-cols-3 gap-3 text-xs">
                  {[
                    { label: "Controls checked", value: jobOutput.total_controls },
                    { label: "Proposals created", value: jobOutput.mappings_created },
                    { label: "Already linked",   value: jobOutput.mappings_skipped },
                  ].map(({ label, value }) => (
                    <div key={label} className="bg-muted/30 rounded p-2.5">
                      <p className="text-muted-foreground">{label}</p>
                      <p className="font-semibold text-sm">{value ?? "—"}</p>
                    </div>
                  ))}
                </div>
              )}

              {job.error_message && (
                <p className="text-xs text-red-400 bg-red-500/10 rounded px-3 py-2">{job.error_message}</p>
              )}
            </div>
          )}

          {/* ── Review ── */}
          {step === "review" && !doneCount && (
            <div className="space-y-3">
              {loadingPending ? (
                <div className="flex items-center gap-2 py-8 justify-center text-muted-foreground text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" /> Loading proposals…
                </div>
              ) : pendingItems.length === 0 ? (
                <div className="text-center py-10">
                  <GitMerge className="w-8 h-8 text-muted-foreground/30 mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No pending proposals found.</p>
                  <p className="text-xs text-muted-foreground mt-1">All links may already exist or no matches were found above the confidence threshold.</p>
                </div>
              ) : (
                <>
                  {/* Bulk actions */}
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-muted-foreground">{pendingItems.length} proposals to review</p>
                    <div className="flex items-center gap-2">
                      <button
                        className="text-xs text-green-600 hover:text-green-500 flex items-center gap-1 font-medium"
                        onClick={() => setAllDecisions("approve")}
                      >
                        <ThumbsUp className="w-3 h-3" /> Approve all
                      </button>
                      <span className="text-muted-foreground/40">|</span>
                      <button
                        className="text-xs text-red-500 hover:text-red-400 flex items-center gap-1 font-medium"
                        onClick={() => setAllDecisions("reject")}
                      >
                        <ThumbsDown className="w-3 h-3" /> Reject all
                      </button>
                    </div>
                  </div>

                  {/* Proposals list */}
                  <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                    {pendingItems.map(item => {
                      const decision = decisions[item.id]
                      return (
                        <div
                          key={item.id}
                          className={`p-3 rounded-lg border transition-colors ${
                            decision === "approve" ? "border-green-500/30 bg-green-500/5"
                            : decision === "reject" ? "border-red-500/30 bg-red-500/5 opacity-60"
                            : "border-border/60"
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-1 min-w-0 space-y-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-[10px] text-muted-foreground font-mono">{item.risk_code}</span>
                                <span className="text-xs text-muted-foreground">→</span>
                                <span className="text-[10px] font-mono text-muted-foreground">{item.control_code}</span>
                                <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${LINK_TYPE_COLORS[item.link_type] ?? ""}`}>
                                  {item.link_type}
                                </span>
                                {item.ai_confidence !== null && (
                                  <span className={`text-[10px] font-semibold ml-auto ${
                                    (item.ai_confidence ?? 0) >= 80 ? "text-green-500"
                                    : (item.ai_confidence ?? 0) >= 65 ? "text-yellow-500"
                                    : "text-muted-foreground"
                                  }`}>
                                    {item.ai_confidence}%
                                  </span>
                                )}
                              </div>
                              <p className="text-sm font-medium truncate">{item.risk_title ?? item.risk_code}</p>
                              <p className="text-xs text-muted-foreground truncate">{item.control_name ?? item.control_code}</p>
                              {item.ai_rationale && (
                                <p className="text-[11px] text-muted-foreground/70 leading-relaxed line-clamp-2">{item.ai_rationale}</p>
                              )}
                            </div>
                            <div className="flex items-center gap-1 shrink-0">
                              <button
                                title="Approve"
                                onClick={() => setDecisions(d => ({ ...d, [item.id]: "approve" }))}
                                className={`p-1.5 rounded transition-colors ${decision === "approve" ? "bg-green-500/20 text-green-600" : "text-muted-foreground hover:text-green-600 hover:bg-green-500/10"}`}
                              >
                                <ThumbsUp className="w-3.5 h-3.5" />
                              </button>
                              <button
                                title="Reject"
                                onClick={() => setDecisions(d => ({ ...d, [item.id]: "reject" }))}
                                className={`p-1.5 rounded transition-colors ${decision === "reject" ? "bg-red-500/20 text-red-500" : "text-muted-foreground hover:text-red-500 hover:bg-red-500/10"}`}
                              >
                                <ThumbsDown className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {/* Optional reject reason */}
                  {Object.values(decisions).some(d => d === "reject") && (
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground font-medium">Rejection reason (optional)</label>
                      <input
                        type="text"
                        value={rejectReason}
                        onChange={e => setRejectReason(e.target.value)}
                        placeholder="e.g. Not applicable to this workspace"
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                      />
                    </div>
                  )}

                  {processError && <p className="text-xs text-red-400 bg-red-500/10 rounded px-3 py-2">{processError}</p>}
                </>
              )}
            </div>
          )}

          {/* ── Done ── */}
          {step === "review" && doneCount && (
            <div className="text-center py-8 space-y-3">
              <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto" />
              <p className="text-base font-semibold">Done!</p>
              <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
                <span className="text-green-600 font-medium">{doneCount.approved} approved</span>
                {doneCount.rejected > 0 && <span className="text-red-500 font-medium">{doneCount.rejected} rejected</span>}
              </div>
              <p className="text-xs text-muted-foreground">Approved links are now live in the risk registry.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 p-4 border-t border-border">
          <Button variant="ghost" size="sm" onClick={onClose}>
            {doneCount ? "Close" : "Cancel"}
          </Button>
          <div className="flex items-center gap-2">
            {step === "configure" && (
              <Button
                size="sm"
                className="gap-2"
                disabled={submitting || loadingFw}
                onClick={handleRun}
              >
                {submitting
                  ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Starting…</>
                  : <><Play className="w-3.5 h-3.5" /> Run Analysis</>
                }
              </Button>
            )}
            {step === "running" && job && ["failed", "cancelled"].includes(job.status_code) && (
              <Button
                size="sm"
                className="gap-2"
                disabled={submitting}
                onClick={handleRun}
              >
                {submitting
                  ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Starting…</>
                  : <><Play className="w-3.5 h-3.5" /> Retry</>
                }
              </Button>
            )}
            {step === "review" && !doneCount && pendingItems.length > 0 && (
              <Button
                size="sm"
                className="gap-2"
                disabled={processing || Object.values(decisions).every(d => d === null)}
                onClick={handleSubmitDecisions}
              >
                {processing
                  ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Applying…</>
                  : <><CheckCircle2 className="w-3.5 h-3.5" /> Apply {Object.values(decisions).filter(d => d === "approve").length} Approved</>
                }
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

export default function RisksPage() {
  const router = useRouter();
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace();
  const { canWrite } = useAccess();
  const canCreateRisk = canWrite("risk_registry");
  const [risks, setRisks] = useState<RiskResponse[]>([]);
  const [categories, setCategories] = useState<DimensionResponse[]>([]);
  const [levels, setLevels] = useState<RiskLevelResponse[]>([]);
  const [treatmentTypes, setTreatmentTypes] = useState<DimensionResponse[]>([]);
  const [members, setMembers] = useState<OrgMemberResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterLevel, setFilterLevel] = useState("");
  const [filterOwner, setFilterOwner] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<
    "title" | "level" | "status" | "created"
  >("created");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const [showCreate, setShowCreate] = useState(false);
  const [showAutoLink, setShowAutoLink] = useState(false);
  const [showQuestionnaire, setShowQuestionnaire] = useState(false);
  const [editRisk, setEditRisk] = useState<RiskResponse | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<RiskResponse | null>(null);
  const [heatmap, setHeatmap] = useState<HeatMapResponse | null>(null);

  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [importResultOpen, setImportResultOpen] = useState(false)
  const [pendingImportFile, setPendingImportFile] = useState<File | null>(null)
  const [viewMode, setViewMode] = useState<"list" | "spreadsheet">("list")
  const load = useCallback(
    async (quiet = false) => {
      if (quiet) setRefreshing(true);
      else setLoading(true);
      setError(null);
      try {
        const filters = {
          org_id: selectedOrgId || undefined,
          workspace_id: selectedWorkspaceId || undefined,
        };
        const [riskRes, catRes, lvlRes, ttRes, hmRes] = await Promise.all([
          listRisks(filters),
          listRiskCategories(),
          listRiskLevels(),
          listTreatmentTypes(),
          getRiskHeatMap(
            selectedOrgId || undefined,
            selectedWorkspaceId || undefined
          ),
        ]);
        setRisks(riskRes.items ?? []);
        setCategories(Array.isArray(catRes) ? catRes : []);
        setLevels(Array.isArray(lvlRes) ? lvlRes : []);
        setTreatmentTypes(Array.isArray(ttRes) ? ttRes : []);
        setHeatmap(hmRes);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [selectedOrgId, selectedWorkspaceId]
  );

  // Load org members for assignee lookups
  useEffect(() => {
    if (!selectedOrgId) return;
    import("@/lib/api/orgs").then(({ listOrgMembers }) =>
      listOrgMembers(selectedOrgId)
        .then((m) => setMembers(m))
        .catch(() => {})
    );
  }, [selectedOrgId]);

  useEffect(() => {
    if (ready) load();
  }, [load, ready]);

  const filtered = useMemo(() => {
    const base = risks.filter((r) => {
      if (search) {
        const q = search.toLowerCase();
        if (
          !r.title?.toLowerCase().includes(q) &&
          !r.risk_code.toLowerCase().includes(q)
        )
          return false;
      }
      if (filterCategory && r.risk_category_code !== filterCategory)
        return false;
      if (filterStatus && r.risk_status !== filterStatus) return false;
      if (filterLevel && r.risk_level_code !== filterLevel) return false;
      if (filterOwner && r.owner_user_id !== filterOwner) return false;
      return true;
    });
    return [...base].sort((a, b) => {
      let cmp = 0;
      if (sortBy === "title")
        cmp = (a.title ?? "").localeCompare(b.title ?? "");
      else if (sortBy === "level")
        cmp =
          (LEVEL_ORDER[a.risk_level_code] ?? 0) -
          (LEVEL_ORDER[b.risk_level_code] ?? 0);
      else if (sortBy === "status")
        cmp =
          (STATUS_ORDER[a.risk_status] ?? 0) -
          (STATUS_ORDER[b.risk_status] ?? 0);
      else cmp = a.created_at.localeCompare(b.created_at);
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [
    risks,
    search,
    filterCategory,
    filterStatus,
    filterLevel,
    filterOwner,
    sortBy,
    sortDir,
  ]);

  // ── Spreadsheet helpers ──────────────────────────────────────────────────

  // Use filtered (respects active search + category/status/level/owner filters)
  const spreadsheetRows = useMemo<RiskSpreadsheetRow[]>(() => 
    filtered.map((r) => ({
      id: r.id,
      risk_code: r.risk_code,
      title: r.title ?? "",
      description: r.description ?? "",
      risk_level_code: r.risk_level_code ?? "",
      treatment_type: r.treatment_type_code ?? "",
      owner_email: r.owner_display_name ?? members.find(m => m.user_id === r.owner_user_id)?.email ?? "",
      owner_user_id: r.owner_user_id ?? "",
      status: r.risk_status ?? "",
      business_impact: r.business_impact ?? "",
    })),
    [filtered, members]
  )

  // ── Skeleton ──────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 rounded-md bg-muted animate-pulse" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  async function handleSpreadsheetSave(row: RiskSpreadsheetRow) {
    const existing = risks.find((r) => r.id === row.id);
    if (!existing) return;
    await updateRisk(existing.id, {
      title: row.title,
      description: row.description || undefined,
      risk_level_code: row.risk_level_code || undefined,
      treatment_type_code: row.treatment_type || undefined,
      risk_status: row.status || undefined,
      business_impact: row.business_impact || undefined,
    })
    await load()
  }

  async function handleSpreadsheetExport(format: "csv" | "json" | "xlsx") {
    const blob = await exportRisks(
      {
        orgId: selectedOrgId ?? undefined,
        workspaceId: selectedWorkspaceId ?? undefined,
      },
      format
    );
    const ext = format;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `risks_export_${new Date().toISOString().split("T")[0]}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleSpreadsheetImport(file: File, dryRun: boolean) {
    const result = await importRisks(
      file,
      {
        orgId: selectedOrgId ?? undefined,
        workspaceId: selectedWorkspaceId ?? undefined,
      },
      dryRun
    );
    const ir: ImportResult = {
      created: result.created,
      updated: result.updated,
      skipped: result.skipped,
      warnings: result.warnings,
      errors: result.errors,
      dry_run: dryRun,
    };
    setImportResult(ir);
    setImportResultOpen(true);
    if (dryRun) {
      setPendingImportFile(file);
    } else {
      await load();
    }
  }

  async function handleImportCommit() {
    if (!pendingImportFile) return;
    const result = await importRisks(
      pendingImportFile,
      {
        orgId: selectedOrgId ?? undefined,
        workspaceId: selectedWorkspaceId ?? undefined,
      },
      false
    );
    setImportResult({
      created: result.created,
      updated: result.updated,
      skipped: result.skipped,
      warnings: result.warnings,
      errors: result.errors,
      dry_run: false,
    });
    setPendingImportFile(null);
    await load();
  }

  async function handleDownloadTemplate(format: "csv" | "xlsx") {
    const blob = await getRisksImportTemplate(format);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `risks_template.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const hasActiveFilters = !!(search || filterCategory || filterStatus || filterLevel || filterOwner)
  const clearFilters = () => { setSearch(""); setFilterCategory(""); setFilterStatus(""); setFilterLevel(""); setFilterOwner("") }

  return (
    <div className="space-y-4">

      {/* ── Header ── */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Risk Registry</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Track, assess, and manage organisational risks</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <OrgWorkspaceSwitcher />
          <ReadOnlyBanner />
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => load(true)} disabled={refreshing} title="Refresh">
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          </Button>
          {/* View mode toggle */}
          <div className="flex items-center rounded-lg border border-border bg-muted/40 p-0.5 gap-0.5">
            <button
              onClick={() => setViewMode("list")}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                viewMode === "list"
                  ? "bg-background shadow-sm text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              title="List view"
            >
              <LayoutList className="w-3.5 h-3.5" />
              List
            </button>
            <button
              onClick={() => setViewMode("spreadsheet")}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                viewMode === "spreadsheet"
                  ? "bg-background shadow-sm text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              title="Spreadsheet view"
            >
              <Table2 className="w-3.5 h-3.5" />
              Spreadsheet
            </button>
          </div>
          <Button variant="outline" size="sm" className="gap-1.5 h-8 text-xs" onClick={() => setShowQuestionnaire(true)}>
            <ClipboardCheck className="h-3.5 w-3.5" /> Open Questionnaire
          </Button>
          {selectedOrgId && selectedWorkspaceId && (
            <Button variant="outline" size="sm" className="gap-1.5 h-8 text-xs border-primary/40 text-primary hover:bg-primary/5" onClick={() => setShowAutoLink(true)}>
              <GitMerge className="h-3.5 w-3.5" /> Auto-Link AI
            </Button>
          )}
          {canCreateRisk && (
            <Button size="sm" onClick={() => setShowCreate(true)} className="gap-1.5 h-8 text-xs">
              <Plus className="h-3.5 w-3.5" /> Create Risk
            </Button>
          )}
        </div>
      </div>

      {/* ── Overdue Banner ── */}
      <OverdueReviewsBanner orgId={selectedOrgId || undefined} />

      {/* ── KPI Bar ── */}
      <RiskDashboardBar orgId={selectedOrgId || undefined} workspaceId={selectedWorkspaceId || undefined} />

      {/* ── Questionnaire context banner ── */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold">Give the agent context before it generates risks</p>
          <p className="text-xs text-muted-foreground mt-0.5">Use the questionnaire to describe the organisation, operating model, compliance exposure, and appetite so the agent can generate risks that are suitable for that specific organisation.</p>
        </div>
        <Button variant="outline" size="sm" className="gap-1.5 h-8 text-xs shrink-0" onClick={() => setShowQuestionnaire(true)}>
          <ClipboardCheck className="h-3.5 w-3.5" /> Open Questionnaire
        </Button>
      </div>

      {/* ── Filters + sort bar ── */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input placeholder="Search risks..." className="pl-9 h-8 text-sm" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="h-8 rounded-md border border-input bg-background px-2 text-xs" value={filterCategory} onChange={e => setFilterCategory(e.target.value)}>
          <option value="">All Categories</option>
          {categories.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
        </select>
        <select className="h-8 rounded-md border border-input bg-background px-2 text-xs" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          {Object.entries(RISK_STATUS_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        <select className="h-8 rounded-md border border-input bg-background px-2 text-xs" value={filterLevel} onChange={e => setFilterLevel(e.target.value)}>
          <option value="">All Levels</option>
          {levels.map(l => <option key={l.code} value={l.code}>{l.name}</option>)}
        </select>
        <select className="h-8 rounded-md border border-input bg-background px-2 text-xs" value={filterOwner} onChange={e => setFilterOwner(e.target.value)}>
          <option value="">All Owners</option>
          {members.filter(m => m.display_name || m.email).map(m => (
            <option key={m.user_id} value={m.user_id}>{m.display_name || m.email}</option>
          ))}
        </select>
        <div className="flex items-center gap-1 ml-auto">
          <select className="h-8 rounded-md border border-input bg-background px-2 text-xs" value={sortBy} onChange={e => setSortBy(e.target.value as typeof sortBy)}>
            <option value="created">Date</option>
            <option value="title">Title</option>
            <option value="level">Level</option>
            <option value="status">Status</option>
          </select>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => setSortDir(d => d === "asc" ? "desc" : "asc")} title={sortDir === "asc" ? "Ascending" : "Descending"}>
            <ArrowUpDown className="w-3.5 h-3.5" />
          </Button>
          <span className="text-xs text-muted-foreground whitespace-nowrap">{filtered.length} / {risks.length}</span>
        </div>
      </div>

      {/* ── Main content ── */}
      {viewMode === "list" ? (
        <div className="flex gap-4 items-start">
          {/* List */}
          <div className="flex-1 min-w-0 space-y-2">
            {error && (
              <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
              </div>
            )}

            {filtered.length > 0 && (
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest px-1">Registered Risks</p>
            )}

            {filtered.length === 0 && !loading && (
              <Card className="rounded-xl border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-20 gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
                    <ShieldAlert className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <div className="text-center max-w-md space-y-1">
                    <p className="text-lg font-semibold">No risks found</p>
                    <p className="text-sm text-muted-foreground">
                      {hasActiveFilters ? "No risks match your current filters." : "Create your first risk to start tracking exposure."}
                    </p>
                  </div>
                  {hasActiveFilters && (
                    <Button variant="outline" size="sm" onClick={clearFilters}>Clear Filters</Button>
                  )}
                </CardContent>
              </Card>
            )}

            <div className="space-y-1">
              {filtered.map(risk => {
                const isExpanded = expandedId === risk.id
                const lm = LEVEL_COLORS[risk.risk_level_code] ?? LEVEL_COLORS.medium
                return (
                  <div key={risk.id} className={`rounded-xl border overflow-hidden border-l-[3px] ${lm.border} group`}>
                    <div
                      className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${isExpanded ? "bg-primary/5" : "hover:bg-muted/30"}`}
                      onClick={() => setExpandedId(isExpanded ? null : risk.id)}
                    >
                      <span className="text-muted-foreground shrink-0">
                        {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                      </span>
                      <span className={`shrink-0 ${lm.icon}`}><ShieldAlert className="w-4 h-4" /></span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-sm">{risk.title}</span>
                          <span className="font-mono text-[10px] text-muted-foreground/60 hidden sm:inline">{risk.risk_code}</span>
                          <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-bold border ${lm.badge}`}>{lm.label}</span>
                          <StatusBadge status={risk.risk_status} />
                          {risk.version > 1 && (
                            <span className="text-[10px] text-muted-foreground/50">v{risk.version}</span>
                          )}
                          {risk.treatment_plan_status && (() => {
                            const m = TREATMENT_PLAN_STATUS_META[risk.treatment_plan_status]
                            return m ? (
                              <span className={`hidden lg:inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${m.cls}`}>
                                <FileText className="w-2.5 h-2.5" />{m.label}
                              </span>
                            ) : null
                          })()}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" onClick={e => e.stopPropagation()}>
                        <button onClick={() => { window.location.href = `/risks/${risk.id}` }}
                          className="rounded px-2 py-1 text-[10px] font-semibold text-muted-foreground border border-border hover:text-foreground hover:border-foreground/30 transition-colors">
                          View →
                        </button>
                        <button onClick={() => setEditRisk(risk)}
                          className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-accent transition-all" title="Edit">
                          <Pencil className="h-3 w-3" />
                        </button>
                        <button onClick={() => setDeleteTarget(risk)}
                          className="rounded p-1 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-all" title="Delete">
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                      <ExternalLink className="w-3.5 h-3.5 text-muted-foreground/40 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    {isExpanded && (
                      <div className="border-t border-border/60">
                        <RiskDetail
                          risk={risk}
                          members={members}
                          onReload={() => load(true)}
                          onEdit={() => setEditRisk(risk)}
                          onDelete={() => setDeleteTarget(risk)}
                        />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Heatmap sidebar */}
          <div className="w-72 shrink-0 hidden lg:block">
            <RiskHeatmap data={heatmap} risks={risks} loading={loading} />
          </div>
        </div>
      ) : (
        /* ── Spreadsheet view ── */
        <div>
          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive mb-3">
              <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
            </div>
          )}
          <EntitySpreadsheet
            columns={risksColumns}
            rows={spreadsheetRows}
            onSave={handleSpreadsheetSave}
            onDelete={async (row: RiskSpreadsheetRow) => {
              const r = risks.find((risk) => risk.id === row.id)
              if (r) setDeleteTarget(r)
            }}
            loading={loading}
            keyField="id"
            totalCount={risks.length}
            exportButton={
              <ExportImportToolbar
                entityName="Risks"
                onExport={handleSpreadsheetExport}
                onImport={handleSpreadsheetImport}
                onDownloadTemplate={handleDownloadTemplate}
              />
            }
          />
          {importResult && (
            <ImportResultDialog
              open={importResultOpen}
              onClose={() => { setImportResultOpen(false); setImportResult(null) }}
              result={importResult}
              onCommit={pendingImportFile ? handleImportCommit : undefined}
            />
          )}
        </div>
      )}

      {/* ── Modals & Dialogs ── */}
      {showAutoLink && selectedOrgId && selectedWorkspaceId && (
        <AutoLinkModal orgId={selectedOrgId} workspaceId={selectedWorkspaceId} onClose={() => { setShowAutoLink(false); load(true) }} />
      )}
      {showQuestionnaire && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-background border border-border rounded-xl shadow-2xl w-full max-w-7xl my-4">
            <RiskQuestionnaireModal orgId={selectedOrgId} workspaceId={selectedWorkspaceId} onClose={() => setShowQuestionnaire(false)} />
          </div>
        </div>
      )}
      {showCreate && (
        <CreateRiskDialog categories={categories} levels={levels} treatmentTypes={treatmentTypes} defaultOrgId={selectedOrgId || undefined} defaultWorkspaceId={selectedWorkspaceId || undefined} onCreated={() => load(true)} onClose={() => setShowCreate(false)} />
      )}
      {editRisk && (
        <EditRiskDialog risk={editRisk} categories={categories} levels={levels} treatmentTypes={treatmentTypes} members={members} onUpdated={() => load(true)} onClose={() => setEditRisk(null)} />
      )}
      {deleteTarget && (
        <DeleteRiskDialog risk={deleteTarget} onDeleted={() => { setExpandedId(null); load(true) }} onClose={() => setDeleteTarget(null)} />
      )}
    </div>
  );
}
