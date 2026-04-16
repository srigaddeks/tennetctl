/**
 * Signal Pipeline E2E Tests
 * Tests: Signal Spec API, Pipeline Queue UI, Sidebar navigation
 */
import { test, expect } from "@playwright/test";
import { navigateAuthed, API_URL } from "../utils/helpers";
import type { APIRequestContext } from "@playwright/test";

// ── Helpers ──────────────────────────────────────────────────────────────────

async function getToken(request: APIRequestContext): Promise<string> {
  const res = await request.post(`${API_URL}/api/v1/auth/local/login`, {
    data: { login: "test123@kreesalis.com", password: "chaitu@GSK07" },
  });
  if (!res.ok()) return "";
  return (await res.json().catch(() => ({}))).access_token ?? "";
}

async function authedGet(request: APIRequestContext, path: string) {
  const token = await getToken(request);
  const res = await request.get(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return { status: res.status(), body: await res.json().catch(() => ({})) };
}

async function authedPost(request: APIRequestContext, path: string, data: object) {
  const token = await getToken(request);
  const res = await request.post(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    data,
  });
  return { status: res.status(), body: await res.json().catch(() => ({})) };
}

async function getOrgId(request: APIRequestContext): Promise<string> {
  const r = await authedGet(request, "/api/v1/am/orgs");
  return r.body?.items?.[0]?.id ?? "";
}

// ── Backend API Tests ──────────────────────────────────────────────────────────

test.describe("Signal Pipeline — Backend APIs", () => {
  test("signal-spec/sessions returns 401 without auth", async ({ request }) => {
    const res = await request.get(`${API_URL}/api/v1/ai/signal-spec/sessions`);
    expect(res.status()).toBe(401);
  });

  test("list sessions returns items + total", async ({ request }) => {
    const res = await authedGet(request, "/api/v1/ai/signal-spec/sessions");
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.items)).toBe(true);
    expect(typeof res.body.total).toBe("number");
  });

  test("create session returns correct schema", async ({ request }) => {
    const orgId = await getOrgId(request);
    expect(orgId).toBeTruthy();

    const res = await authedPost(request, "/api/v1/ai/signal-spec/sessions", {
      connector_type_code: "github",
      org_id: orgId,
      workspace_id: null,
      initial_prompt: null,
    });

    expect(res.status).toBe(201);
    const s = res.body;
    expect(s).toHaveProperty("id");
    expect(s).toHaveProperty("tenant_key");
    expect(s).toHaveProperty("user_id");
    expect(s).toHaveProperty("created_at");
    expect(s.status).toBe("drafting");
    expect(s.connector_type_code).toBe("github");
    expect(Array.isArray(s.conversation_history)).toBe(true);
    expect(s.current_spec).toBeNull();
    expect(s.feasibility_result).toBeNull();
  });

  test("retrieve session by ID", async ({ request }) => {
    const orgId = await getOrgId(request);
    const create = await authedPost(request, "/api/v1/ai/signal-spec/sessions", {
      connector_type_code: "github",
      org_id: orgId,
    });
    expect(create.status).toBe(201);
    const sessionId = create.body.id;

    const get = await authedGet(request, `/api/v1/ai/signal-spec/sessions/${sessionId}`);
    expect(get.status).toBe(200);
    expect(get.body.id).toBe(sessionId);
    expect(get.body.status).toBe("drafting");
  });

  test("approve with no spec returns 422", async ({ request }) => {
    const orgId = await getOrgId(request);
    const create = await authedPost(request, "/api/v1/ai/signal-spec/sessions", {
      connector_type_code: "github",
      org_id: orgId,
    });
    expect(create.status).toBe(201);

    const approve = await authedPost(
      request,
      `/api/v1/ai/signal-spec/sessions/${create.body.id}/approve`,
      { priority_code: "normal" }
    );
    expect([422, 400]).toContain(approve.status);
  });

  test("non-existent session returns 404", async ({ request }) => {
    const res = await authedGet(
      request,
      "/api/v1/ai/signal-spec/sessions/00000000-0000-0000-0000-000000000000"
    );
    expect(res.status).toBe(404);
  });

  test("list sessions pagination shape", async ({ request }) => {
    const res = await authedGet(request, "/api/v1/ai/signal-spec/sessions?limit=3&offset=0");
    expect(res.status).toBe(200);
    expect(res.body.items.length).toBeLessThanOrEqual(3);
    expect(typeof res.body.total).toBe("number");
  });

  test("ai jobs endpoint returns paginated list", async ({ request }) => {
    const orgId = await getOrgId(request);
    const res = await authedGet(request, `/api/v1/ai/jobs?org_id=${orgId}&limit=10`);
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.items)).toBe(true);
  });

  test("ai jobs response shape for pipeline queue", async ({ request }) => {
    const orgId = await getOrgId(request);
    const res = await authedGet(request, `/api/v1/ai/jobs?org_id=${orgId}&limit=5`);
    expect(res.status).toBe(200);
    if (res.body.items.length > 0) {
      const job = res.body.items[0];
      expect(job).toHaveProperty("id");
      expect(job).toHaveProperty("job_type");
      expect(job).toHaveProperty("status_code");
    }
  });
});

