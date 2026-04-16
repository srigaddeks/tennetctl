"use client"

import { useMemo } from "react"
import { Card, CardContent } from "@kcontrol/ui"
import { ShieldAlert, TrendingUp, ArrowRight } from "lucide-react"
import type { HeatMapResponse, RiskResponse } from "@/lib/types/grc"
import { Skeleton } from "@kcontrol/ui"

interface RiskHeatmapProps {
  data: HeatMapResponse | null
  risks: RiskResponse[]
  loading?: boolean
}

export function RiskHeatmap({ data, risks, loading }: RiskHeatmapProps) {
  // Map risk level codes to 1-5 scores for unassessed fallback
  const LEVEL_MAP: Record<string, number> = {
    critical: 5,
    high: 4,
    medium: 3,
    low: 2,
    very_low: 1,
  }

  // 5x5 Grid: Likelihood (Y) vs Impact (X)
  const grid = useMemo(() => {
    const matrix = Array(5).fill(null).map(() => Array(5).fill({ count: 0, ids: [] }))
    
    // 1. Fill with assessed data from API
    const assessedIds = new Set<string>()
    if (data?.cells) {
      data.cells.forEach(cell => {
        const l = Math.max(1, Math.min(5, cell.likelihood_score))
        const i = Math.max(1, Math.min(5, cell.impact_score))
        matrix[5 - l][i - 1] = { count: cell.risk_count, ids: cell.risk_ids }
        cell.risk_ids.forEach(id => assessedIds.add(id))
      })
    }

    // 2. Fill with unassessed risks using their level as fallback (placed on diagonal)
    risks.forEach(risk => {
      if (assessedIds.has(risk.id)) return
      const levelCode = risk.risk_level_code?.toLowerCase() || "medium"
      const score = LEVEL_MAP[levelCode] || 3
      // We place unassessed risks on the diagonal (Likelihood = Impact = Score)
      const current = matrix[5 - score][score - 1]
      matrix[5 - score][score - 1] = {
        count: current.count + 1,
        ids: [...current.ids, risk.id]
      }
    })

    return matrix
  }, [data, risks])

  const getCellColor = (l: number, i: number, count: number) => {
    if (count === 0) return "bg-muted/5 border-border/10 opacity-30"
    const score = l * i
    if (score >= 20) return "bg-red-500 text-white border-red-600 shadow-md shadow-red-500/20"
    if (score >= 12) return "bg-orange-500 text-white border-orange-600 shadow-md shadow-orange-500/20"
    if (score >= 8) return "bg-amber-400 text-black border-amber-500 shadow-sm shadow-amber-500/10"
    if (score >= 4) return "bg-yellow-200 text-black border-yellow-300 shadow-sm shadow-yellow-500/10"
    return "bg-emerald-400 text-white border-emerald-500 shadow-sm shadow-emerald-500/10"
  }

  // "List down" Top Risks (Highest Score first)
  const topRisks = useMemo(() => {
    return [...risks]
      .map(r => ({
        ...r,
        // Heuristic score if real one is null
        effective_score: r.inherent_risk_score ?? (LEVEL_MAP[r.risk_level_code?.toLowerCase() || ""] ? (LEVEL_MAP[r.risk_level_code!.toLowerCase()] ** 2) : 0)
      }))
      .sort((a, b) => b.effective_score - a.effective_score)
      .slice(0, 5)
  }, [risks])

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-700">
      <Card className="rounded-2xl overflow-hidden border-border bg-card/50 backdrop-blur-md shadow-xl border-t-primary/20">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-8">
            <div className="space-y-1">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-primary" />
                Risk Heatmap
              </h3>
              <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-tighter opacity-70">
                Visualizing {risks.length} Active Risks
              </p>
            </div>
          </div>

          <div className="relative mt-2 mb-8 mx-auto max-w-[220px]">
            {/* Y Axis Label (Likelihood) */}
            <div className="absolute -left-12 top-1/2 -rotate-90 origin-center text-[9px] font-black tracking-[0.2em] text-muted-foreground/40 whitespace-nowrap">
              LIKELIHOOD
            </div>

            {/* X Axis Label (Impact) */}
            <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 text-[9px] font-black tracking-[0.2em] text-muted-foreground/40 whitespace-nowrap">
              IMPACT
            </div>

            <div className="grid grid-cols-5 gap-1 aspect-square bg-muted/10 p-1 rounded-lg border border-border/20">
              {grid.map((row, lIdx) => 
                row.map((cell, iIdx) => {
                  const likelihood = 5 - lIdx
                  const impact = iIdx + 1
                  return (
                    <div
                      key={`${likelihood}-${impact}`}
                      className={`relative flex items-center justify-center rounded-sm border text-[10px] font-black transition-all duration-500
                        ${getCellColor(likelihood, impact, cell.count)}
                        ${cell.count > 0 ? "scale-100 hover:scale-110 cursor-help ring-2 ring-white/10" : "scale-95"}
                      `}
                      title={`L: ${likelihood}, I: ${impact} - ${cell.count} Risks`}
                    >
                      {cell.count > 0 ? cell.count : ""}
                    </div>
                  )
                })
              )}
            </div>
            
            {/* Axis Ticks */}
            <div className="flex justify-between mt-2 px-1 text-[9px] text-muted-foreground font-bold opacity-40">
              <span>1</span><span>2</span><span>3</span><span>4</span><span>5</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* "List down" section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <h4 className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] flex items-center gap-2 opacity-80">
            <ShieldAlert className="w-3.5 h-3.5 text-primary" />
            Top Exposure
          </h4>
          <span className="text-[10px] font-bold text-muted-foreground/40">Sorted by Rank</span>
        </div>
        
        <div className="space-y-4">
          {loading ? (
            [1, 2, 3].map(i => (
              <div key={i} className="p-4 rounded-2xl border border-border bg-card/30 space-y-3">
                <div className="flex justify-between">
                  <Skeleton className="h-4 w-12" />
                  <Skeleton className="h-4 w-8" />
                </div>
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            ))
          ) : topRisks.length === 0 ? (
            <div className="p-8 rounded-2xl border border-dashed border-border bg-muted/20 text-center">
              <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">No active exposure tracked</p>
            </div>
          ) : (
            topRisks.map(risk => (
              <div key={risk.id} className="p-4 rounded-2xl border border-border bg-card/30 hover:bg-card hover:shadow-lg hover:border-primary/20 transition-all duration-300 group cursor-pointer relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 rounded-full -mr-12 -mt-12 group-hover:bg-primary/10 transition-colors" />
                
                <div className="flex items-center justify-between mb-2 relative z-10">
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-bold text-primary/70 bg-primary/10 px-2 py-0.5 rounded-full leading-none border border-primary/20">
                      {risk.risk_code}
                    </span>
                    <span className={`text-[8px] font-black uppercase tracking-wider ${
                      risk.risk_level_code?.toLowerCase() === "critical" ? "text-red-500" :
                      risk.risk_level_code?.toLowerCase() === "high" ? "text-orange-500" :
                      "text-muted-foreground/60"
                    }`}>
                      {risk.risk_level_name || risk.risk_level_code}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 bg-muted/50 px-2 py-0.5 rounded-full border border-border/50">
                    <span className="text-[10px] font-black tabular-nums" style={{ color: risk.risk_level_color || undefined }}>
                      {risk.inherent_risk_score || "-"}
                    </span>
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: risk.risk_level_color || undefined }} />
                  </div>
                </div>
                
                <h5 className="text-xs font-bold text-foreground leading-snug group-hover:text-primary transition-colors line-clamp-2 relative z-10 mb-2">
                  {risk.title}
                </h5>
                
                <div className="flex items-center gap-2 relative z-10">
                  {risk.category_name && (
                    <span className="text-[9px] font-bold text-muted-foreground uppercase opacity-50 tracking-wider bg-muted px-1.5 py-0.5 rounded">
                      {risk.category_name}
                    </span>
                  )}
                  <div className="h-1 w-1 rounded-full bg-border" />
                  <span className="text-[9px] font-medium text-muted-foreground capitalize">{risk.risk_status}</span>
                </div>
              </div>
            ))
          )}
        </div>
        
        <a href="/dashboard" className="block p-4 rounded-2xl border border-dashed border-border bg-muted/10 group cursor-pointer hover:bg-primary/5 transition-all">
          <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest text-center group-hover:text-primary transition-colors flex items-center justify-center gap-2">
            View Analytics Dashboard
            <ArrowRight className="w-3 h-3" />
          </p>
        </a>
      </div>
    </div>
  )
}
