"use client"

import { useState, useRef } from "react"
import {
  Button,
  Input,
  Label,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@kcontrol/ui"
import {
  MessageSquarePlus,
  Loader2,
  CheckCircle2,
  Paperclip,
  X,
} from "lucide-react"
import { createTicket, getFeedbackDimensions } from "@/lib/api/feedback"
import { uploadAttachment } from "@/lib/api/attachments"
import type { TicketDimensionsResponse, CreateTicketRequest } from "@/lib/api/feedback"

const MAX_FILES = 5
const MAX_FILE_SIZE_MB = 25

export function QuickFeedbackWidget() {
  const [open, setOpen] = useState(false)
  const [dimensions, setDimensions] = useState<TicketDimensionsResponse | null>(null)
  const [loadingDims, setLoadingDims] = useState(false)
  const [typeCode, setTypeCode] = useState("general_feedback")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [files, setFiles] = useState<File[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function handleOpen() {
    setOpen(true)
    if (!dimensions) {
      setLoadingDims(true)
      try {
        const dims = await getFeedbackDimensions()
        setDimensions(dims)
      } catch {
        // non-fatal
      } finally {
        setLoadingDims(false)
      }
    }
  }

  function handleClose() {
    setOpen(false)
    // Reset after close animation
    setTimeout(() => {
      setTitle("")
      setDescription("")
      setTypeCode("general_feedback")
      setFiles([])
      setError(null)
      setSubmitted(false)
    }, 200)
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(e.target.files ?? [])
    if (selected.length === 0) return

    const oversized = selected.find((f) => f.size > MAX_FILE_SIZE_MB * 1024 * 1024)
    if (oversized) {
      setError(`File "${oversized.name}" exceeds ${MAX_FILE_SIZE_MB}MB limit.`)
      return
    }

    const combined = [...files, ...selected].slice(0, MAX_FILES)
    setFiles(combined)
    if (files.length + selected.length > MAX_FILES) {
      setError(`Maximum ${MAX_FILES} files allowed.`)
    }
    // Reset input so re-selecting same file works
    e.target.value = ""
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  async function handleSubmit() {
    if (!title.trim() || !description.trim()) {
      setError("Title and description are required.")
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const body: CreateTicketRequest = {
        ticket_type_code: typeCode,
        title: title.trim(),
        description: description.trim(),
        context_url: typeof window !== "undefined" ? window.location.href : null,
      }
      const ticket = await createTicket(body)

      // Upload attachments (best-effort — ticket is already created)
      if (files.length > 0) {
        const uploadErrors: string[] = []
        for (const file of files) {
          try {
            await uploadAttachment("feedback_ticket", ticket.id, file)
          } catch {
            uploadErrors.push(file.name)
          }
        }
        if (uploadErrors.length > 0) {
          setError(`Ticket created but failed to upload: ${uploadErrors.join(", ")}`)
          setSubmitted(true)
          return
        }
      }

      setSubmitted(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit feedback")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      {/* Floating button */}
      <div className="fixed bottom-6 right-6 z-40">
        <Button
          onClick={handleOpen}
          size="sm"
          className="rounded-full shadow-lg gap-2 pr-4"
        >
          <MessageSquarePlus className="h-4 w-4" />
          Feedback
        </Button>
      </div>

      <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
        <DialogContent className="max-w-md">
          {submitted ? (
            <>
              <DialogHeader>
                <DialogTitle>Thank you!</DialogTitle>
                <DialogDescription>
                  Your feedback has been submitted. We'll review it and get back to you.
                </DialogDescription>
              </DialogHeader>
              <div className="flex flex-col items-center py-6 gap-3">
                <CheckCircle2 className="h-12 w-12 text-emerald-500" />
                <p className="text-sm text-muted-foreground text-center">
                  You can track your submission in{" "}
                  <a href="/feedback" className="text-primary underline">
                    Feedback &amp; Support
                  </a>
                  .
                </p>
              </div>
              <DialogFooter>
                <Button onClick={handleClose}>Done</Button>
              </DialogFooter>
            </>
          ) : (
            <>
              <DialogHeader>
                <DialogTitle>Quick Feedback</DialogTitle>
                <DialogDescription>
                  Share feedback or report an issue. Takes 30 seconds.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 py-2">
                {error && (
                  <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <div className="space-y-1.5">
                  <Label>Type</Label>
                  {loadingDims ? (
                    <div className="h-9 rounded-md border border-input bg-muted animate-pulse" />
                  ) : (
                    <select
                      className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                      value={typeCode}
                      onChange={(e) => setTypeCode(e.target.value)}
                    >
                      {(dimensions?.ticket_types ?? [
                        { code: "general_feedback", name: "General Feedback" },
                        { code: "bug_report", name: "Bug Report" },
                        { code: "feature_request", name: "Feature Request" },
                        { code: "service_issue", name: "Service Issue" },
                        { code: "security_concern", name: "Security Concern" },
                      ] as { code: string; name: string }[])
                        .filter((t) => !("is_active" in t) || (t as { is_active: boolean }).is_active)
                        .map((t) => (
                          <option key={t.code} value={t.code}>
                            {t.name}
                          </option>
                        ))}
                    </select>
                  )}
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="qf-title">Title <span className="text-destructive">*</span></Label>
                  <Input
                    id="qf-title"
                    placeholder="Brief summary"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    maxLength={300}
                    autoFocus
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="qf-desc">Description <span className="text-destructive">*</span></Label>
                  <textarea
                    id="qf-desc"
                    className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="What happened? What did you expect?"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>

                {/* Attachments */}
                <div className="space-y-1.5">
                  <Label>Attachments</Label>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={handleFileSelect}
                    accept="image/*,.pdf,.doc,.docx,.txt,.csv,.json,.xml,.zip,.yaml,.yml,.md,.rtf"
                  />
                  {files.length > 0 && (
                    <div className="space-y-1">
                      {files.map((f, i) => (
                        <div
                          key={`${f.name}-${i}`}
                          className="flex items-center gap-2 rounded-md border border-input bg-muted/50 px-2 py-1 text-xs"
                        >
                          <Paperclip className="h-3 w-3 shrink-0 text-muted-foreground" />
                          <span className="truncate flex-1">{f.name}</span>
                          <span className="text-muted-foreground shrink-0">
                            {f.size < 1024 * 1024
                              ? `${Math.round(f.size / 1024)}KB`
                              : `${(f.size / (1024 * 1024)).toFixed(1)}MB`}
                          </span>
                          <button
                            type="button"
                            onClick={() => removeFile(i)}
                            className="shrink-0 rounded p-0.5 hover:bg-muted"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  {files.length < MAX_FILES && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-xs"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Paperclip className="h-3 w-3" />
                      {files.length === 0 ? "Attach files" : "Add more"}
                    </Button>
                  )}
                  <p className="text-[11px] text-muted-foreground">
                    Up to {MAX_FILES} files, {MAX_FILE_SIZE_MB}MB each. Screenshots, logs, documents.
                  </p>
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={handleClose} disabled={submitting}>
                  Cancel
                </Button>
                <Button onClick={handleSubmit} disabled={submitting}>
                  {submitting ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <MessageSquarePlus className="h-4 w-4 mr-2" />
                  )}
                  Submit
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
