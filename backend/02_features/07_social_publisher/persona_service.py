"""
social_publisher.persona — persona + AI recommendation service.

Two layers:
  1. Deterministic persona: SQL aggregates over a user's captures to produce
     interests (top hashtags), top authors they follow, platform mix, topic
     fingerprint.  No AI involved — cheap to rebuild on demand.
  2. AI recommendations: ask Claude for comment / post / article suggestions
     given the persona + the capture the user is looking at.  Uses prompt
     caching (persona is constant per request, capture is variable) to keep
     cost low.

All Claude calls use claude-opus-4-7 per the project's default, fall back to
claude-sonnet-4-6 if the opus model id isn't reachable. Prompt caching is
applied so re-querying recommendations for the same user & capture is cheap.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
from importlib import import_module
from typing import Any

logger = logging.getLogger("tennetctl.social.persona")

_repo: Any = import_module(
    "backend.02_features.07_social_publisher.capture_repository"
)

_VIEW    = '"07_social"."v_social_captures"'
_METRICS = '"07_social"."63_evt_capture_metrics"'

# ── Deterministic persona build ────────────────────────────────────────────

async def build_persona(conn: Any, *, user_id: str) -> dict:
    """
    Aggregate a user's captures into a persona profile. Pure SQL — no AI.

    Shape:
      {
        "user_id": str,
        "built_at": ISO str,
        "totals": {total, own_count, today, week},
        "platform_mix": {linkedin: N, x: N, ...},
        "top_authors": [{handle, platform, capture_count, total_likes_seen}, ...],
        "top_hashtags": [{tag, n}, ...],
        "top_mentions": [{handle, n}, ...],
        "recent_own_posts": [{excerpt, likes, observed_at}, ...],
        "company_interests": [{slug, name, capture_count}, ...],
        "reading": [{title, url, read_minutes}, ...],
        "job_interests": [{title, company, location}, ...],
      }
    """
    counts   = await _repo.capture_counts(conn, user_id=user_id)
    authors  = await _repo.top_authors(conn, user_id=user_id, platform=None, limit=15)
    hashtags = await _repo.top_hashtags(conn, user_id=user_id, platform=None, limit=20)

    # Top mentions (people this user sees being @mentioned)
    mentions = await conn.fetch(
        f"""
        SELECT m AS handle, COUNT(*)::int AS n
        FROM {_VIEW},
        LATERAL jsonb_array_elements_text(COALESCE(raw_attrs -> 'mentions', '[]'::jsonb)) AS m
        WHERE user_id = $1
        GROUP BY m
        ORDER BY n DESC
        LIMIT 20
        """,
        user_id,
    )

    # User's own posts — what they write themselves
    own_posts = await conn.fetch(
        f"""
        SELECT text_excerpt, like_count, reply_count, observed_at, platform, url
        FROM {_VIEW}
        WHERE user_id = $1 AND is_own = TRUE AND text_excerpt IS NOT NULL
        ORDER BY observed_at DESC
        LIMIT 15
        """,
        user_id,
    )

    # Companies the user has viewed
    companies = await conn.fetch(
        f"""
        SELECT author_handle AS slug, MAX(author_name) AS name, COUNT(*)::int AS capture_count,
               MAX(raw_attrs ->> 'industry') AS industry,
               MAX(raw_attrs ->> 'hq') AS hq
        FROM {_VIEW}
        WHERE user_id = $1 AND type = 'company_viewed'
        GROUP BY author_handle
        ORDER BY capture_count DESC
        LIMIT 15
        """,
        user_id,
    )

    # Articles the user has opened (not just seen in feed)
    articles = await conn.fetch(
        f"""
        SELECT COALESCE(raw_attrs ->> 'title', text_excerpt) AS title,
               url,
               (raw_attrs ->> 'read_minutes')::int AS read_minutes,
               author_name,
               observed_at
        FROM {_VIEW}
        WHERE user_id = $1 AND type IN ('article_opened', 'article_seen', 'newsletter_seen')
        ORDER BY observed_at DESC
        LIMIT 15
        """,
        user_id,
    )

    # Jobs the user has engaged with
    jobs = await conn.fetch(
        f"""
        SELECT text_excerpt AS title,
               author_name  AS company,
               raw_attrs ->> 'location' AS location,
               url
        FROM {_VIEW}
        WHERE user_id = $1 AND type IN ('job_post_seen', 'job_post_opened')
        ORDER BY observed_at DESC
        LIMIT 15
        """,
        user_id,
    )

    return {
        "user_id": user_id,
        "built_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "totals": {
            "total":       counts["total"],
            "own_count":   counts["own_count"],
            "today_count": counts["today_count"],
            "week_count":  counts["week_count"],
        },
        "platform_mix": {r["platform"]: r["n"] for r in counts["by_platform"]},
        "top_authors":   [dict(r) for r in authors],
        "top_hashtags":  [dict(r) for r in hashtags],
        "top_mentions":  [dict(r) for r in mentions],
        "recent_own_posts":  [dict(r, observed_at=r["observed_at"].isoformat() if r["observed_at"] else None) for r in own_posts],
        "company_interests": [dict(r) for r in companies],
        "reading":           [dict(r, observed_at=r["observed_at"].isoformat() if r["observed_at"] else None) for r in articles],
        "job_interests":     [dict(r) for r in jobs],
    }


# ── Claude client + prompt-cached recommendations ──────────────────────────

def _client():
    try:
        import anthropic  # local import so systems without the SDK still load
    except ImportError:
        return None
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


# Claude Opus 4.7 is the project default per CLAUDE.md, with Sonnet 4.6 fallback.
_MODEL_PREFERENCES = ["claude-opus-4-7", "claude-sonnet-4-6"]


def _persona_brief(persona: dict) -> str:
    """Compact persona as a cache-friendly system context."""
    top_authors = ", ".join(
        f"{a.get('handle')} ({a.get('display_name') or '—'}, {a.get('capture_count')}x)"
        for a in (persona.get("top_authors") or [])[:8]
    )
    top_hashtags = ", ".join(
        f"#{h.get('tag')}" for h in (persona.get("top_hashtags") or [])[:12]
    )
    own_snippets = "\n".join(
        f"  - {(p.get('text_excerpt') or '')[:180]} [♥{p.get('like_count') or 0}]"
        for p in (persona.get("recent_own_posts") or [])[:5]
    )
    companies = ", ".join(
        c.get("name") or c.get("slug") or ""
        for c in (persona.get("company_interests") or [])[:8]
    )
    reading = "\n".join(
        f"  - {(r.get('title') or '')[:150]}"
        for r in (persona.get("reading") or [])[:6]
    )
    totals = persona.get("totals", {})
    return f"""You are helping a LinkedIn/Twitter user who has been sharing and observing content.

