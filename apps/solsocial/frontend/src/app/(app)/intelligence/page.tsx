"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { tc } from "@/lib/api";
import type { ListPage, SocialCapture } from "@/types/api";

// ── Platform + type config ────────────────────────────────────────────────────

const PLATFORM_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  linkedin:  { label: "LinkedIn",   icon: "in", color: "#0A66C2" },
  x:         { label: "X",          icon: "𝕏",  color: "#000000" },
  twitter:   { label: "Twitter",    icon: "𝕏",  color: "#1D9BF0" },
  instagram: { label: "Instagram",  icon: "ig", color: "#E1306C" },
};

const TYPE_LABELS: Record<string, string> = {
  feed_post_seen:     "Saw in feed",
  own_post_published: "Own post",
  comment_seen:       "Comment seen",
  own_comment:        "Own comment",
  profile_viewed:     "Profile viewed",
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function fmt(n: number | null): string {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

// ── Streaming pulse indicator ─────────────────────────────────────────────────

function StreamPulse({ active }: { active: boolean }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span style={{
        width: 8, height: 8, borderRadius: "50%",
        background: active ? "#556A3D" : "var(--ink-20)",
        boxShadow: active ? "0 0 0 0 rgba(85,106,61,0.4)" : "none",
        animation: active ? "stream-pulse 1.5s ease-out infinite" : "none",
        display: "inline-block",
      }} />
      <style>{`
        @keyframes stream-pulse {
          0%  { box-shadow: 0 0 0 0 rgba(85,106,61,0.5); }
          70% { box-shadow: 0 0 0 8px rgba(85,106,61,0); }
          100%{ box-shadow: 0 0 0 0 rgba(85,106,61,0); }
        }
      `}</style>
      <span className="mono" style={{ fontSize: 11, color: active ? "var(--sage)" : "var(--ink-40)" }}>
        {active ? "streaming" : "idle"}
      </span>
    </span>
  );
}

// ── Platform icon pill ────────────────────────────────────────────────────────

function PlatformBadge({ platform }: { platform: string }) {
  const cfg = PLATFORM_CONFIG[platform] ?? { label: platform, icon: "?", color: "#888" };
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 7px", borderRadius: 3,
      background: cfg.color + "18", border: `1px solid ${cfg.color}40`,
      fontSize: 11, fontWeight: 600, color: cfg.color,
      fontFamily: "IBM Plex Mono, monospace",
    }}>
      {cfg.icon} {cfg.label}
    </span>
  );
}

// ── Type badge ────────────────────────────────────────────────────────────────

function TypeBadge({ type, isOwn }: { type: string; isOwn: boolean }) {
  const label = TYPE_LABELS[type] ?? type;
  return (
    <span style={{
      fontSize: 11,
      color: isOwn ? "var(--ember)" : "var(--ink-40)",
      fontWeight: isOwn ? 600 : 400,
    }}>
      {isOwn ? "⬆ " : ""}{label}
    </span>
  );
}

// ── Stat card ─────────────────────────────────────────────────────────────────

