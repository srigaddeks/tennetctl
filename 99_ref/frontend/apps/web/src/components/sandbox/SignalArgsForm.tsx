"use client"

/**
 * SignalArgsForm — renders a dynamic form from a signal's args_schema.
 *
 * Each arg entry in args_schema looks like:
 *   { key: string, label: string, type: "string"|"number"|"boolean"|"select",
 *     default: any, description?: string, min?: number, max?: number, options?: string[] }
 *
 * Usage:
 *   <SignalArgsForm schema={signal_args_schema} values={args} onChange={setArgs} />
 */

import {
  Input,
  Label,
  Switch,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@kcontrol/ui"
import { cn } from "@/lib/utils"

export interface ArgDefinition {
  key: string
  label: string
  type: "string" | "number" | "boolean" | "select"
  default?: unknown
  description?: string
  min?: number
  max?: number
  options?: string[]
}

interface Props {
  schema: ArgDefinition[]
  values: Record<string, unknown>
  onChange: (values: Record<string, unknown>) => void
  disabled?: boolean
  className?: string
}

export function SignalArgsForm({ schema, values, onChange, disabled, className }: Props) {
  if (!schema || schema.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">No configurable arguments for this signal.</p>
    )
  }

  function set(key: string, value: unknown) {
    onChange({ ...values, [key]: value })
  }

  return (
    <div className={cn("space-y-4", className)}>
      {schema.map((arg) => (
        <div key={arg.key} className="space-y-1">
          <Label htmlFor={`arg-${arg.key}`} className="text-sm font-medium">
            {arg.label}
          </Label>
          {arg.description && (
            <p className="text-xs text-muted-foreground">{arg.description}</p>
          )}

          {arg.type === "boolean" ? (
            <div className="flex items-center gap-2 pt-1">
              <Switch
                isSelected={Boolean(values[arg.key] ?? arg.default ?? false)}
                onChange={(v: boolean) => set(arg.key, v)}
                isDisabled={disabled}
              >
                <span className="text-sm text-muted-foreground">
                  {Boolean(values[arg.key] ?? arg.default) ? "Enabled" : "Disabled"}
                </span>
              </Switch>
            </div>
          ) : arg.type === "select" && arg.options ? (
            <Select
              value={String(values[arg.key] ?? arg.default ?? "")}
              onValueChange={(v: string) => set(arg.key, v)}
              disabled={disabled}
            >
              <SelectTrigger id={`arg-${arg.key}`} className="h-8 text-sm">
                <SelectValue placeholder="Select…" />
              </SelectTrigger>
              <SelectContent>
                {arg.options.map((opt) => (
                  <SelectItem key={opt} value={opt}>
                    {opt}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : arg.type === "number" ? (
            <Input
              id={`arg-${arg.key}`}
              type="number"
              className="h-8 text-sm"
              value={String(values[arg.key] ?? arg.default ?? "")}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                set(arg.key, e.target.value === "" ? undefined : Number(e.target.value))
              }
              min={arg.min}
              max={arg.max}
              disabled={disabled}
            />
          ) : (
            <Input
              id={`arg-${arg.key}`}
              type="text"
              className="h-8 text-sm"
              value={String(values[arg.key] ?? arg.default ?? "")}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => set(arg.key, e.target.value)}
              disabled={disabled}
            />
          )}
        </div>
      ))}
    </div>
  )
}