# Their persona (built from what they publish + what they engage with)
- Total captures observed: {totals.get('total', 0)} (mine={totals.get('own_count', 0)}, past 7d={totals.get('week_count', 0)})
- Platform mix: {persona.get('platform_mix')}
- Top authors they watch: {top_authors or '—'}
- Top topics/hashtags: {top_hashtags or '—'}
- Companies of interest: {companies or '—'}
- Recently read articles:
{reading or '  —'}
- Their recent own posts (tone/voice reference):
{own_snippets or '  —'}

Use this as a calibration for voice/tone. When giving recommendations, mirror
the user's typical cadence and topic focus — do not pretend to be a different
person, just match the register they already use.
""".strip()


def _capture_brief(capture: dict) -> str:
    a = capture.get("raw_attrs") or {}
    full = a.get("full_text") or capture.get("text_excerpt") or ""
    hashtags = " ".join(f"#{t}" for t in (a.get("hashtags") or []))
    mentions = " ".join(f"@{m}" for m in (a.get("mentions") or []))
    likes = capture.get("like_count")
    replies = capture.get("reply_count")
    return f"""# The post you're about to react to
Author: {capture.get('author_name')} (@{capture.get('author_handle')})
Headline: {a.get('author_headline') or ''}
Platform: {capture.get('platform')}
Engagement: ♥{likes or 0} 💬{replies or 0} 🔁{capture.get('repost_count') or 0}
Hashtags: {hashtags or '—'}
Mentions: {mentions or '—'}