// ── UI Tests ──────────────────────────────────────────────────────────────────

test.describe("Signal Pipeline — Sandbox Pages UI", () => {
  test("signals page shows Spec Builder button", async ({ page }) => {
    await navigateAuthed(page, "/sandbox/signals");
    await page.waitForTimeout(2000);
    await expect(page.getByRole("button", { name: /spec builder/i })).toBeVisible({ timeout: 10_000 });
  });

  test("Spec Builder button navigates to /sandbox/signals/new", async ({ page }) => {
    await navigateAuthed(page, "/sandbox/signals");
    await page.waitForTimeout(2000);
    const btn = page.getByRole("button", { name: /spec builder/i });
    await expect(btn).toBeVisible({ timeout: 10_000 });
    await btn.click();
    await page.waitForURL(/\/sandbox\/signals\/new/, { timeout: 10_000 });
    expect(page.url()).toContain("/sandbox/signals/new");
  });

  test("Pipeline Queue page loads with header and controls", async ({ page }) => {
    await navigateAuthed(page, "/sandbox/pipeline-queue");
    await expect(page.getByText("Signal Pipeline Queue")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("button", { name: /refresh/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /new signal/i })).toBeVisible();
    await expect(page.getByText("All").first()).toBeVisible();
  });

  test("Pipeline Queue filter buttons respond to clicks", async ({ page }) => {
    await navigateAuthed(page, "/sandbox/pipeline-queue");
    await expect(page.getByText("Signal Pipeline Queue")).toBeVisible({ timeout: 15_000 });
    for (const label of ["Running", "Failed", "Completed", "Queued", "All"]) {
      const btn = page.getByText(label).first();
      if (await btn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await btn.click();
        await page.waitForTimeout(200);
      }
    }
  });

  test("Pipeline Queue New Signal button navigates to spec wizard", async ({ page }) => {
    await navigateAuthed(page, "/sandbox/pipeline-queue");
    await expect(page.getByText("Signal Pipeline Queue")).toBeVisible({ timeout: 15_000 });
    await page.getByRole("button", { name: /new signal/i }).click();
    await page.waitForURL(/\/sandbox\/signals\/new/, { timeout: 10_000 });
    expect(page.url()).toContain("/sandbox/signals/new");
  });

  test("Spec Builder page loads with content", async ({ page }) => {
    await navigateAuthed(page, "/sandbox/signals/new");
    await page.waitForTimeout(3000);
    const bodyText = await page.evaluate(() => document.body.innerText.toLowerCase());
    expect(bodyText).toMatch(/connector|signal|spec|dataset/i);
  });
});

// ── Sidebar Navigation Tests ──────────────────────────────────────────────────

test.describe("Signal Pipeline — Sidebar Navigation", () => {
  test("sandbox sidebar has Pipeline Queue link", async ({ page }) => {
    await navigateAuthed(page, "/sandbox");
    await page.waitForTimeout(2000);
    await expect(page.getByRole("link", { name: /pipeline queue/i })).toBeVisible({ timeout: 10_000 });
  });

  test("Pipeline Queue sidebar link navigates to correct page", async ({ page }) => {
    await navigateAuthed(page, "/sandbox");
    await page.waitForTimeout(2000);
    const link = page.getByRole("link", { name: /pipeline queue/i });
    await expect(link).toBeVisible({ timeout: 10_000 });
    await link.click();
    await page.waitForURL(/pipeline-queue/, { timeout: 10_000 });
    expect(page.url()).toContain("pipeline-queue");
    await expect(page.getByText("Signal Pipeline Queue")).toBeVisible({ timeout: 10_000 });
  });

  test("sandbox sidebar has Signals link", async ({ page }) => {
    await navigateAuthed(page, "/sandbox");
    await page.waitForTimeout(2000);
    await expect(page.getByRole("link", { name: /^signals$/i }).first()).toBeVisible({ timeout: 10_000 });
  });
});
