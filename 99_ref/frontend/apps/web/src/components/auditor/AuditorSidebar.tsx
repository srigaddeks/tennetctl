"use client"

import * as React from "react"
import { 
  LayoutDashboard,
  FileCheck,
  ShieldCheck,
  AlertCircle,
  FileText,
  Settings,
  BarChart3,
  Loader2
} from "lucide-react"

import { Badge } from "@kcontrol/ui"

interface BadgeCounts {
  auditWorkspace: number
  frameworks: number
  controls: number
  findings: number
  evidenceTasks: number
}

interface AuditorSidebarProps {
  activeView: string
  onViewChange: (view: string) => void
  badgeCounts: BadgeCounts
  isLoading?: boolean
}

export function AuditorSidebar({ 
  activeView, 
  onViewChange, 
  badgeCounts,
  isLoading = false 
}: AuditorSidebarProps) {
  const navItems = [
    {
      section: "Audit",
      items: [
        {
          id: "workspace",
          label: "Audit Workspace",
          icon: LayoutDashboard,
          badge: badgeCounts.auditWorkspace,
          badgeColor: "bg-red-500/20 text-red-400"
        }
      ]
    },
    {
      section: "Compliance",
      items: [
        {
          id: "frameworks",
          label: "Frameworks",
          icon: FileCheck,
          badge: badgeCounts.frameworks,
          badgeColor: "bg-blue-500/20 text-blue-400"
        },
        {
          id: "controls",
          label: "Controls",
          icon: ShieldCheck,
          badge: badgeCounts.controls,
          badgeColor: "bg-red-500/20 text-red-400"
        },
        {
          id: "findings",
          label: "Findings",
          icon: AlertCircle,
          badge: badgeCounts.findings,
          badgeColor: "bg-amber-500/20 text-amber-400"
        },
        {
          id: "evidence-tasks",
          label: "Evidence Tasks",
          icon: FileText,
          badge: badgeCounts.evidenceTasks,
          badgeColor: "bg-red-500/20 text-red-400"
        }
      ]
    },
    {
      section: "Admin",
      items: [
        {
          id: "reports",
          label: "Reports",
          icon: BarChart3,
          badge: 0,
          badgeColor: ""
        },
        {
          id: "settings",
          label: "Settings",
          icon: Settings,
          badge: 0,
          badgeColor: ""
        }
      ]
    }
  ]

  return (
    <div className="w-64 bg-card border-r border-border flex flex-col h-full">
      {/* Logo */}
      <div className="p-4 border-b border-border">
        <div className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-1">
          Kreesalis
        </div>
        <div className="text-lg font-black text-foreground">
          K-<span className="text-primary">Control</span>
        </div>
        <div className="mt-2 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 text-xs font-semibold">
          🔍 Auditor Portal
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          navItems.map((section) => (
            <div key={section.section} className="mb-4">
              <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {section.section}
              </div>
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon
                  const isActive = activeView === item.id
                  
                  return (
                    <button
                      key={item.id}
                      onClick={() => onViewChange(item.id)}
                      className={`
                        w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all
                        ${isActive 
                          ? 'bg-primary/10 text-primary border-l-2 border-primary' 
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                        }
                      `}
                    >
                      <Icon className="h-4 w-4 flex-shrink-0" />
                      <span className="flex-1 text-left">{item.label}</span>
                      {item.badge > 0 && (
                        <Badge 
                          variant="secondary" 
                          className={`${item.badgeColor} text-xs font-bold`}
                        >
                          {item.badge}
                        </Badge>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          ))
        )}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted-foreground text-center">
          Auditor Portal v1.0
        </div>
      </div>
    </div>
  )
}
