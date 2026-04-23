"use client";

import Link from "next/link";
import { KeyRound, SlidersHorizontal, ShieldAlert, ArrowRight, Lock } from "lucide-react";

export default function VaultIndex() {
  return (
    <div className="flex-1 overflow-y-auto px-8 py-10" style={{ background: "var(--bg-base)" }}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl"
            style={{
              background: "var(--warning-muted)",
              border: "1px solid var(--warning)",
            }}
          >
            <Lock className="h-5 w-5" style={{ color: "var(--warning)" }} />
          </div>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
              Vault
            </h1>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Envelope-encrypted secrets and typed runtime configuration
            </p>
          </div>
        </div>

        {/* Warning banner */}
        <div
          className="flex items-start gap-3 rounded-xl px-4 py-3 mt-4"
          style={{
            background: "var(--warning-muted)",
            border: "1px solid var(--warning)",
          }}
        >
          <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" style={{ color: "var(--warning)" }} />
          <div>
            <p className="text-xs font-semibold" style={{ color: "var(--warning)" }}>
              Sensitive area — all access is audit-logged
            </p>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>
              Secret values are shown exactly once at create or rotate and never re-displayed. Config values are plaintext and always visible.
            </p>
          </div>
        </div>
      </div>

      {/* Hub cards */}
      <div className="grid gap-5 sm:grid-cols-2 max-w-2xl">
        {/* Secrets */}
        <Link
          href="/vault/secrets"
          className="group relative flex flex-col gap-4 rounded-2xl p-6 transition-all duration-150"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.border = "1px solid var(--warning)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.border = "1px solid var(--border)";
          }}
        >
          {/* Amber accent bar */}
          <div
            className="absolute left-0 top-4 bottom-4 w-0.5 rounded-full"
            style={{ background: "var(--warning)" }}
          />

          <div className="flex items-start justify-between">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl"
              style={{
                background: "var(--warning-muted)",
                border: "1px solid var(--warning)",
              }}
            >
              <KeyRound className="h-5 w-5" style={{ color: "var(--warning)" }} />
            </div>
            <ArrowRight
              className="h-4 w-4 transition-transform group-hover:translate-x-1"
              style={{ color: "var(--text-muted)" }}
            />
          </div>

          <div>
            <h2 className="text-base font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
              Secrets
            </h2>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Envelope-encrypted sensitive values. Revealed exactly once at creation or rotation. Keys, tokens, peppers, credentials.
            </p>
          </div>

          <div className="flex items-center gap-4 pt-1">
            <div className="text-xs" style={{ color: "var(--text-muted)" }}>
              <span
                className="inline-block rounded-full px-2 py-0.5 mr-1.5 text-[10px] font-medium"
                style={{ background: "var(--warning-muted)", color: "var(--warning)", border: "1px solid var(--warning)" }}
              >
                global
              </span>
              <span
                className="inline-block rounded-full px-2 py-0.5 mr-1.5 text-[10px] font-medium"
                style={{ background: "var(--bg-elevated)", color: "var(--accent)", border: "1px solid var(--accent-dim)" }}
              >
                org
              </span>
              <span
                className="inline-block rounded-full px-2 py-0.5 text-[10px] font-medium"
                style={{ background: "var(--bg-elevated)", color: "#a855f7", border: "1px solid #3b0764" }}
              >
                workspace
              </span>
            </div>
          </div>
        </Link>

        {/* Configs */}
        <Link
          href="/vault/configs"
          className="group relative flex flex-col gap-4 rounded-2xl p-6 transition-all duration-150"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.border = "1px solid var(--accent)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.border = "1px solid var(--border)";
          }}
        >
          {/* Blue accent bar */}
          <div
            className="absolute left-0 top-4 bottom-4 w-0.5 rounded-full"
            style={{ background: "var(--accent)" }}
          />

          <div className="flex items-start justify-between">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl"
              style={{
                background: "var(--accent-muted)",
                border: "1px solid var(--accent-dim)",
              }}
            >
              <SlidersHorizontal className="h-5 w-5" style={{ color: "var(--accent)" }} />
            </div>
            <ArrowRight
              className="h-4 w-4 transition-transform group-hover:translate-x-1"
              style={{ color: "var(--text-muted)" }}
            />
          </div>

          <div>
            <h2 className="text-base font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
              Configs
            </h2>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Plaintext typed runtime configuration. Always readable and editable. Boolean, string, number, or JSON values.
            </p>
          </div>

          <div className="flex items-center gap-4 pt-1">
            <div className="text-xs" style={{ color: "var(--text-muted)" }}>
              <span
                className="inline-block rounded-full px-2 py-0.5 mr-1.5 text-[10px] font-medium"
                style={{ background: "var(--success-muted)", color: "var(--success)", border: "1px solid var(--success)" }}
              >
                boolean
              </span>
              <span
                className="inline-block rounded-full px-2 py-0.5 mr-1.5 text-[10px] font-medium"
                style={{ background: "var(--accent-muted)", color: "var(--accent)", border: "1px solid var(--accent-dim)" }}
              >
                string
              </span>
              <span
                className="inline-block rounded-full px-2 py-0.5 text-[10px] font-medium"
                style={{ background: "var(--warning-muted)", color: "var(--warning)", border: "1px solid var(--warning)" }}
              >
                number
              </span>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}
