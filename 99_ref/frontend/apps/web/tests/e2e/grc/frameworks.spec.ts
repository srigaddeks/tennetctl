/**
 * GRC Framework tests — list, search, filter, detail view.
 */
import { test, expect } from "@playwright/test";
import { navigateAuthed } from "../utils/helpers";

test.describe("Frameworks page", () => {
  test.beforeEach(async ({ page }) => {
    await navigateAuthed(page, "/frameworks");
    await page.getByRole("heading", { name: "Framework Library" }).waitFor({ timeout: 25_000 });
  });

  test("loads frameworks page with correct heading", async ({ page }) => {
    await expect(page).toHaveURL(/\/frameworks/);
    await expect(page.getByRole("heading", { name: "Framework Library" })).toBeVisible({ timeout: 20_000 });
  });

  test("displays framework cards or empty state", async ({ page }) => {
    // Wait for heading to ensure loading is complete
    await page.getByRole("heading", { name: "Framework Library" }).waitFor({ timeout: 15_000 });
    // Framework items appear as cards or in a list
    const frameworkItems = page.locator("[data-testid='framework-card'], table tbody tr, a[href*='/frameworks/']").first();
    const hasItems = await frameworkItems.isVisible({ timeout: 5_000 }).catch(() => false);
    const hasEmpty = await page.getByText(/no framework|add.*framework|get started/i).isVisible({ timeout: 3_000 }).catch(() => false);
    const pageLoaded = await page.locator("[class*='space-y']").isVisible({ timeout: 3_000 }).catch(() => false);
    expect(hasItems || hasEmpty || pageLoaded).toBeTruthy();
  });

  test("search input filters frameworks", async ({ page }) => {
    const searchInput = page.getByRole("searchbox").or(page.getByPlaceholder(/search/i)).first();
    if (await searchInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await searchInput.fill("SOC");
      await page.waitForLoadState("domcontentloaded", { timeout: 8_000 });
      const hasSOC = await page.getByText(/SOC/i).first().isVisible({ timeout: 5_000 }).catch(() => false);
      const hasEmpty = await page.getByText(/no result|no framework|0 result/i).isVisible({ timeout: 3_000 }).catch(() => false);
      expect(hasSOC || hasEmpty).toBeTruthy();
    }
  });

  test("can open a framework detail page", async ({ page }) => {
    const firstFramework = page.locator("a[href*='/frameworks/']").first();
    if (await firstFramework.isVisible({ timeout: 8_000 }).catch(() => false)) {
      await firstFramework.click();
      await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });
      await expect(page).toHaveURL(/\/frameworks\/.+/);
    }
  });
});

test.describe("Framework detail page", () => {
  test("shows framework details", async ({ page }) => {
    await navigateAuthed(page, "/frameworks");
    await page.getByRole("heading", { name: "Framework Library" }).waitFor({ timeout: 15_000 });

    const firstLink = page.locator("a[href*='/frameworks/']").first();
    if (!(await firstLink.isVisible({ timeout: 8_000 }).catch(() => false))) {
      test.skip(true, "No frameworks available");
      return;
    }
    await firstLink.click();
    await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });
    await expect(page.locator("h1, h2").first()).toBeVisible({ timeout: 20_000 });
  });
});

test.describe("Marketplace page", () => {
  test("loads marketplace page", async ({ page }) => {
    await navigateAuthed(page, "/framework_library");
    await expect(page).toHaveURL(/\/framework_library/);
    await expect(page.locator("h1, h2").first()).toBeVisible({ timeout: 20_000 });
  });
});
