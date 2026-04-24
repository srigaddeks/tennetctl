"use client";

import Link from "next/link";

export default function QualityLandingPage() {
  return (
    <div className="max-w-5xl">
      <div className="mb-8">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Quality</h1>
        <p className="mt-2 max-w-xl text-sm ">
          Define reusable QC checkpoints and record append-only check events
          across pre-production, in-production, post-production, FSSAI, and
          receiving stages.
        </p>
      </div>

      <ul className="grid max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
        <li>
          <Link
            href="/quality/checkpoints"
            className="block rounded border p-4 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Checkpoints</div>
            <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Reusable QC definitions — per recipe step, raw material, kitchen,
              product, or universal.
            </div>
          </Link>
        </li>
        <li>
          <Link
            href="/quality/checks"
            className="block rounded border p-4 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Recent Checks</div>
            <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Append-only event feed of performed QC checks.
            </div>
          </Link>
        </li>
      </ul>
    </div>
  );
}
