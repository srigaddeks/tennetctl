"use client"

import * as React from "react"
import { Search } from "lucide-react"
import { Input, Badge } from "@kcontrol/ui"
import type { EngagementControl } from "@/lib/api/engagements"

interface SearchableControlSelectorProps {
  controls: EngagementControl[]
  value: string
  onChange: (value: string) => void
  label?: string
}

export function SearchableControlSelector({ 
  controls, 
  value, 
  onChange, 
  label 
}: SearchableControlSelectorProps) {
  const [search, setSearch] = React.useState("")
  
  const filteredControls = React.useMemo(() => {
    if (!search) return controls
    const q = search.toLowerCase()
    return controls.filter(c => 
      c.control_code.toLowerCase().includes(q) || 
      c.name.toLowerCase().includes(q) ||
      (c.category_name || "").toLowerCase().includes(q)
    )
  }, [controls, search])

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between px-1">
        {label && (
          <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
            {label}
          </label>
        )}
        <span className="text-[9px] font-bold text-muted-foreground/60 uppercase">
          {filteredControls.length} Controls
        </span>
      </div>
      
      <div className="relative group">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground transition-colors group-focus-within:text-primary" />
        <Input
          placeholder="Filter by code, name, or category..."
          className="pl-10 h-11 text-sm rounded-2xl border-border/60 bg-background/50 focus:bg-background transition-all"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="border border-border/60 rounded-2xl overflow-hidden bg-muted/10 backdrop-blur-sm">
        <div className="max-h-56 overflow-y-auto divide-y divide-border/40 scrollbar-thin scrollbar-thumb-muted-foreground/20">
          <div 
            className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-all ${!value ? 'bg-primary/10 border-l-4 border-primary' : 'hover:bg-muted/40 border-l-4 border-transparent'}`}
            onClick={() => onChange("")}
          >
            <div className={`h-2 w-2 rounded-full ${!value ? 'bg-primary shadow-[0_0_8px_rgba(var(--primary),0.5)]' : 'bg-muted-foreground/30'}`} />
            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">General (Engagement Level)</span>
          </div>
          
          {filteredControls.map((control) => (
            <div 
              key={control.id}
              className={`flex flex-col gap-1 px-4 py-3 cursor-pointer transition-all ${value === control.id ? 'bg-primary/10 border-l-4 border-primary' : 'hover:bg-muted/40 border-l-4 border-transparent'}`}
              onClick={() => onChange(control.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`h-2 w-2 rounded-full ${value === control.id ? 'bg-primary shadow-[0_0_8px_rgba(var(--primary),0.5)]' : 'bg-muted-foreground/30'}`} />
                  <span className="text-[11px] font-black font-mono text-primary tracking-tighter">
                    {control.control_code}
                  </span>
                </div>
                {control.category_name && (
                  <Badge variant="outline" className="text-[9px] h-4 px-2 font-bold uppercase tracking-tighter opacity-70 bg-background/50">
                    {control.category_name}
                  </Badge>
                )}
              </div>
              <span className={`text-[11px] font-bold truncate pl-5 ${value === control.id ? 'text-foreground' : 'text-muted-foreground'}`}>
                {control.name}
              </span>
            </div>
          ))}
          
          {filteredControls.length === 0 && (
            <div className="py-10 text-center space-y-2">
              <Search className="h-6 w-6 text-muted-foreground/20 mx-auto" />
              <p className="text-[10px] font-medium text-muted-foreground italic uppercase tracking-widest">
                No matching controls
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
