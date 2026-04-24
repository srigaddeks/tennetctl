/* SolSocial Collector — Popup controller */

const $ = id => document.getElementById(id);

async function send(msg) {
  return chrome.runtime.sendMessage(msg);
}

function timeAgo(ms) {
  const diff = Date.now() - ms;
  const s = Math.floor(diff / 1000);
  if (s < 5) return "just now";
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  return `${Math.floor(m / 60)}h ago`;
}

// ─── Render ───────────────────────────────────────────────────────────────────

function showAuth() {
  $("auth-panel").style.display = "block";
  $("status-panel").style.display = "none";
  $("pulse").className = "pulse-dot";
  $("stream-label").textContent = "not signed in";
  $("stream-label").className = "stream-label";
}

function showStatus(status) {
  $("auth-panel").style.display = "none";
  $("status-panel").style.display = "block";

  const user = status.user ?? {};
  $("avatar").textContent = (user.display_name || user.email || "?")[0].toUpperCase();
  $("display-name").textContent = user.display_name || user.email || "Signed in";
  $("display-email").textContent = user.email ?? "";

  $("today-count").textContent = status.todayCount ?? 0;
  $("queue-size").textContent = status.queueSize ?? 0;

  // Stream status bar
  const enabled = status.enabled ?? false;
  const lastFlush = status.lastFlushAt ?? 0;
  const recentlyFlushed = lastFlush && (Date.now() - lastFlush) < 90_000;
  const bar = $("stream-bar");
  const dot = $("stream-dot");
  const title = $("stream-title");
  const sub = $("stream-sub");

  if (enabled && recentlyFlushed) {
    bar.className = "stream-bar active";
    dot.className = "pulse-dot active";
    title.textContent = "Streaming";
    sub.textContent = `last flush ${timeAgo(lastFlush)} · ${status.queueSize ?? 0} pending`;
  } else if (enabled) {
    bar.className = "stream-bar";
    dot.className = "pulse-dot";
    title.textContent = "Collecting";
    sub.textContent = lastFlush ? `last flush ${timeAgo(lastFlush)}` : "waiting for first flush…";
  } else {
    bar.className = "stream-bar";
    dot.className = "pulse-dot";
    title.textContent = "Paused";
    sub.textContent = "Toggle to resume collection";
  }

  // Header pulse
  if (enabled && recentlyFlushed) {
    $("pulse").className = "pulse-dot active";
    $("stream-label").textContent = "live";
    $("stream-label").className = "stream-label active";
  } else if (enabled) {
    $("pulse").className = "pulse-dot";
    $("stream-label").textContent = "on";
    $("stream-label").className = "stream-label";
  } else {
    $("pulse").className = "pulse-dot";
    $("stream-label").textContent = "off";
    $("stream-label").className = "stream-label";
  }

  // Toggle
  const toggle = $("toggle-btn");
  enabled ? toggle.classList.add("on") : toggle.classList.remove("on");

  // Platform pills
  const pillContainer = $("platform-pills");
  const breakdown = status.platformBreakdown ?? {};
  pillContainer.innerHTML = Object.keys(breakdown).length === 0
    ? `<span style="font-size:10px; color:var(--ink-20);">No captures yet — browse LinkedIn or X</span>`
    : Object.entries(breakdown)
        .sort((a, b) => b[1] - a[1])
        .map(([p, n]) => {
          const cls = p === "linkedin" ? "platform-pill li" : p === "x" || p === "twitter" ? "platform-pill x" : "platform-pill";
          return `<span class="${cls}">${p} · ${n}</span>`;
        }).join("");

  // Open app URL
  const appUrl = `${status.baseUrl?.replace("51734", "51835") ?? "http://localhost:51835"}/intelligence`;
  if ($("open-app")) $("open-app").href = appUrl;

  // Fetch authoritative counts + type breakdown from backend
  if (status.baseUrl && status.token) {
    fetchInsights(status.baseUrl, status.token);
  }
}

// ─── Backend insights (total, today, by_type) ────────────────────────────────

async function fetchInsights(baseUrl, token) {
  try {
    const res = await fetch(baseUrl + "/v1/social/insights/counts", {
      headers: { "Authorization": "Bearer " + token },
    });
    const d = await res.json();
    if (!d.ok) return;
    const c = d.data || {};
    if ($("today-count")) $("today-count").textContent = c.today_count ?? 0;
    if ($("total-count")) $("total-count").textContent = c.total ?? 0;

    // Type breakdown: top 6 types
    const box = $("type-breakdown");
    if (box) {
      box.innerHTML = (c.by_type || []).slice(0, 6).map(r => {
        const label = (r.type || "").replace(/_/g, " ");
        return `<span style="font-size:10px;padding:2px 7px;background:var(--paper-deep);border:1px solid var(--rule);border-radius:3px;color:var(--ink-70);">${label} <span style="color:var(--ink-40);">${r.n}</span></span>`;
      }).join("");
    }
  } catch (err) {
    // best-effort: don't break the popup if backend is unreachable
    console.warn("insights fetch failed:", err?.message);
  }
}

