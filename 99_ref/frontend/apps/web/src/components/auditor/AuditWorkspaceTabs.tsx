"use client"

import * as React from "react"
import { 
  Building2,
  AlertCircle,
  FileText,
  MessageSquare,
  FolderOpen,
  CheckSquare,
  UserCheck,
  Loader2
} from "lucide-react"

import { Badge } from "@kcontrol/ui"

interface TabCounts {
  engagements: number
  findings: number
  evidenceRequests: number
  messages: number
  evidenceLibrary: number
  evidenceTasks: number
  myAccess: number
}

interface AuditWorkspaceTabsProps {
  activeTab: string
  onTabChange: (tab: string) => void
  tabCounts: TabCounts
  visibleTabs?: string[]
  isLoading?: boolean
  isEngagementContext?: boolean
}

export function AuditWorkspaceTabs({ 
  activeTab, 
  onTabChange, 
  tabCounts,
  visibleTabs,
  isLoading = false,
  isEngagementContext = false,
}: AuditWorkspaceTabsProps) {
  const tabs = [
    {
      id: "overview",
      label: "Overview",
      icon: FileText,
      count: 0,
      countColor: ""
    },
    {
      id: "engagements",
      label: isEngagementContext ? "Controls" : "Engagements",
      icon: Building2,
      count: tabCounts.engagements,
      countColor: "bg-indigo-500/20 text-indigo-400"
    },
    {
      id: "findings",
      label: "Findings",
      icon: AlertCircle,
      count: tabCounts.findings,
      countColor: "bg-amber-500/20 text-amber-400"
    },
    {
      id: "evidence-requests",
      label: "Evidence Requests",
      icon: FileText,
      count: tabCounts.evidenceRequests,
      countColor: "bg-red-500/20 text-red-400"
    },
    {
      id: "messages",
      label: "Messages",
      icon: MessageSquare,
      count: tabCounts.messages,
      countColor: "bg-indigo-500/20 text-indigo-400"
    },
    {
      id: "evidence-library",
      label: "Evidence Library",
      icon: FolderOpen,
      count: tabCounts.evidenceLibrary,
      countColor: ""
    },
    {
      id: "evidence-tasks",
      label: "Tasks",
      icon: CheckSquare,
      count: tabCounts.evidenceTasks,
      countColor: "bg-red-500/20 text-red-400"
    },
    {
      id: "my-access",
      label: "Evidence Access",
      icon: UserCheck,
      count: 0,
      countColor: ""
    }
  ]
  const filteredTabs = visibleTabs?.length
    ? tabs.filter((tab) => visibleTabs.includes(tab.id))
    : tabs

  return (
    <div className="border-b border-border bg-card">
      <div className="flex items-center gap-1 px-4 overflow-x-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-4 w-full">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : (
          filteredTabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-all
                  ${isActive 
                    ? 'border-primary text-primary' 
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
                  }
                `}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
                {tab.count > 0 && (
                  <Badge 
                    variant="secondary" 
                    className={`${tab.countColor} text-xs font-bold ml-1`}
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
