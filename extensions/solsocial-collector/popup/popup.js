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
  $("open-app").href = appUrl;
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

init();
