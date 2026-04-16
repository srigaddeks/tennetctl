"use client"

import * as React from "react"
import { 
  ShieldCheck,
  Search,
  Filter,
  Clock,
  Loader2,
  RefreshCw,
  MessageSquare
} from "lucide-react"

import { 
  Button, 
  Card, 
  CardContent, 
  Badge,
  Input
} from "@kcontrol/ui"

import { 
  listAllControls
} from "@/lib/api/grc"
import { toast } from "sonner"

interface Control {
  id: string
  framework_id: string
  control_code: string
  control_category_code: string
  criticality_code: string
  control_type: string
  automation_potential: string
  name: string
  description: string | null
  guidance: string | null
  implementation_notes: string | null
  test_count: number
  created_at: string
  updated_at: string
}

interface ControlsViewProps {
  orgId?: string
  workspaceId?: string
  frameworkId?: string
  engagementId?: string
}

export function ControlsView({ 
  orgId,
  workspaceId,
  frameworkId,
  engagementId
}: ControlsViewProps) {
  const [controls, setControls] = React.useState<Control[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [activeFilter, setActiveFilter] = React.useState("all")

  // Fetch controls
  const fetchControls = React.useCallback(async () => {
    if (!orgId && !frameworkId && !workspaceId && !engagementId) {
      setIsLoading(false)
      setControls([])
      return
    }
    setIsLoading(true)
    try {
      const data = await listAllControls({
        deployed_org_id: orgId,
        deployed_workspace_id: workspaceId,
        framework_id: frameworkId,
        engagement_id: engagementId,
        limit: 100
      })
      // Cast to local Control interface
      setControls((data.items as any) || [])
    } catch (error: any) {
      console.error("Failed to fetch controls:", error)
      toast.error(error.message || "Failed to load controls")
    } finally {
      setIsLoading(false)
    }
  }, [orgId, workspaceId, frameworkId, engagementId])

  React.useEffect(() => {
    fetchControls()
  }, [fetchControls])

  // Real-time polling every 60 seconds
  React.useEffect(() => {
    const interval = setInterval(() => {
      fetchControls()
    }, 60000)
    return () => clearInterval(interval)
  }, [fetchControls])

  // Filter controls
  const filteredControls = React.useMemo(() => {
    let filtered = controls

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(ctrl => 
        ctrl.name.toLowerCase().includes(query) ||
        ctrl.control_code.toLowerCase().includes(query) ||
        ctrl.description?.toLowerCase().includes(query)
      )
    }

    // Apply status filter
    if (activeFilter !== "all") {
      filtered = filtered.filter(ctrl => {
        if (activeFilter === "critical") {
          return ctrl.criticality_code === 'critical'
        }
        if (activeFilter === "high") {
          return ctrl.criticality_code === 'high'
        }
        if (activeFilter === "preventive") {
          return ctrl.control_type === 'preventive'
        }
        if (activeFilter === "detective") {
          return ctrl.control_type === 'detective'
        }
        return true
      })
    }

    return filtered
  }, [controls, searchQuery, activeFilter])

  // Get criticality badge
  const getCriticalityBadge = (criticalityCode: string) => {
    const colors: { [key: string]: string } = {
      critical: 'bg-red-500/20 text-red-400 border-red-500/30',
      high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      low: 'bg-green-500/20 text-green-400 border-green-500/30'
    }
    return (
      <Badge variant="outline" className={colors[criticalityCode] || ''}>
        {criticalityCode}
      </Badge>
    )
  }

  // Get control type badge
  const getControlTypeBadge = (controlType: string) => {
    const colors: { [key: string]: string } = {
      preventive: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      detective: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      corrective: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      compensating: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
    }
    return (
      <Badge variant="outline" className={colors[controlType] || ''}>
        {controlType}
      </Badge>
    )
  }

  // Handle navigate to control (placeholder for detail view)
  const handleViewDetails = (controlId: string) => {
    toast.info("Detailed control view coming soon. Please use Engagements tab to verify specific audit controls.")
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground">Portfolio Controls</h2>
          <p className="text-sm font-medium text-primary/80">
            {filteredControls.length} of {controls.length} controls in this organization
          </p>
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={fetchControls}
          disabled={isLoading}
          className="border border-border/60 bg-background/70 text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Sync
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col items-start gap-4 rounded-2xl border border-border/60 bg-card/80 p-4 md:flex-row md:items-center">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/60" />
          <Input
            placeholder="Search by name, code or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-10 border-border/60 bg-background pl-10 text-foreground placeholder:text-muted-foreground/60"
          />
        </div>
        <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0 w-full md:w-auto">
          <Filter className="h-4 w-4 shrink-0 text-muted-foreground/60" />
          <div className="flex gap-1 shrink-0">
            {["all", "critical", "high", "preventive", "detective"].map(filter => (
              <Button
                key={filter}
                variant={activeFilter === filter ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setActiveFilter(filter)}
                className={`capitalize h-8 transition-all ${
                  activeFilter === filter 
                    ? "border border-primary/30 bg-primary/15 text-primary" 
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {filter}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Controls Table */}
      <Card className="overflow-hidden border-border/60 bg-card/85 shadow-sm">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-24">
              <Loader2 className="mb-4 h-10 w-10 animate-spin text-primary" />
              <p className="animate-pulse text-muted-foreground">Loading controls...</p>
            </div>
          ) : filteredControls.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <div className="mb-4 rounded-full bg-muted p-6">
                <ShieldCheck className="h-12 w-12 text-muted-foreground/40" />
              </div>
              <p className="text-lg font-medium text-foreground/80">No controls matched your criteria</p>
              <p className="mx-auto mt-1 max-w-xs text-sm text-muted-foreground">
                Try clearing your filters or searching for a different keyword.
              </p>
              <Button 
                variant="link" 
                onClick={() => {setSearchQuery(""); setActiveFilter("all")}}
                className="text-teal-400 mt-4 h-auto p-0"
              >
                Clear all filters
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border/60 bg-muted/40">
                    <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Control Identity</th>
                    <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Category</th>
                    <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Criticality</th>
                    <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Type</th>
                    <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Tests</th>
                    <th className="px-6 py-4 pr-8 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredControls.map(control => (
                    <tr 
                      key={control.id}
                      className="hover:bg-teal-500/5 transition-colors group"
                    >
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="text-sm font-medium text-foreground transition-colors group-hover:text-primary">
                            {control.name}
                          </span>
                          <span className="mt-0.5 text-xs font-mono text-muted-foreground">
                            {control.control_code}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant="outline" className="border-border/60 bg-muted/40 text-[10px] font-mono text-muted-foreground">
                          {control.control_category_code}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        {getCriticalityBadge(control.criticality_code)}
                      </td>
                      <td className="px-6 py-4">
                        {getControlTypeBadge(control.control_type)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                          <Clock className="h-3.5 w-3.5 text-primary/60" />
                          {control.test_count} tests
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right pr-6">
                        <div className="flex items-center justify-end gap-1 opacity-40 group-hover:opacity-100 transition-opacity">
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => handleViewDetails(control.id)}
                            className="h-8 border border-transparent bg-muted/40 text-xs text-muted-foreground hover:border-primary/20 hover:bg-primary/10 hover:text-primary"
                          >
                            <Search className="h-3.5 w-3.5 mr-1.5" />
                            Details
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            title="Message contextually"
                            className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          >
                            <MessageSquare className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
      
    </div>
  )
}
