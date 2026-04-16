"use client"

import React, { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, Button, Badge, Input } from "@kcontrol/ui"
import {
  ChevronLeft, Layers, ShieldCheck, ChevronDown, ChevronRight,
  BookOpen, Search, Loader2,
  AlertTriangle, FlaskConical, LayoutList
} from "lucide-react"
import {
  getFramework, listRequirements, listControls
} from "@/lib/api/grc"
import type {
  FrameworkResponse, RequirementResponse, ControlResponse
} from "@/lib/types/grc"

function categoryBadgeClass(category: string): string {
  switch (category?.toLowerCase()) {
    case "security": return "bg-blue-500/10 text-blue-600 border-blue-500/20"
    case "privacy": return "bg-purple-500/10 text-purple-600 border-purple-500/20"
    case "compliance": return "bg-green-500/10 text-green-600 border-green-500/20"
    case "risk": return "bg-amber-500/10 text-amber-600 border-amber-500/20"
    default: return "bg-muted text-muted-foreground border-border"
  }
}

const CRITICALITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/10 text-red-700 border-red-500/20",
  high:     "bg-orange-500/10 text-orange-700 border-orange-500/20",
  medium:   "bg-yellow-500/10 text-yellow-700 border-yellow-500/20",
  low:      "bg-green-500/10 text-green-700 border-green-500/20",
}

const CONTROL_TYPE_COLORS: Record<string, string> = {
  preventive:    "bg-blue-500/10 text-blue-500 border-blue-500/20",
  detective:     "bg-purple-500/10 text-purple-500 border-purple-500/20",
  corrective:    "bg-amber-500/10 text-amber-600 border-amber-500/20",
  compensating:  "bg-teal-500/10 text-teal-500 border-teal-500/20",
}

function StatPill({ icon, value, label }: { icon: React.ReactNode; value: number | string; label: string }) {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-muted/50 border border-border">
      {icon}
      <span className="text-sm font-bold tabular-nums">{value}</span>
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</span>
    </div>
  )
}

