"use client"

import { useState } from "react"
import {
  Sparkles,
  CheckCircle2,
  ArrowRight,
  X,
  Loader2,
  ChevronRight,
} from "lucide-react"
import { Button, cn, Dialog, DialogContent } from "@kcontrol/ui"
import {
  FrameworkHierarchyTree,
  type HierarchyNode,
  type ProposedControl,
} from "@/components/grc/FrameworkHierarchyTree"
import { type PagePhase } from "../hooks/useBuilder"

interface BuilderWorkbenchProps {
  phase: PagePhase
  hierarchyNodes: HierarchyNode[]
  selectedCode: string | null
  setSelectedCode: (code: string | null) => void
  nodeOverrides: Record<string, string>
  setNodeOverrides: (overrides: (prev: Record<string, string>) => Record<string, string>) => void
  isStreaming: boolean
  onGenerateControls: () => void
  onCreateFramework: () => void
  onReset: () => void
  buildCreateApproved: boolean
  setBuildCreateApproved: (approved: boolean) => void
  resultFrameworkId: string | null
  onLaunchFramework: (id: string) => void
  onEditNode?: (code: string, field: "name" | "description", value: string) => void
  onEditControl?: (code: string, field: "name" | "description" | "guidance" | "implementation_guidance", value: string | string[]) => void
  selectedItems?: Set<string>
  onToggleItem?: (code: string) => void
  className?: string
}

// ── Selection state: either a requirement node or a control ──────────────────

type Selection =
  | { type: "requirement"; node: HierarchyNode }
  | { type: "control"; control: ProposedControl }
  | null

