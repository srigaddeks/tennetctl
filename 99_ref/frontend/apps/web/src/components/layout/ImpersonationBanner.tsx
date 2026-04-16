"use client"

import { useEffect, useState, useCallback } from "react"
import { X, Loader2, AlertTriangle } from "lucide-react"
import { getImpersonationStatus, endImpersonation } from "@/lib/api/admin"
import { clearAccessToken } from "@/lib/api/apiClient"
import type { ImpersonationStatusResponse } from "@/lib/types/admin"

interface ImpTargetInfo {
  email: string | null
  username: string | null
  user_id: string
}

export function ImpersonationBanner() {
  const [status, setStatus] = useState<ImpersonationStatusResponse | null>(null)
  const [target, setTarget] = useState<ImpTargetInfo | null>(null)
  const [ending, setEnding] = useState(false)
  const [checked, setChecked] = useState(false)

  const check = useCallback(async () => {
    try {
      const s = await getImpersonationStatus()
      if (s.is_impersonating) {
        setStatus(s)
        // Read target info stored before page reload
        try {
          const stored = sessionStorage.getItem("kc_imp_target")
          if (stored) setTarget(JSON.parse(stored))
        } catch {}
      } else {
        setStatus(null)
        sessionStorage.removeItem("kc_imp_target")
      }
    } catch {
      setStatus(null)
    } finally {
      setChecked(true)
    }
  }, [])

  useEffect(() => { check() }, [check])

  async function doEnd() {
    setEnding(true)
    try {
      // 1. Call backend to properly revoke the impersonation session (uses current impersonation token)
      await endImpersonation()
      // 2. Swap cookies: restore admin's refresh token, clear impersonation cookie
      await fetch("/api/auth/end-impersonation", { method: "POST" })
      sessionStorage.removeItem("kc_imp_target")
      clearAccessToken()
      window.location.href = "/dashboard"
    } catch {
      // If backend end fails, still try cookie swap so admin can recover
      await fetch("/api/auth/end-impersonation", { method: "POST" }).catch(() => {})
      sessionStorage.removeItem("kc_imp_target")
      clearAccessToken()
      window.location.href = "/dashboard"
    }
  }

  if (!checked || !status) return null

  const targetLabel = target?.email ?? target?.username ?? status.target_user_id?.slice(0, 8) + "…"

  return (
    <div className="flex items-center justify-between gap-3 bg-red-600 px-4 py-1.5 text-white text-xs font-medium z-50 shrink-0">
      <div className="flex items-center gap-2 min-w-0 flex-wrap">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-red-200" />
        <span className="text-red-100 font-semibold shrink-0 uppercase tracking-wide text-[10px]">Impersonating</span>
        <span className="text-red-200 shrink-0">·</span>
        <span className="shrink-0">
          Viewing as <span className="font-bold text-white">{targetLabel}</span>
        </span>
        {status.expires_at && (
          <>
            <span className="text-red-200 shrink-0">·</span>
            <span className="text-red-300 font-normal shrink-0">
              session expires {new Date(status.expires_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </>
        )}
      </div>
      <button
        type="button"
        onClick={doEnd}
        disabled={ending}
        className="flex items-center gap-1.5 rounded-md border border-white/40 bg-white/15 hover:bg-white/25 px-3 py-1 text-xs font-semibold text-white transition-colors disabled:opacity-60 shrink-0"
      >
        {ending ? <Loader2 className="h-3 w-3 animate-spin" /> : <X className="h-3 w-3" />}
        {ending ? "Ending…" : "End Impersonation"}
      </button>
    </div>
  )
}
