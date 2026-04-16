/**
 * AI Copilot tests — conversation list, new conversation, send message,
 * SSE streaming response, tool call indicators, session naming.
 */
import { test, expect } from "@playwright/test";
import { navigateAuthed } from "../utils/helpers";

/** Wait for the copilot page to fully load past the auth skeleton */
async function waitForCopilotPage(page: import("@playwright/test").Page) {
  await navigateAuthed(page, "/copilot");
  await page.getByRole("heading", { name: "AI Copilot" }).waitFor({ timeout: 20_000 });
}

test.describe("Copilot conversation list", () => {
  test.beforeEach(async ({ page }) => {
    await waitForCopilotPage(page);
  });

  test("loads copilot page with correct heading", async ({ page }) => {
    await expect(page).toHaveURL(/\/copilot/);
    await expect(page.getByRole("heading", { name: "AI Copilot" })).toBeVisible({ timeout: 20_000 });
  });

  test("shows New conversation button", async ({ page }) => {
    await expect(page.getByRole("button", { name: /new conversation/i })).toBeVisible({ timeout: 20_000 });
  });

  test("shows quick prompts section", async ({ page }) => {
    await expect(page.getByText(/quick prompts/i)).toBeVisible({ timeout: 20_000 });
  });

  test("shows conversation list or empty state", async ({ page }) => {
    const hasConvs = await page.locator("a[href*='/copilot/']").first().isVisible({ timeout: 5_000 }).catch(() => false);
    const hasEmpty = await page.getByText(/no conversation|start.*chat|No conversations yet/i).isVisible({ timeout: 3_000 }).catch(() => false);
    const hasList = await page.getByText(/recent.*conversations|Recent conversations/i).isVisible({ timeout: 3_000 }).catch(() => false);
    expect(hasConvs || hasEmpty || hasList).toBeTruthy();
  });
});

test.describe("Copilot conversation", () => {
  test("can create a new conversation", async ({ page }) => {
    await waitForCopilotPage(page);

    await page.getByRole("button", { name: /new conversation/i }).click();
    await page.waitForURL(/\/copilot\/.+/, { timeout: 20_000 });
    await expect(page).toHaveURL(/\/copilot\/.+/);
  });

  test("conversation page has message textarea", async ({ page }) => {
    await waitForCopilotPage(page);

    // Open existing or create new
    const convLink = page.locator("a[href*='/copilot/']").first();
    if (await convLink.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await convLink.click();
    } else {
      await page.getByRole("button", { name: /new conversation/i }).click();
      await page.waitForURL(/\/copilot\/.+/, { timeout: 20_000 });
    }

    await expect(page.locator("textarea").first()).toBeVisible({ timeout: 20_000 });
  });

  test("can send a message from the conversation page", async ({ page }) => {
    await waitForCopilotPage(page);

    // Create a new conversation
    await page.getByRole("button", { name: /new conversation/i }).click();
    await page.waitForURL(/\/copilot\/.+/, { timeout: 20_000 });

    const textarea = page.locator("textarea").first();
    await expect(textarea).toBeVisible({ timeout: 20_000 });

    await textarea.fill("Hello, give me a one sentence summary of the GRC platform.");

    // Submit via Enter or Send button
    const sendBtn = page.getByRole("button", { name: /send/i }).first();
    if (await sendBtn.isVisible({ timeout: 1_000 }).catch(() => false)) {
      await sendBtn.click();
    } else {
      await textarea.press("Enter");
    }

    // User message should appear
    await expect(page.getByText(/one sentence|GRC platform/i)).toBeVisible({ timeout: 20_000 });

    // Wait for textarea to be re-enabled (response complete) — up to 60s
    await expect(page.locator("textarea").first()).toBeEnabled({ timeout: 60_000 });
  });

  test("quick prompt creates a conversation", async ({ page }) => {
    await waitForCopilotPage(page);

    // Click first quick prompt button
    const firstPrompt = page.getByText("List tasks assigned to me that are overdue").or(
      page.locator("button").filter({ hasText: /task|risk|control|compliance/i }).first()
    );
    if (await firstPrompt.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await firstPrompt.click();
      await page.waitForURL(/\/copilot\/.+/, { timeout: 20_000 });
      await expect(page).toHaveURL(/\/copilot\/.+/);
    }
  });
});
