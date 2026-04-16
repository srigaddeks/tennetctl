import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false, // sequential — tests share login state
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
  ],
  timeout: 30_000,
  expect: { timeout: 8_000 },
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",
    headless: process.env.HEADED !== "1",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    // Setup project: logs in and saves auth state
    {
      name: "setup",
      testMatch: "**/auth.setup.ts",
      use: { ...devices["Desktop Chrome"] },
    },
    // All feature tests re-use the saved auth state
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: "tests/e2e/.auth/user.json",
      },
      dependencies: ["setup"],
    },
  ],
  webServer: process.env.CI
    ? {
        command: "pnpm start",
        port: 3000,
        reuseExistingServer: false,
        timeout: 60_000,
      }
    : {
        command: "pnpm dev",
        port: 3000,
        reuseExistingServer: true, // reuse local dev server
        timeout: 60_000,
      },
});
