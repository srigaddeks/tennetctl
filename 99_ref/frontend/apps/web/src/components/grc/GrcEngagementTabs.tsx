"use client"

import * as React from "react"
import { 
  FileText,
  ShieldCheck,
  AlertCircle,
  BarChart3,
  Users,
  MessageSquare,
  Inbox,
  ClipboardList,
  Loader2
} from "lucide-react"

import { Badge } from "@kcontrol/ui"

interface TabCounts {
  requests: number
  findings: number
  tasks: number
  messages: number
}

interface GrcEngagementTabsProps {
  activeTab: string
  onTabChange: (tab: string) => void
  tabCounts: TabCounts
  isLoading?: boolean
}

export function GrcEngagementTabs({ 
  activeTab, 
  onTabChange, 
  tabCounts,
  isLoading = false,
}: GrcEngagementTabsProps) {
  const tabs = [
    {
      id: "overview",
      label: "Overview",
      icon: FileText,
      count: 0,
      countColor: ""
    },
    {
      id: "controls",
      label: "Controls & Evidence",
      icon: ShieldCheck,
      count: 0,
      countColor: ""
    },
    {
      id: "requests",
      label: "Auditor Requests",
      icon: Inbox,
      count: tabCounts.requests,
      countColor: "bg-amber-500/20 text-amber-500"
    },
    {
      id: "findings",
      label: "Findings",
      icon: AlertCircle,
      count: tabCounts.findings,
      countColor: "bg-red-500/20 text-red-500"
    },
    {
      id: "tasks",
      label: "Tasks",
      icon: ClipboardList,
      count: tabCounts.tasks,
      countColor: "bg-indigo-500/20 text-indigo-500"
    },
    {
      id: "reports",
      label: "Reports",
      icon: BarChart3,
      count: 0,
      countColor: ""
    },
    {
      id: "team",
      label: "Team",
      icon: Users,
      count: 0,
      countColor: ""
    },
    {
      id: "messages",
      label: "Messages",
      icon: MessageSquare,
      count: tabCounts.messages,
      countColor: "bg-indigo-500/20 text-indigo-500"
    }
  ]

  return (
    <div className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-40">
      <div className="flex items-center gap-1 px-4 overflow-x-auto scrollbar-none">
        {isLoading ? (
          <div className="flex items-center justify-center py-4 w-full">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : (
          tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-4 text-[10px] font-black uppercase tracking-widest whitespace-nowrap border-b-2 transition-all group
                  ${isActive 
                    ? 'border-indigo-500 text-indigo-500' 
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
                  }
                `}
              >
                <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-indigo-500' : 'text-muted-foreground group-hover:text-foreground'}`} />
                <span>{tab.label}</span>
                {tab.count > 0 && (
                  <Badge 
                    variant="secondary" 
                    className={`${tab.countColor} text-[8px] font-black h-4 px-1 rounded-sm ml-1 border-none`}
                  >
                    {tab.count}
                  </Badge>
                )}
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}
