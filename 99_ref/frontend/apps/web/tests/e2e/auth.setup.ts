/**
 * Global auth setup — runs once before all tests.
 * Logs in as the test user and saves browser storage state so all
 * subsequent tests start already authenticated.
 */
import { test as setup, expect } from "@playwright/test";

const AUTH_FILE = "tests/e2e/.auth/user.json";

setup("authenticate", async ({ page }) => {
  await page.goto("/login");
  await page.waitForLoadState("domcontentloaded", { timeout: 20_000 });

  await page.getByPlaceholder("Email").fill("test123@kreesalis.com");
  await page.getByPlaceholder("Password").fill("chaitu@GSK07");
  await page.getByRole("button", { name: "Sign In" }).click();

  // Should land on any authenticated route after login
  await page.waitForURL(/\/(dashboard|frameworks|copilot|workspaces|reports|risks|tasks|settings|sandbox)/, { timeout: 20_000 });

  // Save storage state (cookies + localStorage) for reuse
  await page.context().storageState({ path: AUTH_FILE });
});
