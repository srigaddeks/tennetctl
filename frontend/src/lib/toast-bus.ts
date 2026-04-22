/**
 * Module-level singleton that bridges the MutationCache (constructed outside
 * React) to the ToastProvider (lives inside React).
 *
 * ToastProvider calls `registerToastFn` once on mount.
 * MutationCache.onError calls `busToast` — a no-op until registration happens.
 */

type ToastFn = (message: string, kind?: "success" | "error" | "info" | "warning") => void;

let _toastFn: ToastFn | null = null;

export function registerToastFn(fn: ToastFn): void {
  _toastFn = fn;
}

export function unregisterToastFn(): void {
  _toastFn = null;
}

export function busToast(message: string, kind: "success" | "error" | "info" | "warning" = "error"): void {
  if (_toastFn) {
    _toastFn(message, kind);
  } else {
    console.error("[mutation error]", message);
  }
}
