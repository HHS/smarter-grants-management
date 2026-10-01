/*
  Temporary API-key modal authentication helpers
  This module is intentionally scoped to frontend-dev/frontend-staging deployed hosts and is
  called by authenticate-e2e-user-utils when the PLAYWRIGHT_BASE_URL hostname
  matches the temporary modal URL gate.
*/

import { type Page } from "@playwright/test";
import playwrightEnv from "tests/e2e/playwright-env";
import { openMobileNav } from "tests/e2e/playwrightUtils";

const { baseUrl } = playwrightEnv;
const TEMPORARY_MODAL_HOST_PREFIXES = ["frontend-dev-", "frontend-staging-"];
const TEMPORARY_MODAL_HOST_SUFFIX = ".us-east-1.elb.amazonaws.com";
const TEMPORARY_MODAL_LOGIN_TIMEOUT_MS = 60_000;

const isTemporaryModalHost = (hostname: string): boolean =>
  TEMPORARY_MODAL_HOST_PREFIXES.some((prefix) => hostname.startsWith(prefix)) &&
  hostname.endsWith(TEMPORARY_MODAL_HOST_SUFFIX);

const effectiveTemporaryModalBaseUrl = (() => {
  try {
    const parsedUrl = new URL(baseUrl);
    if (
      isTemporaryModalHost(parsedUrl.hostname) &&
      parsedUrl.protocol === "https:"
    ) {
      parsedUrl.protocol = "http:";
      return parsedUrl.toString();
    }
  } catch {
    return baseUrl;
  }

  return baseUrl;
})();

export const isTemporaryApiKeyModalFlow = (): boolean => {
  try {
    const { hostname } = new URL(baseUrl);
    return isTemporaryModalHost(hostname);
  } catch {
    return false;
  }
};

const clickTemporaryApiKeySignInTrigger = async (page: Page) => {
  const candidateTriggers = [
    page.getByRole("button", { name: /open login modal/i }).first(),
    page.getByRole("button", { name: /sign in/i }).first(),
    page.getByRole("link", { name: /sign in/i }).first(),
  ];

  for (const trigger of candidateTriggers) {
    const isVisible = await trigger
      .isVisible({ timeout: 3000 })
      .catch(() => false);
    if (isVisible) {
      await trigger.click();
      return;
    }
  }

  throw new Error(
    "Temporary API-key modal login failed: no visible Sign in trigger found.",
  );
};

const waitForTemporaryApiKeyModalReady = async (page: Page) => {
  const apiKeyInput = page.locator('input[name="apiKey"]').first();

  for (let attempt = 0; attempt < 5; attempt += 1) {
    const inputVisible = await apiKeyInput.isVisible().catch(() => false);
    if (inputVisible) {
      return apiKeyInput;
    }

    await clickTemporaryApiKeySignInTrigger(page);
    await page.waitForTimeout(800);
  }

  throw new Error(
    [
      "Temporary API-key modal login failed: API-key modal did not open after clicking Sign in.",
      `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
      `Base URL: ${effectiveTemporaryModalBaseUrl}.`,
    ].join("\n"),
  );
};

const isAnySignInTriggerVisible = async (page: Page): Promise<boolean> => {
  const triggerLocators = [
    page.getByRole("button", { name: /open login modal/i }).first(),
    page.getByRole("button", { name: /sign in/i }).first(),
    page.getByRole("link", { name: /sign in/i }).first(),
  ];

  for (const locator of triggerLocators) {
    const visible = await locator.isVisible().catch(() => false);
    if (visible) {
      return true;
    }
  }

  return false;
};

const waitForTemporaryApiKeyModalLoginState = async (page: Page) => {
  const startedAt = Date.now();
  const invalidApiKeyAlert = page
    .getByRole("alert")
    .filter({ hasText: /invalid api key/i })
    .first();
  const authenticatedMarker = page
    .locator(
      'button[aria-controls="Account"], [data-testid="user-menu-trigger"], a:has-text("Sign out"), button:has-text("Sign out")',
    )
    .first();
  const loginHeading = page.getByRole("heading", {
    name: /login with api key/i,
  });

  while (Date.now() - startedAt < TEMPORARY_MODAL_LOGIN_TIMEOUT_MS) {
    if (await invalidApiKeyAlert.isVisible().catch(() => false)) {
      throw new Error(
        [
          "Temporary API-key modal login failed: UI returned 'Invalid API key'.",
          `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
          `Base URL: ${effectiveTemporaryModalBaseUrl}.`,
          "Set E2E_API_KEY (or TEST_USER_API_KEY fallback) to a valid key for this host.",
        ].join("\n"),
      );
    }

    if (await authenticatedMarker.isVisible().catch(() => false)) {
      return;
    }

    const signInVisible = await isAnySignInTriggerVisible(page);
    const loginModalVisible = await loginHeading.isVisible().catch(() => false);
    if (!signInVisible && !loginModalVisible) {
      return;
    }

    await page.waitForTimeout(500);
  }

  throw new Error(
    [
      "Temporary API-key modal login timed out waiting for authenticated state.",
      "No account marker became visible and Sign in trigger/modal state did not resolve to authenticated.",
      `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
      `Base URL: ${effectiveTemporaryModalBaseUrl}.`,
    ].join("\n"),
  );
};

export const authenticateWithTemporaryApiKeyModal = async (
  page: Page,
  isMobile: boolean,
) => {
  const apiKeyForTemporaryModal = playwrightEnv.e2eApiKey;

  if (!apiKeyForTemporaryModal) {
    throw new Error(
      [
        "Unable to run temporary API-key modal login: neither E2E_API_KEY nor TEST_USER_API_KEY is set.",
        `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
        `Base URL: ${effectiveTemporaryModalBaseUrl}.`,
        "This temporary fallback is enabled only for frontend-dev-* or frontend-staging-* URLs.",
      ].join("\n"),
    );
  }

  // Temporary fallback. Remove after dev/staging auth is unified.

  await page.goto(effectiveTemporaryModalBaseUrl, {
    waitUntil: "domcontentloaded",
  });

  if (isMobile) {
    await openMobileNav(page);
  }

  const apiKeyInput = await waitForTemporaryApiKeyModalReady(page);
  await apiKeyInput.fill(apiKeyForTemporaryModal);

  const loginButton = page.getByRole("button", { name: /^login$/i }).first();
  await loginButton.waitFor({
    state: "visible",
    timeout: TEMPORARY_MODAL_LOGIN_TIMEOUT_MS,
  });
  await loginButton.click();

  await waitForTemporaryApiKeyModalLoginState(page);
};
