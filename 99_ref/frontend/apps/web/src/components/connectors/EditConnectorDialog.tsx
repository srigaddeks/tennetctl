"use client"

import { useEffect, useState } from "react"
import {
  Button,
  Input,
  Label,
  Separator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  Pencil,
  Lock,
  Settings2,
  Activity,
  Loader2,
} from "lucide-react"
import {
  getConnectorConfigSchema,
  getConnectorProperties,
  updateConnector,
  updateConnectorCredentials,
  testConnector,
} from "@/lib/api/sandbox"
import type {
  ConnectorInstanceResponse,
  ConnectorConfigField,
} from "@/lib/api/sandbox"

const SCHEDULE_OPTIONS = [
  { value: "manual", label: "Manual" },
  { value: "realtime", label: "Real-time" },
  { value: "hourly", label: "Every hour" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
]

export function EditConnectorDialog({
  connector,
  orgId,
  onSaved,
  onClose,
}: {
  connector: ConnectorInstanceResponse | null
  orgId: string
  onSaved: () => void
  onClose: () => void
}) {
  const [schedule, setSchedule] = useState("manual")
  const [isActive, setIsActive] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [configFields, setConfigFields] = useState<ConnectorConfigField[]>([])
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [loadingFields, setLoadingFields] = useState(false)

  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ health_status: string; message: string } | null>(null)

  useEffect(() => {
    if (connector) {
      setSchedule(connector.collection_schedule)
      setIsActive(connector.is_active)
      setSaving(false)
      setError(null)
      setTestResult(null)
      setFieldValues({})
      setLoadingFields(true)

      Promise.all([
        getConnectorConfigSchema(connector.connector_type_code).catch(() => null),
        getConnectorProperties(connector.id).catch((): Record<string, string> => ({})),
      ]).then(([schema, props]) => {
        if (schema) {
          setConfigFields(schema.fields)
          const initial: Record<string, string> = {}
          for (const f of schema.fields) {
            if (!f.credential && props[f.key]) {
              initial[f.key] = props[f.key]
            }
          }
          setFieldValues(initial)
        }
      }).finally(() => setLoadingFields(false))
    }
  }, [connector])

  if (!connector) return null

  const propFields = configFields.filter((f) => !f.credential)
  const credFields = configFields.filter((f) => f.credential)

  function setField(key: string, value: string) {
    setFieldValues((prev) => ({ ...prev, [key]: value }))
    setTestResult(null) // require re-test after edits
  }

  async function handleSave() {
    setSaving(true)
    setError(null)
    setTestResult(null)
    try {
      const propUpdates: Record<string, string> = {}
      for (const f of propFields) {
        const val = fieldValues[f.key]?.trim()
        if (val !== undefined) propUpdates[f.key] = val
      }
      await updateConnector(orgId, connector!.id, {
        collection_schedule: schedule,
        is_active: isActive,
        properties: Object.keys(propUpdates).length > 0 ? propUpdates : undefined,
      })

      const credUpdates: Record<string, string> = {}
      for (const f of credFields) {
        const val = fieldValues[f.key]?.trim()
        if (val) credUpdates[f.key] = val
      }
      if (Object.keys(credUpdates).length > 0) {
        await updateConnectorCredentials(orgId, connector!.id, credUpdates)
      }

      onSaved()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save")
    } finally {
      setSaving(false)
    }
  }

  async function handleTest() {
    setTesting(true)
    setTestResult(null)
    setError(null)
    try {
      const result = await testConnector(connector!.id)
      setTestResult(result)
      onSaved()
    } catch (e) {
      setTestResult({ health_status: "error", message: e instanceof Error ? e.message : "Test failed" })
    } finally {
      setTesting(false)
    }
  }

  const typeName = connector.connector_type_name || connector.connector_type_code

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Pencil className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>{connector.name || connector.instance_code}</DialogTitle>
              <DialogDescription>
                <code className="text-xs font-mono text-foreground/60">{connector.instance_code}</code>
                <span className="mx-2 text-foreground/30">&middot;</span>
                <span className="text-xs text-foreground/50">{typeName}</span>
                {connector.is_draft && (
                  <span className="ml-2 text-[10px] font-bold text-primary uppercase">Draft</span>
                )}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        {loadingFields ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Configuration fields */}
            {propFields.length > 0 && (
              <div className="rounded-lg border border-border/50 p-3 space-y-3">
                <div className="flex items-center gap-2">
                  <Settings2 className="h-3.5 w-3.5 text-muted-foreground" />
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Configuration</p>
                </div>
                {propFields.map((field) => (
                  <div key={field.key} className="space-y-1">
                    <Label className="text-xs">{field.label}{field.required && <span className="text-red-500 ml-0.5">*</span>}</Label>
                    <Input
                      type={field.type === "password" ? "password" : "text"}
                      placeholder={field.placeholder ?? ""}
                      value={fieldValues[field.key] ?? ""}
                      onChange={(e) => setField(field.key, e.target.value)}
                      className="h-8 text-xs"
                    />
                    {field.hint && <p className="text-[10px] text-muted-foreground leading-relaxed">{field.hint}</p>}
                  </div>
                ))}
              </div>
            )}

            {/* Credentials */}
            {credFields.length > 0 && (
              <div className="rounded-lg border border-primary/20 bg-primary/[0.02] p-3 space-y-3">
                <div className="flex items-center gap-2">
                  <Lock className="h-3.5 w-3.5 text-primary/60" />
                  <p className="text-xs font-medium text-primary/80 uppercase tracking-wide">Credentials</p>
                  <span className="text-[10px] text-muted-foreground ml-auto">Leave blank to keep existing</span>
                </div>
                {credFields.map((field) => (
                  <div key={field.key} className="space-y-1">
                    <Label className="text-xs">{field.label}{field.required && <span className="text-red-500 ml-0.5">*</span>}</Label>
                    <Input
                      type="password"
                      placeholder={`Enter ${field.label.toLowerCase()}...`}
                      value={fieldValues[field.key] ?? ""}
                      onChange={(e) => setField(field.key, e.target.value)}
                      className="h-8 text-xs font-mono"
                    />
                    {field.hint && <p className="text-[10px] text-muted-foreground leading-relaxed">{field.hint}</p>}
                  </div>
                ))}
              </div>
            )}

            {/* Settings */}
            <div className="rounded-lg border border-border/30 p-3 space-y-3">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Settings</p>
              <div className="space-y-1">
                <Label className="text-xs">Collection Schedule</Label>
                <select
                  className="h-8 w-full rounded-md border border-input bg-background px-3 text-xs"
                  value={schedule}
                  onChange={(e) => setSchedule(e.target.value)}
                >
                  {SCHEDULE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="edit-is-active"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="h-4 w-4 rounded border-input"
                />
                <Label htmlFor="edit-is-active" className="text-xs cursor-pointer">Active</Label>
              </div>
            </div>
          </div>
        )}

        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-xs text-red-500 mt-2">{error}</p>}
        {testResult && (
          <div className={`flex items-center gap-2 rounded-lg border px-3 py-2.5 text-xs mt-2 ${
            testResult.health_status === "healthy"
              ? "border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-400"
              : "border-red-500/30 bg-red-500/10 text-red-500"
          }`}>
            <span className={`h-2 w-2 rounded-full shrink-0 ${testResult.health_status === "healthy" ? "bg-green-500" : "bg-red-500"}`} />
            <span className="font-medium">{testResult.health_status === "healthy" ? "Connected" : "Failed"}</span> — {testResult.message}
          </div>
        )}

        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving || testing}>Cancel</Button>
          <Button variant="outline" size="sm" onClick={handleTest} disabled={saving || testing} className="gap-1.5">
            {testing ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <Activity className="h-3 w-3" />
                Test Connection
              </>
            )}
          </Button>
          <Button size="sm" onClick={handleSave} disabled={saving || testing || testResult?.health_status !== "healthy"}>
            {saving ? (
              <span className="flex items-center gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin" />
                Saving...
              </span>
            ) : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
