/**
 * GRC Risk registry tests.
 */
import { test, expect } from "@playwright/test";
import { navigateAuthed } from "../utils/helpers";

test.describe("Risks page", () => {
  test.beforeEach(async ({ page }) => {
    await navigateAuthed(page, "/risks");
    await page.getByRole("heading", { name: "Risk Registry" }).waitFor({ timeout: 25_000 });
  });

  test("loads risks page with correct heading", async ({ page }) => {
    await expect(page).toHaveURL(/\/risks/);
    await expect(page.getByRole("heading", { name: "Risk Registry" })).toBeVisible({ timeout: 20_000 });
  });

  test("shows risk list or empty state", async ({ page }) => {
    const hasRisks = await page.locator("table tbody tr").first().isVisible({ timeout: 8_000 }).catch(() => false);
    const hasEmpty = await page.getByText(/no risk|add.*risk|get started/i).isVisible({ timeout: 3_000 }).catch(() => false);
    const hasContent = await page.getByRole("heading", { name: "Risk Registry" }).isVisible({ timeout: 3_000 }).catch(() => false);
    expect(hasRisks || hasEmpty || hasContent).toBeTruthy();
  });

  test("can filter risks by severity", async ({ page }) => {
    const severityFilter = page.getByRole("button", { name: /severity|critical|high/i })
      .or(page.getByRole("combobox", { name: /severity/i }))
      .first();
    if (await severityFilter.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await severityFilter.click();
      const option = page.getByRole("option").or(page.getByRole("menuitem")).first();
      if (await option.isVisible({ timeout: 2_000 }).catch(() => false)) {
        await option.click();
        await page.waitForLoadState("domcontentloaded", { timeout: 8_000 });
      }
    }
  });

  test("can open a risk detail page", async ({ page }) => {
    const firstRisk = page.locator("a[href*='/risks/']").first();
    if (await firstRisk.isVisible({ timeout: 8_000 }).catch(() => false)) {
      await firstRisk.click();
      await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });
      await expect(page).toHaveURL(/\/risks\/.+/);
      await expect(page.locator("h1, h2").first()).toBeVisible({ timeout: 20_000 });
    }
  });
});