export function BuilderWorkbench({
  phase,
  hierarchyNodes,
  selectedCode,
  setSelectedCode,
  nodeOverrides,
  setNodeOverrides,
  isStreaming,
  onGenerateControls,
  onCreateFramework,
  onReset,
  buildCreateApproved,
  setBuildCreateApproved,
  resultFrameworkId,
  onLaunchFramework,
  onEditNode,
  onEditControl,
  selectedItems,
  onToggleItem,
  className,
}: BuilderWorkbenchProps) {
  const [selection, setSelection] = useState<Selection>(null)

  // Flatten hierarchy to find a node by code
  function findNode(code: string): HierarchyNode | null {
    function search(nodes: HierarchyNode[]): HierarchyNode | null {
      for (const n of nodes) {
        if (n.code === code) return n
        if (n.children) { const found = search(n.children); if (found) return found }
      }
      return null
    }
    return search(hierarchyNodes)
  }

  function handleSelectNode(code: string) {
    setSelectedCode(code)
    const node = findNode(code)
    if (node) setSelection({ type: "requirement", node })
  }

  function handleSelectControl(control: ProposedControl) {
    setSelection({ type: "control", control })
    setSelectedCode(null)
  }

  function handleClose() {
    setSelection(null)
    setSelectedCode(null)
  }

  const panelOpen = selection !== null
  const selectedControlCode = selection?.type === "control" ? selection.control.code : null

  return (
    <div className={cn("space-y-5 overflow-y-auto custom-scrollbar p-3 sm:p-4 lg:p-6", className)}>
      {/* Creation Success Banner */}
      {phase === "complete" && resultFrameworkId && (
        <div className="rounded-[24px] border border-emerald-500/20 bg-emerald-500/5 px-8 py-6 flex flex-col md:flex-row items-center gap-6 shadow-2xl shadow-emerald-500/10 animate-in slide-in-from-top-8 duration-700">
          <div className="h-16 w-16 rounded-3xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/30 shadow-inner group overflow-hidden">
            <CheckCircle2 className="h-8 w-8 text-emerald-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="flex-1 text-center md:text-left">
            <h3 className="text-xl md:text-2xl font-black bg-gradient-to-r from-emerald-400 to-emerald-600 bg-clip-text text-transparent tracking-tight">Framework Ready</h3>
            <p className="text-sm text-emerald-300/60 mt-1 font-medium tracking-wide">Requirement hierarchy and controls successfully cataloged.</p>
          </div>
          <Button
            size="lg"
            className="h-12 px-8 text-[11px] font-black uppercase tracking-[0.2em] gap-3 shadow-2xl shadow-emerald-500/30 active:scale-95 transition-all bg-emerald-500 hover:bg-emerald-400 border-none rounded-2xl"
            onClick={() => onLaunchFramework(resultFrameworkId)}
          >
            Launch Portfolio
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Header bar */}
      <div className="flex flex-col xl:flex-row items-stretch xl:items-center justify-between gap-3">
        <div className="space-y-1">
          <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground/40 translate-y-px">Requirement Workbench</h2>
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-primary/40 animate-pulse" />
            <p className="text-[9px] font-bold text-muted-foreground/30 uppercase tracking-[0.1em]">AI-Assisted Structural Mapping</p>
          </div>
        </div>

        <div className="flex flex-wrap items-stretch gap-2 w-full xl:w-auto xl:justify-end">
          {phase === "phase1_review" && (
            <Button
              className="w-full sm:w-auto h-auto min-h-10 px-4 sm:px-6 py-2.5 text-[10px] font-black uppercase tracking-[0.15em] gap-2.5 shadow-2xl shadow-primary/30 rounded-xl whitespace-normal text-center leading-tight"
              onClick={onGenerateControls}
              disabled={isStreaming}
            >
              {isStreaming ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              {isStreaming ? "Streaming..." : "Construct Controls"}
            </Button>
          )}

          {(phase === "phase2_review" || phase === "failed") && (
            <div className="flex flex-wrap items-stretch gap-2 w-full xl:w-auto xl:justify-end">
              <label className="flex min-h-10 w-full sm:w-auto items-center gap-3 text-[10px] font-black uppercase tracking-widest text-muted-foreground/60 cursor-pointer bg-card/40 px-4 sm:px-5 py-2.5 rounded-2xl border border-border/40 transition-all hover:bg-card/80 hover:border-primary/20 group">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded-lg border-primary/20 bg-background accent-primary transition-all group-hover:scale-110"
                  checked={buildCreateApproved}
                  onChange={e => setBuildCreateApproved(e.target.checked)}
                />
                <span>Approve & Commit</span>
              </label>
              <Button
                className="w-full sm:w-auto h-auto min-h-10 px-4 sm:px-6 py-2.5 text-[10px] font-black uppercase tracking-[0.15em] gap-2.5 shadow-2xl shadow-primary/30 rounded-xl whitespace-normal text-center leading-tight"
                onClick={onCreateFramework}
                disabled={!buildCreateApproved}
              >
                <CheckCircle2 className="h-4 w-4" />
                Create Framework
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-10 w-10 shrink-0 text-muted-foreground/40 hover:text-red-400 hover:bg-red-400/5 transition-all rounded-xl border border-transparent hover:border-red-400/20"
                onClick={onReset}
                title="Discard Session"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Tree */}
      <div className="rounded-[24px] sm:rounded-[28px] xl:rounded-[32px] border border-border/40 bg-card/5 backdrop-blur-2xl p-3 sm:p-5 xl:p-8 min-h-[440px] sm:min-h-[540px] 2xl:min-h-[600px] shadow-[0_32px_80px_-16px_rgba(0,0,0,0.6)] relative overflow-hidden group/board ring-1 ring-white/5">
        <div className="absolute top-0 right-0 p-12 opacity-[0.03] group-hover/board:opacity-[0.06] transition-opacity duration-1000 pointer-events-none">
          <Sparkles className="h-48 w-48 -rotate-12" />
        </div>
        <FrameworkHierarchyTree
          nodes={hierarchyNodes}
          mode={phase === "phase2_review" || phase === "complete" || phase === "failed" ? "review" : "build"}
          selectedCode={selectedCode}
          onSelectNode={handleSelectNode}
          selectedControlCode={selectedControlCode}
          onSelectControl={handleSelectControl}
          isStreaming={isStreaming || phase === "phase1_streaming"}
          onEditNode={onEditNode}
          onEditControl={onEditControl}
          selectedItems={phase === "phase2_review" ? selectedItems : undefined}
          onToggleItem={phase === "phase2_review" ? onToggleItem : undefined}
        />
      </div>

      {/* Detail dialog */}
      <Dialog open={panelOpen} onOpenChange={open => { if (!open) handleClose() }}>
        <DialogContent className="sm:max-w-lg max-h-[85vh] flex flex-col p-0 gap-0 rounded-[24px] border border-border/40 bg-card/95 backdrop-blur-3xl overflow-hidden">
          {selection?.type === "requirement" ? (
            <RequirementDetailPanel
              node={selection.node}
              nodeOverrides={nodeOverrides}
              setNodeOverrides={setNodeOverrides}
              onEditNode={onEditNode}
              onGenerateControls={onGenerateControls}
              isStreaming={isStreaming}
              onClose={handleClose}
            />
          ) : selection?.type === "control" ? (
            <ControlDetailPanel
              control={selection.control}
              onEditControl={onEditControl}
              isStreaming={isStreaming}
              onClose={handleClose}
            />
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ── Criticality + type maps ───────────────────────────────────────────────────

const critColors: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: "bg-red-500/10",     text: "text-red-500",     border: "border-red-500/20" },
  high:     { bg: "bg-orange-500/10",  text: "text-orange-500",  border: "border-orange-500/20" },
  medium:   { bg: "bg-yellow-500/10",  text: "text-yellow-500",  border: "border-yellow-500/20" },
  low:      { bg: "bg-emerald-500/10", text: "text-emerald-500", border: "border-emerald-500/20" },
}
const typeStyles: Record<string, { label: string; bg: string; text: string }> = {
  preventive:   { label: "PRV", bg: "bg-blue-500/10",   text: "text-blue-500" },
  detective:    { label: "DET", bg: "bg-purple-500/10", text: "text-purple-500" },
  corrective:   { label: "COR", bg: "bg-indigo-500/10", text: "text-indigo-500" },
  compensating: { label: "CMP", bg: "bg-pink-500/10",   text: "text-pink-500" },
}

// ── Requirement Detail Panel ──────────────────────────────────────────────────

function RequirementDetailPanel({
  node,
  nodeOverrides,
  setNodeOverrides,
  onEditNode,
  onGenerateControls,
  isStreaming,
  onClose,
}: {
  node: HierarchyNode
  nodeOverrides: Record<string, string>
  setNodeOverrides: (fn: (prev: Record<string, string>) => Record<string, string>) => void
  onEditNode?: (code: string, field: "name" | "description", value: string) => void
  onGenerateControls: () => void
  isStreaming: boolean
  onClose: () => void
}) {
  const [name, setName] = useState(node.name)
  const [description, setDescription] = useState(node.description ?? "")
  const tuningPrompt = nodeOverrides[node.code] ?? ""
  const hasChanges = name !== node.name || description !== (node.description ?? "")

  function save() {
    if (name !== node.name) onEditNode?.(node.code, "name", name)
    if (description !== (node.description ?? "")) onEditNode?.(node.code, "description", description)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="shrink-0 flex items-center gap-3 px-5 py-4 border-b border-border/30">
        <div className="flex-1 min-w-0">
          <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40 mb-0.5">Requirement</p>
          <p className="text-[11px] font-bold font-mono text-primary">{node.code}</p>
        </div>
        <button
          onClick={onClose}
          className="h-7 w-7 flex items-center justify-center rounded-lg hover:bg-muted/60 text-muted-foreground/50 hover:text-foreground transition-colors shrink-0"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-5 py-4 space-y-4">
        {/* Name */}
        <div className="space-y-1.5">
          <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40">Name</label>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            className="w-full rounded-xl border border-border/40 bg-background/60 px-3 py-2 text-[13px] text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>

        {/* Description */}
        <div className="space-y-1.5">
          <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40">Description</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={4}
            className="w-full rounded-xl border border-border/40 bg-background/60 px-3 py-2 text-[13px] text-foreground resize-y focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>

        {/* Controls summary */}
        {node.controls && node.controls.length > 0 && (
          <div className="rounded-xl border border-border/30 bg-muted/5 p-3 space-y-2">
            <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40">{node.controls.length} Control{node.controls.length !== 1 ? "s" : ""}</p>
            <div className="space-y-1">
              {node.controls.map(ctrl => {
                const crit = critColors[ctrl.criticality] ?? critColors.medium
                const type = typeStyles[ctrl.control_type] ?? typeStyles.preventive
                return (
                  <div key={ctrl.code} className="flex items-center gap-2 text-[11px]">
                    <span className="font-mono font-bold text-primary/60 shrink-0">{ctrl.code}</span>
                    <span className="flex-1 text-foreground/70 truncate">{ctrl.name}</span>
                    <span className={cn("px-1.5 py-0.5 rounded text-[9px] font-black uppercase border", type.bg, type.text, "border-current/10")}>{type.label}</span>
                    <span className={cn("px-1.5 py-0.5 rounded text-[9px] font-bold uppercase border", crit.bg, crit.text, crit.border)}>{ctrl.criticality}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* AI tuning prompt */}
        <div className="space-y-1.5 border-t border-border/20 pt-4">
          <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40 flex items-center gap-1.5">
            <Sparkles className="h-3 w-3 text-primary/50" />
            AI Enhancement Prompt
          </label>
          <textarea
            value={tuningPrompt}
            onChange={e => setNodeOverrides(prev => ({ ...prev, [node.code]: e.target.value }))}
            rows={3}
            placeholder="Add context for AI to regenerate controls for this requirement…"
            className="w-full rounded-xl border border-border/40 bg-background/60 px-3 py-2 text-[12px] text-foreground resize-y focus:outline-none focus:ring-2 focus:ring-primary/30 placeholder:text-muted-foreground/20"
          />
        </div>
      </div>

      {/* Footer */}
      <div className="shrink-0 px-5 py-4 border-t border-border/30 flex gap-2">
        {hasChanges && (
          <Button
            variant="outline"
            className="flex-1 h-9 text-[10px] font-black uppercase tracking-widest rounded-xl"
            onClick={save}
          >
            Save Changes
          </Button>
        )}
        <Button
          className="flex-1 h-9 text-[10px] font-black uppercase tracking-widest rounded-xl gap-1.5"
          onClick={() => { save(); onGenerateControls() }}
          disabled={isStreaming || !tuningPrompt.trim()}
          title={!tuningPrompt.trim() ? "Add an AI prompt above to enhance controls" : "Re-run AI for this requirement"}
        >
          {isStreaming ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
          AI Enhance
        </Button>
      </div>
    </div>
  )
}

// ── Control Detail Panel ──────────────────────────────────────────────────────

function ControlDetailPanel({
  control,
  onEditControl,
  isStreaming,
  onClose,
}: {
  control: ProposedControl
  onEditControl?: (code: string, field: "name" | "description" | "guidance" | "implementation_guidance", value: string | string[]) => void
  isStreaming: boolean
  onClose: () => void
}) {
  const [name, setName] = useState(control.name)
  const [description, setDescription] = useState(control.description ?? "")
  const [guidance, setGuidance] = useState(control.guidance ?? "")
  const [implLines, setImplLines] = useState(
    Array.isArray(control.implementation_guidance) ? control.implementation_guidance.join("\n") : ""
  )

  const crit = critColors[control.criticality] ?? critColors.medium
  const type = typeStyles[control.control_type] ?? typeStyles.preventive

  const hasChanges =
    name !== control.name ||
    description !== (control.description ?? "") ||
    guidance !== (control.guidance ?? "") ||
    implLines !== (Array.isArray(control.implementation_guidance) ? control.implementation_guidance.join("\n") : "")

  function save() {
    if (name !== control.name) onEditControl?.(control.code, "name", name)
    if (description !== (control.description ?? "")) onEditControl?.(control.code, "description", description)
    if (guidance !== (control.guidance ?? "")) onEditControl?.(control.code, "guidance", guidance)
    const newImpl = implLines.split("\n").map(s => s.trim()).filter(Boolean)
    const oldImpl = Array.isArray(control.implementation_guidance) ? control.implementation_guidance : []
    if (JSON.stringify(newImpl) !== JSON.stringify(oldImpl)) onEditControl?.(control.code, "implementation_guidance", newImpl)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="shrink-0 flex items-center gap-3 px-5 py-4 border-b border-border/30">
        <div className="flex-1 min-w-0">
          <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40 mb-0.5">Control</p>
          <p className="text-[11px] font-bold font-mono text-primary">{control.code}</p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <span className={cn("px-2 py-0.5 rounded-md text-[9px] font-black tracking-wider uppercase border", type.bg, type.text, "border-current/10")}>{type.label}</span>
          <span className={cn("px-2 py-0.5 rounded-md text-[9px] font-bold uppercase border", crit.bg, crit.text, crit.border)}>{control.criticality}</span>
          {(control.automation_potential === "full" || control.automation_potential === "partial") && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-md text-[9px] font-semibold text-primary/70 bg-primary/5 border border-primary/10 capitalize">
              <Sparkles className="h-2.5 w-2.5" />{control.automation_potential}
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="h-7 w-7 flex items-center justify-center rounded-lg hover:bg-muted/60 text-muted-foreground/50 hover:text-foreground transition-colors shrink-0"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-5 py-4 space-y-4">
        {/* Name */}
        <div className="space-y-1.5">
          <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40">Name</label>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            className="w-full rounded-xl border border-border/40 bg-background/60 px-3 py-2 text-[13px] text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>

        {/* Description */}
        <div className="space-y-1.5">
          <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40">Description</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={3}
            className="w-full rounded-xl border border-border/40 bg-background/60 px-3 py-2 text-[13px] text-foreground resize-y focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>

        {/* Guidance */}
        <div className="space-y-1.5">
          <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40">Guidance</label>
          <textarea
            value={guidance}
            onChange={e => setGuidance(e.target.value)}
            rows={3}
            placeholder="Implementation guidance…"
            className="w-full rounded-xl border border-border/40 bg-background/60 px-3 py-2 text-[13px] text-foreground resize-y focus:outline-none focus:ring-2 focus:ring-primary/30 placeholder:text-muted-foreground/20"
          />
        </div>

        {/* Implementation steps */}
        <div className="space-y-1.5">
          <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40 flex items-center gap-1.5">
            <ChevronRight className="h-3 w-3" />
            Implementation Steps
            <span className="text-muted-foreground/30 normal-case font-normal tracking-normal">(one per line)</span>
          </label>
          <textarea
            value={implLines}
            onChange={e => setImplLines(e.target.value)}
            rows={5}
            placeholder={"Step 1\nStep 2\nStep 3"}
            className="w-full rounded-xl border border-border/40 bg-background/60 px-3 py-2 text-[12px] text-foreground resize-y focus:outline-none focus:ring-2 focus:ring-primary/30 placeholder:text-muted-foreground/20 font-mono"
          />
        </div>
      </div>

      {/* Footer */}
      <div className="shrink-0 px-5 py-4 border-t border-border/30 flex gap-2">
        {hasChanges && (
          <Button
            variant="outline"
            className="flex-1 h-9 text-[10px] font-black uppercase tracking-widest rounded-xl"
            onClick={save}
          >
            Save Changes
          </Button>
        )}
        <Button
          className="flex-1 h-9 text-[10px] font-black uppercase tracking-widest rounded-xl gap-1.5"
          disabled={isStreaming}
          title="AI enhancement for individual controls coming soon"
        >
          {isStreaming ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
          AI Enhance
        </Button>
      </div>
    </div>
  )
}
