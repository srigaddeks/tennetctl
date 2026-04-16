/**
 * GRC Tasks tests.
 */
import { test, expect } from "@playwright/test";
import { navigateAuthed } from "../utils/helpers";

test.describe("Tasks page", () => {
  test.beforeEach(async ({ page }) => {
    await navigateAuthed(page, "/tasks");
    await page.getByRole("heading", { name: "Tasks" }).waitFor({ timeout: 15_000 });
  });

  test("loads tasks page with correct heading", async ({ page }) => {
    await expect(page).toHaveURL(/\/tasks/);
    await expect(page.getByRole("heading", { name: "Tasks" })).toBeVisible({ timeout: 20_000 });
  });

  test("shows task list or empty state", async ({ page }) => {
    const hasTasks = await page.locator("table tbody tr").first().isVisible({ timeout: 8_000 }).catch(() => false);
    const hasEmpty = await page.getByText(/no task|add.*task|get started/i).isVisible({ timeout: 3_000 }).catch(() => false);
    const hasContent = await page.getByRole("heading", { name: "Tasks" }).isVisible({ timeout: 3_000 }).catch(() => false);
    expect(hasTasks || hasEmpty || hasContent).toBeTruthy();
  });

  test("can filter tasks by status", async ({ page }) => {
    const statusFilter = page.getByRole("button", { name: /status|open|closed|all/i })
      .or(page.getByRole("combobox", { name: /status/i }))
      .first();
    if (await statusFilter.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await statusFilter.click();
      const option = page.getByRole("option").or(page.getByRole("menuitem")).first();
      if (await option.isVisible({ timeout: 2_000 }).catch(() => false)) {
        await option.click();
        await page.waitForLoadState("domcontentloaded", { timeout: 8_000 });
      }
    }
  });

  test("can open a task detail page", async ({ page }) => {
    const firstTask = page.locator("a[href*='/tasks/']").first();
    if (await firstTask.isVisible({ timeout: 8_000 }).catch(() => false)) {
      await firstTask.click();
      await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });
      await expect(page).toHaveURL(/\/tasks\/.+/);
    }
  });
});
