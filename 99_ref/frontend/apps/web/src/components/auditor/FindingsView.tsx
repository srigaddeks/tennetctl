"use client"

import * as React from "react"
import {
  AlertCircle,
  FilePlus2,
  Filter,
  Loader2,
  RefreshCw,
  Search,
  ShieldAlert,
} from "lucide-react"
import { toast } from "sonner"
import { SearchableControlSelector } from "./SearchableControlSelector"

import {
  Badge,
  Button,
  Card,
  CardContent,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@kcontrol/ui"

import {
  engagementsApi,
  type EngagementAssessment,
  type EngagementFinding,
  type EngagementControl,
} from "@/lib/api/engagements"

interface FindingsViewProps {
  engagementId?: string
  orgId?: string
  workspaceId?: string
}

const FINDING_SEVERITY_OPTIONS = [
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
]

const FINDING_TYPE_OPTIONS = [
  { value: "observation", label: "Observation" },
  { value: "non_conformity", label: "Non Conformity" },
  { value: "opportunity", label: "Opportunity" },
  { value: "recommendation", label: "Recommendation" },
]

export function FindingsView({ engagementId }: FindingsViewProps) {
  const [assessments, setAssessments] = React.useState<EngagementAssessment[]>([])
  const [selectedAssessmentId, setSelectedAssessmentId] = React.useState("")
  const [findings, setFindings] = React.useState<EngagementFinding[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [activeFilter, setActiveFilter] = React.useState("all")
  const [isComposerOpen, setIsComposerOpen] = React.useState(false)
  const [controls, setControls] = React.useState<EngagementControl[]>([])
  const [form, setForm] = React.useState({
    title: "",
    description: "",
    recommendation: "",
    control_id: "",
    severity_code: "medium",
    finding_type: "observation" as "observation" | "non_conformity" | "opportunity" | "recommendation",
  })
  const [isAssessmentComposerOpen, setIsAssessmentComposerOpen] = React.useState(false)
  const [assessmentForm, setAssessmentForm] = React.useState({
    name: "",
    description: "",
    assessment_type_code: "external_audit",
  })

  const loadAssessments = React.useCallback(async () => {
    if (!engagementId) {
      setAssessments([])
      setSelectedAssessmentId("")
      setControls([])
      return
    }
    const [items, engControls] = await Promise.all([
      engagementsApi.listEngagementAssessments(engagementId),
      engagementsApi.listEngagementControls(engagementId)
    ])
    setAssessments(items)
    setControls(engControls)
    setSelectedAssessmentId((current) => {
      if (current && items.some((item) => item.id === current)) {
        return current
      }
      return items[0]?.id ?? ""
    })
  }, [engagementId])

  const loadFindings = React.useCallback(async () => {
    if (!engagementId || !selectedAssessmentId) {
      setFindings([])
      setIsLoading(false)
      return
    }
    setIsLoading(true)
    try {
      const data = await engagementsApi.listEngagementFindings(engagementId, selectedAssessmentId)
      setFindings(data.items ?? [])
    } catch (error: any) {
      console.error("Failed to fetch findings:", error)
      toast.error(error.message || "Failed to load engagement findings")
      setFindings([])
    } finally {
      setIsLoading(false)
    }
  }, [engagementId, selectedAssessmentId])

  React.useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    loadAssessments()
      .catch((error: any) => {
        if (!cancelled) {
          console.error("Failed to fetch engagement assessments:", error)
          toast.error(error.message || "Failed to load engagement assessments")
          setAssessments([])
          setSelectedAssessmentId("")
          setIsLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [loadAssessments])

  React.useEffect(() => {
    loadFindings()
  }, [loadFindings])

  const filteredFindings = React.useMemo(() => {
    let current = findings
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      current = current.filter((finding) =>
        [finding.title, finding.description, finding.recommendation, finding.control_id]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(query)),
      )
    }
    if (activeFilter !== "all") {
      current = current.filter((finding) => {
        if (activeFilter === "open") return finding.finding_status_code === "open"
        if (activeFilter === "review") return finding.finding_status_code === "auditor_review"
        if (activeFilter === "closed") {
          return ["verified_closed", "accepted"].includes(finding.finding_status_code)
        }
        return true
      })
    }
    return current
  }, [activeFilter, findings, searchQuery])

  const selectedAssessment = React.useMemo(
    () => assessments.find((item) => item.id === selectedAssessmentId) ?? null,
    [assessments, selectedAssessmentId],
  )

  const handleCreateFinding = async () => {
    if (!engagementId || !selectedAssessmentId || !form.title.trim()) {
      toast.error("Assessment and title are required")
      return
    }
    setIsSubmitting(true)
    const loadingToast = toast.loading("Creating engagement finding...")
    try {
      await engagementsApi.createEngagementFinding(engagementId, selectedAssessmentId, {
        title: form.title.trim(),
        description: form.description.trim() || undefined,
        recommendation: form.recommendation.trim() || undefined,
        severity_code: form.severity_code,
        finding_type: form.finding_type,
        control_id: form.control_id || undefined,
      })
      toast.success("Finding created", { id: loadingToast })
      setForm({
        title: "",
        description: "",
        recommendation: "",
        control_id: "",
        severity_code: "medium",
        finding_type: "observation",
      })
      setIsComposerOpen(false)
      await loadAssessments()
      await loadFindings()
    } catch (error: any) {
      console.error("Failed to create finding:", error)
      toast.error(error.message || "Failed to create finding", { id: loadingToast })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCreateAssessment = async () => {
    if (!engagementId || !assessmentForm.name.trim()) {
      toast.error("Name is required")
      return
    }
    setIsSubmitting(true)
    const loadingToast = toast.loading("Creating assessment...")
    try {
      const newAssessment = await engagementsApi.createEngagementAssessment(engagementId, {
        name: assessmentForm.name.trim(),
        description: assessmentForm.description.trim() || undefined,
        assessment_type_code: assessmentForm.assessment_type_code,
      })
      toast.success("Assessment created", { id: loadingToast })
      setAssessmentForm({
        name: "",
        description: "",
        assessment_type_code: "external_audit",
      })
      setIsAssessmentComposerOpen(false)
      await loadAssessments()
      setSelectedAssessmentId(newAssessment.id)
    } catch (error: any) {
      console.error("Failed to create assessment:", error)
      toast.error(error.message || "Failed to create assessment", { id: loadingToast })
    } finally {
      setIsSubmitting(false)
    }
  }

  const getSeverityBadge = (severityCode: string) => {
    const styles: Record<string, string> = {
      critical: "bg-red-500/15 text-red-400 border-red-500/30",
      high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
      medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
      low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    }
    return (
      <Badge
        variant="outline"
        className={`h-5 px-2 text-[9px] font-black uppercase tracking-widest ${styles[severityCode] || "border-border/60 bg-muted/30 text-muted-foreground"}`}
      >
        {severityCode}
      </Badge>
    )
  }

  const getStatusBadge = (statusCode: string) => {
    const styles: Record<string, string> = {
      open: "border-border/60 bg-muted/30 text-muted-foreground",
      acknowledged: "bg-blue-500/15 text-blue-400 border-blue-500/30",
      in_remediation: "bg-teal-500/15 text-teal-400 border-teal-500/30",
      responded: "bg-violet-500/15 text-violet-400 border-violet-500/30",
      auditor_review: "bg-amber-500/15 text-amber-400 border-amber-500/30",
      verified_closed: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
      accepted: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
      escalated: "bg-red-500/15 text-red-400 border-red-500/30",
      disputed: "bg-rose-500/15 text-rose-400 border-rose-500/30",
    }
    return (
      <Badge
        variant="outline"
        className={`h-5 px-2 text-[9px] font-black uppercase tracking-widest ${styles[statusCode] || "border-border/60 bg-muted/30 text-muted-foreground"}`}
      >
        {statusCode.replaceAll("_", " ")}
      </Badge>
    )
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
      {/* ── Header & Assessment Control Block ── */}
      <div className="flex flex-col gap-6 rounded-3xl border border-border/60 bg-card/80 p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-primary/10 text-primary">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <h3 className="text-2xl font-black tracking-tight">Audit Findings</h3>
            </div>
            <p className="max-w-md text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground opacity-60 leading-relaxed">
              Log and track audit observations, non-conformities, and remediation efforts for this engagement.
            </p>
          </div>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
            <div className="min-w-[280px] space-y-2">
              <div className="flex items-center justify-between px-1">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                  Active Assessment
                </label>
                {!isLoading && assessments.length > 0 && (
                   <span className="text-[9px] font-bold text-primary/60 uppercase">
                     {assessments.length} Available
                   </span>
                )}
              </div>
              <div className="flex gap-2">
                <select
                  value={selectedAssessmentId}
                  onChange={(event) => setSelectedAssessmentId(event.target.value)}
                  className="h-12 w-full rounded-2xl border border-border/60 bg-background px-4 text-sm font-black outline-none transition focus:border-primary/40 focus:ring-4 focus:ring-primary/5"
                >
                  {assessments.length === 0 ? (
                    <option value="" disabled>No assessments created</option>
                  ) : (
                    assessments.map((assessment) => (
                      <option key={assessment.id} value={assessment.id}>
                        {assessment.name || assessment.assessment_code}
                      </option>
                    ))
                  )}
                </select>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    void loadAssessments()
                    void loadFindings()
                  }}
                  className="h-12 w-12 shrink-0 rounded-2xl border-border/60 hover:bg-muted"
                  title="Refresh Findings"
                >
                  <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
                </Button>
              </div>
            </div>

            <Button
              variant="outline"
              onClick={() => setIsAssessmentComposerOpen(true)}
              className="h-12 rounded-2xl px-6 font-black uppercase tracking-widest border-primary/20 bg-primary/5 text-primary hover:bg-primary/10 transition-all border-dashed"
            >
              <FilePlus2 className="mr-2 h-4 w-4" />
              New Assessment
            </Button>
          </div>
        </div>

        {selectedAssessment && (
          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-border/40">
            <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mr-2">
              Status:
            </div>
            <Badge variant="outline" className="h-6 px-3 text-[9px] font-black uppercase tracking-widest bg-background/50">
              {selectedAssessment.assessment_type_name || selectedAssessment.assessment_type_code}
            </Badge>
            <Badge variant="outline" className="h-6 px-3 text-[9px] font-black uppercase tracking-widest bg-primary/10 text-primary border-primary/20">
              {selectedAssessment.assessment_status_name || selectedAssessment.assessment_status_code}
            </Badge>
            {selectedAssessment.is_locked && (
              <Badge variant="outline" className="h-6 px-3 border-red-500/30 bg-red-500/10 text-[9px] font-black uppercase tracking-widest text-red-400">
                Locked Cycle
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* ── Findings Action Bar ── */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/60" />
          <Input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Filter findings by title, description, or control ID..."
            className="h-14 rounded-3xl pl-12 border-border/40 bg-card/40 backdrop-blur-sm focus:bg-background transition-colors font-medium"
          />
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex h-14 items-center gap-1 rounded-3xl border border-border/40 bg-card/40 p-1.5 backdrop-blur-sm">
            {["all", "open", "review", "closed"].map((filter) => (
              <Button
                key={filter}
                variant={activeFilter === filter ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setActiveFilter(filter)}
                className={`h-11 rounded-2xl px-5 text-[10px] font-black uppercase tracking-widest transition-all ${
                  activeFilter === filter ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {filter}
              </Button>
            ))}
          </div>

          <Button
            onClick={() => setIsComposerOpen(true)}
            disabled={!selectedAssessmentId || selectedAssessment?.is_locked}
            className="h-14 rounded-3xl px-8 font-black uppercase tracking-widest shadow-lg shadow-primary/20 gap-3 group"
          >
            <AlertCircle className="h-5 w-5 group-hover:scale-110 transition-transform" />
            Create Finding
          </Button>
        </div>
      </div>

        <Dialog open={isComposerOpen} onOpenChange={setIsComposerOpen}>
          <DialogContent className="max-w-2xl bg-card border-border/60">
            <DialogHeader>
              <DialogTitle className="text-xl font-black tracking-tight">Create Finding</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                    Title
                  </label>
                  <Input
                    value={form.title}
                    onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
                    placeholder="Describe the observation or deficiency"
                    className="h-11 rounded-xl"
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                      Severity
                    </label>
                    <select
                      value={form.severity_code}
                      onChange={(event) => setForm((current) => ({ ...current, severity_code: event.target.value }))}
                      className="h-11 w-full rounded-xl border border-border/60 bg-background px-4 text-sm font-semibold outline-none transition focus:border-primary/40"
                    >
                      {FINDING_SEVERITY_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                      Type
                    </label>
                    <select
                      value={form.finding_type}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          finding_type: event.target.value as typeof current.finding_type,
                        }))
                      }
                      className="h-11 w-full rounded-xl border border-border/60 bg-background px-4 text-sm font-semibold outline-none transition focus:border-primary/40"
                    >
                      {FINDING_TYPE_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
              <SearchableControlSelector
                label="Associated Control (Optional)"
                controls={controls}
                value={form.control_id}
                onChange={(val) => setForm((current) => ({ ...current, control_id: val }))}
              />
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                    Description
                  </label>
                  <textarea
                    value={form.description}
                    onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                    placeholder="What did the auditor observe?"
                    className="min-h-[120px] w-full rounded-xl border border-border/60 bg-background px-4 py-3 text-sm outline-none transition focus:border-primary/40"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                    Recommendation
                  </label>
                  <textarea
                    value={form.recommendation}
                    onChange={(event) => setForm((current) => ({ ...current, recommendation: event.target.value }))}
                    placeholder="Recommended remediation or follow-up"
                    className="min-h-[120px] w-full rounded-xl border border-border/60 bg-background px-4 py-3 text-sm outline-none transition focus:border-primary/40"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <Button
                onClick={handleCreateFinding}
                disabled={isSubmitting || !selectedAssessmentId || !form.title.trim()}
                className="rounded-xl px-5 font-black uppercase tracking-widest"
              >
                {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <AlertCircle className="mr-2 h-4 w-4" />}
                Save Finding
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={isAssessmentComposerOpen} onOpenChange={setIsAssessmentComposerOpen}>
          <DialogContent className="max-w-md border-border/60 bg-card">
            <DialogHeader>
              <DialogTitle className="text-xl font-black tracking-tight">Create Assessment</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                  Assessment Name
                </label>
                <Input
                  value={assessmentForm.name}
                  onChange={(event) => setAssessmentForm((current) => ({ ...current, name: event.target.value }))}
                  placeholder="e.g. Q1 Internal Audit Review"
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                  Type
                </label>
                <select
                  value={assessmentForm.assessment_type_code}
                  onChange={(event) => setAssessmentForm((current) => ({ ...current, assessment_type_code: event.target.value }))}
                  className="h-11 w-full rounded-xl border border-border/60 bg-background px-4 text-sm font-semibold outline-none transition focus:border-primary/40"
                >
                  <option value="internal_audit">Internal Audit</option>
                  <option value="gap_analysis">Gap Analysis</option>
                  <option value="readiness_review">Readiness Review</option>
                  <option value="external_audit">External Audit</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                  Description
                </label>
                <textarea
                  value={assessmentForm.description}
                  onChange={(event) => setAssessmentForm((current) => ({ ...current, description: event.target.value }))}
                  placeholder="Briefly describe the scope or goal of this assessment"
                  className="min-h-[100px] w-full rounded-xl border border-border/60 bg-background px-4 py-3 text-sm outline-none transition focus:border-primary/40"
                />
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <Button
                onClick={handleCreateAssessment}
                disabled={isSubmitting || !assessmentForm.name.trim()}
                className="rounded-xl px-5 font-black uppercase tracking-widest"
              >
                {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FilePlus2 className="mr-2 h-4 w-4" />}
                Create Assessment
              </Button>
            </div>
          </DialogContent>
        </Dialog>


      <Card className="overflow-hidden rounded-3xl border border-border/60 bg-card/85">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex min-h-[240px] items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : !selectedAssessmentId ? (
            <div className="flex min-h-[400px] flex-col items-center justify-center gap-6 px-10 text-center animate-in fade-in zoom-in-95 duration-700">
              <div className="relative">
                <div className="absolute inset-0 scale-150 animate-pulse bg-primary/20 blur-3xl rounded-full" />
                <div className="relative z-10 flex h-24 w-24 items-center justify-center rounded-full bg-card shadow-2xl ring-1 ring-border/60">
                  <ShieldAlert className="h-10 w-10 text-primary" />
                </div>
              </div>
              <div className="max-w-md space-y-3">
                <h4 className="text-xl font-black tracking-tight text-foreground uppercase">
                  No Active Assessment
                </h4>
                <p className="text-sm font-medium leading-relaxed text-muted-foreground">
                  Audit findings must be grouped within an Engagement Assessment. Create your first assessment to begin logging observations.
                </p>
              </div>
              <Button
                onClick={() => setIsAssessmentComposerOpen(true)}
                className="h-14 rounded-3xl px-10 font-black uppercase tracking-widest shadow-xl shadow-primary/20 transition-all hover:scale-105 active:scale-95"
              >
                <FilePlus2 className="mr-2 h-5 w-5" />
                Create First Assessment
              </Button>
            </div>
          ) : filteredFindings.length === 0 ? (
            <div className="flex min-h-[320px] flex-col items-center justify-center gap-4 px-6 text-center animate-in fade-in duration-500">
              <div className="h-16 w-16 rounded-full bg-muted/30 flex items-center justify-center mb-2">
                <AlertCircle className="h-8 w-8 text-muted-foreground/30" />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
                  Zero findings found
                </p>
                <p className="text-[11px] font-medium text-muted-foreground/60 italic">
                  Try adjusting your filters or search query
                </p>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-border/60">
              {filteredFindings.map((finding) => (
                <div key={finding.id} className="grid gap-4 p-6 lg:grid-cols-[220px_minmax(0,1fr)_180px]">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      {getSeverityBadge(finding.severity_code)}
                      {getStatusBadge(finding.finding_status_code)}
                    </div>
                    <div className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                      {finding.finding_type.replaceAll("_", " ")}
                    </div>
                    {finding.control_id ? (
                      <div className="text-xs font-semibold text-muted-foreground">
                        Control: <span className="font-black text-foreground">{finding.control_id}</span>
                      </div>
                    ) : null}
                  </div>
                  <div className="space-y-2">
                    <div className="text-lg font-black tracking-tight">
                      {finding.title || "Untitled finding"}
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      {finding.description || "No detailed narrative was captured for this finding."}
                    </p>
                    {finding.recommendation ? (
                      <div className="rounded-2xl border border-primary/15 bg-primary/[0.03] px-4 py-3 text-sm text-foreground/85">
                        <span className="mr-2 text-[10px] font-black uppercase tracking-[0.2em] text-primary/80">
                          Recommendation
                        </span>
                        {finding.recommendation}
                      </div>
                    ) : null}
                  </div>
                  <div className="space-y-2 text-sm">
                    <div>
                      <div className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                        Created
                      </div>
                      <div className="font-semibold">
                        {new Date(finding.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    {finding.remediation_due_date ? (
                      <div>
                        <div className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                          Remediation Due
                        </div>
                        <div className="font-semibold">
                          {new Date(finding.remediation_due_date).toLocaleDateString()}
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
