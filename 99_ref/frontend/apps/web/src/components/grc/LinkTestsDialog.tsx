"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import {
  Button,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import { Search, Layers, CheckCircle2, Plus, Loader2, AlertTriangle, Zap, ClipboardCheck, Building2, FlaskConical } from "lucide-react"
import { listAvailableTestsForControl, createTestMapping } from "@/lib/api/grc"
import type { TestResponse } from "@/lib/types/grc"

interface LinkTestsDialogProps {
  open: boolean
  controlId: string
  controlName: string
  frameworkId: string
  onClose: () => void
  onLinked: () => void
}

const TEST_TYPE_STYLES: Record<string, string> = {
  manual: "bg-blue-500/10 text-blue-600 border-blue-500/30",
  automated: "bg-green-500/10 text-green-600 border-green-500/30",
  semi_automated: "bg-amber-500/10 text-amber-600 border-amber-500/30",
}

type ScopeTab = "platform" | "org" | "workspace"

function getTestScope(test: TestResponse): ScopeTab {
  if (test.scope_workspace_id) return "workspace"
  if (test.scope_org_id) return "org"
  return "platform"
}

export function LinkTestsDialog({ open, controlId, controlName, frameworkId, onClose, onLinked }: LinkTestsDialogProps) {
  const [search, setSearch] = useState("")
  const [tests, setTests] = useState<TestResponse[]>([])
  const [activeTab, setActiveTab] = useState<ScopeTab>("platform")
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const searchRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const runSearch = useCallback(async (q: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await listAvailableTestsForControl(frameworkId, controlId, {
        search: q || undefined,
        limit: 200,
      })
      setTests(res.items ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load tests")
    } finally {
      setLoading(false)
    }
  }, [frameworkId, controlId])

  useEffect(() => {
    if (!open) return
    if (searchRef.current) clearTimeout(searchRef.current)
    searchRef.current = setTimeout(() => runSearch(search), 300)
    return () => { if (searchRef.current) clearTimeout(searchRef.current) }
  }, [search, open, runSearch])

  async function handleLink(test: TestResponse) {
    setSaving(test.id)
    setError(null)
    setSuccessMsg(null)
    try {
      await createTestMapping(test.id, { control_id: controlId })
      setTests((prev) => prev.filter((t) => t.id !== test.id))
      setSuccessMsg(`Linked "${test.name ?? test.test_code}" to control`)
      onLinked()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to link test")
    } finally {
      setSaving(null)
    }
  }

  function handleClose() {
    setSearch("")
    setError(null)
    setSuccessMsg(null)
    setTests([])
    setActiveTab("platform")
    onClose()
  }

  const filteredTests = tests.filter((t) => getTestScope(t) === activeTab)
  const platformCount = tests.filter((t) => getTestScope(t) === "platform").length
  const orgCount = tests.filter((t) => getTestScope(t) === "org").length
  const workspaceCount = tests.filter((t) => getTestScope(t) === "workspace").length

  const TABS: { id: ScopeTab; label: string; icon: React.ReactNode; count: number }[] = [
    { id: "platform", label: "Platform", icon: <Zap className="w-3 h-3" />, count: platformCount },
    { id: "org", label: "Org", icon: <Building2 className="w-3 h-3" />, count: orgCount },
    { id: "workspace", label: "Workspace", icon: <FlaskConical className="w-3 h-3" />, count: workspaceCount },
  ]

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            Link Tests to Control
          </DialogTitle>
          <DialogDescription>
            Link control tests to <span className="font-medium text-foreground">{controlName}</span>.
          </DialogDescription>
        </DialogHeader>

        {successMsg && (
          <div className="flex items-center gap-2 text-xs text-green-600 bg-green-500/10 rounded-md px-3 py-2 border border-green-500/20">
            <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
            {successMsg}
          </div>
        )}

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            className="pl-8 h-9 text-sm"
            placeholder="Search tests by name or code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />
        </div>

        {/* Scope tabs */}
        <div className="flex items-center gap-0 border-b border-border/50">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors -mb-px ${
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.icon}
              {tab.label}
              <span className={`ml-1 text-[10px] px-1.5 py-0 rounded-full ${
                activeTab === tab.id ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {error && (
          <div className="flex items-center gap-2 text-xs text-destructive bg-destructive/5 rounded-md px-3 py-2">
            <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
            {error}
          </div>
        )}

        <div className="border border-border rounded-lg overflow-hidden max-h-80 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8 gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Searching…
            </div>
          ) : filteredTests.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              {search ? "No tests match your search." : `No ${activeTab} tests available.`}
            </div>
          ) : (
            <div className="divide-y divide-border">
              {filteredTests.map((t) => {
                const isSaving = saving === t.id
                return (
                  <div
                    key={t.id}
                    className="flex items-center gap-3 px-3 py-2.5 hover:bg-muted/40 transition-colors"
                  >
                    <div className="h-1.5 w-1.5 rounded-full shrink-0 bg-border" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {getTestScope(t) === "platform"
                          ? <Zap className="w-3 h-3 text-amber-500 shrink-0" />
                          : <ClipboardCheck className="w-3 h-3 text-blue-500 shrink-0" />
                        }
                        <span className="text-[11px] font-mono text-primary shrink-0">{t.test_code}</span>
                        <span className="text-xs font-medium truncate">{t.name ?? t.test_code}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className={`text-[10px] px-1.5 py-0 rounded border font-semibold ${TEST_TYPE_STYLES[t.test_type_code] ?? "bg-muted text-muted-foreground border-border"}`}>
                          {t.test_type_name ?? t.test_type_code}
                        </span>
                        {t.integration_type && t.integration_type !== "none" && (
                          <span className="text-[10px] text-muted-foreground">{t.integration_type}</span>
                        )}
                        <span className="text-[10px] text-muted-foreground">{t.monitoring_frequency}</span>
                      </div>
                    </div>
                    <button
                      disabled={isSaving}
                      onClick={() => handleLink(t)}
                      className="shrink-0 flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-primary hover:bg-primary/10 transition-colors disabled:opacity-50"
                    >
                      {isSaving ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <><Plus className="h-3 w-3" /> Link</>
                      )}
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <DialogFooter>
          <span className="text-xs text-muted-foreground flex-1">
            {filteredTests.length} test{filteredTests.length !== 1 ? "s" : ""} available
          </span>
          <Button onClick={handleClose}>Done</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
