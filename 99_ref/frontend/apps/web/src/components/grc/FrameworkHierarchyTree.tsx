"use client"

import { useState, useEffect, useRef } from "react"
import {
  ChevronRight,
  ChevronDown,
  AlertCircle,
  Sparkles,
  CheckCircle2,
  Pencil,
} from "lucide-react"
import { cn } from "@kcontrol/ui"

// ── Color maps (declared early — used in tooltip content below) ───────────────

const criticalityColorsEarly: Record<string, { bg: string; text: string; border: string; icon: any }> = {
  critical: { bg: "bg-red-500/10", text: "text-red-500", border: "border-red-500/20", icon: AlertCircle },
  high: { bg: "bg-orange-500/10", text: "text-orange-500", border: "border-orange-500/20", icon: AlertCircle },
  medium: { bg: "bg-yellow-500/10", text: "text-yellow-500", border: "border-yellow-500/20", icon: AlertCircle },
  low: { bg: "bg-emerald-500/10", text: "text-emerald-500", border: "border-emerald-500/20", icon: CheckCircle2 },
}

const controlTypeStylesEarly: Record<string, { label: string; bg: string; text: string }> = {
  preventive: { label: "PRV", bg: "bg-blue-500/10", text: "text-blue-500" },
  detective: { label: "DET", bg: "bg-purple-500/10", text: "text-purple-500" },
  corrective: { label: "COR", bg: "bg-indigo-500/10", text: "text-indigo-500" },
  compensating: { label: "CMP", bg: "bg-pink-500/10", text: "text-pink-500" },
}


// ── Types ─────────────────────────────────────────────────────────────────────

export interface HierarchyNode {
  code: string
  name: string
  description?: string
  parent_code: string | null
  depth: number
  sort_order: number
  children?: HierarchyNode[]
  controls?: ProposedControl[]
  is_new?: boolean
  diff_status?: "unchanged" | "modified" | "new"
}

export interface ProposedControl {
  code: string
  name: string
  description?: string
  guidance?: string
  implementation_guidance?: string[]
  requirement_code: string
  criticality: "critical" | "high" | "medium" | "low"
  control_type: "preventive" | "detective" | "corrective" | "compensating"
  automation_potential: "full" | "partial" | "manual"
  is_new?: boolean
}

export interface NodeEditState {
  [code: string]: { name?: string; description?: string }
}

export interface ControlEditState {
  [code: string]: {
    name?: string
    description?: string
    guidance?: string
    implementation_guidance?: string[]
  }
}

export interface ChangeProposal {
  change_type: string
  entity_type: string
  entity_id: string | null
  entity_code: string
  field: string
  current_value: unknown
  proposed_value: unknown
  reason: string
  accepted?: boolean
}

export type TreeMode = "build" | "review" | "enhance"

interface Props {
  nodes: HierarchyNode[]
  mode: TreeMode
  selectedCode: string | null
  onSelectNode: (code: string) => void
  selectedControlCode?: string | null
  onSelectControl?: (control: ProposedControl) => void
  proposals?: ChangeProposal[]
  onAcceptChange?: (proposal: ChangeProposal) => void
  onRejectChange?: (proposal: ChangeProposal) => void
  isStreaming?: boolean
  onEditNode?: (code: string, field: "name" | "description", value: string) => void
  onEditControl?: (code: string, field: "name" | "description" | "guidance" | "implementation_guidance", value: string | string[]) => void
  selectedItems?: Set<string>
  onToggleItem?: (code: string) => void
}

// Aliases so ControlChip can use the same maps declared at top of file
const criticalityColors = criticalityColorsEarly
const controlTypeStyles = controlTypeStylesEarly

// ── Control chip ──────────────────────────────────────────────────────────────

