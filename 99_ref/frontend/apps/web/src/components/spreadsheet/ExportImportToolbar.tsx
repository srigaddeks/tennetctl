"use client"

import React, { useRef, useState } from "react"
import {
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@kcontrol/ui"
import {
  Download,
  Upload,
  ChevronDown,
  FileDown,
  Loader2,
} from "lucide-react"

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type ExportFormat = "csv" | "json" | "xlsx"
export type TemplateFormat = "csv" | "xlsx"

export interface ExportImportToolbarProps {
  entityName: string
  onExport: (format: ExportFormat) => Promise<void>
  onImport: (file: File, dryRun: boolean) => Promise<void>
  onDownloadTemplate?: (format: TemplateFormat) => Promise<void>
  loading?: boolean
}

// ─────────────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────────────

export function ExportImportToolbar({
  entityName,
  onExport,
  onImport,
  onDownloadTemplate,
  loading = false,
}: ExportImportToolbarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dryRun, setDryRun] = useState(true)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [exporting, setExporting] = useState(false)
  const [importing, setImporting] = useState(false)
  const [downloadingTemplate, setDownloadingTemplate] = useState(false)

  const isBusy = loading || exporting || importing || downloadingTemplate

  const handleExport = async (format: ExportFormat) => {
    setExporting(true)
    try {
      await onExport(format)
    } finally {
      setExporting(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null
    setSelectedFile(file)
    // Reset input so the same file can be re-selected
    e.target.value = ""
  }

  const handleImport = async () => {
    if (!selectedFile) return
    setImporting(true)
    try {
      await onImport(selectedFile, dryRun)
      setSelectedFile(null)
    } finally {
      setImporting(false)
    }
  }

  const handleDownloadTemplate = async (format: TemplateFormat) => {
    if (!onDownloadTemplate) return
    setDownloadingTemplate(true)
    try {
      await onDownloadTemplate(format)
    } finally {
      setDownloadingTemplate(false)
    }
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* ── Export dropdown ── */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            size="sm"
            variant="outline"
            disabled={isBusy}
            className="gap-1"
          >
            {exporting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Download className="h-3.5 w-3.5" />
            )}
            Export
            <ChevronDown className="h-3 w-3 ml-0.5 opacity-60" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem
            onClick={() => void handleExport("csv")}
            className="gap-2"
          >
            <FileDown className="h-4 w-4" />
            Export as CSV
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => void handleExport("xlsx")}
            className="gap-2"
          >
            <FileDown className="h-4 w-4" />
            Export as Excel (.xlsx)
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => void handleExport("json")}
            className="gap-2"
          >
            <FileDown className="h-4 w-4" />
            Export as JSON
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* ── Import section ── */}
      <div className="flex items-center gap-1.5">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json,.xlsx"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* File picker button */}
        <Button
          size="sm"
          variant="outline"
          disabled={isBusy}
          onClick={() => fileInputRef.current?.click()}
          className="gap-1"
        >
          <Upload className="h-3.5 w-3.5" />
          {selectedFile ? selectedFile.name : `Import ${entityName}`}
        </Button>

        {/* Dry run checkbox */}
        <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer select-none whitespace-nowrap">
          <input
            type="checkbox"
            checked={dryRun}
            onChange={(e) => setDryRun(e.target.checked)}
            className="h-3.5 w-3.5 rounded"
          />
          Dry run
        </label>

        {/* Upload button — only shown when a file is selected */}
        {selectedFile && (
          <Button
            size="sm"
            disabled={isBusy}
            onClick={() => void handleImport()}
            className="gap-1"
          >
            {importing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Upload className="h-3.5 w-3.5" />
            )}
            {dryRun ? "Preview" : "Upload"}
          </Button>
        )}
      </div>

      {/* ── Download template ── */}
      {onDownloadTemplate && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              disabled={isBusy}
              className="text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground transition-colors disabled:opacity-50 disabled:pointer-events-none flex items-center gap-1"
            >
              {downloadingTemplate ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : null}
              Download template
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuItem
              onClick={() => void handleDownloadTemplate("csv")}
              className="gap-2"
            >
              <FileDown className="h-4 w-4" />
              CSV template
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => void handleDownloadTemplate("xlsx")}
              className="gap-2"
            >
              <FileDown className="h-4 w-4" />
              Excel template (.xlsx)
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  )
}
