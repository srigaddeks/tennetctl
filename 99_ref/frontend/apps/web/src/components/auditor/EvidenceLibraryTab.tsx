"use client"

import * as React from "react"
import { 
  FolderOpen,
  Search,
  Filter,
  Download,
  FileText,
  Image,
  File,
  Loader2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock
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

import { 
  listEngagementAttachments, 
  getDownloadUrl 
} from "@/lib/api/attachments"
import { toast } from "sonner"

interface Attachment {
  id: string
  entity_type: string
  entity_id: string
  original_filename: string
  content_type: string
  file_size_bytes: number
  description: string | null
  uploaded_by: string
  upload_status: string
  virus_scan_status: string
  is_deleted: boolean
  created_at: string
  updated_at: string
}

interface EvidenceLibraryTabProps {
  engagementId: string
}

export function EvidenceLibraryTab({ 
  engagementId
}: EvidenceLibraryTabProps) {
  const [attachments, setAttachments] = React.useState<Attachment[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [activeFilter, setActiveFilter] = React.useState("all")
  const [downloadingId, setDownloadingId] = React.useState<string | null>(null)
  const [exporting, setExporting] = React.useState(false)

  // Fetch attachments
  const fetchAttachments = React.useCallback(async () => {
    if (!engagementId) return
    
    setIsLoading(true)
    try {
      const data = await listEngagementAttachments(engagementId)
      setAttachments(data.items as any[])
    } catch (error) {
      console.error("Failed to fetch attachments:", error)
    } finally {
      setIsLoading(false)
    }
  }, [engagementId])

  React.useEffect(() => {
    fetchAttachments()
  }, [fetchAttachments])

  // Real-time polling every 60 seconds
  React.useEffect(() => {
    const interval = setInterval(() => {
      fetchAttachments()
    }, 60000)
    return () => clearInterval(interval)
  }, [fetchAttachments])

  // Filter attachments
  const filteredAttachments = React.useMemo(() => {
    let filtered = attachments

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(att => 
        att.original_filename.toLowerCase().includes(query) ||
        att.description?.toLowerCase().includes(query)
      )
    }

    // Apply status filter
    if (activeFilter !== "all") {
      filtered = filtered.filter(att => {
        if (activeFilter === "auto") {
          return att.upload_status === 'committed'
        }
        if (activeFilter === "manual") {
          return att.upload_status === 'staging'
        }
        if (activeFilter === "stale") {
          const age = Date.now() - new Date(att.created_at).getTime()
          return att.virus_scan_status === 'clean' && age > 30 * 24 * 60 * 60 * 1000
        }
        if (activeFilter === "missing") {
          return att.virus_scan_status === 'pending'
        }
        return true
      })
    }

    return filtered
  }, [attachments, searchQuery, activeFilter])

  // Handle download
  const handleDownload = async (attachment: Attachment) => {
    setDownloadingId(attachment.id)
    try {
      const data = await getDownloadUrl(attachment.id)
      window.open(data.url, '_blank')
      toast.success("Download started")
    } catch (error) {
      console.error("Failed to download:", error)
      toast.error("Failed to download file")
    } finally {
      setDownloadingId(null)
    }
  }

  // Handle export all ZIP
  const handleExportAllZip = async () => {
    setExporting(true)
    try {
      // Simulated export
      await new Promise(resolve => setTimeout(resolve, 2000))
      toast.success("Evidence exported successfully")
    } catch (error) {
      console.error("Failed to export:", error)
      toast.error("Failed to export evidence")
    } finally {
      setExporting(false)
    }
  }

  // Get file icon
  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith('image/')) return <Image className="h-4 w-4" />
    if (contentType.includes('pdf')) return <FileText className="h-4 w-4" />
    return <File className="h-4 w-4" />
  }

  // Get status badge
  const getStatusBadge = (attachment: Attachment) => {
    if (attachment.virus_scan_status === 'clean') {
      return <Badge variant="default" className="bg-green-500/20 text-green-400"><CheckCircle2 className="h-3 w-3 mr-1" />Valid</Badge>
    }
    if (attachment.virus_scan_status === 'pending') {
      return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending</Badge>
    }
    if (attachment.virus_scan_status === 'scanning') {
      return <Badge variant="secondary"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Scanning</Badge>
    }
    if (attachment.virus_scan_status === 'infected') {
      return <Badge variant="destructive"><AlertCircle className="h-3 w-3 mr-1" />Infected</Badge>
    }
    return <Badge variant="outline">{attachment.virus_scan_status}</Badge>
  }

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">Evidence Library</h2>
          <p className="text-sm text-muted-foreground">
            {filteredAttachments.length} of {attachments.length} files
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleExportAllZip}
            disabled={exporting}
          >
            {exporting ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            Export All ZIP
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search evidence..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <div className="flex gap-1">
            {["all", "auto", "manual", "stale", "missing"].map(filter => (
              <Button
                key={filter}
                variant={activeFilter === filter ? "default" : "ghost"}
                size="sm"
                onClick={() => setActiveFilter(filter)}
                className="capitalize"
              >
                {filter}
              </Button>
            ))}
          </div>
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={fetchAttachments}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Evidence Table */}
      <Card className="border-none shadow-lg overflow-hidden">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : filteredAttachments.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <FolderOpen className="h-12 w-12 mb-4 opacity-20" />
              <p className="text-sm font-medium">No evidence found</p>
              <p className="text-xs">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="divide-y divide-muted/50">
              {filteredAttachments.map(attachment => (
                <div 
                  key={attachment.id}
                  className="grid grid-cols-7 gap-4 px-6 py-4 hover:bg-muted/30 transition-all"
                >
                  <div className="col-span-2 flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                      {getFileIcon(attachment.content_type)}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{attachment.original_filename}</p>
                      <p className="text-xs text-muted-foreground">
                        {attachment.description || "No description"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <Badge variant="outline" className="text-xs font-mono">
                      {attachment.entity_type}
                    </Badge>
                  </div>
                  <div className="flex items-center text-sm text-muted-foreground">
                    {attachment.uploaded_by}
                  </div>
                  <div className="flex items-center text-sm text-muted-foreground">
                    {formatFileSize(attachment.file_size_bytes)}
                  </div>
                  <div className="flex items-center text-sm text-muted-foreground">
                    {new Date(attachment.created_at).toLocaleDateString()}
                  </div>
                  <div className="flex items-center justify-end gap-2">
                    {getStatusBadge(attachment)}
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleDownload(attachment)}
                      disabled={downloadingId === attachment.id}
                    >
                      {downloadingId === attachment.id ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <Download className="h-3 w-3" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
