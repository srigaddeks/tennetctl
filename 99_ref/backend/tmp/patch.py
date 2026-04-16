import sys

file_path = r'c:\Users\lenovo\Desktop\Kreesalis\kcontrol\frontend\apps\web\src\app\(002_dashboard)\frameworks\[frameworkId]\page.tsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add API imports
import_str = '''
import {
  suggestTestsForControl,
  applyTestLinkerSuggestionsForControl,
  type TestSuggestion,
} from "@/lib/api/testLinker"
'''
if 'suggestTestsForControl' not in content:
    content = content.replace(
        'import { listTasks } from "@/lib/api/grc"',
        import_str.strip() + '\nimport { listTasks } from "@/lib/api/grc"'
    )

# 2. Add Component and Styles
component_str = '''
const LINK_TYPE_STYLES: Record<string, string> = {
  covers: "bg-green-500/10 text-green-600 border-green-500/30",
  partially_covers: "bg-amber-500/10 text-amber-600 border-amber-500/30",
  related: "bg-sky-500/10 text-sky-600 border-sky-500/30",
}

function AiSuggestTestsPanel({
  controlId,
  orgId,
  workspaceId,
  onLinked,
  onClose,
}: {
  controlId: string
  orgId?: string
  workspaceId?: string
  onLinked: () => void
  onClose: () => void
}) {
  const [loading, setLoading] = useState(true)
  const [suggestions, setSuggestions] = useState<TestSuggestion[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [applyMsg, setApplyMsg] = useState<string | null>(null)

  useEffect(() => {
    suggestTestsForControl({
      control_id: controlId,
      org_id: orgId,
      workspace_id: workspaceId,
    })
      .then((s) => {
        setSuggestions(s)
        setSelected(new Set(s.map((x) => x.test_id)))
      })
      .catch((e) => setError(e instanceof Error ? e.message : "AI suggestion failed"))
      .finally(() => setLoading(false))
  }, [controlId, orgId, workspaceId])

  async function handleApply() {
    const approved = suggestions.filter((s) => selected.has(s.test_id))
    if (!approved.length) return
    setApplying(true)
    setError(null)
    try {
      const r = await applyTestLinkerSuggestionsForControl({ control_id: controlId, suggestions: approved })
      setApplyMsg(
        `Submitted ${r.created} mapping${r.created !== 1 ? "s" : ""} for approval${r.skipped ? ` (${r.skipped} already existed)` : ""}`,
      )
      setSuggestions([])
      setSelected(new Set())
      onLinked()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to apply")
    } finally {
      setApplying(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-3 text-xs text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin text-violet-500" />
        Finding relevant control tests…
      </div>
    )
  }

  return (
    <div className="mt-2 border border-violet-500/20 rounded-lg bg-violet-500/5 p-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-violet-600 flex items-center gap-1">
          <Sparkles className="h-3 w-3" /> AI Suggestions
        </span>
        <button className="text-[11px] text-muted-foreground hover:text-foreground" onClick={onClose}>
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {error && (
        <div className="text-xs text-destructive flex items-center gap-1.5">
          <AlertTriangle className="h-3 w-3 shrink-0" /> {error}
        </div>
      )}

      {applyMsg && (
        <div className="text-xs text-green-600 flex items-center gap-1.5">
          <CheckCircle2 className="h-3 w-3 shrink-0" /> {applyMsg}
        </div>
      )}

      {!applyMsg && (
        <p className="text-[10px] text-muted-foreground">
          AI-suggested links are submitted as pending mappings and need approval before they become active.
        </p>
      )}

      {suggestions.length === 0 && !error && !applyMsg && (
        <p className="text-xs text-muted-foreground">No relevant control tests found.</p>
      )}

      {suggestions.length > 0 && (
        <>
          <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
            {suggestions.map((s) => {
              const isSel = selected.has(s.test_id)
              return (
                <div
                  key={s.test_id}
                  className={`flex items-start gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors ${isSel ? "bg-violet-500/10" : "hover:bg-muted/40"}`}
                  onClick={() => setSelected((prev) => {
                    const n = new Set(prev)
                    n.has(s.test_id) ? n.delete(s.test_id) : n.add(s.test_id)
                    return n
                  })}
                >
                  <div className={`mt-0.5 h-3.5 w-3.5 rounded border shrink-0 flex items-center justify-center ${isSel ? "border-violet-500 bg-violet-500" : "border-border"}`}>
                    {isSel && <CheckCircle2 className="h-2.5 w-2.5 text-white" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[11px] font-mono text-primary">{s.test_code}</span>
                      <span className={`text-[9px] px-1 rounded border font-semibold ${LINK_TYPE_STYLES[s.link_type] ?? ""}`}>
                        {s.link_type.replace("_", " ")}
                      </span>
                      <span className="text-[10px] text-muted-foreground ml-auto">{Math.round(s.confidence * 100)}%</span>
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-0.5 leading-relaxed">{s.rationale}</p>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="flex items-center gap-2 pt-1">
            <span className="text-[11px] text-muted-foreground flex-1">{selected.size} of {suggestions.length} selected</span>
            <button className="text-[11px] underline text-muted-foreground" onClick={() => setSelected(new Set(suggestions.map(s => s.test_id)))}>All</button>
            <button className="text-[11px] underline text-muted-foreground" onClick={() => setSelected(new Set())}>None</button>
            <button
              className="flex items-center gap-1 text-[11px] font-semibold text-white bg-violet-600 hover:bg-violet-700 px-2.5 py-1 rounded-md disabled:opacity-50 transition-colors"
              disabled={selected.size === 0 || applying}
              onClick={handleApply}
            >
              {applying ? <Loader2 className="h-2.5 w-2.5 animate-spin" /> : <Sparkles className="h-2.5 w-2.5" />}
              Submit {selected.size}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
'''
if 'AiSuggestTestsPanel(' not in content:
    content = content.replace(
        'function ControlHierarchyPanel({',
        component_str + '\n\nfunction ControlHierarchyPanel({'
    )