// ─── Init ─────────────────────────────────────────────────────────────────────

async function init() {
  const status = await send({ type: "status" });
  if (status.signedIn) showStatus(status);
  else showAuth();
}

// ─── Sign in ─────────────────────────────────────────────────────────────────

$("signin-btn").addEventListener("click", async () => {
  const email = $("email").value.trim();
  const password = $("password").value;
  const baseUrl = $("base-url").value.trim() || "http://localhost:51734";
  $("auth-error").textContent = "";

  if (!email || !password) {
    $("auth-error").textContent = "Email and password are required.";
    return;
  }

  $("signin-btn").disabled = true;
  $("signin-btn").textContent = "Signing in…";

  try {
    const result = await send({ type: "signin", email, password, baseUrl });
    if (result.ok) {
      const status = await send({ type: "status" });
      showStatus(status);
    } else {
      $("auth-error").textContent = result.error || "Sign in failed — check email and password.";
    }
  } catch (err) {
    $("auth-error").textContent = err.message || "Could not reach backend. Check the URL.";
  } finally {
    $("signin-btn").disabled = false;
    $("signin-btn").textContent = "Sign in to SolSocial";
  }
});

$("password").addEventListener("keydown", e => {
  if (e.key === "Enter") $("signin-btn").click();
});

// ─── Sign out ────────────────────────────────────────────────────────────────

$("signout-btn").addEventListener("click", async () => {
  await send({ type: "signout" });
  showAuth();
});

// ─── Toggle ──────────────────────────────────────────────────────────────────

$("toggle-btn").addEventListener("click", async () => {
  const result = await send({ type: "toggle" });
  if (result.ok) {
    const status = await send({ type: "status" });
    showStatus(status);
  }
});

// ─── Flush ───────────────────────────────────────────────────────────────────

$("flush-btn").addEventListener("click", async () => {
  $("flush-btn").disabled = true;
  $("flush-btn").textContent = "Flushing…";
  await send({ type: "flush" });
  const status = await send({ type: "status" });
  showStatus(status);
  $("flush-btn").disabled = false;
  $("flush-btn").textContent = "Flush queue now";
});

// ─── Scan active tab + display extractor health ──────────────────────────────

async function queryActiveTabScanner() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) return null;
    if (!/linkedin\.com|twitter\.com|x\.com/.test(tab.url || "")) {
      return { page_url: tab.url, unsupported: true };
    }
    const resp = await chrome.tabs.sendMessage(tab.id, { type: "scanner_stats" });
    return { ...resp?.stats, page_url: tab.url };
  } catch (err) {
    return { error: err?.message || String(err) };
  }
}

async function refreshHealth() {
  const s = await queryActiveTabScanner();
  const line = $("scanner-line") || $("health-line");
  const warn = $("scanner-warn");
  if (!line) return;
  if (!s || s.error) {
    line.textContent = s?.error ? `tab error: ${s.error.slice(0, 60)}` : "no active tab";
    if (warn) warn.textContent = "";
    return;
  }
  if (s.unsupported) {
    line.textContent = "open a LinkedIn or X tab to see scanner health";
    if (warn) warn.textContent = "";
    return;
  }
  const parts = [];
  parts.push(`${s.platform || "?"} v${s.version || "?"}`);
  parts.push(`${s.last_page_type || "?"}`);
  parts.push(`${s.scans ?? 0} scans`);
  parts.push(`${s.captures_emitted ?? 0} captured`);
  if (s.last_scan_at) {
    const ago = Math.round((Date.now() - s.last_scan_at) / 1000);
    parts.push(`last ${ago}s ago${s.last_scan_count ? ` (+${s.last_scan_count})` : ""}`);
  }
  line.textContent = parts.join(" · ");
  if (warn) {
    warn.textContent = s.zero_scan_streak > 3
      ? `⚠ ${s.zero_scan_streak} consecutive zero-scans — selectors may be stale`
      : "";
  }
}

$("scan-btn").addEventListener("click", async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab?.id) {
      await chrome.tabs.sendMessage(tab.id, { type: "force_scan" });
      $("scan-btn").textContent = "Scanning…";
      setTimeout(() => { $("scan-btn").textContent = "Scan now"; refreshHealth(); }, 1200);
    }
  } catch (err) {
    console.warn("scan trigger failed:", err);
  }
});

// ─── AI Recommendations ───────────────────────────────────────────────────────

