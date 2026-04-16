"use client"

import {
  Sparkles,
  CheckCircle2,
  ArrowRight,
  Settings2,
  Loader2,
  Upload,
  FileText,
  PlusCircle,
  X,
} from "lucide-react"
import { Button, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, cn } from "@kcontrol/ui"
import { type ChangeProposal } from "@/components/grc/FrameworkHierarchyTree"
import { type PagePhase } from "../hooks/useBuilder"
import { type FrameworkResponse } from "@/lib/types/grc"

interface BuilderEnhanceTabProps {
  phase: PagePhase
  isStreaming: boolean
  availableFrameworks: FrameworkResponse[]
  enhanceFrameworkId: string | null
  setEnhanceFrameworkId: (id: string | null) => void
  enhanceContext: string
  setEnhanceContext: (ctx: string) => void
  loadingFrameworks: boolean
  onAnalyze: () => void
  proposals: ChangeProposal[]
  onAcceptAll: () => void
  onRejectAll: () => void
  onToggleProposal: (index: number, accepted: boolean) => void
  onApply: (proposals: ChangeProposal[]) => void
  onCancelApply: () => void
  enhanceApplyApproved: boolean
  setEnhanceApplyApproved: (approved: boolean) => void
  enhanceAppliedCount: number | null
  enhanceApplyStats: {
    requested_count: number
    applied_count: number
    failed_count: number
  } | null
  resultFrameworkId: string | null
  onLaunchFramework: (id: string) => void
  failedApplyEvents: any[]
  enhanceUserContext: string
  setEnhanceUserContext: (v: string) => void
  enhanceUploadedFiles: File[]
  setEnhanceUploadedFiles: (files: File[] | ((prev: File[]) => File[])) => void
  enhanceDragOver: boolean
  setEnhanceDragOver: (v: boolean) => void
  enhanceUploading: boolean
}

