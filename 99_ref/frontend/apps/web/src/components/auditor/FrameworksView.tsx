"use client"

import * as React from "react"
import { 
  FileCheck,
  Search,
  Filter,
  Download,
  Eye,
  Loader2,
  RefreshCw,
  CheckCircle2,
  Clock,
  AlertCircle,
  Database,
  Globe,
  ShieldAlert
} from "lucide-react"

import { 
  Button, 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Badge,
  Input
} from "@kcontrol/ui"

import { useRouter } from "next/navigation"
import { listFrameworks } from "@/lib/api/grc"
import { toast } from "sonner"

interface Framework {
  id: string
  framework_code: string
  framework_type_code: string
  framework_category_code: string
  approval_status: string
  is_marketplace_visible: boolean
  is_active: boolean
  name: string
  description: string | null
  publisher_type: string
  publisher_name: string
  documentation_url: string | null
  created_at: string
  updated_at: string
}

interface FrameworksViewProps {
  orgId?: string
  manualSearchQuery?: string
  onSearchChange?: (val: string) => void
  colorScheme?: "primary" | "indigo" | "teal"
  baseRoute?: string
  hideImportTemplate?: boolean
  engagementId?: string
}

export function FrameworksView({ 
  orgId,
  manualSearchQuery,
  onSearchChange,
  colorScheme = "primary",
  baseRoute = "/frameworks",
  hideImportTemplate = false,
  engagementId
}: FrameworksViewProps) {
  const router = useRouter()
  const [frameworks, setFrameworks] = React.useState<Framework[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [internalSearch, setInternalSearch] = React.useState("")
  const [activeFilter, setActiveFilter] = React.useState("all")

  // Sync internal and external search
  const searchQuery = manualSearchQuery !== undefined ? manualSearchQuery : internalSearch;
  const setSearchQuery = (val: string) => {
    if (onSearchChange) onSearchChange(val);
    else setInternalSearch(val);
  }
  
  const theme = {
    primary: colorScheme === "indigo" ? "indigo-500" : (colorScheme === "teal" ? "teal-500" : "primary"),
    bg: colorScheme === "indigo" ? "bg-indigo-500/10" : (colorScheme === "teal" ? "bg-teal-500/10" : "bg-primary/10"),
    text: colorScheme === "indigo" ? "text-indigo-600" : (colorScheme === "teal" ? "text-teal-600" : "text-primary"),
    border: colorScheme === "indigo" ? "border-indigo-500/30" : (colorScheme === "teal" ? "border-teal-500/30" : "border-primary/30"),
    glow: colorScheme === "indigo" ? "shadow-[0_0_15px_rgba(99,102,241,0.15)]" : (colorScheme === "teal" ? "shadow-[0_0_15px_rgba(20,184,166,0.15)]" : "shadow-[0_0_15px_rgba(var(--primary),0.15)]"),
    button: colorScheme === "indigo" ? "bg-indigo-500 hover:bg-indigo-600 text-white" : (colorScheme === "teal" ? "bg-teal-500 hover:bg-teal-600 text-white" : "bg-primary hover:bg-primary/90 text-primary-foreground")
  }

  // Fetch frameworks
  const fetchFrameworks = React.useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await listFrameworks({
         deployed_org_id: orgId,
         only_engaged: !!engagementId || true // Enforce strict engagement-only view in Command Center
      })
      setFrameworks((data.items as any[]) || [])
    } catch (error: any) {
      console.error("Failed to fetch frameworks:", error)
      toast.error(error.message || "Failed to load audit frameworks")
    } finally {
      setIsLoading(false)
    }
  }, [orgId, engagementId])

  React.useEffect(() => {
    fetchFrameworks()
  }, [fetchFrameworks])

  // Real-time polling every 60 seconds
  React.useEffect(() => {
    const interval = setInterval(() => {
      fetchFrameworks()
    }, 60000)
    return () => clearInterval(interval)
  }, [fetchFrameworks])

  // Filter frameworks
  const filteredFrameworks = React.useMemo(() => {
    let filtered = frameworks

    // If engagementId is provided, we might want to filter to only that engagement's framework
    // However, the engagement already has the framework_id. 
    // For now, let's just make sure we handle the search/active filter first.

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(fw => 
        fw.name.toLowerCase().includes(query) ||
        fw.framework_code.toLowerCase().includes(query) ||
        fw.description?.toLowerCase().includes(query)
      )
    }

    // Apply status filter
    if (activeFilter !== "all") {
      filtered = filtered.filter(fw => {
        if (activeFilter === "draft") {
          return fw.approval_status === 'draft'
        }
        if (activeFilter === "active" || activeFilter === "approved") {
          return fw.is_active
        }
        return true
      })
    }

    return filtered
  }, [frameworks, searchQuery, activeFilter])

  // Get status badge
  const getStatusBadge = (framework: Framework) => {
    if (framework.is_active) {
      return (
        <Badge variant="outline" className="bg-green-500/10 text-green-700 border-green-500/20 px-2 h-5 text-[10px] font-black uppercase">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Active
        </Badge>
      )
    }
    if (framework.approval_status === 'draft') {
      return <Badge variant="outline" className="bg-muted/10 text-muted-foreground/50 border-border/20 px-2 h-5 text-[10px] font-black uppercase tracking-widest">Draft</Badge>
    }
    return <Badge variant="outline" className="bg-amber-500/10 text-amber-700 border-amber-500/20 px-2 h-5 text-[10px] font-black uppercase tracking-widest">{framework.approval_status || "Inactive"}</Badge>
  }

  // Get type badge
  const getTypeBadge = (typeCode: string) => {
    const colors: { [key: string]: string } = {
      compliance_standard: 'bg-blue-500/10 text-blue-700 border-blue-500/30',
      security_framework: 'bg-purple-500/10 text-purple-700 border-purple-500/30',
      regulatory: 'bg-orange-500/10 text-orange-700 border-orange-500/30'
    }
    return (
      <Badge variant="outline" className={`${colors[typeCode] || 'bg-muted/10 text-muted-foreground'} text-[9px] h-5 font-black uppercase tracking-tighter`}>
        {typeCode.replace('_', ' ')}
      </Badge>
    )
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/30 pb-6">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-foreground uppercase">Audit Portfolio Frameworks</h2>
          <p className={`text-sm ${theme.text} opacity-70 font-medium uppercase tracking-[0.2em] mt-1`}>
             Manage compliance standards across {frameworks.length} deployments
          </p>
        </div>
        <div className="flex items-center gap-3">
            <Button 
                variant="outline" 
                size="sm" 
                onClick={fetchFrameworks}
                disabled={isLoading}
                className="rounded-full bg-muted/30 border-border/40 hover:bg-muted/50 text-muted-foreground h-10 px-4 font-bold uppercase tracking-widest"
            >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Sync
            </Button>
            {!hideImportTemplate && (
                <Button 
                    className={`rounded-full h-10 px-6 font-black uppercase tracking-widest text-[11px] ${theme.button}`}
                    onClick={() => toast.info("Template import wizard will be available in the next iteration.")}
                >
                    Import Template
                </Button>
            )}
        </div>
      </div>

      {/* Filters Area */}
      <div className="flex flex-col md:flex-row items-center gap-4 bg-muted/20 p-4 rounded-3xl border border-border/30 backdrop-blur-xl">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground/40" />
          <Input
            placeholder="Search within organization frameworks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={`pl-12 bg-background/50 border-border/30 text-foreground placeholder:text-muted-foreground/40 h-12 rounded-2xl focus-visible:ring-${theme.primary}/50`}
          />
        </div>
        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto shrink-0 pb-2 md:pb-0">
          <div className="flex gap-1 p-1 bg-muted/30 rounded-2xl border border-border/20">
            {["all", "approved", "draft", "active"].map(filter => (
              <Button
                key={filter}
                variant={activeFilter === filter ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setActiveFilter(filter)}
                className={`capitalize h-10 px-6 rounded-xl text-[11px] font-black tracking-widest transition-all ${
                  activeFilter === filter 
                    ? `${theme.bg} ${theme.text} hover:opacity-80 border ${theme.border} ${theme.glow}` 
                    : "text-muted-foreground/50 hover:text-foreground"
                }`}
              >
                {filter}
              </Button>
            ))}
          </div>
        </div>
      </div>
      {/* Frameworks Grid */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-24">
          <Loader2 className={`h-12 w-12 animate-spin ${theme.text} opacity-50 mb-4`} />
          <p className="text-[10px] font-black text-muted-foreground/30 uppercase tracking-[0.3em] animate-pulse">Scanning Registry...</p>
        </div>
      ) : filteredFrameworks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-32 text-center bg-muted/10 rounded-3xl border border-dashed border-border/30">
          <Database className="h-16 w-16 text-muted-foreground/10 mb-4" />
          <p className="text-lg font-black text-foreground/60 tracking-tight">NO ALIGNED FRAMEWORKS</p>
          <p className="text-xs text-muted-foreground/50 mt-1 uppercase font-bold tracking-widest">Adjust filters or initialize a new compliance schema</p>
          <Button 
            variant="link" 
            onClick={() => {setSearchQuery(""); setActiveFilter("all")}}
            className={`${theme.text} mt-6 font-bold uppercase tracking-widest text-[10px]`}
          >
            Reset Active View
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredFrameworks.map(framework => (
            <Card 
              key={framework.id}
              onClick={() => router.push(`${baseRoute}/${framework.id}`)}
              className="bg-card/60 border-border/40 shadow-lg hover:border-teal-500/30 transition-all cursor-pointer group overflow-hidden backdrop-blur-xl"
            >
              <CardHeader className="pb-4 bg-muted/20 border-b border-border/20">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                      <CardTitle className="text-sm font-black text-foreground group-hover:text-primary transition-colors uppercase tracking-tight">{framework.name}</CardTitle>
                      <p className="text-[10px] font-mono text-muted-foreground/40">
                        {framework.framework_code}
                      </p>
                  </div>
                  {getStatusBadge(framework)}
                </div>
              </CardHeader>
              <CardContent className="pt-5 space-y-5">
                <p className="text-xs text-muted-foreground leading-relaxed font-medium line-clamp-2 min-h-[32px]">
                  {framework.description || "Historical compliance standard with no localized description provided."}
                </p>
                
                <div className="flex flex-wrap items-center gap-2">
                  {getTypeBadge(framework.framework_type_code)}
                  <Badge variant="outline" className="bg-muted/20 border-border/20 text-[9px] h-5 rounded-full px-2 text-muted-foreground/50 font-bold">
                    {framework.publisher_name}
                  </Badge>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-border/20">
                  <div className="space-y-0.5">
                      <p className="text-[9px] font-black text-muted-foreground/40 uppercase tracking-widest">Creation Date</p>
                      <span className="text-[10px] font-bold text-muted-foreground/60">
                        {new Date(framework.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                  </div>
                  <div className="flex items-center gap-1">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-9 w-9 rounded-xl bg-muted/30 hover:bg-muted/50:bg-white/10 text-muted-foreground/50"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (framework.documentation_url) {
                            window.open(framework.documentation_url, '_blank');
                          }
                        }}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