function Stat({ value, label, sub }: { value: string | number; label: string; sub?: string }) {
  return (
    <div style={{
      padding: "14px 18px",
      background: "var(--paper-deep)",
      border: "1px solid var(--rule)",
      borderRadius: 4,
    }}>
      <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--ink-40)", marginTop: 4 }}>
        {label}
      </div>
      {sub && <div style={{ fontSize: 11, color: "var(--ink-40)", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function IntelligencePage() {
  const [platform, setPlatform] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [ownOnly, setOwnOnly] = useState(false);
  const [limit] = useState(100);

  // Auto-refresh every 15s to show streaming data
  const { data, dataUpdatedAt, isLoading, refetch } = useQuery({
    queryKey: ["captures", platform, typeFilter, ownOnly],
    queryFn: () => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (platform !== "all") params.set("platform", platform);
      if (typeFilter !== "all") params.set("type", typeFilter);
      if (ownOnly) params.set("is_own", "true");
      return tc.get<ListPage<SocialCapture>>(`/v1/social/captures?${params}`);
    },
    refetchInterval: 15_000,
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  // Streaming active = data updated in last 2 minutes
  const streamActive = dataUpdatedAt > 0 && (Date.now() - dataUpdatedAt) < 120_000;

  // Stats computed from current items
  const byPlatform = items.reduce<Record<string, number>>((acc, c) => {
    acc[c.platform] = (acc[c.platform] ?? 0) + 1;
    return acc;
  }, {});
  const ownCount = items.filter(c => c.is_own).length;
  const todayItems = items.filter(c => {
    const today = new Date().toISOString().slice(0, 10);
    return c.observed_at.slice(0, 10) === today;
  });

  const PLATFORMS = ["all", "linkedin", "x", "instagram"];
  const TYPES = ["all", "feed_post_seen", "own_post_published", "comment_seen", "own_comment"];

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div style={{ marginBottom: 24, display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 className="display" style={{ fontSize: 32 }}>Feed Intelligence</h1>
          <p style={{ color: "var(--ink-40)", marginTop: 6, fontSize: 14 }}>
            Everything your browser extension has collected — posts, engagements, profiles.
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6, paddingTop: 6 }}>
          <StreamPulse active={streamActive} />
          <button
            onClick={() => refetch()}
            style={{ fontSize: 11, color: "var(--ink-40)", background: "none", border: "none", cursor: "pointer", textDecoration: "underline" }}
          >
            refresh
          </button>
        </div>
      </div>

      {/* Stats strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 24 }}>
        <Stat value={total} label="Total captured" />
        <Stat value={todayItems.length} label="Today" />
        <Stat value={ownCount} label="Your posts" sub="own_post_published + own_comment" />
        <Stat
          value={Object.entries(byPlatform).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—"}
          label="Top platform"
          sub={`${Object.entries(byPlatform).sort((a, b) => b[1] - a[1])[0]?.[1] ?? 0} captures`}
        />
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 16, flexWrap: "wrap" }}>
        {/* Platform tabs */}
        <div style={{ display: "flex", gap: 2, background: "var(--paper-edge)", borderRadius: 4, padding: 2 }}>
          {PLATFORMS.map(p => (
            <button
              key={p}
              onClick={() => setPlatform(p)}
              style={{
                padding: "4px 12px", borderRadius: 3, border: "none", cursor: "pointer",
                fontSize: 12, fontWeight: platform === p ? 600 : 400,
                background: platform === p ? "var(--paper)" : "transparent",
                color: platform === p ? "var(--ink)" : "var(--ink-40)",
                boxShadow: platform === p ? "0 1px 2px rgba(0,0,0,0.08)" : "none",
              }}
            >
              {p === "all" ? "All platforms" : (PLATFORM_CONFIG[p]?.label ?? p)}
            </button>
          ))}
        </div>

        {/* Type select */}
        <select
          value={typeFilter}
          onChange={e => setTypeFilter(e.target.value)}
          style={{
            padding: "5px 10px", fontSize: 12, borderRadius: 4,
            border: "1px solid var(--rule)", background: "var(--paper)",
            color: "var(--ink)", cursor: "pointer",
          }}
        >
          <option value="all">All types</option>
          {TYPES.filter(t => t !== "all").map(t => (
            <option key={t} value={t}>{TYPE_LABELS[t] ?? t}</option>
          ))}
        </select>

        {/* Own only toggle */}
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={ownOnly}
            onChange={e => setOwnOnly(e.target.checked)}
            style={{ accentColor: "var(--ember)" }}
          />
          Own posts only
        </label>

        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--ink-40)" }} className="mono">
          {items.length} of {total} shown · auto-refreshes every 15s
        </span>
      </div>

      {/* Table */}
      {isLoading ? (
        <div style={{ textAlign: "center", padding: "48px 0", color: "var(--ink-40)" }}>Loading…</div>
      ) : items.length === 0 ? (
        <EmptyState />
      ) : (
        <div style={{ border: "1px solid var(--rule)", borderRadius: 4, overflow: "hidden" }}>
          {/* Table header */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "100px 130px 1fr 52px 52px 52px 52px 90px",
            padding: "8px 14px",
            background: "var(--paper-edge)",
            fontSize: 10,
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            color: "var(--ink-40)",
            fontWeight: 600,
            gap: 8,
          }}>
            <span>Platform</span>
            <span>Type</span>
            <span>Author · Content</span>
            <span style={{ textAlign: "right" }}>♥</span>
            <span style={{ textAlign: "right" }}>💬</span>
            <span style={{ textAlign: "right" }}>🔁</span>
            <span style={{ textAlign: "right" }}>👁</span>
            <span style={{ textAlign: "right" }}>When</span>
          </div>

          {/* Rows */}
          {items.map((c, i) => (
            <CaptureRow key={c.id} capture={c} even={i % 2 === 0} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Capture row ───────────────────────────────────────────────────────────────

function CaptureRow({ capture: c, even }: { capture: SocialCapture; even: boolean }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <div
        onClick={() => setExpanded(e => !e)}
        style={{
          display: "grid",
          gridTemplateColumns: "100px 130px 1fr 52px 52px 52px 52px 90px",
          padding: "9px 14px",
          gap: 8,
          alignItems: "center",
          background: even ? "var(--paper)" : "var(--paper-deep)",
          borderTop: "1px solid var(--rule)",
          cursor: "pointer",
          transition: "background 0.1s",
        }}
        onMouseEnter={e => (e.currentTarget.style.background = "rgba(220,75,25,0.04)")}
        onMouseLeave={e => (e.currentTarget.style.background = even ? "var(--paper)" : "var(--paper-deep)")}
      >
        <div><PlatformBadge platform={c.platform} /></div>
        <div><TypeBadge type={c.type} isOwn={c.is_own} /></div>
        <div style={{ overflow: "hidden" }}>
          {c.author_handle && (
            <span style={{ fontSize: 11, fontWeight: 600, color: "var(--ink-70)", marginRight: 6 }}>
              @{c.author_handle}
            </span>
          )}
          {c.text_excerpt && (
            <span style={{ fontSize: 12, color: "var(--ink-40)", fontStyle: c.is_own ? "normal" : "italic" }}>
              {c.text_excerpt.slice(0, 80)}{c.text_excerpt.length > 80 ? "…" : ""}
            </span>
          )}
        </div>
        <div className="mono" style={{ fontSize: 11, color: "var(--ink-40)", textAlign: "right" }}>{fmt(c.like_count)}</div>
        <div className="mono" style={{ fontSize: 11, color: "var(--ink-40)", textAlign: "right" }}>{fmt(c.reply_count)}</div>
        <div className="mono" style={{ fontSize: 11, color: "var(--ink-40)", textAlign: "right" }}>{fmt(c.repost_count)}</div>
        <div className="mono" style={{ fontSize: 11, color: "var(--ink-40)", textAlign: "right" }}>{fmt(c.view_count)}</div>
        <div className="mono" style={{ fontSize: 11, color: "var(--ink-40)", textAlign: "right" }}>{timeAgo(c.observed_at)}</div>
      </div>

      {expanded && (
        <div style={{
          padding: "10px 14px 12px 114px",
          background: "rgba(220,75,25,0.03)",
          borderTop: "1px dashed var(--rule)",
          fontSize: 12,
        }}>
          {c.text_excerpt && (
            <p style={{ color: "var(--ink-70)", marginBottom: 8, lineHeight: 1.5 }}>{c.text_excerpt}</p>
          )}
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            {c.url && (
              <a href={c.url} target="_blank" rel="noopener noreferrer"
                style={{ color: "var(--lapis)", fontSize: 11 }}>
                Open original ↗
              </a>
            )}
            <span className="mono" style={{ fontSize: 10, color: "var(--ink-20)" }}>
              {c.platform_post_id}
            </span>
            <span className="mono" style={{ fontSize: 10, color: "var(--ink-20)" }}>
              extractor: {c.extractor_version}
            </span>
            <span className="mono" style={{ fontSize: 10, color: "var(--ink-20)" }}>
              {new Date(c.observed_at).toLocaleString()}
            </span>
          </div>
        </div>
      )}
    </>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div style={{
      border: "1px solid var(--rule)", borderRadius: 4,
      padding: "48px 32px", textAlign: "center",
    }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>📡</div>
      <p className="display-italic" style={{ fontSize: 22, marginBottom: 8 }}>No captures yet</p>
      <p style={{ color: "var(--ink-40)", fontSize: 14, maxWidth: 380, margin: "0 auto" }}>
        Install the SolSocial browser extension, sign in, then browse LinkedIn or X.
        Posts you see will appear here automatically.
      </p>
      <div style={{
        marginTop: 20, padding: "10px 16px",
        background: "var(--paper-deep)", border: "1px solid var(--rule)",
        borderRadius: 4, display: "inline-block", textAlign: "left",
        fontSize: 12, fontFamily: "IBM Plex Mono, monospace",
        color: "var(--ink-40)",
      }}>
        Chrome → Load unpacked →<br />
        <span style={{ color: "var(--ink-70)" }}>extensions/solsocial-collector/</span>
      </div>
    </div>
  );
}