export function BuilderEnhanceTab({
  phase,
  isStreaming,
  availableFrameworks,
  enhanceFrameworkId,
  setEnhanceFrameworkId,
  enhanceContext,
  setEnhanceContext,
  loadingFrameworks,
  onAnalyze,
  proposals,
  onAcceptAll,
  onRejectAll,
  onToggleProposal,
  onApply,
  onCancelApply,
  enhanceApplyApproved,
  setEnhanceApplyApproved,
  enhanceAppliedCount,
  enhanceApplyStats,
  resultFrameworkId,
  onLaunchFramework,
  failedApplyEvents,
  enhanceUserContext,
  setEnhanceUserContext,
  enhanceUploadedFiles,
  setEnhanceUploadedFiles,
  enhanceDragOver,
  setEnhanceDragOver,
  enhanceUploading,
}: BuilderEnhanceTabProps) {
  const acceptedProposals = proposals.filter(p => p.accepted !== false)
  const isDisabled = isStreaming || phase === "enhance_applying" || enhanceUploading

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar max-w-5xl mx-auto w-full">

      {/* ── Target Framework + Evolution Config ──────────────────────────── */}
      <div className="rounded-2xl md:rounded-[32px] border border-border/60 bg-card/10 backdrop-blur-sm shadow-2xl ring-1 ring-white/[0.08] overflow-hidden">
        <div className="grid grid-cols-1 xl:grid-cols-2 divide-y xl:divide-y-0 xl:divide-x divide-border/40">

          {/* Left: framework select + context */}
          <section className="p-5 md:p-8 space-y-5">
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/80 ml-1">Target Framework Architecture</label>
              <Select value={enhanceFrameworkId ?? ""} onValueChange={id => setEnhanceFrameworkId(id || null)}>
                <SelectTrigger className="w-full h-12 rounded-xl border border-border/60 bg-background/50 px-5 text-sm font-bold focus:ring-4 focus:ring-primary/5 shadow-inner focus:border-primary/40">
                  <SelectValue placeholder={loadingFrameworks ? "Syncing Repositories…" : "Select a framework to evolve"} />
                </SelectTrigger>
                <SelectContent>
                  {availableFrameworks.map(f => (
                    <SelectItem key={f.id} value={f.id}>
                      {f.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/80 ml-1">Enhancement Directive</label>
              <textarea
                placeholder="Describe what you want to improve, fill gaps, or align to…"
                className="w-full min-h-[140px] rounded-2xl border border-border/60 bg-background/50 px-5 py-4 text-sm font-medium placeholder:text-muted-foreground/60 focus:ring-4 focus:ring-primary/5 transition-all resize-none shadow-inner focus:border-primary/40 leading-relaxed text-foreground/90 scrollbar-none"
                value={enhanceUserContext}
                onChange={e => setEnhanceUserContext(e.target.value)}
                disabled={isDisabled}
              />
            </div>
          </section>

          {/* Right: file upload + action */}
          <section className="flex flex-col h-full">
            <div
              onDragOver={e => { e.preventDefault(); setEnhanceDragOver(true) }}
              onDragLeave={() => setEnhanceDragOver(false)}
              onDrop={e => {
                e.preventDefault()
                setEnhanceDragOver(false)
                setEnhanceUploadedFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)])
              }}
              className={cn(
                "flex-1 flex flex-col items-center justify-center p-5 md:p-8 transition-all duration-700 relative overflow-hidden group/drop",
                enhanceDragOver ? "bg-primary/5 scale-[0.98]" : "bg-primary/[0.02] hover:bg-primary/[0.04]",
                enhanceUploadedFiles.length > 0 ? "bg-emerald-500/[0.02]" : ""
              )}
            >
              {enhanceUploadedFiles.length === 0 ? (
                <div className="text-center space-y-4 relative z-10 transition-transform group-hover/drop:scale-105 duration-700">
                  <div className="h-14 w-14 rounded-[20px] bg-primary/10 flex items-center justify-center mx-auto border border-primary/20 shadow-lg">
                    <Upload className="h-6 w-6 text-primary" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-foreground/90">Reference Documents</h3>
                    <p className="text-[10px] text-muted-foreground/50 font-medium max-w-[200px] mx-auto leading-tight">Drop standards, policies, or specs to enrich the framework</p>
                  </div>
                  <Button variant="outline" size="sm" className="h-9 px-6 text-[10px] font-black uppercase tracking-[0.2em] rounded-xl border-primary/20 hover:bg-primary/10 shadow-xl shadow-primary/5" asChild>
                    <label className="cursor-pointer">
                      Browse Files
                      <input type="file" multiple className="hidden" onChange={e => setEnhanceUploadedFiles(prev => [...prev, ...Array.from(e.target.files || [])])} />
                    </label>
                  </Button>
                </div>
              ) : (
                <div className="w-full space-y-3 relative z-10">
                  <div className="flex items-center justify-between px-1">
                    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">Docs ({enhanceUploadedFiles.length})</span>
                    <button onClick={() => setEnhanceUploadedFiles([])} className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40 hover:text-red-400 transition-colors">Clear All</button>
                  </div>
                  <ul className="space-y-2 max-h-[160px] overflow-y-auto px-1 custom-scrollbar">
                    {enhanceUploadedFiles.map((file, i) => (
                      <li key={i} className="group/file flex items-center gap-3 rounded-2xl bg-background/40 border border-border/20 p-3 transition-all hover:bg-emerald-500/10 hover:border-emerald-500/40">
                        <div className="h-8 w-8 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                          <FileText className="h-4 w-4 text-emerald-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-[10px] font-bold text-foreground truncate">{file.name}</p>
                          <p className="text-[8px] font-black text-muted-foreground/40 uppercase tracking-tighter">{(file.size / 1024).toFixed(0)} KB</p>
                        </div>
                        <button
                          onClick={() => setEnhanceUploadedFiles(prev => prev.filter((_, idx) => idx !== i))}
                          className="h-7 w-7 flex items-center justify-center rounded-lg hover:bg-red-500/20 text-muted-foreground/30 hover:text-red-400 transition-all opacity-0 group-hover/file:opacity-100"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </li>
                    ))}
                  </ul>
                  <Button variant="ghost" className="w-full h-10 border border-dashed border-emerald-500/20 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] text-emerald-500/40 hover:text-emerald-500 hover:bg-emerald-500/5" asChild>
                    <label className="cursor-pointer">
                      <PlusCircle className="h-3.5 w-3.5 mr-2" /> Add More
                      <input type="file" multiple className="hidden" onChange={e => setEnhanceUploadedFiles(prev => [...prev, ...Array.from(e.target.files || [])])} />
                    </label>
                  </Button>
                </div>
              )}
            </div>

            <div className="p-5 md:p-8 bg-primary/5 border-t border-border/20 relative overflow-hidden mt-auto">
              <div className="space-y-3 relative z-10">
                <div className="flex flex-col gap-1">
                  <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/80">Framework Evolution</h4>
                  <p className="text-[11px] font-medium text-muted-foreground/60 leading-relaxed">AI will analyze the framework and propose targeted enhancements to make it more complete.</p>
                </div>
                <Button
                  size="lg"
                  onClick={onAnalyze}
                  disabled={!enhanceFrameworkId || isDisabled}
                  className="w-full min-h-[44px] rounded-xl text-[10px] font-bold uppercase tracking-widest gap-2 shadow-[0_20px_40px_-10px_rgba(var(--primary-rgb),0.3)] active:scale-[0.98] transition-all relative overflow-hidden group/btn h-auto px-4 py-2"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/btn:translate-x-full transition-transform duration-1000" />
                  {enhanceUploading ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Indexing Documents…</>
                  ) : isStreaming ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Analyzing…</>
                  ) : (
                    <><Sparkles className="h-4 w-4" /> Initiate Evolution</>
                  )}
                </Button>
              </div>
            </div>
          </section>
        </div>
      </div>

      <div className="space-y-3">
        <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/50 ml-1">Evolution Instructions</label>
        <textarea
          value={enhanceContext}
          onChange={e => setEnhanceContext(e.target.value)}
          placeholder="Describe what to improve: add controls, deepen descriptions, expand acceptance criteria, map risks, restructure hierarchy…"
          className="w-full min-h-[140px] rounded-2xl border border-border/40 bg-card/40 px-5 py-4 text-sm font-medium text-foreground placeholder:text-muted-foreground/30 focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/40 transition-all shadow-inner resize-y"
          disabled={isStreaming || phase === "enhance_applying"}
        />
      </div>

      {phase === "enhance_applying" && (
        <div className="rounded-2xl border border-primary/20 bg-primary/5 px-6 py-4 text-xs font-bold text-primary flex items-center gap-4">
          <Loader2 className="h-4 w-4 shrink-0 animate-spin" />
          <span className="uppercase tracking-widest flex-1 animate-pulse">Applying approved architectural enhancements…</span>
          <button
            onClick={onCancelApply}
            className="ml-auto shrink-0 flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 px-3 py-1.5 rounded-xl transition-colors"
            title="Stop polling and return to review"
          >
            <X className="h-3 w-3" />
            Cancel
          </button>
        </div>
      )}

      {phase === "enhance_complete" && (
        <div className={cn(
          "rounded-[32px] border px-8 py-6 space-y-4 shadow-2xl transition-all duration-700 animate-in zoom-in-95",
          (enhanceApplyStats?.failed_count ?? 0) > 0
            ? "border-amber-500/20 bg-amber-500/5 shadow-amber-500/5"
            : "border-emerald-500/20 bg-emerald-500/5 shadow-emerald-500/5",
        )}>
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className={cn(
              "h-14 w-14 rounded-3xl flex items-center justify-center border shadow-inner",
              (enhanceApplyStats?.failed_count ?? 0) > 0 ? "bg-amber-500/10 border-amber-500/30" : "bg-emerald-500/10 border-emerald-500/30"
            )}>
              <CheckCircle2 className={cn("h-7 w-7", (enhanceApplyStats?.failed_count ?? 0) > 0 ? "text-amber-400" : "text-emerald-400")} />
            </div>
            <div className="flex-1 text-center md:text-left">
              <h3 className={cn(
                "text-lg md:text-xl lg:text-2xl font-black tracking-tight",
                (enhanceApplyStats?.failed_count ?? 0) > 0 ? "text-amber-200" : "text-emerald-200"
              )}>
                Evolution Cycle Finalized
              </h3>
              <p className={cn(
                "text-[10px] font-bold uppercase tracking-widest mt-1 opacity-60",
                (enhanceApplyStats?.failed_count ?? 0) > 0 ? "text-amber-400" : "text-emerald-400"
              )}>
                Changes successfully integrated into core architecture
              </p>
            </div>
            {resultFrameworkId && (
              <Button
                size="lg"
                className="h-11 px-8 text-[10px] font-black uppercase tracking-[0.2em] gap-2.5 rounded-2xl shadow-xl shadow-primary/20"
                onClick={() => onLaunchFramework(resultFrameworkId)}
              >
                Launch Result
                <ArrowRight className="h-4 w-4" />
              </Button>
            )}
          </div>
          {enhanceApplyStats && (
            <div className={cn(
               "flex gap-6 pt-4 border-t border-current/10 text-[9px] font-black uppercase tracking-[0.2em]",
              enhanceApplyStats.failed_count > 0 ? "text-amber-400" : "text-emerald-500/60",
            )}>
              <div className="flex flex-col">
                <span className="opacity-40">Proposals</span>
                <span>{enhanceApplyStats.requested_count}</span>
              </div>
              <div className="flex flex-col">
                <span className="opacity-40">Integrated</span>
                <span>{enhanceApplyStats.applied_count}</span>
              </div>
              <div className="flex flex-col">
                <span className="opacity-40 text-red-400">Rejections</span>
                <span className={enhanceApplyStats.failed_count > 0 ? "text-red-400" : ""}>{enhanceApplyStats.failed_count}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {phase === "enhance_complete" && (enhanceApplyStats?.failed_count ?? 0) > 0 && (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 px-6 py-4 space-y-3">
          <div className="text-[10px] font-black uppercase tracking-widest text-red-400">
            Runtime Integration Errors
          </div>
          {failedApplyEvents.length > 0 ? (
            <ul className="space-y-2">
              {failedApplyEvents.slice(0, 5).map((item, idx) => (
                <li key={idx} className="text-[10px] font-medium text-red-300/60 flex items-center gap-3">
                   <div className="h-1 w-1 rounded-full bg-red-500/40" />
                  <span className="font-mono text-foreground/80">{item.entity_code}</span>
                  <ArrowRight className="h-3 w-3 opacity-20" />
                  <span>{item.error}</span>
                </li>
              ))}
            </ul>
          ) : (
             <p className="text-[10px] text-red-300/40">Partial integration failure. Consult system logs.</p>
          )}
        </div>
      )}

      {proposals.length > 0 && (
        <div className="space-y-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-8 rounded-[40px] border border-border/40 bg-card/20 backdrop-blur-xl shadow-2xl relative overflow-hidden group/actions ring-1 ring-white/5">
             <div className="absolute top-0 right-0 p-12 opacity-[0.02] group-hover/actions:opacity-[0.05] transition-opacity duration-1000 rotate-12">
                <Settings2 className="h-32 w-32" />
             </div>

            <div className="space-y-4 relative z-10 w-full md:w-auto">
              <div>
                <h4 className="text-lg md:text-xl font-black tracking-tight text-foreground/90">{proposals.length} Proposed Enhancements</h4>
                <p className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest mt-0.5">A.I. Generated Optimization Strategy</p>
              </div>

               <label className="flex items-start gap-3 bg-background/40 hover:bg-background/80 p-4 rounded-2xl border border-border/40 transition-colors cursor-pointer group/check">
                <input
                  type="checkbox"
                  className="mt-0.5 h-4 w-4 rounded-lg border-input accent-primary group-hover/check:scale-110 transition-transform"
                  checked={enhanceApplyApproved}
                  onChange={(e) => setEnhanceApplyApproved(e.target.checked)}
                />
                <span className="text-[11px] font-semibold text-muted-foreground/80 leading-relaxed">
                   Review and validate integration set. I approve the selected enhancements including all new controls, risk links and entity enrichments.
                </span>
              </label>
            </div>

            <div className="flex flex-wrap gap-3 relative z-10 w-full md:w-auto justify-end">
                <div className="flex gap-2 w-full md:w-auto">
                    <Button variant="outline" size="sm" className="flex-1 md:flex-none h-10 px-6 text-[9px] font-black uppercase tracking-widest rounded-xl border-border/40 bg-background/20" onClick={onAcceptAll}>Accept All</Button>
                    <Button variant="outline" size="sm" className="flex-1 md:flex-none h-10 px-6 text-[9px] font-black uppercase tracking-widest rounded-xl border-border/40 bg-background/20" onClick={onRejectAll}>Reject All</Button>
                </div>
                <Button
                    className="w-full md:w-auto h-12 px-10 text-[10px] font-black uppercase tracking-[0.2em] gap-3 shadow-2xl shadow-primary/30 rounded-2xl"
                    disabled={acceptedProposals.length === 0 || phase === "enhance_applying" || !enhanceApplyApproved}
                    onClick={() => onApply(acceptedProposals)}
                >
                    <CheckCircle2 className="h-4 w-4" />
                    Apply {acceptedProposals.length} Enhancements
                </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
            {proposals.map((p, i) => (
              <ProposalCard
                key={i}
                proposal={p}
                isAccepted={p.accepted !== false}
                onToggle={(accepted) => onToggleProposal(i, accepted)}
                disabled={phase === "enhance_applying"}
              />
            ))}
          </div>
        </div>
      )}

      {proposals.length === 0 && !isStreaming && (
        <div className="flex flex-col items-center justify-center py-32 gap-6 text-muted-foreground/40 text-center animate-in fade-in zoom-in-95 duration-1000">
          <div className="h-24 w-24 rounded-[40px] bg-muted/20 flex items-center justify-center border border-border/40 shadow-inner">
             <Settings2 className="h-10 w-10 opacity-40 animate-spin-slow" />
          </div>
          <div className="space-y-1">
             <h3 className="text-sm font-black uppercase tracking-[0.3em]">Neural Analyzer Idle</h3>
             <p className="text-[10px] font-bold tracking-widest uppercase opacity-60">Select a framework to begin architectural expansion</p>
          </div>
        </div>
      )}

      {isStreaming && proposals.length === 0 && (
        <div className="flex flex-col items-center justify-center py-32 gap-6 text-primary text-center">
          <div className="h-24 w-24 rounded-[40px] bg-primary/10 flex items-center justify-center border border-primary/20 shadow-2xl shadow-primary/10 relative overflow-hidden">
             <div className="absolute inset-0 bg-gradient-to-t from-primary/20 to-transparent animate-pulse" />
             <Loader2 className="h-10 w-10 animate-spin relative z-10" />
          </div>
          <div className="space-y-2">
             <h3 className="text-sm font-black uppercase tracking-[0.3em] animate-pulse">Running Structural Analysis</h3>
             <div className="flex items-center gap-1 justify-center">
                <div className="h-1 w-1 rounded-full bg-primary/40 animate-bounce" style={{animationDelay: "0ms"}} />
                <div className="h-1 w-1 rounded-full bg-primary/40 animate-bounce" style={{animationDelay: "200ms"}} />
                <div className="h-1 w-1 rounded-full bg-primary/40 animate-bounce" style={{animationDelay: "400ms"}} />
             </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ProposalCard({
  proposal: p,
  isAccepted,
  onToggle,
  disabled
}: {
  proposal: ChangeProposal
  isAccepted: boolean
  onToggle: (accepted: boolean) => void
  disabled: boolean
}) {
    const typeLabel = p.change_type === "enrich_description" ? "Description"
    : p.change_type === "enrich_detail" ? "Architecture"
      : p.change_type === "enrich_acceptance_criteria" ? "Validation"
        : p.change_type === "add_control" ? "New Control"
          : p.change_type === "add_risk_mapping" ? "Risk Link"
            : p.change_type ?? "Change"

    const badgeStyle = p.change_type === "add_control" ? "bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-blue-500/5 text-blue-300"
    : p.change_type === "add_risk_mapping" ? "bg-purple-500/10 text-purple-400 border-purple-500/20 shadow-purple-500/5 text-purple-300"
      : "bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-amber-500/5 text-amber-300"

    const structured = asRecord(p.proposed_value)
    const proposedList = toStringList(p.proposed_value)
    const implementationGuidance = structured ? toStringList(structured.implementation_guidance) : []
    const acceptanceCriteria = structured ? toStringList(structured.acceptance_criteria) : []
    const riskMappings = structured ? asRecordList(structured.risk_mappings) : []
    const riskLink = p.change_type === "add_risk_mapping" ? structured : null
    const newRisk = riskLink ? asRecord(riskLink.new_risk) : null
    const hasCurrentValue = typeof p.current_value === "string"
      ? p.current_value.trim().length > 0
      : p.current_value !== null && p.current_value !== undefined

    return (
        <div className={cn(
            "rounded-[32px] border p-8 space-y-4 text-sm transition-all duration-500 relative overflow-hidden ring-1 ring-white/5",
            isAccepted
                ? "border-border/40 bg-card/40 opacity-100 shadow-2xl hover:bg-card/60"
                : "border-dashed border-muted-foreground/20 bg-muted/10 opacity-50 grayscale scale-[0.98]"
        )}>
             <div className="absolute top-0 right-0 p-8 opacity-[0.02] pointer-events-none">
                 <Settings2 className="h-20 w-20" />
             </div>

            <header className="flex items-center gap-3 relative z-10 w-full mb-2">
                <span className={cn("text-[8px] font-black px-2.5 py-1 rounded-lg border uppercase tracking-[0.2em]", badgeStyle)}>
                    {typeLabel}
                </span>
                <span className="font-mono text-[10px] font-black text-muted-foreground/30 truncate flex-1 uppercase tracking-tighter">
                    {p.entity_code || p.entity_type}
                </span>
                <div className="flex gap-2">
                    <button
                        onClick={() => onToggle(true)}
                        disabled={disabled}
                        className={cn(
                            "h-9 w-9 rounded-xl flex items-center justify-center transition-all border",
                            isAccepted
                                ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-400 shadow-lg shadow-emerald-500/10"
                                : "bg-background/20 border-border/40 text-muted-foreground/40 hover:bg-emerald-500/10 hover:border-emerald-500/20"
                        )}
                    >
                        ✓
                    </button>
                    <button
                        onClick={() => onToggle(false)}
                        disabled={disabled}
                        className={cn(
                            "h-9 w-9 rounded-xl flex items-center justify-center transition-all border",
                            !isAccepted
                                ? "bg-red-500/20 border-red-500/40 text-red-400 shadow-lg shadow-red-500/10"
                                : "bg-background/20 border-border/40 text-muted-foreground/40 hover:bg-red-500/10 hover:border-red-500/20"
                        )}
                    >
                        ✗
                    </button>
                </div>
            </header>

            <div className="space-y-4 relative z-10">
                {p.reason && (
                    <div className="flex gap-3">
                        <div className="h-1 flex-1 mt-2.5 bg-border/20 rounded-full" />
                        <p className="text-[10px] font-bold text-muted-foreground/50 uppercase italic tracking-tighter leading-tight max-w-[80%] text-right">{p.reason}</p>
                    </div>
                )}

                {(p.change_type === "enrich_description" || p.change_type === "enrich_detail" || p.change_type === "enrich_acceptance_criteria") && (
                    <div className="space-y-3">
                        <div className="rounded-2xl border border-border/40 bg-muted/20 p-4 shadow-inner">
                            <div className="text-[8px] font-black uppercase tracking-[0.2em] text-muted-foreground/40">Current State</div>
                            <div className="mt-2 text-[11px] font-medium italic text-muted-foreground/40 line-through opacity-60">
                                {hasCurrentValue ? String(p.current_value) : "(empty state)"}
                            </div>
                        </div>
                        {!structured && proposedList.length === 0 && (
                            <div className="rounded-2xl p-5 bg-emerald-500/5 border border-emerald-500/20 text-[11px] font-bold text-emerald-300 leading-relaxed shadow-inner">
                                {String(p.proposed_value || "")}
                            </div>
                        )}
                    </div>
                )}

                {riskLink && (
                    <div className="rounded-3xl p-6 bg-purple-500/5 border border-purple-500/20 text-xs space-y-4 shadow-inner ring-1 ring-white/5">
                        <div className="space-y-1.5">
                            <div className="text-[8px] font-black uppercase tracking-[0.2em] text-purple-300/60">Target Risk</div>
                            <div className="text-sm font-black tracking-tight text-foreground/90">
                                {typeof riskLink.risk_code === "string" && riskLink.risk_code.trim()
                                    ? riskLink.risk_code
                                    : typeof newRisk?.title === "string" && newRisk.title.trim()
                                      ? newRisk.title
                                      : "Risk mapping proposal"}
                            </div>
                        </div>

                        {typeof riskLink.coverage_type === "string" && riskLink.coverage_type.trim() && (
                            <div className="space-y-1.5">
                                <div className="text-[8px] font-black uppercase tracking-[0.2em] text-purple-300/60">Coverage Type</div>
                                <div className="inline-flex rounded-full border border-purple-500/20 bg-background/50 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.15em] text-purple-200">
                                    {riskLink.coverage_type}
                                </div>
                            </div>
                        )}

                        {typeof newRisk?.description === "string" && newRisk.description.trim() && (
                            <div className="space-y-1.5">
                                <div className="text-[8px] font-black uppercase tracking-[0.2em] text-purple-300/60">Risk Description</div>
                                <div className="text-[11px] font-medium leading-relaxed text-muted-foreground/90">{newRisk.description}</div>
                            </div>
                        )}

                        <div className="flex flex-wrap gap-2 pt-1">
                            {typeof p.entity_type === "string" && p.entity_type.trim() && (
                                <span className="rounded-full border border-purple-500/15 bg-background/50 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.15em] text-purple-200/80">
                                    {p.entity_type}
                                </span>
                            )}
                            {typeof newRisk?.category_code === "string" && newRisk.category_code.trim() && (
                                <span className="rounded-full border border-purple-500/15 bg-background/50 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.15em] text-purple-200/80">
                                    {newRisk.category_code}
                                </span>
                            )}
                            {typeof newRisk?.risk_level_code === "string" && newRisk.risk_level_code.trim() && (
                                <span className="rounded-full border border-purple-500/15 bg-background/50 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.15em] text-purple-200/80">
                                    {newRisk.risk_level_code}
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {structured && !riskLink && (
                    <div className="rounded-3xl p-6 bg-primary/5 border border-primary/10 text-xs space-y-4 shadow-inner ring-1 ring-white/5">
                        {typeof structured.name === 'string' ? (
                            <div className="space-y-1.5">
                                <div className="text-[8px] font-black uppercase tracking-[0.2em] text-primary/40">Control Name</div>
                                <div className="text-sm font-black tracking-tight text-foreground/90">{structured.name}</div>
                            </div>
                        ) : null}
                        {typeof structured.description === 'string' ? (
                            <div className="space-y-1.5">
                                <div className="text-[8px] font-black uppercase tracking-[0.2em] text-primary/40">Consolidated Description</div>
                                <div className="text-[11px] font-bold leading-relaxed text-foreground/90">{structured.description}</div>
                            </div>
                        ) : null}
                        {typeof structured.guidance === 'string' ? (
                            <div className="space-y-1.5">
                                <div className="text-[8px] font-black uppercase tracking-[0.2em] text-primary/40">Guidance</div>
                                <div className="text-[11px] font-bold leading-relaxed text-muted-foreground">{structured.guidance}</div>
                            </div>
                        ) : null}
                        {implementationGuidance.length > 0 && (
                            <div className="space-y-1.5">
                                <div className="text-[8px] font-black uppercase tracking-[0.2em] text-primary/40">Implementation Guidance</div>
                                <ul className="space-y-1 pl-1">
                                    {implementationGuidance.map((item, idx) => (
                                        <li key={idx} className="flex gap-2 text-[10px] font-medium text-muted-foreground/80">
                                            <div className="h-1 w-1 rounded-full bg-primary/40 mt-1.5 shrink-0" />
                                            {item}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {acceptanceCriteria.length > 0 && (
                            <div className="space-y-1.5">
                                <div className="text-[8px] font-black uppercase tracking-[0.2em] text-primary/40">Assurance Criteria</div>
                                <ul className="space-y-1 pl-1">
                                    {acceptanceCriteria.map((c, idx) => (
                                        <li key={idx} className="flex gap-2 text-[10px] font-medium text-muted-foreground/80">
                                            <div className="h-1 w-1 rounded-full bg-primary/40 mt-1.5 shrink-0" />
                                            {c}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {riskMappings.length > 0 && (
                            <div className="space-y-1.5">
                                <div className="text-[8px] font-black uppercase tracking-[0.2em] text-primary/40">Risk Mappings</div>
                                <ul className="space-y-1 pl-1">
                                    {riskMappings.map((mapping, idx) => (
                                        <li key={idx} className="flex gap-2 text-[10px] font-medium text-muted-foreground/80">
                                            <div className="h-1 w-1 rounded-full bg-primary/40 mt-1.5 shrink-0" />
                                            <span className="font-mono text-foreground/90">{String(mapping.risk_code ?? "risk")}</span>
                                            <span className="text-muted-foreground/50">({String(mapping.coverage_type ?? "coverage")})</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {typeof structured.control_code === 'string' || typeof structured.criticality_code === 'string' || typeof structured.control_type === 'string' || typeof structured.automation_potential === 'string' ? (
                            <div className="flex flex-wrap gap-2 pt-1">
                                {typeof structured.control_code === 'string' && (
                                    <span className="rounded-full border border-primary/15 bg-background/50 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.15em] text-primary/70">
                                        {structured.control_code}
                                    </span>
                                )}
                                {typeof structured.criticality_code === 'string' && (
                                    <span className="rounded-full border border-primary/15 bg-background/50 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.15em] text-primary/70">
                                        {structured.criticality_code}
                                    </span>
                                )}
                                {typeof structured.control_type === 'string' && (
                                    <span className="rounded-full border border-primary/15 bg-background/50 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.15em] text-primary/70">
                                        {structured.control_type}
                                    </span>
                                )}
                                {typeof structured.automation_potential === 'string' && (
                                    <span className="rounded-full border border-primary/15 bg-background/50 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.15em] text-primary/70">
                                        {structured.automation_potential}
                                    </span>
                                )}
                            </div>
                        ) : null}
                    </div>
                )}

                {!structured && proposedList.length > 0 && (
                    <div className="rounded-3xl p-6 bg-primary/5 border border-primary/10 text-xs space-y-4 shadow-inner ring-1 ring-white/5">
                        <div className="space-y-1.5">
                            <div className="text-[8px] font-black uppercase tracking-[0.2em] text-primary/40">
                                {p.field === "acceptance_criteria" ? "Assurance Criteria" : "Proposed Values"}
                            </div>
                            <ul className="space-y-1 pl-1">
                                {proposedList.map((item, idx) => (
                                    <li key={idx} className="flex gap-2 text-[10px] font-medium text-muted-foreground/80">
                                        <div className="h-1 w-1 rounded-full bg-primary/40 mt-1.5 shrink-0" />
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                )}

                 {p.change_type === "add_control" && typeof p.proposed_value === "object" && p.proposed_value && !structured?.description && (
                    <div className="rounded-3xl p-6 bg-blue-500/5 border border-blue-500/20 text-xs space-y-4 shadow-inner">
                         <div className="space-y-1">
                            <div className="text-[9px] font-black uppercase tracking-widest text-blue-400/60">Functional Intent</div>
                            <div className="text-sm font-black text-blue-100 italic tracking-tight">{(p.proposed_value as any).name as string}</div>
                         </div>
                         <div className="text-[11px] font-medium leading-relaxed text-blue-300/80">{(p.proposed_value as any).description as string}</div>
                    </div>
                 )}
            </div>
        </div>
    )
}

// Low-level helper internal to file for robustness
function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null
}
function toStringList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(v => String(v ?? ""))
  return []
}
function asRecordList(value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is Record<string, unknown> => !!item && typeof item === "object" && !Array.isArray(item))
}
