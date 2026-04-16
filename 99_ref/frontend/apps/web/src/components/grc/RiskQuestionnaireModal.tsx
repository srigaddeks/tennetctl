"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
} from "@kcontrol/ui";
import {
  Check,
  ChevronDown,
  ChevronUp,
  ClipboardCheck,
  FileText,
  Loader2,
  Save,
  Send,
  X,
  Zap,
  TriangleAlert,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  LayoutGrid,
  Target,
  TrendingUp,
  ArrowRight,
} from "lucide-react";
import {
  completeQuestionnaire,
  fetchCurrentQuestionnaire,
  fetchQuestionnaireVersion,
  listActiveQuestionnaires,
  saveDraftAnswers,
  upsertQuestionnaireAssignment,
} from "@/lib/api/questionnaires";
import type {
  CurrentQuestionnaireResponse,
  QuestionSchema,
  SectionSchema,
  QuestionnaireResponse,
  QuestionnaireVersionResponse,
} from "@/lib/types/questionnaires";

/* ─────────────────────────────────────────────────────────────────────────────
   Circular progress ring component
───────────────────────────────────────────────────────────────────────────── */
function CircularProgress({
  percent,
  size = 56,
  strokeWidth = 5,
  color = "hsl(var(--primary))",
}: {
  percent: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
}) {
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const dash = (percent / 100) * circumference;

  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="hsl(var(--border))"
        strokeWidth={strokeWidth}
        opacity={0.3}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={`${dash} ${circumference - dash}`}
        strokeLinecap="round"
        style={{ transition: "stroke-dasharray 0.6s ease" }}
      />
    </svg>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Question input
───────────────────────────────────────────────────────────────────────────── */
interface QuestionInputProps {
  question: QuestionSchema;
  value: string | string[] | undefined;
  onChange: (val: string | string[]) => void;
  readOnly?: boolean;
}

function QuestionnaireQuestionInput({
  question,
  value,
  onChange,
  readOnly = false,
}: QuestionInputProps) {
  if (question.type === "text") {
    return (
      <textarea
        id={question.id}
        rows={3}
        value={(value as string) ?? ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={readOnly}
        placeholder={
          readOnly
            ? "Previewing..."
            : question.placeholder ?? "Type your answer here..."
        }
        className="w-full rounded-xl border border-border/60 bg-background/60 backdrop-blur-sm px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all placeholder:text-muted-foreground/40 disabled:opacity-50 shadow-sm"
      />
    );
  }

  const multiValue = Array.isArray(value) ? value : [];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
      {question.options?.map((opt) => {
        const isSelected =
          question.type === "multi"
            ? multiValue.includes(opt.value)
            : value === opt.value;

        return (
          <div
            key={opt.value}
            onClick={() => {
              if (readOnly) return;
              if (question.type === "multi") {
                if (isSelected)
                  onChange(multiValue.filter((v) => v !== opt.value));
                else onChange([...multiValue, opt.value]);
              } else {
                if (isSelected) onChange("");
                else onChange(opt.value);
              }
            }}
            className={`group flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium border transition-all duration-200 cursor-pointer select-none ${
              isSelected
                ? "bg-primary/10 text-primary border-primary/60 shadow-sm shadow-primary/10"
                : "bg-background/50 border-border/50 text-muted-foreground hover:border-primary/40 hover:bg-primary/5 hover:text-foreground hover:shadow-sm"
            } ${readOnly && "opacity-60 cursor-not-allowed pointer-events-none"}`}
          >
            <div
              className={`h-4 w-4 rounded-full border-2 flex items-center justify-center shrink-0 transition-all duration-200 ${
                isSelected
                  ? "bg-primary border-primary scale-110"
                  : "border-border/60 group-hover:border-primary/50"
              }`}
            >
              {isSelected && (
                <Check
                  className="h-2.5 w-2.5 text-primary-foreground"
                  strokeWidth={3.5}
                />
              )}
            </div>
            <span className="line-clamp-1 leading-tight">{opt.label}</span>
          </div>
        );
      })}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Sidebar template card
───────────────────────────────────────────────────────────────────────────── */
interface QuestionnaireCardProps {
  template: QuestionnaireResponse;
  isSelected: boolean;
  isPreviewing: boolean;
  answeredCount?: number;
  totalQuestions?: number;
  isNew?: boolean;
  onSelect: () => void;
}

function QuestionnaireCard({
  template,
  isSelected,
  isPreviewing,
  answeredCount = 0,
  totalQuestions = 0,
  isNew = false,
  onSelect,
}: QuestionnaireCardProps) {
  const isActive = isSelected || isPreviewing;
  const isComplete = totalQuestions > 0 && answeredCount >= totalQuestions;
  const showMetadata = isNew || totalQuestions > 0;
  
  return (
    <div
      onClick={onSelect}
      className={`group cursor-pointer rounded-xl border transition-all duration-200 overflow-hidden ${
        isActive
          ? "border-primary/50 bg-primary/5 shadow-sm ring-1 ring-primary/10"
          : "border-border/50 bg-card hover:border-primary/30 hover:bg-muted/20 hover:shadow-sm"
      }`}
    >
      <div className="p-3.5">
        <div className="flex items-start gap-3 mb-2">
          <div
            className={`h-8 w-8 shrink-0 rounded-lg flex items-center justify-center transition-colors duration-200 ${
              isActive
                ? "bg-primary/12 text-primary"
                : "bg-muted/70 text-muted-foreground/70 group-hover:text-muted-foreground"
            }`}
          >
            <FileText className="h-4 w-4" strokeWidth={1.75} />
          </div>
          <div className="flex-1 min-w-0 pt-1">
            <h5 className="text-sm font-semibold truncate group-hover:text-primary/90 transition-colors">
              {template.name}
            </h5>
            {template.description && (
              <p
                className="text-[11px] text-muted-foreground mt-0.5 cursor-help"
                style={{
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
                title={template.description}
              >
                {template.description}
              </p>
            )}
          </div>
        </div>

        {showMetadata && (
          <div className="flex items-center justify-end gap-1.5 pt-1">
            {isNew && (
              <div className="flex items-center gap-1 text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-amber-500/10 text-amber-600 border border-amber-500/20 shadow-sm animate-in fade-in zoom-in duration-300">
                <Zap className="h-2 w-2" />
                NEW
              </div>
            )}
            {totalQuestions > 0 && (
              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-md border shadow-sm ${
                isComplete
                  ? "bg-green-100/50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800/40"
                  : "bg-amber-100/50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800/40"
              }`}>
                {answeredCount}/{totalQuestions}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Main Modal
──────────────────────────────────────────────────────────────────────────── */
export interface RiskQuestionnaireModalProps {
  orgId?: string | null;
  workspaceId?: string | null;
  onClose: () => void;
}

export function RiskQuestionnaireModal({
  orgId,
  workspaceId,
  onClose,
}: RiskQuestionnaireModalProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [templates, setTemplates] = useState<QuestionnaireResponse[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [currentData, setCurrentData] = useState<CurrentQuestionnaireResponse | null>(null);
  const [previewData, setPreviewData] = useState<QuestionnaireVersionResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [saving, setSaving] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [completeSuccess, setCompleteSuccess] = useState(false);
  const [assigningId, setAssigningId] = useState<string | null>(null);
  const [isSwitching, setIsSwitching] = useState(false);
  const [appliedVersions, setAppliedVersions] = useState<Record<string, { version: number; hasResponse: boolean; answered: number; total: number }>>({});
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const toggleSection = (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const allTemplates = await listActiveQuestionnaires();
      setTemplates(allTemplates);

      const targetId = allTemplates.length > 0 ? allTemplates[0].id : null;

      if (orgId) {
        const statuses = await Promise.all(
          allTemplates.map((t) =>
            fetchCurrentQuestionnaire(orgId, t.id, workspaceId).catch(() => null)
          )
        );

        const vMap: Record<string, { version: number; hasResponse: boolean; answered: number; total: number }> = {};
        statuses.forEach((s, idx) => {
          if (s) {
            const sections = (s.content_jsonb.sections ?? []).filter(sec => sec.is_active !== false);
            const questions = sections.flatMap(sec => sec.questions ?? []).filter(q => q.is_active !== false);
            const total = questions.length;
            const answered = questions.filter(q => {
              const v = s.answers_jsonb?.[q.id];
              return v !== undefined && v !== "" && (Array.isArray(v) ? v.length > 0 : true);
            }).length;

            vMap[allTemplates[idx].id] = {
              version: s.version_number,
              hasResponse: s.response_status !== null,
              answered,
              total,
            };
          }
        });
        setAppliedVersions(vMap as any);

        if (targetId) {
          const current = statuses[allTemplates.findIndex((t) => t.id === targetId)];
          if (current) {
            setCurrentData(current);
            setAnswers(current.answers_jsonb ?? {});
            setPreviewData(null);
          } else {
            setCurrentData(null);
            const tmpl = allTemplates.find((t) => t.id === targetId);
            if (tmpl?.active_version_id) {
              const version = await fetchQuestionnaireVersion(tmpl.active_version_id);
              setPreviewData({ ...version, questionnaire_id: tmpl.id });
            }
          }
          setSelectedTemplateId(targetId);
        }
      } else if (targetId) {
        setSelectedTemplateId(targetId);
      }
    } catch (err) {
      console.error("Failed to load questionnaire data:", err);
      setError(err instanceof Error ? err.message : "Failed to load questionnaire data");
    } finally {
      setIsLoading(false);
    }
  }, [orgId, workspaceId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleChange = useCallback((qid: string, val: string | string[]) => {
    setAnswers((prev) => ({ ...prev, [qid]: val }));
    setSaveSuccess(false);
    setCompleteSuccess(false);
  }, []);

  const handleSelectTemplate = useCallback(
    async (template: QuestionnaireResponse) => {
      if (!orgId) return;
      setIsSwitching(true);
      setPreviewData(null);
      try {
        const current = await fetchCurrentQuestionnaire(orgId, template.id, workspaceId);
        if (current) {
          setCurrentData(current);
          setAnswers(current.answers_jsonb ?? {});
        } else if (template.active_version_id) {
          const version = await fetchQuestionnaireVersion(template.active_version_id);
          setPreviewData({ ...version, questionnaire_id: template.id });
          setCurrentData(null);
          setAnswers({});
        }
        setSelectedTemplateId(template.id);
      } catch (err) {
        console.error("Failed to load template:", err);
      } finally {
        setIsSwitching(false);
      }
    },
    [orgId, workspaceId]
  );

  async function handleConfirmAssignment() {
    if (!orgId || !previewData) return;
    setAssigningId(previewData.questionnaire_id);
    try {
      await upsertQuestionnaireAssignment({
        assignment_scope: "workspace",
        org_id: orgId,
        workspace_id: workspaceId,
        questionnaire_version_id: previewData.id,
      });
      await loadData();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to assign questionnaire.");
    } finally {
      setAssigningId(null);
    }
  }

  async function handleSaveDraft() {
    if (!orgId || !selectedTemplateId) return;
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      await saveDraftAnswers(orgId, selectedTemplateId, answers, workspaceId);
      setSaveSuccess(true);
      setCurrentData((prev) => prev ? { ...prev, response_status: "draft" } : prev);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save draft");
    } finally {
      setTimeout(() => setSaveSuccess(false), 3000);
      setSaving(false);
    }
  }

  async function handleComplete() {
    if (!orgId || !selectedTemplateId) return;
    setCompleting(true);
    setSaveError(null);
    setCompleteSuccess(false);
    try {
      await completeQuestionnaire(orgId, selectedTemplateId, answers, workspaceId);
      setCompleteSuccess(true);
      setCurrentData((prev) => prev ? { ...prev, response_status: "completed" } : prev);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to complete questionnaire");
    } finally {
      setCompleting(false);
    }
  }

  const template = templates.find((t) => t.id === selectedTemplateId);

  const allSections =
    previewData?.content_jsonb.sections ??
    currentData?.content_jsonb.sections ??
    [];

  const sections = allSections
    .filter((s) => s.is_active !== false)
    .map((s) => ({
      ...s,
      questions: s.questions.filter((q) => q.is_active !== false),
    }));

  const totalQuestions = sections.flatMap((s) => s.questions).length;
  const totalRequired = sections.flatMap((s) => s.questions).filter((q) => q.required).length;

  const answeredTotal = sections.flatMap((s) => s.questions).filter((q) => {
    const v = answers[q.id];
    return v !== undefined && v !== "" && (Array.isArray(v) ? v.length > 0 : true);
  }).length;

  const answeredRequired = sections.flatMap((s) => s.questions).filter((q) => {
    const v = answers[q.id];
    const hasValue = v !== undefined && v !== "" && (Array.isArray(v) ? v.length > 0 : true);
    return q.required && hasValue;
  }).length;

  const isComplete = totalQuestions > 0 && answeredRequired >= totalRequired;

  const progressPercent =
    totalRequired > 0
      ? Math.round((answeredRequired / totalRequired) * 100)
      : totalQuestions > 0
      ? Math.round((answeredTotal / totalQuestions) * 100)
      : 0;

  const getSectionStats = (section: SectionSchema) => {
    const questions = section.questions;
    const answeredCount = questions.filter((q) => {
      const v = answers[q.id];
      return v !== undefined && v !== "" && (Array.isArray(v) ? v.length > 0 : true);
    }).length;
    const missingRequired = questions.filter(
      (q) => q.required && (answers[q.id] === undefined || answers[q.id] === "")
    ).length;
    return { answeredCount, missingRequired, totalQuestions: questions.length };
  };

  /* ── Loading state ── */
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center">
              <ClipboardCheck className="h-8 w-8 text-primary" />
            </div>
            <div className="absolute -inset-1 rounded-3xl border-2 border-primary/30 border-t-primary animate-spin" />
          </div>
          <p className="text-sm text-muted-foreground animate-pulse">Loading questionnaires…</p>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} className="absolute top-4 right-4 gap-2">
          <X className="h-4 w-4" />
          Close
        </Button>
      </div>
    );
  }

  /* ── Error state ── */
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-5">
        <div className="h-16 w-16 rounded-2xl bg-red-500/10 ring-1 ring-red-500/20 flex items-center justify-center shadow-lg shadow-red-500/10">
          <AlertTriangle className="h-8 w-8 text-red-500" />
        </div>
        <div className="text-center space-y-1">
          <p className="text-base font-semibold text-red-500">Something went wrong</p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
        <div className="flex items-center gap-2 mt-2">
          <Button variant="outline" size="sm" onClick={loadData} className="gap-2">
            <Loader2 className="h-3.5 w-3.5" />
            Retry
          </Button>
          <Button variant="ghost" size="sm" onClick={onClose} className="gap-2">
            <X className="h-3.5 w-3.5" />
            Close
          </Button>
        </div>
      </div>
    );
  }

  /* ── Empty state ── */
  if (templates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-5">
        <div className="h-20 w-20 rounded-3xl bg-gradient-to-br from-muted to-muted/50 ring-1 ring-border/50 flex items-center justify-center shadow-xl">
          <ClipboardCheck className="h-10 w-10 text-muted-foreground" />
        </div>
        <div className="text-center space-y-1">
          <h3 className="text-lg font-semibold">No Questionnaires Available</h3>
          <p className="text-sm text-muted-foreground">There are no active questionnaires at the moment.</p>
        </div>
        <Button variant="outline" size="sm" onClick={onClose} className="mt-2 text-muted-foreground gap-2">
          <X className="h-4 w-4" />
          Close
        </Button>
      </div>
    );
  }

  /* ── Main render ── */
  return (
    <div className="flex flex-col h-full max-h-[85vh] custom-scrollbar">
      {/* Custom Premium Scrollbar Styles */}
      <style dangerouslySetInnerHTML={{ __html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
          height: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(156, 163, 175, 0.25);
          border-radius: 20px;
          border: 1px solid transparent;
          background-clip: content-box;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(156, 163, 175, 0.4);
          background-clip: content-box;
        }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.12);
        }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.25);
        }
      `}} />

      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="relative flex items-center justify-between px-6 py-5 border-b border-border/60 overflow-hidden shrink-0">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-primary/8 via-primary/4 to-transparent pointer-events-none" />
        <div className="absolute top-0 left-0 w-72 h-full bg-gradient-to-r from-primary/5 to-transparent blur-xl pointer-events-none" />

        <div className="relative flex items-center gap-4">
          <div className="relative">
            <div className="h-11 w-11 rounded-2xl bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center shadow-lg shadow-primary/25">
              <ClipboardCheck className="h-5 w-5 text-primary-foreground" />
            </div>
            <div className="absolute -bottom-1 -right-1 h-4 w-4 rounded-full bg-emerald-500 border-2 border-background flex items-center justify-center">
              <Sparkles className="h-2 w-2 text-white" />
            </div>
          </div>
          <div>
            <h2 className="text-lg font-bold tracking-tight">Risk Questionnaires</h2>
            <p className="text-xs text-muted-foreground">
              Complete business context questionnaires to drive AI-powered risk generation
            </p>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="relative gap-2 hover:bg-muted/70 rounded-xl"
        >
          <X className="h-4 w-4" />
          Close
        </Button>
      </div>

      {/* ── Body ──────────────────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">

        {/* ── Sidebar ────────────────────────────────────────────────────── */}
        <div className="w-72 shrink-0 overflow-y-auto border-r border-border/50 bg-gradient-to-b from-muted/20 to-background/5 custom-scrollbar">
          <div className="p-4 space-y-3">
            {/* Sidebar header */}
            <div className="flex items-center gap-2 px-1 py-2">
              <div className="h-5 w-5 rounded-md bg-primary/10 flex items-center justify-center">
                <LayoutGrid className="h-3 w-3 text-primary" />
              </div>
              <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Available Templates
              </span>
            </div>

            {/* Template cards */}
            <div className="space-y-3">
              {templates.map((t) => {
                const isSelected = selectedTemplateId === t.id && currentData !== null;
                const isPreviewing = selectedTemplateId === t.id && previewData !== null;
                const applied = appliedVersions[t.id] as unknown as { version: number; hasResponse: boolean; answered: number; total: number };
                // Only show "NEW" if there's an active assessment AND the latest version is strictly greater
                const isNew = !!applied?.hasResponse && t.latest_version_number > applied.version;
                const answered = isSelected || isPreviewing ? answeredTotal : (applied?.answered ?? 0);
                const total = isSelected || isPreviewing ? totalQuestions : (applied?.total ?? 0);
                
                return (
                  <QuestionnaireCard
                    key={t.id}
                    template={t}
                    isSelected={isSelected}
                    isPreviewing={isPreviewing}
                    isNew={!!isNew}
                    answeredCount={answered}
                    totalQuestions={total}
                    onSelect={() => handleSelectTemplate(t)}
                  />
                );
              })}
            </div>
          </div>
        </div>

        {/* ── Main content ───────────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto custom-scrollbar relative group/main">
          {isSwitching && (
            <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/40 backdrop-blur-[1px] animate-in fade-in duration-300">
              <div className="flex flex-col items-center gap-3">
                <div className="h-10 w-10 rounded-xl border-2 border-primary/20 animate-spin border-t-primary shadow-sm" />
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/60 animate-pulse">
                  Updating View
                </p>
              </div>
            </div>
          )}

          <div className={`p-6 space-y-5 transition-all duration-500 ease-in-out ${isSwitching ? "opacity-30 blur-[1px] scale-[0.99] grayscale-[0.3]" : "opacity-100 blur-0 scale-100"}`}>
            {currentData || previewData ? (
              <>
                {/* ── Preview Banner ──────────────────────────────────────── */}
                {previewData && (
                  <div className="relative rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-500/8 to-orange-500/5 p-4 overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-amber-400/10 blur-3xl -translate-y-6 translate-x-6 pointer-events-none" />
                    <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-amber-500/15 border border-amber-500/20 flex items-center justify-center shadow-sm">
                          <Zap className="h-5 w-5 text-amber-500" />
                        </div>
                        <div>
                          <p className="font-semibold text-sm text-amber-600 dark:text-amber-400">
                            Template Preview Mode
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Viewing {previewData.content_jsonb.sections.length} sections · version {previewData.version_number}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Button
                          size="sm"
                          onClick={handleConfirmAssignment}
                          disabled={!!assigningId}
                          className="gap-2 bg-amber-500 hover:bg-amber-600 text-white shadow-md shadow-amber-500/20"
                        >
                          {assigningId ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <CheckCircle2 className="h-3.5 w-3.5" />
                          )}
                          Apply Template
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setPreviewData(null)}
                          className="hover:bg-amber-500/10 hover:text-amber-600"
                        >
                          Discard
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* ── Upgrade Banner ─────────────────────────────────────── */}
                {!previewData && currentData && template && currentData.questionnaire_version_id !== template.active_version_id && (
                  <div className="relative rounded-2xl border border-amber-500/20 bg-gradient-to-r from-amber-500/[0.08] to-transparent p-4 overflow-hidden mb-4 group shadow-sm">
                    {/* Soft background glow */}
                    <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-amber-500/10 blur-2xl -translate-y-8 translate-x-8 pointer-events-none group-hover:bg-amber-500/15 transition-colors duration-500" />
                    
                    <div className="relative flex flex-col sm:flex-row items-center justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <div className="relative h-10 w-10 shrink-0">
                          <div className="absolute inset-0 rounded-xl bg-amber-500/10 blur-sm animate-pulse" />
                          <div className="relative h-10 w-10 rounded-xl bg-amber-500/15 border border-amber-500/20 flex items-center justify-center shadow-inner">
                            <Zap className="h-5 w-5 text-amber-500" />
                          </div>
                        </div>
                        <div className="space-y-0.5">
                          <h4 className="font-bold text-sm text-amber-600 dark:text-amber-400 tracking-tight leading-none">
                            Update Available
                          </h4>
                          <p className="text-xs text-muted-foreground leading-relaxed">
                            Version <span className="font-semibold text-amber-500/80">v{template.latest_version_number}</span> is now available with improved risk assessment logic.
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-9 px-4 text-xs font-semibold gap-2 border-amber-500/30 bg-background/50 hover:bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-xl shadow-sm transition-all hover:shadow-amber-500/10"
                        onClick={async () => {
                          if (template.active_version_id) {
                            const v = await fetchQuestionnaireVersion(template.active_version_id);
                            setPreviewData({ ...v, questionnaire_id: template.id });
                            setCurrentData(null);
                          }
                        }}
                      >
                        <ArrowRight className="h-3.5 w-3.5" />
                        Preview & Update
                      </Button>
                    </div>
                  </div>
                )}

                {/* ── Active Assessment Header ─────────────────────────────── */}
                {!previewData && currentData && (
                  <div className="relative rounded-2xl border border-primary/20 bg-gradient-to-r from-primary/8 via-primary/4 to-transparent p-5 overflow-hidden">
                    <div className="absolute top-0 right-0 w-40 h-40 rounded-full bg-primary/8 blur-3xl -translate-y-8 translate-x-8 pointer-events-none" />

                    <div className="relative flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2.5 flex-wrap">
                          <Badge
                            variant="default"
                            className={`text-xs font-semibold shadow-sm ${
                              currentData.response_status === "completed"
                                ? "bg-emerald-500/15 text-emerald-600 border-emerald-500/30 hover:bg-emerald-500/15"
                                : "bg-primary/15 text-primary border-primary/30 hover:bg-primary/15"
                            }`}
                          >
                            {currentData.response_status === "completed" ? (
                              <><CheckCircle2 className="h-3 w-3 mr-1" />Completed</>
                            ) : (
                              <><TrendingUp className="h-3 w-3 mr-1" />In Progress</>
                            )}
                          </Badge>
                          <h3 className="font-bold text-base">
                            {templates.find((t) => t.id === selectedTemplateId)?.name ?? "Current Assessment"}
                          </h3>
                          <span className="text-xs text-muted-foreground font-medium">
                            v{currentData.version_number}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Complete all required fields to finalize your organisational profile.
                        </p>
                      </div>

                      {/* Stats pills */}
                      <div className="flex items-center gap-3 shrink-0">
                        {/* Circular progress */}
                        <div className="relative flex items-center justify-center">
                          <CircularProgress
                            percent={progressPercent}
                            size={56}
                            strokeWidth={5}
                            color={isComplete ? "hsl(142, 71%, 45%)" : "hsl(var(--primary))"}
                          />
                          <span className="absolute text-xs font-bold">{progressPercent}%</span>
                        </div>

                        {/* Stat blocks */}
                        <div className="flex items-center gap-2">
                          <div className="text-center px-3 py-2 rounded-xl bg-background/70 border border-border/50 shadow-sm min-w-[52px]">
                            <div className="text-lg font-bold leading-none mb-0.5">{answeredTotal}</div>
                            <div className="text-[10px] text-muted-foreground">Answered</div>
                          </div>
                          <div className="text-center px-3 py-2 rounded-xl bg-background/70 border border-border/50 shadow-sm min-w-[52px]">
                            <div className="text-lg font-bold leading-none mb-0.5">{totalQuestions}</div>
                            <div className="text-[10px] text-muted-foreground">Total</div>
                          </div>
                          <div className="text-center px-3 py-2 rounded-xl bg-primary/10 border border-primary/20 shadow-sm min-w-[52px]">
                            <div className="text-lg font-bold text-primary leading-none mb-0.5">
                              {totalRequired - answeredRequired}
                            </div>
                            <div className="text-[10px] text-muted-foreground">Remaining</div>
                          </div>
                        </div>
                      </div>
                    </div>


                  </div>
                )}

                {/* ── Sections ─────────────────────────────────────────────── */}
                <div className="space-y-4">
                  {sections.map((section, sIdx) => {
                    const stats = getSectionStats(section);
                    const isCollapsed = collapsedSections.has(section.id);
                    const sectionPct = stats.totalQuestions > 0
                      ? Math.round((stats.answeredCount / stats.totalQuestions) * 100)
                      : 0;
                    const sectionDone = stats.missingRequired === 0;

                    return (
                      <div
                        key={section.id}
                        id={`section-${section.id}`}
                        className="group rounded-2xl border border-border/60 bg-card shadow-sm hover:shadow-md transition-shadow duration-300 overflow-hidden"
                      >
                        {/* Section header */}
                        <button
                          type="button"
                          onClick={(e) => toggleSection(section.id, e)}
                          className="w-full text-left"
                        >
                          <div className={`flex items-start justify-between gap-4 px-6 py-4 transition-colors ${
                            isCollapsed ? "rounded-2xl" : "border-b border-border/40 bg-muted/20 hover:bg-muted/30"
                          }`}>
                            <div className="flex items-start gap-4 flex-1 min-w-0">

                              {/* Section number disc */}
                              <div className={`mt-0.5 h-7 w-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold transition-all ${
                                sectionDone
                                  ? "bg-emerald-500/15 text-emerald-600 ring-1 ring-emerald-500/30"
                                  : "bg-primary/10 text-primary ring-1 ring-primary/20"
                              }`}>
                                {sectionDone ? <Check className="h-3.5 w-3.5" strokeWidth={3} /> : sIdx + 1}
                              </div>

                              <div className="flex-1 min-w-0 space-y-1">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <h3 className="font-bold text-base text-foreground leading-tight">
                                    {section.title}
                                  </h3>
                                  <div className={`text-xs px-2 py-0.5 rounded-full font-medium border ${
                                    sectionDone
                                      ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                                      : stats.answeredCount > 0
                                      ? "bg-primary/10 text-primary border-primary/20"
                                      : "bg-muted text-muted-foreground border-border/40"
                                  }`}>
                                    {stats.answeredCount}/{stats.totalQuestions} answered
                                  </div>
                                </div>
                                {section.description && (
                                  <p className="text-xs text-muted-foreground leading-relaxed">
                                    {section.description}
                                  </p>
                                )}

                              </div>
                            </div>

                            {/* Collapse toggle */}
                            <div className={`h-7 w-7 rounded-lg border border-border/50 flex items-center justify-center shrink-0 transition-all mt-0.5 ${
                              isCollapsed ? "bg-muted/60 hover:bg-muted" : "bg-background hover:bg-muted"
                            }`}>
                              {isCollapsed ? (
                                <ChevronDown className="h-4 w-4 text-muted-foreground" />
                              ) : (
                                <ChevronUp className="h-4 w-4 text-muted-foreground" />
                              )}
                            </div>
                          </div>
                        </button>

                        {/* Section questions */}
                        {!isCollapsed && (
                          <div className="px-6 pt-5 pb-6 space-y-7">
                            {section.questions.map((q, qIdx) => {
                              const v = answers[q.id];
                              const isAnswered =
                                v !== undefined &&
                                v !== "" &&
                                (Array.isArray(v) ? v.length > 0 : true);

                              return (
                                <div key={q.id} className="space-y-3">
                                  {/* Question label row */}
                                  <div className="flex items-start justify-between gap-3">
                                    <div className="flex items-start gap-3 flex-1 min-w-0">
                                      {/* Question number */}
                                      <span className="mt-0.5 text-[10px] font-bold text-muted-foreground/60 shrink-0 w-5 text-right">
                                        {qIdx + 1}.
                                      </span>
                                      <div className="space-y-0.5 flex-1 min-w-0">
                                        <label
                                          htmlFor={q.id}
                                          className="text-sm font-semibold text-foreground leading-snug"
                                        >
                                          {q.label}
                                          {q.required && (
                                            <span className="ml-1 text-primary" title="Required">*</span>
                                          )}
                                        </label>
                                        {q.helperText && (
                                          <p className="text-xs text-muted-foreground leading-relaxed">
                                            {q.helperText}
                                          </p>
                                        )}
                                      </div>
                                    </div>
                                    {/* Status badges */}
                                    <div className="flex items-center gap-1.5 shrink-0">
                                      {isAnswered && (
                                        <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-600 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                                          <Check className="h-2.5 w-2.5" strokeWidth={3} />
                                          Answered
                                        </span>
                                      )}
                                      {!q.required && !isAnswered && (
                                        <span className="text-[10px] font-medium text-muted-foreground bg-muted/60 border border-border/40 px-2 py-0.5 rounded-full">
                                          Optional
                                        </span>
                                      )}
                                    </div>
                                  </div>

                                  {/* Input */}
                                  <div className="pl-8">
                                    <QuestionnaireQuestionInput
                                      question={q}
                                      value={answers[q.id]}
                                      onChange={(val) => handleChange(q.id, val)}
                                      readOnly={!!previewData}
                                    />
                                  </div>
                                </div>
                              );
                            })}

                            {!previewData && (
                              <div className="pt-4 mt-1 border-t border-border/40 flex items-center justify-between gap-4">
                                {/* Section status */}
                                <div className={`text-xs font-medium flex items-center gap-1.5 ${
                                  sectionDone ? "text-emerald-600" : "text-amber-500"
                                }`}>
                                  {sectionDone ? (
                                    <>
                                      <CheckCircle2 className="h-3.5 w-3.5" />
                                      All required questions answered
                                    </>
                                  ) : (
                                    <>
                                      <TriangleAlert className="h-3.5 w-3.5" />
                                      {stats.missingRequired} required field{stats.missingRequired !== 1 ? "s" : ""} remaining
                                    </>
                                  )}
                                </div>

                                {/* CTA buttons */}
                                <div className="flex items-center gap-2 shrink-0">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleSaveDraft}
                                    disabled={saving || completing}
                                    className="gap-2 h-8 text-xs rounded-lg hover:bg-muted/60"
                                  >
                                    {saving ? (
                                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    ) : (
                                      <Save className="h-3.5 w-3.5" />
                                    )}
                                    Save Draft
                                  </Button>
                                  <Button
                                    size="sm"
                                    onClick={handleComplete}
                                    disabled={completing || saving || !isComplete}
                                    className="gap-2 h-8 text-xs rounded-lg shadow-sm shadow-primary/20"
                                  >
                                    {completing ? (
                                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    ) : (
                                      <Send className="h-3.5 w-3.5" />
                                    )}
                                    Complete
                                  </Button>
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              /* ── Empty content placeholder ─────────────────────────────── */
              <div className="flex flex-col items-center justify-center h-[420px] gap-5 text-center">
                <div className="relative">
                  <div className="h-24 w-24 rounded-3xl bg-gradient-to-br from-muted via-muted/80 to-muted/40 ring-1 ring-border/30 flex items-center justify-center shadow-xl">
                    <ClipboardCheck className="h-12 w-12 text-muted-foreground/60" />
                  </div>
                  <div className="absolute -bottom-2 -right-2 h-8 w-8 rounded-xl bg-primary/10 ring-1 ring-primary/20 flex items-center justify-center">
                    <Target className="h-4 w-4 text-primary" />
                  </div>
                </div>
                <div className="space-y-1.5 max-w-sm">
                  <h3 className="text-xl font-bold">No Questionnaire Selected</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Select a template from the sidebar to begin your risk assessment and drive AI-powered insights.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Toast notifications ──────────────────────────────────────────── */}
      {(saveSuccess || completeSuccess || saveError) && (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
          {(saveSuccess || completeSuccess) && (
            <div className="flex items-center gap-3 rounded-2xl border border-emerald-500/20 bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 backdrop-blur-md p-4 shadow-xl shadow-emerald-500/10 animate-in slide-in-from-bottom-4 duration-300">
              <div className="h-8 w-8 rounded-xl bg-emerald-500/15 flex items-center justify-center shrink-0">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              </div>
              <div>
                <p className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                  {saveSuccess ? "Progress Saved" : "Assessment Completed!"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {saveSuccess ? "Your answers have been saved successfully." : "Questionnaire results recorded."}
                </p>
              </div>
            </div>
          )}
          {saveError && (
            <div className="flex items-center gap-3 rounded-2xl border border-red-500/20 bg-gradient-to-r from-red-500/10 to-red-500/5 backdrop-blur-md p-4 shadow-xl shadow-red-500/10 animate-in slide-in-from-bottom-4 duration-300">
              <div className="h-8 w-8 rounded-xl bg-red-500/15 flex items-center justify-center shrink-0">
                <TriangleAlert className="h-4 w-4 text-red-500" />
              </div>
              <div>
                <p className="text-sm font-semibold text-red-600">Operation Failed</p>
                <p className="text-xs text-muted-foreground">{saveError}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
