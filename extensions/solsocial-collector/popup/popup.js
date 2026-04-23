/* SolSocial Collector — Popup controller */

const $ = (id) => document.getElementById(id);

async function send(msg) {
  return chrome.runtime.sendMessage(msg);
}

// ─── Render helpers ──────────────────────────────────────────────────────────

function showAuth() {
  $("auth-panel").style.display = "block";
  $("status-panel").style.display = "none";
}

function showStatus(status) {
  $("auth-panel").style.display = "none";
  $("status-panel").style.display = "block";

  const user = status.user || {};
  $("display-name").textContent = user.display_name || user.email || "Signed in";
  $("display-email").textContent = user.email || "";
  $("avatar").textContent = (user.display_name || user.email || "?")[0].toUpperCase();
  $("today-count").textContent = status.todayCount ?? 0;
  $("queue-size").textContent = status.queueSize ?? 0;

  const toggle = $("toggle-btn");
  if (status.enabled) {
    toggle.classList.add("on");
  } else {
    toggle.classList.remove("on");
  }
}

// ─── Init ─────────────────────────────────────────────────────────────────────

async function init() {
  const status = await send({ type: "status" });
  if (status.signedIn) {
    showStatus(status);
  } else {
    showAuth();
  }
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
      $("auth-error").textContent = result.error || "Sign in failed.";
    }
  } catch (err) {
    $("auth-error").textContent = err.message || "Sign in failed.";
  } finally {
    $("signin-btn").disabled = false;
    $("signin-btn").textContent = "Sign in";
  }
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
    const toggle = $("toggle-btn");
    result.enabled ? toggle.classList.add("on") : toggle.classList.remove("on");
  }
});

// ─── Flush ───────────────────────────────────────────────────────────────────

$("flush-btn").addEventListener("click", async () => {
  $("flush-btn").textContent = "Flushing…";
  $("flush-btn").disabled = true;
  await send({ type: "flush" });
  const status = await send({ type: "status" });
  showStatus(status);
  $("flush-btn").textContent = "Flush queue now";
  $("flush-btn").disabled = false;
});

// Allow enter key on password field
$("password").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("signin-btn").click();
});

init();
