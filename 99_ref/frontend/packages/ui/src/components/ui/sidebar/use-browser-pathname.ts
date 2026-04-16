"use client"

import * as React from "react"

const PATHNAME_CHANGE_EVENT = "kcontrol:pathname-change"

let historyPatched = false
let pathnameDispatchQueued = false

function normalizePath(path: string): string {
  if (!path) return "/"
  return path.length > 1 && path.endsWith("/") ? path.slice(0, -1) : path
}

function dispatchPathnameChange() {
  if (pathnameDispatchQueued) return

  pathnameDispatchQueued = true

  window.setTimeout(() => {
    pathnameDispatchQueued = false
    window.dispatchEvent(new Event(PATHNAME_CHANGE_EVENT))
  }, 0)
}

function patchHistoryMethods() {
  if (historyPatched || typeof window === "undefined") return

  historyPatched = true

  for (const method of ["pushState", "replaceState"] as const) {
    const original = window.history[method]
    const wrapped = function (this: History, ...args: Parameters<History[typeof method]>) {
      const result = original.apply(this, args)
      dispatchPathnameChange()
      return result
    }

    window.history[method] = wrapped as History[typeof method]
  }
}

function subscribe(onStoreChange: () => void) {
  if (typeof window === "undefined") return () => undefined

  patchHistoryMethods()

  window.addEventListener(PATHNAME_CHANGE_EVENT, onStoreChange)
  window.addEventListener("popstate", onStoreChange)
  window.addEventListener("hashchange", onStoreChange)

  return () => {
    window.removeEventListener(PATHNAME_CHANGE_EVENT, onStoreChange)
    window.removeEventListener("popstate", onStoreChange)
    window.removeEventListener("hashchange", onStoreChange)
  }
}

function getBrowserPathname(): string {
  if (typeof window === "undefined") return "/"
  return normalizePath(window.location.pathname || "/")
}

export function useBrowserPathname(controlledPath?: string): string {
  const browserPathname = React.useSyncExternalStore(subscribe, getBrowserPathname, () => "/")
  return normalizePath(controlledPath ?? browserPathname)
}