function ControlChip({
  control,
  onSelectControl,
  isSelected,
  selectable,
  selected,
  onToggle,
}: {
  control: ProposedControl
  onSelectControl?: (control: ProposedControl) => void
  isSelected?: boolean
  selectable?: boolean
  selected?: boolean
  onToggle?: (code: string) => void
}) {
  const crit = criticalityColors[control.criticality] || criticalityColors.medium
  const CritIcon = crit.icon
  const typeStyle = controlTypeStyles[control.control_type] || controlTypeStyles.preventive

  return (
    <div
      className={cn(
        "group flex items-center gap-2.5 px-3 py-2 rounded-xl transition-all",
        onSelectControl && "cursor-pointer hover:bg-muted/40",
        isSelected && "bg-primary/[0.08] ring-1 ring-primary/20",
        selectable && !selected && "opacity-50",
        control.is_new && "bg-emerald-500/[0.02] ring-1 ring-emerald-500/10",
      )}
      onClick={onSelectControl ? (e) => { e.stopPropagation(); onSelectControl(control) } : undefined}
    >
      {selectable && (
        <input
          type="checkbox"
          checked={selected ?? false}
          onChange={() => onToggle?.(control.code)}
          onClick={e => e.stopPropagation()}
          className="h-3.5 w-3.5 rounded accent-primary shrink-0 cursor-pointer"
        />
      )}

      <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-background border border-border/40 shadow-sm text-[10px] font-bold font-mono text-muted-foreground">
        {(control.automation_potential === "full" || control.automation_potential === "partial") && (
          <Sparkles className="h-2.5 w-2.5 text-primary" />
        )}
        {control.code}
      </div>

      <span className="flex-1 text-[13px] font-medium text-foreground/75 leading-tight min-w-0 truncate">{control.name}</span>

      <div className="shrink-0 flex items-center gap-1.5">
        <span className={cn("px-1.5 py-0.5 rounded-md text-[9px] font-black tracking-wider uppercase border", typeStyle.bg, typeStyle.text, "border-current/10")}>
          {typeStyle.label}
        </span>
        <div className={cn("flex items-center gap-1 px-1.5 py-0.5 rounded-md border", crit.bg, crit.text, crit.border)}>
          <CritIcon className="h-2.5 w-2.5" />
          <span className="text-[9px] font-bold uppercase hidden sm:inline">{control.criticality}</span>
        </div>
      </div>
    </div>
  )
}

// ── Single Tree Node ──────────────────────────────────────────────────────────

