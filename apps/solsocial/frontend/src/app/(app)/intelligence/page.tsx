"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { tc } from "@/lib/api";
import type {
  CaptureCounts,
  ListPage,
  MetricHistory,
  SocialCapture,
  TopAuthor,
  TopHashtag,
} from "@/types/api";

// ── Platform + type config ──────────────────────────────────────────────────

const PLATFORM_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  linkedin:  { label: "LinkedIn",  icon: "in", color: "#0A66C2" },
  x:         { label: "X",         icon: "𝕏",  color: "#000000" },
  twitter:   { label: "Twitter",   icon: "𝕏",  color: "#1D9BF0" },
  instagram: { label: "Instagram", icon: "ig", color: "#E1306C" },
};

const TYPE_LABELS: Record<string, string> = {
  feed_post_seen:       "in feed",
  own_post_published:   "published",
  comment_seen:         "comment",
  own_comment:          "my comment",
  profile_viewed:       "profile seen",
  article_seen:         "article",
  article_opened:       "article read",
  newsletter_seen:      "newsletter",
  company_viewed:       "company",
  profile_page_viewed:  "profile",
  job_post_seen:        "job",
  job_post_opened:      "job detail",
  poll_seen:            "poll",
  event_seen:           "event",
  hashtag_feed_seen:    "#hashtag",
  search_result_seen:   "search",
  reshare_seen:         "repost",
  reaction_detail:      "reactions",
  connection_suggested: "pymk",
  notification_seen:    "notification",
  live_broadcast_seen:  "live",
  quote_tweet_seen:     "quote tweet",
  thread_seen:          "thread",
  list_viewed:          "list",
  space_seen:           "space",
  community_seen:       "community",
};

const TYPE_CATEGORY: Record<
  string,
  "post" | "comment" | "profile" | "company" | "job" | "article" | "discovery" | "meta"
> = {
  feed_post_seen:       "post",
  own_post_published:   "post",
  reshare_seen:         "post",
  quote_tweet_seen:     "post",
  thread_seen:          "post",
  poll_seen:            "post",
  live_broadcast_seen:  "post",
  comment_seen:         "comment",
  own_comment:          "comment",
  profile_viewed:       "profile",
  profile_page_viewed:  "profile",
  company_viewed:       "company",
  job_post_seen:        "job",
  job_post_opened:      "job",
  article_seen:         "article",
  article_opened:       "article",
  newsletter_seen:      "article",
  event_seen:           "article",
  connection_suggested: "discovery",
  search_result_seen:   "discovery",
  hashtag_feed_seen:    "discovery",
  notification_seen:    "meta",
  reaction_detail:      "meta",
  list_viewed:          "meta",
  space_seen:           "meta",
  community_seen:       "meta",
};

const REACTION_ICON: Record<string, string> = {
  like: "👍",
  celebrate: "🎉",
  support: "🤝",
  love: "❤️",
  insightful: "💡",
  curious: "🤔",
  funny: "😄",
};

// ── Time helpers ────────────────────────────────────────────────────────────

function parseUtc(iso: string): Date {
  return new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : iso + "Z");
}

