/**
 * Settings tests — profile, security, org settings.
 */
import { test, expect } from "@playwright/test";
import { navigateAuthed } from "../utils/helpers";

test.describe("Profile settings", () => {
  test.beforeEach(async ({ page }) => {
    await navigateAuthed(page, "/settings/profile");
    await page.getByRole("heading", { name: "Profile" }).waitFor({ timeout: 15_000 });
  });

  test("loads profile settings page", async ({ page }) => {
    await expect(page).toHaveURL(/\/settings\/profile/);
    await expect(page.getByRole("heading", { name: "Profile" })).toBeVisible({ timeout: 20_000 });
  });

  test("shows user email on profile page", async ({ page }) => {
    // Email appears as text after profile data loads (async)
    await expect(page.getByText(/test123@kreesalis\.com/i).first()).toBeVisible({ timeout: 15_000 });
  });
});

test.describe("Security settings", () => {
  test("loads security settings page", async ({ page }) => {
    await navigateAuthed(page, "/settings/security");
    await expect(page).toHaveURL(/\/settings\/security/);
    await expect(page.locator("h1, h2").first()).toBeVisible({ timeout: 20_000 });
  });
});

test.describe("Settings sidebar navigation", () => {
  test("can navigate between settings sections", async ({ page }) => {
    await navigateAuthed(page, "/settings/profile");
    await page.getByRole("heading", { name: "Profile" }).waitFor({ timeout: 15_000 });

    const securityLink = page.getByRole("link", { name: /security/i }).first();
    if (await securityLink.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await securityLink.click();
      await expect(page).toHaveURL(/\/settings\/security/, { timeout: 8_000 });
    }
  });
});