function TreeNode({
  node,
  mode,
  selectedCode,
  onSelectNode,
  selectedControlCode,
  onSelectControl,
  proposals,
  onAcceptChange,
  onRejectChange,
  onEditNode,
  onEditControl,
  isNew,
  selectedItems,
  onToggleItem,
}: {
  node: HierarchyNode
  mode: TreeMode
  selectedCode: string | null
  onSelectNode: (code: string) => void
  selectedControlCode?: string | null
  onSelectControl?: (control: ProposedControl) => void
  proposals?: ChangeProposal[]
  onAcceptChange?: (p: ChangeProposal) => void
  onRejectChange?: (p: ChangeProposal) => void
  onEditNode?: (code: string, field: "name" | "description", value: string) => void
  onEditControl?: (code: string, field: "name" | "description" | "guidance" | "implementation_guidance", value: string | string[]) => void
  isNew?: boolean
  selectedItems?: Set<string>
  onToggleItem?: (code: string) => void
}) {
  const [expanded, setExpanded] = useState(node.depth === 0)
  const [editingDesc, setEditingDesc] = useState(false)
  const [descDraft, setDescDraft] = useState(node.description ?? "")

  const hasChildren = node.children && node.children.length > 0
  const hasControls = node.controls && node.controls.length > 0
  const isSelected = selectedCode === node.code
  const selectable = !!selectedItems
  const isItemSelected = selectedItems ? selectedItems.has(node.code) : true

  const nodeProposals = proposals?.filter(
    p => p.entity_code === node.code && p.entity_type === "requirement"
  ) || []
  const hasPendingProposal = nodeProposals.some(p => p.accepted === undefined)
  const newControlProposals = proposals?.filter(
    p => p.entity_code?.startsWith(node.code) && p.change_type === "add_control"
  ) || []

  const depthIndent = node.depth * 20

  return (
    <div className="select-none">
      <div
        className={cn(
          "group flex items-center gap-3 px-3 py-2 rounded-xl cursor-pointer transition-all duration-200",
          isSelected
            ? "bg-primary/[0.08] shadow-[0_0_20px_rgba(var(--primary),0.05)] ring-1 ring-primary/20"
            : "hover:bg-muted/40",
          isNew && "ring-1 ring-emerald-400/30 bg-emerald-500/[0.03]",
          node.depth === 0 && "py-3",
          selectable && !isItemSelected && "opacity-50",
        )}
        style={{ marginLeft: `${depthIndent}px` }}
        onClick={() => {
          onSelectNode(node.code)
          if (hasChildren || hasControls) setExpanded(v => !v)
        }}
      >
        {selectable && (
          <input
            type="checkbox"
            checked={isItemSelected}
            onChange={() => onToggleItem?.(node.code)}
            onClick={e => e.stopPropagation()}
            className="h-3.5 w-3.5 rounded accent-primary shrink-0 cursor-pointer"
          />
        )}

        <div className="shrink-0 flex items-center justify-center w-5 h-5 rounded-md hover:bg-muted/80 transition-colors">
          {hasChildren || hasControls ? (
            expanded
              ? <ChevronDown className="h-4 w-4 text-muted-foreground/70" />
              : <ChevronRight className="h-4 w-4 text-muted-foreground/70" />
          ) : (
            <div className="w-4 h-4 rounded-full border border-muted-foreground/10 shrink-0" />
          )}
        </div>

        <div
          className={cn(
            "shrink-0 h-6 px-2 rounded-lg border flex items-center justify-center cursor-default",
            node.depth === 0
              ? "bg-primary text-primary-foreground border-primary shadow-[0_2px_8px_rgba(var(--primary),0.3)]"
              : "bg-muted/80 border-border/50 text-muted-foreground font-mono text-[10px]",
          )}
        >
          <span className={cn("text-[10px] font-bold uppercase tracking-tight", node.depth === 0 ? "text-[11px]" : "")}>
            {node.code}
          </span>
        </div>

        <div className="flex-1 flex items-center min-w-0">
          <span className={cn(
            "text-[13px] leading-tight truncate font-bold tracking-tight",
            node.depth === 0 ? "text-sm text-foreground" : "text-foreground/80",
            isSelected && "text-primary",
          )}>
            {node.name}
          </span>
        </div>

        <div className="shrink-0 flex items-center gap-2 pr-1">
          {isNew && (
            <span className="text-[9px] font-black tracking-[0.1em] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">NEW</span>
          )}
          {hasPendingProposal && <Sparkles className="h-3.5 w-3.5 text-amber-500 animate-pulse" />}
          {(hasControls || hasChildren) && (
            <div className="flex items-center gap-1 text-[10px] font-bold text-muted-foreground/40 bg-muted/30 px-2 py-0.5 rounded-full">
              {hasChildren && <span>{node.children!.length} Req</span>}
              {hasChildren && hasControls && <span className="w-px h-2 bg-muted-foreground/20" />}
              {hasControls && <span>{node.controls!.length} Ctrl</span>}
            </div>
          )}
          {expanded && onEditNode && (
            <button
              onClick={e => { e.stopPropagation(); setEditingDesc(true) }}
              className="opacity-0 group-hover:opacity-60 hover:!opacity-100 h-6 w-6 flex items-center justify-center rounded-md hover:bg-muted transition-all text-muted-foreground"
              title="Edit description"
            >
              <Pencil className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {editingDesc && (
        <div
          className="mx-3 mb-2 rounded-xl border border-primary/20 bg-card/60 p-3 space-y-2"
          style={{ marginLeft: `${depthIndent + 12}px` }}
          onClick={e => e.stopPropagation()}
        >
          <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/50">Description</p>
          <textarea
            autoFocus
            value={descDraft}
            onChange={e => setDescDraft(e.target.value)}
            className="w-full min-h-[72px] rounded-lg border border-border/40 bg-background/60 px-3 py-2 text-[13px] text-foreground resize-y focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
          <div className="flex gap-2 justify-end">
            <button onClick={() => setEditingDesc(false)} className="text-[11px] px-3 py-1 rounded-lg text-muted-foreground hover:bg-muted transition-colors">Cancel</button>
            <button
              onClick={() => {
                onEditNode?.(node.code, "description", descDraft)
                setEditingDesc(false)
              }}
              className="text-[11px] px-3 py-1 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors font-bold"
            >Save</button>
          </div>
        </div>
      )}

      {expanded && (hasChildren || hasControls) && (
        <div className="relative ml-[10px] pl-[18px] border-l border-border/40 mt-0.5 space-y-0.5">
          {hasChildren && node.children!.map(child => (
            <TreeNode
              key={child.code}
              node={child}
              mode={mode}
              selectedCode={selectedCode}
              onSelectNode={onSelectNode}
              selectedControlCode={selectedControlCode}
              onSelectControl={onSelectControl}
              proposals={proposals}
              onAcceptChange={onAcceptChange}
              onRejectChange={onRejectChange}
              onEditNode={onEditNode}
              onEditControl={onEditControl}
              isNew={child.is_new}
              selectedItems={selectedItems}
              onToggleItem={onToggleItem}
            />
          ))}
          {hasControls && (
            <div className="py-1 space-y-0.5">
              <div className="flex items-center gap-2 mb-1.5 px-1">
                <div className="h-px bg-border/40 flex-1" />
                <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/30">Controls</span>
                <div className="h-px bg-border/40 flex-1" />
              </div>
              {node.controls!.map(ctrl => (
                <ControlChip
                  key={ctrl.code}
                  control={ctrl}
                  onSelectControl={onSelectControl}
                  isSelected={selectedControlCode === ctrl.code}
                  selectable={selectable}
                  selected={selectedItems?.has(ctrl.code)}
                  onToggle={onToggleItem}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {expanded && mode === "enhance" && newControlProposals.length > 0 && (
        <div className="ml-4 mt-0.5 space-y-1">
          {newControlProposals.map((p, i) => (
            <ProposalRow key={i} proposal={p} onAccept={onAcceptChange} onReject={onRejectChange} />
          ))}
        </div>
      )}

      {mode === "enhance" && nodeProposals.length > 0 && expanded && (
        <div className="ml-4 mt-1 space-y-1">
          {nodeProposals.map((p, i) => (
            <ProposalRow key={i} proposal={p} onAccept={onAcceptChange} onReject={onRejectChange} />
          ))}
        </div>
      )}
    </div>
  )
}

// ── Proposal Row ──────────────────────────────────────────────────────────────

function ProposalRow({
  proposal,
  onAccept,
  onReject,
}: {
  proposal: ChangeProposal
  onAccept?: (p: ChangeProposal) => void
  onReject?: (p: ChangeProposal) => void
}) {
  const accepted = proposal.accepted === true
  const rejected = proposal.accepted === false
  return (
    <div className={cn(
      "rounded-xl border text-xs p-3 transition-all",
      accepted && "bg-emerald-500/5 border-emerald-500/20 opacity-70",
      rejected && "bg-red-500/5 border-red-500/20 opacity-50 line-through",
      !accepted && !rejected && "bg-amber-500/5 border-amber-500/20",
    )}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0 space-y-1">
          <span className="font-black uppercase tracking-widest text-[9px] text-muted-foreground/60">{proposal.field}</span>
          <div className="text-[13px] flex flex-col gap-1">
            {proposal.current_value !== undefined && proposal.current_value !== "" && (
              <span className="line-through text-red-500/50">{String(proposal.current_value)}</span>
            )}
            <span className="text-foreground font-medium">
              {typeof proposal.proposed_value === "string" ? proposal.proposed_value : JSON.stringify(proposal.proposed_value)}
            </span>
          </div>
        </div>
        {!accepted && !rejected && (
          <div className="shrink-0 flex gap-1">
            <button onClick={e => { e.stopPropagation(); onAccept?.(proposal) }} className="h-7 w-7 flex items-center justify-center rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-lg shadow-emerald-600/20">✓</button>
            <button onClick={e => { e.stopPropagation(); onReject?.(proposal) }} className="h-7 w-7 flex items-center justify-center rounded-lg bg-muted text-muted-foreground hover:bg-red-500/10 hover:text-red-700 transition-colors">✕</button>
          </div>
        )}
        {accepted && <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />}
      </div>
    </div>
  )
}

// ── Tree Root ─────────────────────────────────────────────────────────────────

export function FrameworkHierarchyTree({
  nodes,
  mode,
  selectedCode,
  onSelectNode,
  selectedControlCode,
  onSelectControl,
  proposals,
  onAcceptChange,
  onRejectChange,
  isStreaming,
  onEditNode,
  onEditControl,
  selectedItems,
  onToggleItem,
}: Props) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isStreaming) endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [nodes.length, isStreaming])

  if (nodes.length === 0 && !isStreaming) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground py-16">
        <AlertCircle className="h-8 w-8 opacity-30" />
        <p className="text-sm">No hierarchy proposed yet.</p>
        <p className="text-xs opacity-60">Upload documents and click "Propose Structure".</p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {nodes.map(node => (
        <TreeNode
          key={node.code}
          node={node}
          mode={mode}
          selectedCode={selectedCode}
          onSelectNode={onSelectNode}
          selectedControlCode={selectedControlCode}
          onSelectControl={onSelectControl}
          proposals={proposals}
          onAcceptChange={onAcceptChange}
          onRejectChange={onRejectChange}
          onEditNode={onEditNode}
          onEditControl={onEditControl}
          isNew={node.is_new}
          selectedItems={selectedItems}
          onToggleItem={onToggleItem}
        />
      ))}
      {isStreaming && (
        <div className="flex items-center gap-3 px-4 py-3 text-xs text-muted-foreground animate-pulse bg-primary/5 rounded-xl border border-primary/10">
          <div className="flex gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
            <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
            <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" />
          </div>
          Generating architecture…
        </div>
      )}
      <div ref={endRef} />
    </div>
  )
}
