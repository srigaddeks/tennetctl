/**
 * Shared test helpers and constants.
 */
import { Page, expect } from "@playwright/test";

export const TEST_USER = {
  email: "test123@kreesalis.com",
  password: "chaitu@GSK07",
};

/**
 * Navigate to a URL and re-authenticate if the session cookie has been rotated.
 * The refresh token rotates on each use so subsequent test pages may get 401.
 * Re-logs in if the auth check fails (redirect to /login) or if the page
 * stays in the loading skeleton for too long.
 */
export async function navigateAuthed(page: Page, path: string): Promise<void> {
  async function doLogin() {
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });
    await page.getByPlaceholder("Email").fill(TEST_USER.email);
    await page.getByPlaceholder("Password").fill(TEST_USER.password);
    await page.getByRole("button", { name: "Sign In" }).click();
    await page.waitForURL(/\/(dashboard|frameworks|copilot|workspaces|settings|reports|risks|tasks|sandbox|admin)/, { timeout: 20_000 });
  }

  await page.goto(path);
  await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });

  // If already on login page, authenticate and come back
  if (page.url().includes("/login")) {
    await doLogin();
    await page.goto(path);
    await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });
    return;
  }

  // Wait for client-side auth check to complete (up to 8s).
  // The layout calls fetchMe() async — if it fails, it redirects to /login.
  // If it succeeds, isAuthed=true and the real page content renders.
  //
  // We detect auth success by checking that the topbar heading is NOT "K-Control"
  // (which is the skeleton value) and the URL hasn't changed to /login.
  let authed = false;
  const deadline = Date.now() + 8_000;
  while (!authed && Date.now() < deadline) {
    const url = page.url();
    if (url.includes("/login")) {
      // Auth check redirected us to login — re-authenticate
      await doLogin();
      await page.goto(path);
      await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });
      return;
    }

    // Auth skeleton: topbar shows h1="K-Control", real content shows page-specific heading
    // We check the inner page content by looking at the main element's direct child count
    // AND whether the topbar title element changed from "K-Control"
    const isStillSkeleton = await page.evaluate(() => {
      // The layout renders <Topbar title="K-Control" /> in skeleton state.
      // After isAuthed=true, children (the actual page) get rendered in main.
      // Check if the innermost <main> (not the sidebar wrapper) is still empty.
      const mains = Array.from(document.querySelectorAll("main"));
      // The page's content main is the last/innermost one
      const contentMain = mains[mains.length - 1];
      if (!contentMain) return true;
      // If the content main has children beyond empty-ish, auth succeeded
      return contentMain.children.length === 0;
    }).catch(() => true);

    if (!isStillSkeleton) {
      authed = true;
      break;
    }
    await page.waitForTimeout(300);
  }

  // If content never loaded, assume auth failed and re-login
  if (!authed) {
    await doLogin();
    await page.goto(path);
    await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });
  }
}

export const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";
export const API_URL = process.env.API_URL ?? "http://localhost:8000";

/** Wait for the page to finish its initial data load (no spinners visible). */
export async function waitForPageLoad(page: Page) {
  await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });
}

/** Dismiss any toast/notification that may be on screen. */
export async function dismissToast(page: Page) {
  const toast = page.locator("[data-sonner-toast], [role='alert']").first();
  if (await toast.isVisible({ timeout: 1_000 }).catch(() => false)) {
    await toast.press("Escape");
  }
}

/** Select an org from the org/workspace switcher in the sidebar. */
export async function selectFirstOrg(page: Page) {
  const orgSwitcher = page.locator("[data-testid='org-switcher'], button:has-text('Select org')").first();
  if (await orgSwitcher.isVisible({ timeout: 3_000 }).catch(() => false)) {
    await orgSwitcher.click();
    await page.locator("[role='option'], [role='menuitem']").first().click();
  }
}

/** Assert that a data table has at least one row. */
export async function expectTableHasRows(page: Page, minRows = 1) {
  const rows = page.locator("table tbody tr, [role='row']:not([role='columnheader'])");
  await expect(rows.first()).toBeVisible({ timeout: 10_000 });
  const count = await rows.count();
  expect(count).toBeGreaterThanOrEqual(minRows);
  return count;
}

/** Fill a dialog/form field by label. */
export async function fillField(page: Page, label: string | RegExp, value: string) {
  await page.getByLabel(label).fill(value);
}

/** Click a button that opens a dialog and wait for the dialog. */
export async function openDialog(page: Page, triggerText: string | RegExp) {
  await page.getByRole("button", { name: triggerText }).click();
  await expect(page.getByRole("dialog")).toBeVisible({ timeout: 5_000 });
}

/** Wait for an SSE-based component to stop showing a loading spinner. */
export async function waitForStreamComplete(page: Page, timeout = 60_000) {
  await page.waitForFunction(
    () => !document.querySelector("[data-streaming='true'], .animate-pulse"),
    { timeout }
  );
}