export default function FrameworkLibraryDetailPage() {
  const params = useParams()
  const router = useRouter()
  const frameworkId = params.frameworkId as string

  const [framework, setFramework] = useState<FrameworkResponse | null>(null)
  const [requirements, setRequirements] = useState<RequirementResponse[]>([])
  const [controls, setControls] = useState<ControlResponse[]>([])
  
  const [mainTab, setMainTab] = useState<"controls" | "requirements">("controls")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")

  const [expandedReqs, setExpandedReqs] = useState<Set<string>>(new Set())

  const toggleReq = (id: string) => {
    setExpandedReqs(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const fw = await getFramework(frameworkId)
      // listRequirements doesn't take limit/offset, fetch all directly
      const reqsRes = await listRequirements(frameworkId)
      
      let allCtrls: ControlResponse[] = []
      let ctrlOffset = 0
      while (true) {
        const res = await listControls(frameworkId, { limit: 500, offset: ctrlOffset })
        const items = res.items ?? []
        allCtrls = [...allCtrls, ...items]
        if (items.length < 500) break
        ctrlOffset += 500
      }

      setFramework(fw)
      // @ts-ignore
      const allReqValues = (reqsRes.items ?? reqsRes ?? []) as RequirementResponse[]
      setRequirements(allReqValues)
      setControls(allCtrls)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load framework details")
    } finally {
      setLoading(false)
    }
  }, [frameworkId])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Auto-expand on search
  useEffect(() => {
    if (search.trim()) {
      const searchLower = search.toLowerCase()
      const matchSet = new Set<string>()
      for (const c of controls) {
        const matches = searchLower && !(
          c.name?.toLowerCase().includes(searchLower) ||
          c.control_code.toLowerCase().includes(searchLower) ||
          c.description?.toLowerCase().includes(searchLower)
        ) ? false : true

        if (matches && c.requirement_id) {
          matchSet.add(c.requirement_id)
        }
      }
      setExpandedReqs(matchSet)
    }
  }, [search, controls])

  if (loading) {
    return (
      <div className="space-y-4 p-6">
        <div className="h-5 w-28 rounded bg-muted animate-pulse" />
        <div className="h-8 w-72 rounded bg-muted animate-pulse" />
        <div className="h-14 rounded-xl bg-muted animate-pulse" />
        <div className="space-y-1 mt-6">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />)}
        </div>
      </div>
    )
  }

  if (error || !framework) {
    return (
      <div className="space-y-4 p-6">
        <Button variant="ghost" size="sm" onClick={() => router.back()} className="gap-2">
          <ChevronLeft className="h-4 w-4" /> Back to Library
        </Button>
        <Card className="rounded-xl">
          <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <p className="text-sm font-medium">{error || "Framework not found"}</p>
            <Button size="sm" onClick={loadData}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const searchLower = search.toLowerCase()
  const filteredControls = controls.filter((c) => {
    if (searchLower && !(
      c.name?.toLowerCase().includes(searchLower) ||
      c.control_code.toLowerCase().includes(searchLower) ||
      c.description?.toLowerCase().includes(searchLower)
    )) return false
    return true
  })

  // Group controls by requirement
  const sortedReqs = [...requirements].sort((a, b) => a.sort_order - b.sort_order)
  const reqMap = new Map<string, RequirementResponse>(sortedReqs.map((r) => [r.id, r]))

  const grouped = new Map<string | null, ControlResponse[]>()
  for (const ctrl of filteredControls) {
    const key = ctrl.requirement_id ?? null
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(ctrl)
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <Button
            variant="ghost" size="sm"
            onClick={() => router.back()}
            className="gap-1.5 -ml-2 h-7 text-xs text-muted-foreground"
          >
            <ChevronLeft className="h-3.5 w-3.5" /> Framework Library
          </Button>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold tracking-tight font-secondary">{framework.name}</h1>
          </div>
          <p className="text-xs text-muted-foreground">
            {framework.category_name ? `${framework.category_name}` : ""}
            {framework.publisher_name ? ` · ${framework.publisher_name}` : ""}
          </p>
          {framework.description && (
            <p className="text-xs text-muted-foreground max-w-2xl mt-0.5">{framework.description}</p>
          )}
        </div>
        {framework.latest_version_code && (
          <Badge variant="outline" className="text-xs font-medium shrink-0 mt-8">
            version: {framework.latest_version_code}
          </Badge>
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-2 flex-wrap">
        <StatPill icon={<Layers className="w-3 h-3 text-blue-500" />} value={controls.length} label="Controls" />
        <StatPill icon={<BookOpen className="w-3 h-3 text-purple-500" />} value={requirements.length} label="Requirements" />
      </div>

      <div className="border-t border-border mt-4 mb-2"></div>

      <div className="flex flex-col gap-4 mb-4 mt-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 bg-muted/30 p-1 rounded-lg border border-border">
            <button
              onClick={() => setMainTab("controls")}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                mainTab === "controls"
                  ? "bg-background shadow-sm text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All Controls
            </button>
            <button
              onClick={() => setMainTab("requirements")}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                mainTab === "requirements"
                  ? "bg-background shadow-sm text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Requirements
            </button>
          </div>
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search controls..."
              className="pl-9 h-9 text-sm"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Display */}
      <div className="space-y-6">
        {filteredControls.length === 0 ? (
          <div className="py-12 text-center border rounded-xl bg-muted/20 border-dashed">
            <p className="text-muted-foreground">No controls match your search.</p>
          </div>
        ) : mainTab === "controls" ? (
          <div className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
            <div className="bg-muted/30 px-4 py-3 border-b border-border/60">
              <h4 className="text-sm font-semibold text-foreground">Controls ({filteredControls.length})</h4>
            </div>
            <div className="divide-y divide-border/40">
              {filteredControls.map(ctrl => (
                <ControlRow key={ctrl.id} control={ctrl} />
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Map grouped requirements */}
            {sortedReqs.filter(r => grouped.has(r.id)).map(req => {
              const reqControls = grouped.get(req.id) || []
              const isExpanded = expandedReqs.has(req.id)
              return (
                <div key={req.id} className="rounded-xl border border-border bg-card overflow-hidden shadow-sm transition-all duration-200">
                  <div 
                    onClick={() => toggleReq(req.id)}
                    className="bg-muted/30 px-4 py-3 border-b border-border/60 cursor-pointer hover:bg-muted/50 transition-colors flex items-center justify-between"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-purple-500/10 mt-0.5">
                        <BookOpen className="h-3.5 w-3.5 text-purple-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-foreground">
                            {req.requirement_code}: {req.name || "Unnamed"}
                          </span>
                          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">
                            {reqControls.length} controls
                          </span>
                        </div>
                        {req.description && (
                          <p className={`text-xs text-muted-foreground mt-0.5 ${isExpanded ? "" : "line-clamp-1"}`}>{req.description}</p>
                        )}
                      </div>
                    </div>
                    <div className="text-muted-foreground ml-4">
                      {isExpanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                    </div>
                  </div>
                  {isExpanded && (
                    <div className="divide-y divide-border/40 animate-in slide-in-from-top-2 duration-200">
                      {reqControls.map(ctrl => (
                        <ControlRow key={ctrl.id} control={ctrl} />
                      ))}
                    </div>
                  )}
                </div>
              )
            })}

            {/* Ungrouped Controls */}
            {grouped.has(null) && (
              <div className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
                <div className="bg-muted/30 px-4 py-3 border-b border-border/60">
                  <div className="flex items-start gap-3">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground mt-0.5">
                      <LayoutList className="h-3.5 w-3.5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-foreground">Ungrouped Controls</h4>
                      <p className="text-xs text-muted-foreground mt-0.5">Controls not mapped to any requirement group</p>
                    </div>
                  </div>
                </div>
                <div className="divide-y divide-border/40">
                  {grouped.get(null)!.map(ctrl => (
                    <ControlRow key={ctrl.id} control={ctrl} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function ControlRow({ control }: { control: ControlResponse }) {
  return (
    <div className="px-4 py-3 hover:bg-muted/10 transition-colors">
      <div className="flex gap-4">
        <div className="w-20 shrink-0">
          <span className="text-[11px] font-mono text-primary bg-primary/5 px-1.5 py-0.5 rounded border border-primary/20">
            {control.control_code}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-foreground leading-snug">{control.name}</p>
              {control.description && (
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2 md:line-clamp-none">
                  {control.description}
                </p>
              )}
            </div>
            <div className="flex items-center gap-1.5 shrink-0 flex-wrap justify-end max-w-[150px]">
              {control.control_type && (
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide border ${CONTROL_TYPE_COLORS[control.control_type] ?? "bg-muted text-muted-foreground"}`}>
                  {control.control_type}
                </span>
              )}
              {control.criticality_code && (
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide border ${CRITICALITY_COLORS[control.criticality_code] ?? "bg-muted text-muted-foreground"}`}>
                  {control.criticality_code}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