Body:
{full}
""".strip()


async def _call_claude(client, *, system_blocks: list[dict], user_msg: str, max_tokens: int = 1024) -> str:
    import anthropic as _anth
    last_err: Exception | None = None
    for model in _MODEL_PREFERENCES:
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_blocks,
                messages=[{"role": "user", "content": user_msg}],
            )
            parts = []
            for block in resp.content:
                if getattr(block, "type", None) == "text":
                    parts.append(block.text)
            return "".join(parts).strip()
        except _anth.NotFoundError as e:
            last_err = e
            continue
        except Exception as e:
            last_err = e
            break
    raise last_err or RuntimeError("Claude call failed with no error")


async def recommend_comments(
    conn: Any, *, user_id: str, capture_id: str, n: int = 3,
) -> dict:
    """Suggest `n` comment drafts for a capture, personalised by the user's persona."""
    client = _client()
    capture = await conn.fetchrow(f"SELECT * FROM {_VIEW} WHERE id = $1 AND user_id = $2", capture_id, user_id)
    if capture is None:
        return {"error": "capture not found", "suggestions": []}
    capture_dict = dict(capture)

    if client is None:
        # Fallback: heuristic suggestions with clear "fallback" marker
        return {
            "model": "fallback-heuristic",
            "suggestions": [
                {"text": f"Great point — the data on {(capture_dict.get('text_excerpt') or '')[:60].lower()} is telling.", "tone": "supportive"},
                {"text": "Curious what drove the engagement spike here — worth a deeper breakdown?", "tone": "inquisitive"},
                {"text": "Resharing — this lines up with what we're seeing on our side too.", "tone": "resharer"},
            ][:n],
            "note": "ANTHROPIC_API_KEY not configured; showing heuristic fallback.",
        }

    persona = await build_persona(conn, user_id=user_id)
    system_blocks = [
        {
            "type": "text",
            "text": _persona_brief(persona),
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": (
                "Return exactly a JSON array of objects with keys `text` (the comment, 1–3 sentences) "
                "and `tone` (one of: supportive, inquisitive, resharer, challenger, humorous). "
                "Do not wrap in markdown. Just the JSON array."
            ),
        },
    ]

    user_msg = (
        _capture_brief(capture_dict)
        + f"\n\nGive me {n} distinct comment drafts I could leave on this post. "
          f"Each should sound like my voice (reference my persona). Vary the tone across the drafts."
    )

    text = await _call_claude(client, system_blocks=system_blocks, user_msg=user_msg, max_tokens=1024)
    suggestions = _parse_json_array(text)
    return {"model": _MODEL_PREFERENCES[0], "suggestions": suggestions[:n], "raw": text[:2000]}


async def recommend_posts(conn: Any, *, user_id: str, n: int = 3) -> dict:
    """Suggest `n` new post ideas for the user to publish, based on their persona."""
    client = _client()
    persona = await build_persona(conn, user_id=user_id)

    if client is None:
        return {
            "model": "fallback-heuristic",
            "suggestions": [
                {"headline": f"A take on {t['tag']}", "draft": f"Quick thought on #{t['tag']}: …", "why": f"you track #{t['tag']} ({t['n']} captures)"}
                for t in (persona.get("top_hashtags") or [])[:n]
            ],
            "note": "ANTHROPIC_API_KEY not configured; showing heuristic fallback.",
        }

    system_blocks = [
        {"type": "text", "text": _persona_brief(persona), "cache_control": {"type": "ephemeral"}},
        {
            "type": "text",
            "text": (
                "Return a JSON array of objects with keys `headline` (a one-line hook), "
                "`draft` (a 3-5 sentence post body in the user's voice), and `why` (one line rationale: "
                "which of their interests this targets). No markdown fences."
            ),
        },
    ]
    user_msg = (
        f"Suggest {n} original post ideas I could publish this week. Each should play to my top "
        f"interests and authors I follow. Use my usual voice/tone as shown in my recent own posts."
    )
    text = await _call_claude(client, system_blocks=system_blocks, user_msg=user_msg, max_tokens=1600)
    return {"model": _MODEL_PREFERENCES[0], "suggestions": _parse_json_array(text)[:n], "raw": text[:2500]}


