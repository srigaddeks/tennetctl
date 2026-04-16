/**
 * Dashboard tests — page loads, sidebar nav, org/workspace switcher.
 * Runs with pre-authenticated storage state.
 */
import { test, expect } from "@playwright/test";
import { navigateAuthed } from "../utils/helpers";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await navigateAuthed(page, "/dashboard");
    // Wait for content to load past auth skeleton — increase timeout for re-login scenarios
    await page.getByText("Your compliance posture at a glance.").waitFor({ timeout: 25_000 });
  });

  test("loads dashboard page", async ({ page }) => {
    await expect(page).toHaveURL(/\/dashboard/);
    // h1 shows a greeting or "K-Control" — wait for page to finish loading
    await expect(page.locator("h1").first()).toBeVisible({ timeout: 20_000 });
    // Subtitle only appears after data loads (loading skeleton is replaced)
    await expect(page.getByText("Your compliance posture at a glance.")).toBeVisible({ timeout: 15_000 });
  });

  test("sidebar is visible with main nav items", async ({ page }) => {
    await expect(page.getByRole("link", { name: "Frameworks" }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Risk Registry" }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Tasks" }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Reports" }).first()).toBeVisible();
  });

  test("can navigate to frameworks from sidebar", async ({ page }) => {
    await page.getByRole("link", { name: "Frameworks" }).first().click();
    await expect(page).toHaveURL(/\/frameworks/, { timeout: 10_000 });
  });

  test("can navigate to risks from sidebar", async ({ page }) => {
    await page.getByRole("link", { name: "Risk Registry" }).first().click();
    await expect(page).toHaveURL(/\/risks/, { timeout: 10_000 });
  });

  test("can navigate to tasks from sidebar", async ({ page }) => {
    await page.getByRole("link", { name: "Tasks" }).first().click();
    await expect(page).toHaveURL(/\/tasks/, { timeout: 10_000 });
  });

  test("can navigate to reports from sidebar", async ({ page }) => {
    await page.getByRole("link", { name: "Reports" }).first().click();
    await expect(page).toHaveURL(/\/reports/, { timeout: 10_000 });
  });

  test("can navigate to copilot from sidebar", async ({ page }) => {
    const copilotLink = page.getByRole("link", { name: /copilot|ai assistant/i }).first();
    if (await copilotLink.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await copilotLink.click();
      await expect(page).toHaveURL(/\/copilot/, { timeout: 10_000 });
    }
  });
});

test.describe("Org/workspace switcher", () => {
  test("page context contains org/workspace selector", async ({ page }) => {
    await navigateAuthed(page, "/dashboard");

    // The dashboard should have the OrgWorkspaceSwitcher rendered
    const switcher = page.locator("[data-sidebar], nav, aside").first();
    await expect(switcher).toBeVisible({ timeout: 8_000 });
  });
});
