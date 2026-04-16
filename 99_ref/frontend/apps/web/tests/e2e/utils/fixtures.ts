/**
 * Custom Playwright fixtures that provide a pre-authenticated page
 * and org/workspace context for every test.
 */
import { test as base, expect, type Page } from "@playwright/test";

type TestFixtures = {
  /** Page that is already on the dashboard, org/workspace selected. */
  authedPage: Page;
};

export const test = base.extend<TestFixtures>({
  authedPage: async ({ page }, use) => {
    // Navigate to dashboard — storage state already loaded from setup
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded", { timeout: 15_000 });
    await use(page);
  },
});

export { expect };