async def recommend_articles(conn: Any, *, user_id: str, n: int = 5) -> dict:
    """
    Suggest `n` articles — pulled from articles the extension has ACTUALLY
    captured (not hallucinated). The AI ranks them against the user's persona.
    """
    # Pool of candidate articles from what we've observed in feed + opened
    candidates = await conn.fetch(
        f"""
        SELECT DISTINCT ON (url)
               id, url, text_excerpt,
               COALESCE(raw_attrs ->> 'title', text_excerpt) AS title,
               author_name,
               (raw_attrs ->> 'read_minutes')::int AS read_minutes,
               observed_at
        FROM {_VIEW}
        WHERE user_id = $1
          AND type IN ('article_seen','newsletter_seen','article_opened')
          AND url IS NOT NULL
        ORDER BY url, observed_at DESC
        LIMIT 40
        """,
        user_id,
    )
    pool = [dict(r, observed_at=r["observed_at"].isoformat() if r["observed_at"] else None) for r in candidates]

    if not pool:
        return {"model": "n/a", "suggestions": [], "note": "no captured articles to rank yet"}

    client = _client()
    if client is None:
        # Fallback: reverse-chronological top N
        return {
            "model": "fallback-recent",
            "suggestions": [
                {"title": p["title"], "url": p["url"], "why": "recently observed; ANTHROPIC_API_KEY not set"}
                for p in pool[:n]
            ],
        }

    persona = await build_persona(conn, user_id=user_id)
    system_blocks = [
        {"type": "text", "text": _persona_brief(persona), "cache_control": {"type": "ephemeral"}},
        {
            "type": "text",
            "text": (
                "Given a list of candidate articles the user has observed in their feed, rank them "
                "against the user's persona. Return a JSON array of objects with keys `title`, `url`, "
                "and `why` (a short one-line justification of why this article will resonate). "
                "Only return articles from the candidate list — do not invent."
            ),
        },
    ]
    pool_str = "\n".join(
        f"- {p.get('title')} — {p.get('url')} ({p.get('author_name') or 'n/a'}, {p.get('read_minutes') or '?'} min)"
        for p in pool
    )
    user_msg = f"Candidates:\n{pool_str}\n\nPick the top {n} for me."
    text = await _call_claude(client, system_blocks=system_blocks, user_msg=user_msg, max_tokens=1600)
    return {"model": _MODEL_PREFERENCES[0], "suggestions": _parse_json_array(text)[:n], "raw": text[:2500]}


def _parse_json_array(text: str) -> list[dict]:
    """Best-effort: find the JSON array in the model's response."""
    s = text.strip()
    # Strip markdown fences if present
    if s.startswith("```"):
        s = s.strip("`")
        # drop leading 'json\n'
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1:]
        s = s.rstrip("` \n")
    # Try direct parse
    try:
        v = json.loads(s)
        return v if isinstance(v, list) else []
    except Exception:
        pass
    # Find first '[' and last ']'
    lb = s.find("[")
    rb = s.rfind("]")
    if lb != -1 and rb > lb:
        try:
            v = json.loads(s[lb:rb + 1])
            return v if isinstance(v, list) else []
        except Exception:
            pass
    return []