# 3. Add state inside ControlHierarchyPanel
state_str = '''
  // Link test dialog state
  const [linkTestOpen, setLinkTestOpen] = useState(false)
  const [aiSuggestOpen, setAiSuggestOpen] = useState(false)
'''
if 'aiSuggestOpen' not in content:
    content = content.replace(
        '// Link test dialog state\n  const [linkTestOpen, setLinkTestOpen] = useState(false)',
        state_str.strip()
    )

# 4. Add action button to tests tab
ai_button_str = '''
            <span className="text-border/50\">|</span>
            <button
              type="button"
              onClick={() => setAiSuggestOpen((v) => !v)}
              className="flex items-center gap-1.5 text-[11px] text-violet-600 hover:text-violet-500 transition-colors"
            >
              <Sparkles className="w-3 h-3" /> AI Find Tests
            </button>
'''
if 'AI Find Tests' not in content:
    content = content.replace(
        '            <button\n              type="button"\n              onClick={() => setTaskSlideOver({ open: true, typeCode: "control_remediation", typeName: "Remediation" })}\n              className="flex items-center gap-1.5 text-[11px] text-orange-600 hover:text-orange-500 transition-colors"\n            >\n              <Target className="w-3 h-3" /> Add Remediation Task\n            </button>\n          </div>',
        '            <button\n              type="button"\n              onClick={() => setTaskSlideOver({ open: true, typeCode: "control_remediation", typeName: "Remediation" })}\n              className="flex items-center gap-1.5 text-[11px] text-orange-600 hover:text-orange-500 transition-colors"\n            >\n              <Target className="w-3 h-3" /> Add Remediation Task\n            </button>\n' + ai_button_str + '          </div>'
    )

# 5. Add rendering of AiSuggestTestsPanel inside ControlHierarchyPanel
ai_panel_mount_str = '''
      {/* AI Suggest Tests panel */}
      {aiSuggestOpen && (
        <AiSuggestTestsPanel
          controlId={control.id}
          orgId={defaultOrgId}
          workspaceId={defaultWorkspaceId}
          onLinked={loadData}
          onClose={() => setAiSuggestOpen(false)}
        />
      )}

      {/* Link test dialog */}
'''
if '<AiSuggestTestsPanel' not in content:
    content = content.replace(
        '{/* Link test dialog */}',
        ai_panel_mount_str.strip()
    )

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Patched successfully!')
