"use client"

import React, {
  useState,
  useRef,
  useCallback,
  useEffect,
  KeyboardEvent,
} from "react"
import Link from "next/link"
import {
  Button,
  Input,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@kcontrol/ui"
import { Textarea } from "@/components/ui/textarea"
import {
  Plus, Trash2, Eye, EyeOff, ExternalLink,
  ArrowUpDown, ArrowUp, ArrowDown, Loader2, Copy, Check, AlertCircle, X,
} from "lucide-react"

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_COL_WIDTH = 160

/** A badge style entry: maps a cell value to a Tailwind class string */
export type BadgeStyleMap = Record<string, string>

export interface SpreadsheetColumn<T = Record<string, unknown>> {
  key: keyof T & string
  label: string
  width?: number
  type?: "text" | "select" | "textarea" | "number" | "date" | "readonly" | "link"
  /** For link type: returns the href given a row */
  getLinkHref?: (row: T) => string | null
  options?: { value: string; label: string }[]
  hidden?: boolean
  required?: boolean
  /** If provided, render the display value as a colored badge chip */
  badgeStyles?: BadgeStyleMap
  /** Whether this column is sortable (default true for all non-link columns) */
  sortable?: boolean
}

export interface EntitySpreadsheetProps<T extends Record<string, unknown>> {
  columns: SpreadsheetColumn<T>[]
  rows: T[]
  onSave: (row: T, index: number) => Promise<void>
  onDelete?: (row: T, index: number) => Promise<void>
  onBulkDelete?: (rows: T[]) => Promise<void>
  loading?: boolean
  exportButton?: React.ReactNode
  importButton?: React.ReactNode
  keyField?: string
  readOnly?: boolean
  hideAddButton?: boolean
  /** Total count (when rows are pre-filtered, show "X of Y") */
  totalCount?: number
  /** Callback when selection changes */
  onSelectionChange?: (selectedIndices: number[]) => void
  /** Initial selected indices */
  initialSelectedIndices?: number[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Internal types
// ─────────────────────────────────────────────────────────────────────────────

interface CellCoord {
  rowIndex: number
  colKey: string
}

interface PendingRow<T> {
  data: Partial<T>
  isPending: true
}

type DisplayRow<T> = { data: T; isPending: false } | PendingRow<T>

type SortDir = "asc" | "desc" | null

// ─────────────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────────────

export function EntitySpreadsheet<T extends Record<string, unknown>>({
  columns,
  rows,
  onSave,
  onDelete,
  onBulkDelete,
  loading = false,
  exportButton,
  importButton,
  keyField = "id",
  readOnly = false,
  hideAddButton = false,
  totalCount,
  onSelectionChange,
  initialSelectedIndices,
}: EntitySpreadsheetProps<T>) {
  const [hiddenCols, setHiddenCols] = useState<Set<string>>(
    () => new Set(columns.filter((c) => c.hidden).map((c) => c.key))
  )
  const [colWidths, setColWidths] = useState<Record<string, number>>(() => {
    const init: Record<string, number> = {}
    columns.forEach((c) => { init[c.key] = c.width ?? DEFAULT_COL_WIDTH })
    return init
  })
  const [pendingRows, setPendingRows] = useState<Partial<T>[]>([])
  const [editCell, setEditCell] = useState<CellCoord | null>(null)
  const [editValue, setEditValue] = useState<string>("")
  const [selectedRows, setSelectedRows] = useState<Set<number>>(() => new Set(initialSelectedIndices ?? []))
  
  // Sync selectedRows if initialSelectedIndices changes (e.g. from a parent prop)
  useEffect(() => {
    if (initialSelectedIndices) {
      setSelectedRows(new Set(initialSelectedIndices))
    }
  }, [initialSelectedIndices])
  const [savingRows, setSavingRows] = useState<Set<number>>(new Set())
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<SortDir>(null)
  const [copiedRows, setCopiedRows] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement | null>(null)
  const resizeRef = useRef<{ key: string; startX: number; startWidth: number } | null>(null)
  
  // ── Selection sync ──
  useEffect(() => {
    onSelectionChange?.(Array.from(selectedRows))
  }, [selectedRows, onSelectionChange])

  // ── Column resize ──
  const startResize = useCallback((e: React.MouseEvent, colKey: string) => {
    e.preventDefault()
    e.stopPropagation()
    resizeRef.current = { key: colKey, startX: e.clientX, startWidth: colWidths[colKey] ?? DEFAULT_COL_WIDTH }

    const onMove = (ev: MouseEvent) => {
      const current = resizeRef.current
      if (!current) return
      const delta = ev.clientX - current.startX
      const newWidth = Math.max(60, current.startWidth + delta)
      const key = current.key
      setColWidths((prev) => ({ ...prev, [key]: newWidth }))
    }
    const onUp = () => {
      resizeRef.current = null
      window.removeEventListener("mousemove", onMove)
      window.removeEventListener("mouseup", onUp)
    }
    window.addEventListener("mousemove", onMove)
    window.addEventListener("mouseup", onUp)
  }, [colWidths])

  // ── Sorting ──
  const handleSortClick = useCallback((colKey: string) => {
    setSortKey((prev) => {
      if (prev !== colKey) {
        setSortDir("asc")
        return colKey
      }
      setSortDir((d) => {
        if (d === "asc") return "desc"
        if (d === "desc") { setSortKey(null); return null }
        return "asc"
      })
      return colKey
    })
  }, [])

  // ── Sort + display rows ──
  const sortedRows = React.useMemo(() => {
    if (!sortKey || !sortDir) return rows
    return [...rows].sort((a, b) => {
      const av = String(a[sortKey] ?? "").toLowerCase()
      const bv = String(b[sortKey] ?? "").toLowerCase()
      const cmp = av.localeCompare(bv, undefined, { numeric: true })
      return sortDir === "asc" ? cmp : -cmp
    })
  }, [rows, sortKey, sortDir])

  const displayRows: DisplayRow<T>[] = [
    ...sortedRows.map((r) => ({ data: r, isPending: false as const })),
    ...pendingRows.map((r) => ({ data: r as Partial<T>, isPending: true as const })),
  ]

  const visibleColumns = columns.filter((c) => !hiddenCols.has(c.key))

  // ── Focus input on edit ──
  useEffect(() => {
    if (editCell && inputRef.current) {
      inputRef.current.focus()
      if (inputRef.current instanceof HTMLInputElement) inputRef.current.select()
    }
  }, [editCell])

  // ── Start edit ──
  const startEdit = useCallback(
    (rowIndex: number, colKey: string, currentValue: unknown) => {
      if (readOnly) return
      const col = columns.find((c) => c.key === colKey)
      if (!col || col.type === "readonly") return
      setEditCell({ rowIndex, colKey })
      setEditValue(currentValue != null ? String(currentValue) : "")
    },
    [columns, readOnly]
  )

  // ── Commit edit ──
  const commitEdit = useCallback(async () => {
    if (!editCell) return
    const { rowIndex, colKey } = editCell
    setEditCell(null)
    setSaveError(null)

    const isExisting = rowIndex < sortedRows.length
    if (isExisting) {
      const existing = sortedRows[rowIndex]
      const updated = { ...existing, [colKey]: editValue } as T
      setSavingRows((prev) => new Set(prev).add(rowIndex))
      try {
        await onSave(updated, rowIndex)
      } catch (e) {
        setSaveError(e instanceof Error ? e.message : "Failed to save — please try again.")
      } finally {
        setSavingRows((prev) => { const next = new Set(prev); next.delete(rowIndex); return next })
      }
    } else {
      const pendingIndex = rowIndex - sortedRows.length
      setPendingRows((prev) =>
        prev.map((r, i) => i === pendingIndex ? { ...r, [colKey]: editValue } : r)
      )
    }
  }, [editCell, editValue, sortedRows, onSave])

  // ── Cancel edit ──
  const cancelEdit = useCallback(() => {
    setEditCell(null)
    setEditValue("")
  }, [])

  // ── Keyboard navigation ──
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLElement>) => {
      if (!editCell) return

      if (e.key === "Escape") { e.preventDefault(); cancelEdit(); return }

      const isTextarea = columns.find((c) => c.key === editCell.colKey)?.type === "textarea"

      if (e.key === "Enter" && !isTextarea) { e.preventDefault(); void commitEdit(); return }

      if (e.key === "Tab") {
        e.preventDefault()
        void commitEdit().then(() => {
          const colIndex = visibleColumns.findIndex((c) => c.key === editCell.colKey)
          const nextColIndex = e.shiftKey ? colIndex - 1 : colIndex + 1
          if (nextColIndex >= 0 && nextColIndex < visibleColumns.length) {
            const nextCol = visibleColumns[nextColIndex]
            const row = displayRows[editCell.rowIndex]
            const val = row ? (row.data as Record<string, unknown>)[nextCol.key] : undefined
            startEdit(editCell.rowIndex, nextCol.key, val)
          }
        })
        return
      }

      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        const isTextarea = columns.find((c) => c.key === editCell.colKey)?.type === "textarea"
        if (isTextarea) return
        e.preventDefault()
        void commitEdit().then(() => {
          const nextRow = e.key === "ArrowDown"
            ? editCell.rowIndex + 1
            : editCell.rowIndex - 1
          if (nextRow >= 0 && nextRow < displayRows.length) {
            const row = displayRows[nextRow]
            const val = row ? (row.data as Record<string, unknown>)[editCell.colKey] : undefined
            startEdit(nextRow, editCell.colKey, val)
          }
        })
        return
      }
    },
    [editCell, columns, visibleColumns, displayRows, commitEdit, cancelEdit, startEdit]
  )

  // ── Add pending row ──
  const addPendingRow = useCallback(() => {
    setPendingRows((prev) => [...prev, {} as Partial<T>])
  }, [])

  // ── Commit pending row ──
  const commitPendingRow = useCallback(
    async (pendingIndex: number) => {
      const rowIndex = sortedRows.length + pendingIndex
      const pendingData = pendingRows[pendingIndex] as T
      setSavingRows((prev) => new Set(prev).add(rowIndex))
      try {
        await onSave(pendingData, rowIndex)
        setPendingRows((prev) => prev.filter((_, i) => i !== pendingIndex))
      } finally {
        setSavingRows((prev) => { const next = new Set(prev); next.delete(rowIndex); return next })
      }
    },
    [sortedRows.length, pendingRows, onSave]
  )

  // ── Delete single row ──
  const handleDelete = useCallback(
    async (rowIndex: number) => {
      if (!onDelete) return
      const isExisting = rowIndex < sortedRows.length
      if (isExisting) {
        setSavingRows((prev) => new Set(prev).add(rowIndex))
        try {
          await onDelete(sortedRows[rowIndex], rowIndex)
        } finally {
          setSavingRows((prev) => { const next = new Set(prev); next.delete(rowIndex); return next })
        }
      } else {
        const pendingIndex = rowIndex - sortedRows.length
        setPendingRows((prev) => prev.filter((_, i) => i !== pendingIndex))
      }
    },
    [sortedRows, onDelete]
  )

  // ── Bulk delete selected rows ──
  const handleBulkDelete = useCallback(async () => {
    if (!onBulkDelete && !onDelete) return
    const selectedIndices = [...selectedRows].sort((a, b) => b - a)
    const existingIndices = selectedIndices.filter(i => i < sortedRows.length)
    const pendingIndices = selectedIndices.filter(i => i >= sortedRows.length)

    setBulkDeleting(true)
    try {
      if (onBulkDelete && existingIndices.length > 0) {
        await onBulkDelete(existingIndices.map(i => sortedRows[i]))
      } else if (onDelete) {
        for (const i of existingIndices) {
          await onDelete(sortedRows[i], i)
        }
      }
      // Remove pending rows (reverse order)
      for (const i of pendingIndices) {
        const pi = i - sortedRows.length
        setPendingRows((prev) => prev.filter((_, idx) => idx !== pi))
      }
      setSelectedRows(new Set())
    } finally {
      setBulkDeleting(false)
    }
  }, [selectedRows, sortedRows, onDelete, onBulkDelete])

  // ── Copy selected rows to clipboard (tab-separated, Excel-compatible) ──
  const handleCopyRows = useCallback(async () => {
    if (selectedRows.size === 0) return
    const indices = [...selectedRows].sort((a, b) => a - b)
    const lines = indices.map((i) => {
      const row = displayRows[i]
      if (!row) return ""
      const rowData = row.data as Record<string, unknown>
      return visibleColumns
        .map((col) => {
          const v = rowData[col.key]
          const str = v != null ? String(v) : ""
          // Escape tabs/newlines inside cell values
          return str.replace(/\t/g, " ").replace(/\n/g, " ")
        })
        .join("\t")
    })
    const tsv = lines.join("\n")
    try {
      await navigator.clipboard.writeText(tsv)
      setCopiedRows(true)
      setTimeout(() => setCopiedRows(false), 1800)
    } catch { /* clipboard API unavailable */ }
  }, [selectedRows, displayRows, visibleColumns])

  // ── Paste from clipboard ──
  const handlePaste = useCallback(
    (e: React.ClipboardEvent<HTMLDivElement>) => {
      if (readOnly) return
      const text = e.clipboardData.getData("text/plain")
      if (!text) return

      const lines = text.trim().split("\n")
      const newRows: Partial<T>[] = lines.map((line) => {
        const cells = line.split("\t")
        const row: Partial<T> = {}
        visibleColumns.forEach((col, i) => {
          if (cells[i] !== undefined) {
            ;(row as Record<string, unknown>)[col.key] = cells[i].trim()
          }
        })
        return row
      })
      e.preventDefault()
      setPendingRows((prev) => [...prev, ...newRows])
    },
    [readOnly, visibleColumns]
  )

  // ── Toggle column visibility ──
  const toggleColumn = useCallback((key: string) => {
    setHiddenCols((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key); else next.add(key)
      return next
    })
  }, [])

  // ── Select all ──
  const toggleSelectAll = useCallback(() => {
    if (selectedRows.size === displayRows.length) setSelectedRows(new Set())
    else setSelectedRows(new Set(displayRows.map((_, i) => i)))
  }, [selectedRows.size, displayRows.length])

  // ── Row checkbox ──
  const toggleRowSelect = useCallback((index: number) => {
    setSelectedRows((prev) => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index); else next.add(index)
      return next
    })
  }, [])

  // ── Badge renderer ──
  const renderBadge = (col: SpreadsheetColumn<T>, value: string) => {
    if (!col.badgeStyles || !value) return null
    const cls = col.badgeStyles[value]
    if (!cls) return null
    const label = col.options?.find(o => o.value === value)?.label ?? value
    return (
      <span className={`inline-flex items-center px-1.5 py-0 rounded text-[10px] font-semibold uppercase tracking-wide border ${cls}`}>
        {label}
      </span>
    )
  }

  // ── Render cell content ──
  const renderCell = (
    rowIndex: number,
    col: SpreadsheetColumn<T>,
    value: unknown,
    rowData: T
  ) => {
    const isEditing = editCell?.rowIndex === rowIndex && editCell?.colKey === col.key
    const displayValue = value != null ? String(value) : ""

    // Link type
    if (col.type === "link") {
      const href = col.getLinkHref ? col.getLinkHref(rowData) : null
      if (!displayValue) return <span className="block px-2 py-1.5 text-sm text-muted-foreground">—</span>
      if (href) {
        return (
          <Link
            href={href}
            className="flex items-center gap-1 px-2 py-1.5 text-sm text-primary hover:underline truncate"
            onClick={(e) => e.stopPropagation()}
          >
            <span className="truncate">{displayValue}</span>
            <ExternalLink className="h-3 w-3 flex-shrink-0 opacity-60" />
          </Link>
        )
      }
      return <span className="block px-2 py-1.5 text-sm truncate">{displayValue}</span>
    }

    // Editing
    if (isEditing) {
      if (col.type === "select" && col.options) {
        return (
          <select
            ref={inputRef as unknown as React.RefObject<HTMLSelectElement>}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={() => void commitEdit()}
            onKeyDown={handleKeyDown}
            className="w-full h-full border-0 outline-none bg-white dark:bg-zinc-900 text-sm px-2 py-1 rounded"
            autoFocus
          >
            <option value="">— select —</option>
            {col.options.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        )
      }
      if (col.type === "textarea") {
        return (
          <Textarea
            ref={inputRef as React.RefObject<HTMLTextAreaElement>}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={() => void commitEdit()}
            onKeyDown={handleKeyDown}
            className="w-full min-h-[80px] border-0 outline-none bg-white dark:bg-zinc-900 text-sm px-2 py-1 resize-none"
            autoFocus
          />
        )
      }
      return (
        <Input
          ref={inputRef as React.RefObject<HTMLInputElement>}
          type={col.type === "number" ? "number" : col.type === "date" ? "date" : "text"}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={() => void commitEdit()}
          onKeyDown={handleKeyDown}
          className="w-full h-full border-0 outline-none bg-white dark:bg-zinc-900 text-sm px-2 py-0 h-8 rounded-none focus-visible:ring-0 focus-visible:ring-offset-0"
          autoFocus
        />
      )
    }

    // Display mode — try badge first
    if (col.badgeStyles && displayValue) {
      const badge = renderBadge(col, displayValue)
      if (badge) {
        return <span className="flex items-center px-2 py-1.5">{badge}</span>
      }
    }

    // Display mode — plain
    return (
      <span className="block truncate px-2 py-1.5 text-sm leading-5">
        {col.type === "select" && col.options
          ? (col.options.find((o) => o.value === displayValue)?.label ?? displayValue)
          : displayValue || ""}
      </span>
    )
  }

  const hasSelection = selectedRows.size > 0
  const canDelete = !readOnly && (!!onDelete || !!onBulkDelete)
  const colCount = visibleColumns.length + 2 + (canDelete ? 1 : 0)

  return (
    <TooltipProvider>
      <div className="flex flex-col gap-2" onPaste={handlePaste}>

        {/* ── Toolbar ── */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            {!readOnly && !hideAddButton && (
              <Button size="sm" variant="outline" onClick={addPendingRow} disabled={loading}>
                <Plus className="h-4 w-4 mr-1" />
                New row
              </Button>
            )}
            {exportButton}
            {importButton}

            {/* Copy + bulk-delete — appear when rows are selected */}
            {hasSelection && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => void handleCopyRows()}
              >
                {copiedRows
                  ? <Check className="h-3.5 w-3.5 mr-1 text-green-600" />
                  : <Copy className="h-3.5 w-3.5 mr-1" />
                }
                {copiedRows ? "Copied!" : `Copy ${selectedRows.size} row${selectedRows.size !== 1 ? "s" : ""}`}
              </Button>
            )}
            {canDelete && hasSelection && (
              <Button
                size="sm"
                variant="destructive"
                onClick={() => void handleBulkDelete()}
                disabled={bulkDeleting}
              >
                {bulkDeleting
                  ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
                  : <Trash2 className="h-3.5 w-3.5 mr-1" />
                }
                Delete {selectedRows.size} row{selectedRows.size !== 1 ? "s" : ""}
              </Button>
            )}
          </div>

          {/* Column visibility toggles */}
          <div className="flex items-center gap-1 flex-wrap">
            {columns
              .filter((c) => c.hidden !== undefined)
              .map((col) => (
                <Tooltip key={col.key}>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => toggleColumn(col.key)}
                      className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded border border-border hover:bg-accent transition-colors"
                    >
                      {hiddenCols.has(col.key) ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                      {col.label}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>{hiddenCols.has(col.key) ? "Show" : "Hide"} column</TooltipContent>
                </Tooltip>
              ))}
          </div>
        </div>

        {/* ── Save error banner ── */}
        {saveError && (
          <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span className="flex-1">{saveError}</span>
            <button onClick={() => setSaveError(null)} className="ml-auto shrink-0 hover:opacity-70">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* ── Table ── */}
        <div className="rounded-md border border-border overflow-auto max-h-[72vh]">
          <table className="w-full border-collapse text-sm">
            <thead className="sticky top-0 z-10">
              <tr className="bg-muted/60 shadow-[0_1px_0_0_hsl(var(--border))]">
                {/* Select-all + row # header */}
                <th className="w-12 border-b border-r border-border px-2 py-2 text-center">
                  <input
                    type="checkbox"
                    checked={displayRows.length > 0 && selectedRows.size === displayRows.length}
                    onChange={toggleSelectAll}
                    className="h-4 w-4 rounded"
                  />
                </th>

                {visibleColumns.map((col) => {
                  const w = colWidths[col.key] ?? DEFAULT_COL_WIDTH
                  const isSorted = sortKey === col.key
                  const canSort = col.sortable !== false && col.type !== "link"
                  return (
                    <th
                      key={col.key}
                      className="border-b border-r border-border px-2 py-2 text-left font-medium text-xs text-muted-foreground uppercase tracking-wide whitespace-nowrap relative select-none"
                      style={{ width: w, minWidth: 60 }}
                    >
                      <div
                        className={`flex items-center gap-1 pr-3 ${canSort ? "cursor-pointer hover:text-foreground" : ""}`}
                        onClick={() => canSort && handleSortClick(col.key)}
                      >
                        <span className="truncate">
                          {col.label}
                          {col.required && <span className="text-destructive ml-0.5">*</span>}
                        </span>
                        {canSort && (
                          isSorted
                            ? (sortDir === "asc"
                              ? <ArrowUp className="h-3 w-3 shrink-0 text-primary" />
                              : <ArrowDown className="h-3 w-3 shrink-0 text-primary" />)
                            : <ArrowUpDown className="h-3 w-3 shrink-0 opacity-30 group-hover:opacity-60" />
                        )}
                      </div>
                      {/* Resize handle */}
                      <div
                        className="absolute right-0 top-0 bottom-0 w-3 cursor-col-resize flex items-center justify-center group/resize"
                        onMouseDown={(e) => startResize(e, col.key)}
                      >
                        <div className="w-0.5 h-4 bg-border group-hover/resize:bg-primary transition-colors rounded-full" />
                      </div>
                    </th>
                  )
                })}

                {/* Actions column */}
                {canDelete && (
                  <th className="w-10 border-b border-border px-2 py-2" />
                )}
              </tr>
            </thead>

            <tbody>
              {loading && displayRows.length === 0 && (
                <tr>
                  <td colSpan={colCount} className="px-4 py-8 text-center">
                    <div className="flex items-center justify-center gap-2 text-muted-foreground text-sm">
                      <Loader2 className="h-4 w-4 animate-spin" /> Loading…
                    </div>
                  </td>
                </tr>
              )}

              {!loading && displayRows.length === 0 && (
                <tr>
                  <td colSpan={colCount} className="px-4 py-10 text-center text-muted-foreground text-sm">
                    No rows. Click &quot;New row&quot; to add one, or paste tab-separated data from a spreadsheet.
                  </td>
                </tr>
              )}

              {displayRows.map((displayRow, rowIndex) => {
                const isPending = displayRow.isPending
                const rowData = displayRow.data as Record<string, unknown>
                const isSaving = savingRows.has(rowIndex)
                const isSelected = selectedRows.has(rowIndex)
                const pendingIndex = isPending ? rowIndex - sortedRows.length : -1

                return (
                  <tr
                    key={
                      isPending
                        ? `pending-${pendingIndex}`
                        : String(rowData[keyField] ?? rowIndex)
                    }
                    className={[
                      "group border-b border-border last:border-b-0 transition-colors",
                      isPending ? "bg-amber-50 dark:bg-amber-950/20" : "hover:bg-muted/30",
                      isSelected ? "bg-primary/5" : "",
                      isSaving ? "opacity-70" : "",
                    ].filter(Boolean).join(" ")}
                  >
                    {/* Row # + checkbox */}
                    <td className="w-12 border-r border-border px-2 py-1.5">
                      <div className="flex items-center gap-1.5">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleRowSelect(rowIndex)}
                          className="h-3.5 w-3.5 rounded shrink-0"
                        />
                        {isSaving
                          ? <Loader2 className="h-3 w-3 animate-spin text-primary shrink-0" />
                          : <span className="text-[10px] text-muted-foreground/50 font-mono leading-none tabular-nums w-5 text-right">{rowIndex + 1}</span>
                        }
                      </div>
                    </td>

                    {/* Data cells */}
                    {visibleColumns.map((col) => {
                      const cellValue = rowData[col.key]
                      const isEditing = editCell?.rowIndex === rowIndex && editCell?.colKey === col.key
                      const isReadonly = col.type === "readonly" || col.type === "link" || readOnly
                      const w = colWidths[col.key] ?? DEFAULT_COL_WIDTH

                      return (
                        <td
                          key={col.key}
                          className={[
                            "border-r border-border relative overflow-hidden",
                            isEditing ? "p-0 ring-2 ring-primary ring-inset z-10" : "",
                            !isReadonly && !isEditing ? "cursor-pointer" : "",
                            isReadonly && col.type !== "link" ? "text-muted-foreground" : "",
                          ].filter(Boolean).join(" ")}
                          style={{ width: w, minWidth: 60, maxWidth: w }}
                          onClick={() => {
                            if (!isReadonly && !isEditing) startEdit(rowIndex, col.key, cellValue)
                          }}
                        >
                          {renderCell(rowIndex, col, cellValue, displayRow.data as T)}
                        </td>
                      )
                    })}

                    {/* Row actions */}
                    {canDelete && (
                      <td className="w-10 px-1 py-1">
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          {isPending && (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="h-6 px-2 text-xs text-green-600 hover:text-green-700 hover:bg-green-50"
                                  onClick={() => void commitPendingRow(pendingIndex)}
                                  disabled={isSaving}
                                >
                                  Save
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Save this row</TooltipContent>
                            </Tooltip>
                          )}
                          {onDelete && (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="h-6 w-6 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                                  onClick={() => void handleDelete(rowIndex)}
                                  disabled={isSaving}
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Delete row</TooltipContent>
                            </Tooltip>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* ── Footer ── */}
        <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
          <span className="flex items-center gap-2">
            <span>
              {rows.length}{totalCount != null && totalCount !== rows.length ? ` of ${totalCount}` : ""} row{rows.length !== 1 ? "s" : ""}
            </span>
            {pendingRows.length > 0 && (
              <span className="text-amber-600 dark:text-amber-400">
                + {pendingRows.length} pending
              </span>
            )}
            {sortKey && (
              <span className="text-primary/70">
                sorted by {columns.find(c => c.key === sortKey)?.label ?? sortKey} ({sortDir})
              </span>
            )}
          </span>
          <span className="flex items-center gap-3">
            {hasSelection && (
              <span className="font-medium text-foreground">{selectedRows.size} selected</span>
            )}
            <span className="text-muted-foreground/50">Click to edit · Tab/↑↓ to navigate · Ctrl+V paste from Excel</span>
          </span>
        </div>
      </div>
    </TooltipProvider>
  )
}