function renderRecommendations(items, kind) {
  const box = $("rec-output");
  if (!items || items.length === 0) {
    box.innerHTML = `<em style="color:var(--ink-20);font-size:11px;">No suggestions yet — browse more to build your persona.</em>`;
    return;
  }

  box.innerHTML = items.map((item, i) => {
    const isArticle = kind === "articles";
    const text = isArticle
      ? (item.title || item.text_excerpt || item.url || "")
      : (item.draft || item.text || "");
    const label = isArticle
      ? (item.headline || item.title || "Article")
      : (item.headline || "Post idea");
    const why = item.why || item.note || "";
    const url = item.url || null;
    const shortText = text.slice(0, 140) + (text.length > 140 ? "…" : "");

    return `<div data-rec="${i}" style="margin-bottom:10px;padding:8px 10px;background:var(--paper-deep);border:1px solid var(--rule);border-radius:3px;">
      <div style="font-size:10px;font-weight:600;color:var(--ink-70);margin-bottom:3px;">${label}</div>
      ${shortText ? `<div style="font-size:11px;line-height:1.5;color:var(--ink);margin-bottom:4px;">${shortText}</div>` : ""}
      ${why ? `<div style="font-size:10px;color:var(--ink-40);margin-bottom:6px;font-style:italic;">${why}</div>` : ""}
      ${url ? `<a href="${url}" target="_blank" style="font-size:10px;color:var(--lapis);display:block;margin-bottom:6px;word-break:break-all;">${url.slice(0, 60)}…</a>` : ""}
      ${!isArticle ? `<div style="display:flex;gap:4px;">
        <button class="compose-btn" data-idx="${i}" data-platform="linkedin" data-text="${encodeURIComponent(text)}" style="flex:1;padding:4px 0;border-radius:3px;background:var(--lapis);color:white;border:none;font-size:10px;cursor:pointer;font-family:inherit;">→ LinkedIn</button>
        <button class="compose-btn" data-idx="${i}" data-platform="x" data-text="${encodeURIComponent(text)}" style="flex:1;padding:4px 0;border-radius:3px;background:var(--ink-70);color:white;border:none;font-size:10px;cursor:pointer;font-family:inherit;">→ X</button>
      </div>` : ""}
    </div>`;
  }).join("");

  box.querySelectorAll(".compose-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const platform = btn.dataset.platform;
      const text = decodeURIComponent(btn.dataset.text);
      const orig = btn.textContent;
      btn.disabled = true;
      btn.textContent = "Opening…";
      try {
        const result = await send({ type: "compose_platform", platform, text });
        if (result.ok) {
          btn.textContent = "Done ✓";
          setTimeout(() => { btn.textContent = orig; btn.disabled = false; }, 2500);
        } else {
          btn.textContent = "Failed";
          setTimeout(() => { btn.textContent = orig; btn.disabled = false; }, 2500);
          const errEl = btn.parentElement.nextElementSibling;
          if (!errEl || !errEl.classList.contains("compose-err")) {
            const e = document.createElement("div");
            e.className = "compose-err";
            e.style.cssText = "font-size:10px;color:var(--ember);margin-top:4px;";
            e.textContent = result.error || "Could not fill composer";
            btn.parentElement.after(e);
          }
        }
      } catch (err) {
        btn.textContent = "Error";
        setTimeout(() => { btn.textContent = orig; btn.disabled = false; }, 2500);
      }
    });
  });
}

async function loadRecommendations(kind) {
  const box = $("rec-output");
  box.innerHTML = `<em style="color:var(--ink-40);font-size:11px;">Loading suggestions…</em>`;
  [$("rec-posts"), $("rec-articles")].forEach(b => b && (b.disabled = true));
  try {
    const result = await send({ type: "get_recommendations", kind });
    if (!result.ok) {
      box.innerHTML = `<em style="color:var(--ember);font-size:11px;">${result.error || "Failed to load"}</em>`;
      return;
    }
    const d = result.data || {};
    const items = d.suggestions ?? d.articles ?? d.items ?? (Array.isArray(d) ? d : []);
    renderRecommendations(items, kind);
  } catch (err) {
    box.innerHTML = `<em style="color:var(--ember);font-size:11px;">Error: ${err.message}</em>`;
  } finally {
    [$("rec-posts"), $("rec-articles")].forEach(b => b && (b.disabled = false));
  }
}

$("rec-posts").addEventListener("click", () => loadRecommendations("posts"));
$("rec-articles").addEventListener("click", () => loadRecommendations("articles"));

// ─── Debug flag (console log gating) ─────────────────────────────────────────

async function initDebugFlag() {
  const { solsocial_debug } = await chrome.storage.local.get("solsocial_debug");
  $("debug-toggle").checked = !!solsocial_debug;
  $("debug-toggle").addEventListener("change", async (e) => {
    await chrome.storage.local.set({ solsocial_debug: e.target.checked });
  });
}

init().then(() => {
  initDebugFlag();
  refreshHealth();
  setInterval(refreshHealth, 3000);
});