function timeAgo(iso: string): string {
  const diff = Date.now() - parseUtc(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 30) return `${d}d ago`;
  return parseUtc(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function formatLocal(iso: string): string {
  return parseUtc(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function fmt(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 10_000) return `${Math.round(n / 1000)}K`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

// ── raw_attrs accessors ─────────────────────────────────────────────────────

function attrStr(a: Record<string, unknown>, k: string): string | null {
  const v = a?.[k];
  return typeof v === "string" && v ? v : null;
}
function attrNum(a: Record<string, unknown>, k: string): number | null {
  const v = a?.[k];
  return typeof v === "number" ? v : null;
}
function attrArr<T = unknown>(a: Record<string, unknown>, k: string): T[] | null {
  const v = a?.[k];
  return Array.isArray(v) ? (v as T[]) : null;
}

// ── Atoms ───────────────────────────────────────────────────────────────────

function PlatformBadge({ platform }: { platform: string }) {
  const cfg = PLATFORM_CONFIG[platform] ?? { label: platform, icon: "?", color: "#888" };
  return (
    <span
      style={{
        display: "inline-flex", alignItems: "center", gap: 4,
        padding: "2px 7px", borderRadius: 3,
        background: cfg.color + "18", border: `1px solid ${cfg.color}40`,
        fontSize: 11, fontWeight: 600, color: cfg.color,
        fontFamily: "IBM Plex Mono, monospace",
      }}
    >
      {cfg.icon} {cfg.label}
    </span>
  );
}

function Pill({ children, color = "var(--ink-40)", bg = "var(--paper-deep)" }: { children: React.ReactNode; color?: string; bg?: string }) {
  return (
    <span
      className="mono"
      style={{
        fontSize: 10, padding: "2px 7px", borderRadius: 3,
        background: bg, border: "1px solid var(--rule)", color,
      }}
    >
      {children}
    </span>
  );
}

function Hashtag({ tag, onClick }: { tag: string; onClick?: (t: string) => void }) {
  return (
    <span
      onClick={() => onClick?.(tag)}
      style={{
        color: "var(--lapis)", fontSize: 11, cursor: onClick ? "pointer" : "default",
        marginRight: 6, fontFamily: "IBM Plex Mono, monospace",
      }}
    >
      #{tag}
    </span>
  );
}

function Mention({ handle, onClick }: { handle: string; onClick?: (h: string) => void }) {
  return (
    <span
      onClick={() => onClick?.(handle)}
      style={{
        color: "var(--ember-deep)", fontSize: 11, cursor: onClick ? "pointer" : "default",
        marginRight: 6, fontFamily: "IBM Plex Mono, monospace",
      }}
    >
      @{handle}
    </span>
  );
}

function Stat({ value, label, sub }: { value: string | number; label: string; sub?: string }) {
  return (
    <div style={{
      padding: "14px 18px", background: "var(--paper-deep)",
      border: "1px solid var(--rule)", borderRadius: 4,
    }}>
      <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--ink-40)", marginTop: 4 }}>
        {label}
      </div>
      {sub && <div style={{ fontSize: 11, color: "var(--ink-40)", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function StreamPulse({ active }: { active: boolean }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span style={{
        width: 8, height: 8, borderRadius: "50%",
        background: active ? "#556A3D" : "var(--ink-20)",
        animation: active ? "stream-pulse 1.5s ease-out infinite" : "none",
      }} />
      <style>{`
        @keyframes stream-pulse {
          0%   { box-shadow: 0 0 0 0 rgba(85,106,61,0.5); }
          70%  { box-shadow: 0 0 0 8px rgba(85,106,61,0); }
          100% { box-shadow: 0 0 0 0 rgba(85,106,61,0); }
        }
      `}</style>
      <span className="mono" style={{ fontSize: 11, color: active ? "var(--sage)" : "var(--ink-40)" }}>
        {active ? "streaming" : "idle"}
      </span>
    </span>
  );
}

// ── Card: post / reshare / poll / quote tweet / thread / live ───────────────

function PostCard({ capture, onTagClick, onAuthorClick }: {
  capture: SocialCapture;
  onTagClick: (t: string) => void;
  onAuthorClick: (h: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const a = (capture.raw_attrs ?? {}) as Record<string, unknown>;
  const fullText = attrStr(a, "full_text") || capture.text_excerpt || "";
  const headline = attrStr(a, "author_headline");
  const postedAt = attrStr(a, "posted_at") || capture.observed_at;
  const isSponsored = !!a.is_sponsored;
  const isReshare = !!a.is_reshare;
  const hashtags = attrArr<string>(a, "hashtags") ?? [];
  const mentions = attrArr<string>(a, "mentions") ?? [];
  const reactions = (a.reactions ?? {}) as Record<string, number>;
  const media = attrArr<{ kind: string; url: string; alt?: string }>(a, "media") ?? [];
  const poll = a.poll as { question?: string; total_votes?: number; options?: Array<{ label?: string; pct?: number }> } | undefined;
  const engagers = attrArr<string>(a, "engagers") ?? [];

  // Load comments on demand (child captures with parent_post_id == this URN)
  const shouldLoadComments = expanded;
  const { data: commentsData } = useQuery({
    queryKey: ["comments", capture.platform_post_id],
    enabled: shouldLoadComments,
    queryFn: async () => {
      const params = new URLSearchParams({
        type: "comment_seen", mention: "", limit: "50",
      });
      params.set("type", "comment_seen");
      const res = await tc.get<ListPage<SocialCapture>>(`/v1/social/captures?${params}`);
      // Filter client-side to only those whose raw_attrs.parent_post_id matches us
      return res.items.filter(c => {
        const parent = (c.raw_attrs as Record<string, unknown>)?.parent_post_id;
        return typeof parent === "string" && parent === capture.platform_post_id;
      });
    },
  });

  const { data: metricHistory } = useQuery<MetricHistory>({
    queryKey: ["metrics", capture.id],
    enabled: expanded,
    queryFn: () => tc.get<MetricHistory>(`/v1/social/captures/${capture.id}/metrics`),
  });

  return (
    <article
      style={{
        background: "var(--paper)",
        border: "1px solid var(--rule)",
        borderRadius: 6,
        marginBottom: 14,
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex", justifyContent: "space-between", alignItems: "flex-start",
          padding: "12px 16px 6px 16px", gap: 12,
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3, flexWrap: "wrap" }}>
            {capture.author_name && (
              <span style={{ fontSize: 14, fontWeight: 600, color: "var(--ink)" }}>
                {capture.author_name}
              </span>
            )}
            {capture.author_handle && (
              <a
                href="#"
                onClick={(e) => { e.preventDefault(); onAuthorClick(capture.author_handle!); }}
                style={{ fontSize: 12, color: "var(--ink-40)", textDecoration: "none" }}
              >
                @{capture.author_handle}
              </a>
            )}
            {capture.is_own && <Pill color="var(--ember-deep)" bg="rgba(220,75,25,0.08)">you</Pill>}
            {isSponsored && <Pill color="#B4883A" bg="rgba(180,136,58,0.08)">sponsored</Pill>}
            {isReshare && <Pill>repost</Pill>}
          </div>
          {headline && (
            <div style={{ fontSize: 11, color: "var(--ink-40)", marginBottom: 3 }}>{headline}</div>
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "var(--ink-40)" }}>
            <PlatformBadge platform={capture.platform} />
            <span>{TYPE_LABELS[capture.type] ?? capture.type}</span>
            <span>·</span>
            <span title={formatLocal(postedAt)}>{timeAgo(postedAt)}</span>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {capture.url && (
            <a
              href={capture.url}
              target="_blank" rel="noopener noreferrer"
              style={{ fontSize: 11, color: "var(--lapis)", textDecoration: "none" }}
            >
              open ↗
            </a>
          )}
        </div>
      </header>

      {/* Body */}
      {fullText && (
        <div
          style={{
            padding: "4px 16px 10px 16px", color: "var(--ink)",
            fontSize: 14, lineHeight: 1.5, whiteSpace: "pre-wrap",
          }}
        >
          {fullText}
        </div>
      )}

      {/* Media */}
      {media.length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: media.length === 1 ? "1fr" : "repeat(2, 1fr)",
            gap: 4, padding: "0 16px 8px 16px",
          }}
        >
          {media.slice(0, 4).map((m, i) => (
            <div
              key={i}
              style={{
                background: "var(--paper-deep)",
                border: "1px solid var(--rule)",
                borderRadius: 4,
                padding: 0,
                overflow: "hidden",
                aspectRatio: "16 / 9",
                position: "relative",
              }}
            >
              {/* NOTE: we never fetch media from LinkedIn/X directly; we just
                  display the URL LinkedIn already gave the user's browser.
                  If it 403s, the browser simply shows nothing — no detection signal. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={m.url}
                alt={m.alt || ""}
                referrerPolicy="no-referrer"
                style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                onError={(e) => ((e.target as HTMLImageElement).style.display = "none")}
              />
              {m.kind === "video" && (
                <div style={{
                  position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)",
                  fontSize: 36, color: "white", textShadow: "0 2px 6px rgba(0,0,0,0.5)",
                }}>▶</div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Poll */}
      {poll?.question && (
        <div style={{ padding: "0 16px 10px 16px" }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--ink-70)", marginBottom: 6 }}>
            {poll.question}
          </div>
          {(poll.options ?? []).map((o, i) => (
            <div key={i} style={{ marginBottom: 4 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--ink-70)" }}>
                <span>{(o.label ?? "").replace(/\s*\d+%\s*$/, "")}</span>
                <span className="mono">{o.pct ?? 0}%</span>
              </div>
              <div style={{ height: 4, background: "var(--rule)", borderRadius: 2, overflow: "hidden" }}>
                <div style={{ width: `${o.pct ?? 0}%`, height: "100%", background: "var(--lapis)" }} />
              </div>
            </div>
          ))}
          {poll.total_votes != null && (
            <div style={{ fontSize: 10, color: "var(--ink-40)", marginTop: 4 }}>
              {fmt(poll.total_votes)} votes
            </div>
          )}
        </div>
      )}

      {/* Hashtags + mentions */}
      {(hashtags.length > 0 || mentions.length > 0) && (
        <div style={{ padding: "0 16px 8px 16px", display: "flex", flexWrap: "wrap", gap: 2 }}>
          {hashtags.map((h) => <Hashtag key={h} tag={h} onClick={onTagClick} />)}
          {mentions.map((m) => <Mention key={m} handle={m} onClick={onAuthorClick} />)}
        </div>
      )}

      {/* Engagement bar */}
      <div
        style={{
          padding: "8px 16px", borderTop: "1px solid var(--rule)",
          background: "var(--paper-deep)",
          display: "flex", gap: 18, alignItems: "center", fontSize: 12, color: "var(--ink-70)",
          flexWrap: "wrap",
        }}
      >
        <span>♥ <b>{fmt(capture.like_count)}</b></span>
        <span>💬 <b>{fmt(capture.reply_count)}</b></span>
        <span>🔁 <b>{fmt(capture.repost_count)}</b></span>
        <span>👁 <b>{fmt(capture.view_count)}</b></span>

        {Object.keys(reactions).length > 0 && (
          <span style={{ display: "inline-flex", gap: 4, fontSize: 11 }}>
            {Object.entries(reactions).map(([k, v]) => (
              <span key={k} title={k}>
                {REACTION_ICON[k] ?? "•"}{v > 1 ? `×${v}` : ""}
              </span>
            ))}
          </span>
        )}

        {engagers.length > 0 && (
          <span style={{ fontSize: 11, color: "var(--ink-40)" }} title={engagers.join(", ")}>
            people: {engagers.slice(0, 2).join(", ")}{engagers.length > 2 ? ` +${engagers.length - 2}` : ""}
          </span>
        )}

        <span style={{ marginLeft: "auto" }}>
          <button
            onClick={() => setExpanded(v => !v)}
            style={{
              background: "none", border: "none", cursor: "pointer",
              fontSize: 11, color: "var(--ember-deep)",
            }}
          >
            {expanded ? "hide details" : "show details"}
          </button>
        </span>
      </div>

      {/* Expanded section: metric sparkline + comments */}
      {expanded && (
        <div style={{ padding: "10px 16px", borderTop: "1px dashed var(--rule)", fontSize: 12 }}>
          {/* Metric sparkline */}
          {metricHistory && metricHistory.observations.length > 1 && (
            <MetricSparkline history={metricHistory} />
          )}

          {/* Comments loaded from DB */}
          {commentsData && commentsData.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 11, color: "var(--ink-40)", marginBottom: 6, fontWeight: 600 }}>
                {commentsData.length} captured comment{commentsData.length > 1 ? "s" : ""}
              </div>
              {commentsData.map((c) => (
                <CommentRow key={c.id} comment={c} onAuthorClick={onAuthorClick} />
              ))}
            </div>
          )}

          {/* Diagnostic: technical metadata */}
          <details style={{ marginTop: 10 }}>
            <summary style={{ fontSize: 11, color: "var(--ink-40)", cursor: "pointer" }}>raw metadata</summary>
            <pre style={{
              fontSize: 10, fontFamily: "IBM Plex Mono, monospace",
              background: "var(--paper-deep)", padding: 10, borderRadius: 4, overflow: "auto",
              maxHeight: 260, color: "var(--ink-70)",
            }}>
              {JSON.stringify({ id: capture.id, ...capture.raw_attrs, platform_post_id: capture.platform_post_id }, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </article>
  );
}

// ── Comment row (nested under post) ─────────────────────────────────────────

function CommentRow({ comment, onAuthorClick }: { comment: SocialCapture; onAuthorClick: (h: string) => void }) {
  const a = (comment.raw_attrs ?? {}) as Record<string, unknown>;
  const fullText = attrStr(a, "full_text") || comment.text_excerpt || "";
  return (
    <div style={{
      borderLeft: "2px solid var(--ember)",
      paddingLeft: 10, marginBottom: 8,
    }}>
      <div style={{ fontSize: 11, color: "var(--ink-70)", marginBottom: 2 }}>
        {comment.author_name && <b>{comment.author_name}</b>}{" "}
        {comment.author_handle && (
          <a
            href="#" onClick={(e) => { e.preventDefault(); onAuthorClick(comment.author_handle!); }}
            style={{ color: "var(--ink-40)", textDecoration: "none" }}
          >
            @{comment.author_handle}
          </a>
        )}
        <span style={{ color: "var(--ink-40)", marginLeft: 6 }}>· {timeAgo(comment.observed_at)}</span>
        {comment.is_own && <Pill color="var(--ember-deep)" bg="rgba(220,75,25,0.08)">you</Pill>}
      </div>
      <div style={{ fontSize: 12, color: "var(--ink)", lineHeight: 1.45 }}>{fullText}</div>
      {comment.like_count != null && comment.like_count > 0 && (
        <div style={{ fontSize: 10, color: "var(--ink-40)", marginTop: 2 }}>♥ {fmt(comment.like_count)}</div>
      )}
    </div>
  );
}

// ── Metric sparkline (engagement over time) ─────────────────────────────────

function MetricSparkline({ history }: { history: MetricHistory }) {
  const obs = history.observations;
  const likes = obs.map(o => o.like_count ?? 0);
  const max = Math.max(...likes, 1);
  const points = likes
    .map((v, i) => `${(i / Math.max(1, likes.length - 1)) * 100},${100 - (v / max) * 100}`)
    .join(" ");
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontSize: 11, color: "var(--ink-40)", marginBottom: 4, fontWeight: 600 }}>
        Engagement over time ({obs.length} observations)
      </div>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height: 50, background: "var(--paper-deep)", border: "1px solid var(--rule)", borderRadius: 4 }}>
        <polyline points={points} fill="none" stroke="var(--ember-deep)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      </svg>
      <div style={{ fontSize: 10, color: "var(--ink-40)", display: "flex", justifyContent: "space-between", marginTop: 2 }}>
        <span>{timeAgo(obs[0].observed_at)}: {fmt(obs[0].like_count)}</span>
        <span>now: {fmt(obs[obs.length - 1].like_count)}</span>
      </div>
    </div>
  );
}

// ── Card: article / newsletter / event ──────────────────────────────────────

function ArticleCard({ capture, onTagClick }: { capture: SocialCapture; onTagClick: (t: string) => void }) {
  const a = capture.raw_attrs as Record<string, unknown>;
  const title = attrStr(a, "title") || capture.text_excerpt || "(untitled)";
  const body = attrStr(a, "body_excerpt");
  const readMin = attrNum(a, "read_minutes");
  const isNewsletter = !!a.is_newsletter;
  return (
    <article style={{
      background: "var(--paper)", border: "1px solid var(--rule)",
      borderRadius: 6, marginBottom: 14, padding: "12px 16px",
    }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
        <PlatformBadge platform={capture.platform} />
        <Pill color="var(--lapis)">{isNewsletter ? "newsletter" : "article"}</Pill>
        {readMin && <Pill>{readMin} min read</Pill>}
        <span style={{ fontSize: 11, color: "var(--ink-40)", marginLeft: "auto" }}>{timeAgo(capture.observed_at)}</span>
      </div>
      <h3 style={{ margin: "4px 0", fontSize: 16, fontWeight: 600, lineHeight: 1.3 }}>
        {capture.url ? (
          <a href={capture.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--ink)", textDecoration: "none" }}>{title}</a>
        ) : title}
      </h3>
      {capture.author_name && (
        <div style={{ fontSize: 12, color: "var(--ink-40)", marginBottom: 6 }}>by {capture.author_name}</div>
      )}
      {body && (
        <p style={{ fontSize: 12, color: "var(--ink-70)", lineHeight: 1.5, marginBottom: 8 }}>
          {body.slice(0, 500)}{body.length > 500 ? "…" : ""}
        </p>
      )}
      {(attrArr<string>(a, "hashtags") ?? []).length > 0 && (
        <div>{(attrArr<string>(a, "hashtags") ?? []).map(h => <Hashtag key={h} tag={h} onClick={onTagClick} />)}</div>
      )}
    </article>
  );
}

// ── Card: company ───────────────────────────────────────────────────────────

function CompanyCard({ capture }: { capture: SocialCapture }) {
  const a = capture.raw_attrs as Record<string, unknown>;
  return (
    <article style={{
      background: "var(--paper)", border: "1px solid var(--rule)",
      borderRadius: 6, marginBottom: 14, padding: "12px 16px",
    }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
        <PlatformBadge platform={capture.platform} />
        <Pill color="var(--lapis)">company</Pill>
        <span style={{ fontSize: 11, color: "var(--ink-40)", marginLeft: "auto" }}>{timeAgo(capture.observed_at)}</span>
      </div>
      <h3 style={{ margin: "4px 0", fontSize: 16, fontWeight: 600 }}>
        {capture.url ? (
          <a href={capture.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--ink)", textDecoration: "none" }}>{capture.author_name}</a>
        ) : capture.author_name}
      </h3>
      {capture.text_excerpt && <p style={{ fontSize: 13, color: "var(--ink-70)" }}>{capture.text_excerpt}</p>}
      <div style={{ display: "flex", gap: 14, marginTop: 8, fontSize: 12, color: "var(--ink-70)" }}>
        {attrStr(a, "industry") && <span>🏭 {attrStr(a, "industry")}</span>}
        {attrStr(a, "hq") && <span>📍 {attrStr(a, "hq")}</span>}
        {attrNum(a, "followers") != null && <span>👥 {fmt(attrNum(a, "followers"))} followers</span>}
        {attrStr(a, "employee_info") && <span>{attrStr(a, "employee_info")}</span>}
      </div>
    </article>
  );
}

// ── Card: profile ───────────────────────────────────────────────────────────

function ProfileCard({ capture }: { capture: SocialCapture }) {
  const a = capture.raw_attrs as Record<string, unknown>;
  return (
    <article style={{
      background: "var(--paper)", border: "1px solid var(--rule)",
      borderRadius: 6, marginBottom: 14, padding: "12px 16px",
    }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
        <PlatformBadge platform={capture.platform} />
        <Pill color="var(--lapis)">profile</Pill>
        {!!a.open_to_work && <Pill color="#568" bg="rgba(85,106,136,0.1)">open to work</Pill>}
        <span style={{ fontSize: 11, color: "var(--ink-40)", marginLeft: "auto" }}>{timeAgo(capture.observed_at)}</span>
      </div>
      <h3 style={{ margin: "4px 0", fontSize: 16, fontWeight: 600 }}>
        {capture.url ? (
          <a href={capture.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--ink)", textDecoration: "none" }}>{capture.author_name}</a>
        ) : capture.author_name}
        {capture.author_handle && <span style={{ fontSize: 12, color: "var(--ink-40)", fontWeight: 400 }}> · @{capture.author_handle}</span>}
      </h3>
      {capture.text_excerpt && (
        <p style={{ fontSize: 13, color: "var(--ink-70)", marginBottom: 6 }}>{capture.text_excerpt}</p>
      )}
      <div style={{ display: "flex", gap: 14, fontSize: 12, color: "var(--ink-70)", flexWrap: "wrap" }}>
        {attrStr(a, "location") && <span>📍 {attrStr(a, "location")}</span>}
        {attrStr(a, "current_company") && <span>💼 {attrStr(a, "current_company")}</span>}
        {attrNum(a, "connection_count") != null && <span>👥 {fmt(attrNum(a, "connection_count"))} connections</span>}
      </div>
      {attrStr(a, "about") && (
        <details style={{ marginTop: 8 }}>
          <summary style={{ fontSize: 11, color: "var(--ink-40)", cursor: "pointer" }}>about</summary>
          <p style={{ fontSize: 12, color: "var(--ink-70)", marginTop: 4, lineHeight: 1.5 }}>
            {attrStr(a, "about")}
          </p>
        </details>
      )}
    </article>
  );
}

// ── Card: job ───────────────────────────────────────────────────────────────

function JobCard({ capture }: { capture: SocialCapture }) {
  const a = capture.raw_attrs as Record<string, unknown>;
  return (
    <article style={{
      background: "var(--paper)", border: "1px solid var(--rule)",
      borderRadius: 6, marginBottom: 14, padding: "12px 16px",
    }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
        <PlatformBadge platform={capture.platform} />
        <Pill color="#B4883A" bg="rgba(180,136,58,0.08)">job</Pill>
        <span style={{ fontSize: 11, color: "var(--ink-40)", marginLeft: "auto" }}>{timeAgo(capture.observed_at)}</span>
      </div>
      <h3 style={{ margin: "4px 0", fontSize: 15, fontWeight: 600 }}>
        {capture.url ? (
          <a href={capture.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--ink)", textDecoration: "none" }}>{capture.text_excerpt ?? "(untitled)"}</a>
        ) : capture.text_excerpt}
      </h3>
      <div style={{ fontSize: 13, color: "var(--ink-70)", marginBottom: 4 }}>{capture.author_name}</div>
      <div style={{ fontSize: 12, color: "var(--ink-40)" }}>
        {attrStr(a, "location") && <span>📍 {attrStr(a, "location")}</span>}
        {attrStr(a, "salary") && <span>  ·  💰 {attrStr(a, "salary")}</span>}
      </div>
      {attrStr(a, "description") && (
        <details style={{ marginTop: 6 }}>
          <summary style={{ fontSize: 11, color: "var(--ink-40)", cursor: "pointer" }}>description</summary>
          <p style={{ fontSize: 12, color: "var(--ink-70)", marginTop: 4, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
            {attrStr(a, "description")}
          </p>
        </details>
      )}
    </article>
  );
}

// ── Card: discovery (pymk / search / hashtag-feed) ──────────────────────────

function DiscoveryCard({ capture }: { capture: SocialCapture }) {
  const a = capture.raw_attrs as Record<string, unknown>;
  return (
    <article style={{
      background: "var(--paper)", border: "1px solid var(--rule)",
      borderRadius: 6, marginBottom: 10, padding: "10px 14px", fontSize: 13,
    }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 3 }}>
        <PlatformBadge platform={capture.platform} />
        <Pill>{TYPE_LABELS[capture.type] ?? capture.type}</Pill>
        <span style={{ fontSize: 11, color: "var(--ink-40)", marginLeft: "auto" }}>{timeAgo(capture.observed_at)}</span>
      </div>
      <div style={{ fontWeight: 600 }}>{capture.author_name ?? capture.text_excerpt}</div>
      {capture.text_excerpt && capture.author_name && (
        <div style={{ fontSize: 12, color: "var(--ink-70)" }}>{capture.text_excerpt}</div>
      )}
      {attrStr(a, "query") && (
        <div style={{ fontSize: 11, color: "var(--ink-40)", marginTop: 3 }}>query: {attrStr(a, "query")}</div>
      )}
      {attrNum(a, "mutual_connections") != null && (
        <div style={{ fontSize: 11, color: "var(--ink-40)", marginTop: 3 }}>{attrNum(a, "mutual_connections")} mutual</div>
      )}
    </article>
  );
}

// ── Router: pick the right card for a capture's category ────────────────────

function CaptureCard(props: {
  capture: SocialCapture;
  onTagClick: (t: string) => void;
  onAuthorClick: (h: string) => void;
}) {
  const cat = TYPE_CATEGORY[props.capture.type] ?? "post";
  if (cat === "post" || cat === "comment") return <PostCard {...props} />;
  if (cat === "article")  return <ArticleCard capture={props.capture} onTagClick={props.onTagClick} />;
  if (cat === "company")  return <CompanyCard capture={props.capture} />;
  if (cat === "profile")  return <ProfileCard capture={props.capture} />;
  if (cat === "job")      return <JobCard capture={props.capture} />;
  return <DiscoveryCard capture={props.capture} />;
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function IntelligencePage() {
  const [platform, setPlatform] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [ownOnly, setOwnOnly] = useState(false);
  const [searchText, setSearchText] = useState<string>("");
  const [authorFilter, setAuthorFilter] = useState<string>("");
  const [hashtagFilter, setHashtagFilter] = useState<string>("");
  const [q, setQ] = useState<string>("");

  useEffect(() => {
    const t = setTimeout(() => setQ(searchText.trim()), 400);
    return () => clearTimeout(t);
  }, [searchText]);

  const limit = 100;
  const { data, dataUpdatedAt, isLoading, refetch } = useQuery({
    queryKey: ["captures", platform, typeFilter, ownOnly, q, authorFilter, hashtagFilter],
    queryFn: () => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (platform !== "all") params.set("platform", platform);
      if (typeFilter !== "all") params.set("type", typeFilter);
      if (ownOnly) params.set("is_own", "true");
      if (q) params.set("q", q);
      if (authorFilter.trim()) params.set("author_handle", authorFilter.trim().replace(/^@/, ""));
      if (hashtagFilter.trim()) params.set("hashtag", hashtagFilter.trim().replace(/^#/, ""));
      return tc.get<ListPage<SocialCapture>>(`/v1/social/captures?${params}`);
    },
    refetchInterval: 15_000,
  });

  const { data: counts } = useQuery<CaptureCounts>({
    queryKey: ["capture-counts"],
    queryFn: () => tc.get<CaptureCounts>("/v1/social/insights/counts"),
    refetchInterval: 30_000,
  });

  const { data: topAuthors } = useQuery<{ items: TopAuthor[] }>({
    queryKey: ["top-authors", platform],
    queryFn: () => tc.get<{ items: TopAuthor[] }>(`/v1/social/insights/top-authors?limit=10${platform !== "all" ? `&platform=${platform}` : ""}`),
  });

  const { data: topTags } = useQuery<{ items: TopHashtag[] }>({
    queryKey: ["top-hashtags", platform],
    queryFn: () => tc.get<{ items: TopHashtag[] }>(`/v1/social/insights/top-hashtags?limit=15${platform !== "all" ? `&platform=${platform}` : ""}`),
  });

  const items = useMemo(() => data?.items ?? [], [data]);
  const total = data?.total ?? 0;
  const streamActive = dataUpdatedAt > 0 && Date.now() - dataUpdatedAt < 120_000;

  const topPlatform = counts?.by_platform?.[0]?.platform ?? "—";
  const topPlatformN = counts?.by_platform?.[0]?.n ?? 0;

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 260px", gap: 24 }}>
      {/* Main column — feed */}
      <div>
        {/* Header */}
        <div style={{ marginBottom: 20, display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 className="display" style={{ fontSize: 32 }}>Feed</h1>
            <p style={{ color: "var(--ink-40)", marginTop: 4, fontSize: 13 }}>
              Everything your extension has captured — posts, comments, articles, companies, jobs, profiles.
            </p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
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
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, marginBottom: 16 }}>
          <Stat value={counts?.total ?? 0} label="Total" />
          <Stat value={counts?.today_count ?? 0} label="Today" />
          <Stat value={counts?.own_count ?? 0} label="Your activity" />
          <Stat value={topPlatform} label="Top platform" sub={`${topPlatformN} captures`} />
        </div>

        {/* Filters */}
        <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ display: "flex", gap: 2, background: "var(--paper-edge)", borderRadius: 4, padding: 2 }}>
            {["all", "linkedin", "x", "instagram"].map(p => (
              <button
                key={p}
                onClick={() => setPlatform(p)}
                style={{
                  padding: "4px 12px", borderRadius: 3, border: "none", cursor: "pointer",
                  fontSize: 12, fontWeight: platform === p ? 600 : 400,
                  background: platform === p ? "var(--paper)" : "transparent",
                  color: platform === p ? "var(--ink)" : "var(--ink-40)",
                }}
              >
                {p === "all" ? "All" : (PLATFORM_CONFIG[p]?.label ?? p)}
              </button>
            ))}
          </div>

          <select
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            style={{ padding: "5px 10px", fontSize: 12, borderRadius: 4, border: "1px solid var(--rule)", background: "var(--paper)" }}
          >
            <option value="all">All types</option>
            {Object.entries(TYPE_LABELS).map(([code, label]) => (
              <option key={code} value={code}>{label}</option>
            ))}
          </select>

          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, cursor: "pointer" }}>
            <input type="checkbox" checked={ownOnly} onChange={e => setOwnOnly(e.target.checked)} style={{ accentColor: "var(--ember)" }} />
            mine only
          </label>

          <input
            type="search" placeholder="search text…"
            value={searchText} onChange={e => setSearchText(e.target.value)}
            style={{ padding: "5px 10px", fontSize: 12, borderRadius: 4, border: "1px solid var(--rule)", background: "var(--paper)", minWidth: 160 }}
          />
          <input
            type="text" placeholder="@author"
            value={authorFilter} onChange={e => setAuthorFilter(e.target.value)}
            style={{ padding: "5px 10px", fontSize: 12, borderRadius: 4, border: "1px solid var(--rule)", background: "var(--paper)", width: 120 }}
          />
          <input
            type="text" placeholder="#hashtag"
            value={hashtagFilter} onChange={e => setHashtagFilter(e.target.value)}
            style={{ padding: "5px 10px", fontSize: 12, borderRadius: 4, border: "1px solid var(--rule)", background: "var(--paper)", width: 110 }}
          />

          <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--ink-40)" }} className="mono">
            {items.length} / {total}
          </span>
        </div>

        {/* Feed */}
        {isLoading ? (
          <div style={{ textAlign: "center", padding: 48, color: "var(--ink-40)" }}>loading…</div>
        ) : items.length === 0 ? (
          <EmptyState />
        ) : (
          items.map((c) => (
            <CaptureCard
              key={c.id}
              capture={c}
              onTagClick={setHashtagFilter}
              onAuthorClick={setAuthorFilter}
            />
          ))
        )}
      </div>

      {/* Sidebar — top authors & hashtags */}
      <aside style={{ paddingTop: 92 }}>
        <SidebarSection title="Top authors">
          {(topAuthors?.items ?? []).map((a) => (
            <div
              key={`${a.platform}:${a.handle}`}
              onClick={() => setAuthorFilter(a.handle)}
              style={{ padding: "6px 0", borderBottom: "1px dashed var(--rule)", cursor: "pointer" }}
            >
              <div style={{ fontSize: 12, fontWeight: 600 }}>{a.display_name ?? a.handle}</div>
              <div style={{ fontSize: 10, color: "var(--ink-40)" }} className="mono">
                @{a.handle} · {a.capture_count} · {fmt(a.total_likes_seen)} ♥
              </div>
            </div>
          ))}
          {!topAuthors?.items?.length && (
            <div style={{ fontSize: 11, color: "var(--ink-40)" }}>no data yet</div>
          )}
        </SidebarSection>

        <SidebarSection title="Top hashtags">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {(topTags?.items ?? []).map((t) => (
              <span
                key={t.tag}
                onClick={() => setHashtagFilter(t.tag)}
                style={{
                  fontSize: 11, padding: "2px 7px", borderRadius: 3, cursor: "pointer",
                  color: "var(--lapis)", background: "rgba(52,88,140,0.05)",
                  border: "1px solid rgba(52,88,140,0.2)",
                }}
              >
                #{t.tag} <span style={{ color: "var(--ink-40)" }}>{t.n}</span>
              </span>
            ))}
            {!topTags?.items?.length && (
              <div style={{ fontSize: 11, color: "var(--ink-40)" }}>no hashtags yet</div>
            )}
          </div>
        </SidebarSection>

        <SidebarSection title="By type">
          {(counts?.by_type ?? []).slice(0, 10).map((r) => (
            <div
              key={r.type}
              onClick={() => setTypeFilter(r.type)}
              style={{ display: "flex", justifyContent: "space-between", fontSize: 11, padding: "3px 0", cursor: "pointer" }}
            >
              <span>{TYPE_LABELS[r.type] ?? r.type}</span>
              <span className="mono" style={{ color: "var(--ink-40)" }}>{r.n}</span>
            </div>
          ))}
        </SidebarSection>
      </aside>
    </div>
    <p className="mono" style={{ marginTop: 32, paddingTop: 16, borderTop: "1px solid var(--rule)", fontSize: 10, textAlign: "center", color: "var(--ink-40)", letterSpacing: "0.15em", textTransform: "uppercase" }}>
      Powered by tennetctl
    </p>
    </div>
  );
}

function SidebarSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{
        fontSize: 10, textTransform: "uppercase", letterSpacing: "0.1em",
        color: "var(--ink-40)", marginBottom: 8, fontWeight: 600,
      }}>
        {title}
      </div>
      {children}
    </div>
  );
}

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
    </div>
  );
}
