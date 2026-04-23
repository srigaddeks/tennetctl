"use client";
import { useState } from "react";

type FieldProps = {
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  required?: boolean;
  autoFocus?: boolean;
  autoComplete?: string;
  placeholder?: string;
  minLength?: number;
  hint?: string;
  error?: string | null;
};

export function Field({
  label, type = "text", value, onChange, required, autoFocus,
  autoComplete, placeholder, minLength, hint, error,
}: FieldProps) {
  return (
    <label className="block">
      <span className="kicker block mb-1">{label}</span>
      <input
        className={`input ${error ? "!border-b-[color:var(--ember-deep)]" : ""}`}
        type={type} value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required} autoFocus={autoFocus}
        autoComplete={autoComplete} placeholder={placeholder}
        minLength={minLength}
      />
      {error ? (
        <p className="mt-1 mono text-[11px] text-[color:var(--ember-deep)]">× {error}</p>
      ) : hint ? (
        <p className="mt-1 text-[11px] text-[color:var(--ink-40)]">{hint}</p>
      ) : null}
    </label>
  );
}

export function PasswordField({
  label, value, onChange, autoComplete = "current-password",
  autoFocus, minLength = 8, hint, error, showStrength = false,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  autoComplete?: string;
  autoFocus?: boolean;
  minLength?: number;
  hint?: string;
  error?: string | null;
  showStrength?: boolean;
}) {
  const [show, setShow] = useState(false);
  const strength = showStrength ? passwordStrength(value) : null;

  return (
    <label className="block">
      <span className="kicker block mb-1">{label}</span>
      <div className="relative">
        <input
          className={`input pr-12 ${error ? "!border-b-[color:var(--ember-deep)]" : ""}`}
          type={show ? "text" : "password"}
          value={value} onChange={(e) => onChange(e.target.value)}
          required autoFocus={autoFocus}
          autoComplete={autoComplete} minLength={minLength}
        />
        <button
          type="button" onClick={() => setShow(s => !s)}
          className="absolute right-0 bottom-2 mono text-[10px] tracking-widest uppercase text-[color:var(--ink-40)] hover:text-[color:var(--ink)] px-1"
          tabIndex={-1}
        >
          {show ? "hide" : "show"}
        </button>
      </div>
      {strength && value.length > 0 && (
        <div className="mt-2 flex items-center gap-2" aria-live="polite">
          <div className="flex gap-1 flex-1">
            {[0, 1, 2, 3].map(i => (
              <div
                key={i}
                className="h-[3px] flex-1 rounded-full transition-all"
                style={{
                  background: i < strength.bars ? strength.color : "var(--paper-edge)",
                }}
              />
            ))}
          </div>
          <span className="mono text-[10px] uppercase tracking-widest" style={{ color: strength.color }}>
            {strength.label}
          </span>
        </div>
      )}
      {error ? (
        <p className="mt-2 mono text-[11px] text-[color:var(--ember-deep)]">× {error}</p>
      ) : hint ? (
        <p className="mt-1 text-[11px] text-[color:var(--ink-40)]">{hint}</p>
      ) : null}
    </label>
  );
}

function passwordStrength(v: string): { bars: number; label: string; color: string } {
  let score = 0;
  if (v.length >= 8) score++;
  if (v.length >= 12) score++;
  if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++;
  if (/[0-9]/.test(v) && /[^A-Za-z0-9]/.test(v)) score++;
  const table = [
    { bars: 1, label: "weak",     color: "#9C2A07" },
    { bars: 2, label: "fair",     color: "#B88024" },
    { bars: 3, label: "good",     color: "#556A3D" },
    { bars: 4, label: "strong",   color: "#556A3D" },
  ];
  if (score === 0) return { bars: 0, label: "—", color: "var(--ink-40)" };
  return table[score - 1];
}

export function Spinner({ size = 14 }: { size?: number }) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24"
      className="animate-spin inline-block mr-1.5 align-[-2px]"
      aria-hidden
    >
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3"
              strokeLinecap="round" strokeDasharray="14 36" fill="none" opacity="0.9" />
    </svg>
  );
}
