/**
 * Reviewer conclusion:
 * This module now enforces a single, explicit environment model (local/staging)
 * and emits structured bootstrap errors that are easier to triage in CI logs.
 */

import fs from "fs";
import path from "path";
import dotenv from "dotenv";

// Load environment variables from .env.local if it exists
const envPath = path.resolve(__dirname, "..", "..", ".env.local");
if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath, quiet: true });
}

export const SUPPORTED_ENVS = ["local", "staging"] as const;

export type SupportedEnvs = (typeof SUPPORTED_ENVS)[number];

const targetEnv = process.env.PLAYWRIGHT_TARGET_ENV || "local";

const isLocal = targetEnv === "local";
const baseUrl =
  process.env.PLAYWRIGHT_BASE_URL || (isLocal ? "http://127.0.0.1:3000" : "");
const apiUrl =
  process.env.PLAYWRIGHT_API_URL || (isLocal ? "http://127.0.0.1:8089" : "");

// Keep environment bootstrap failures in one format so CI output is consistent.
const buildPlaywrightEnvError = ({
  step,
  inspect,
  likelyCause,
  details,
}: {
  step: string;
  inspect: string;
  likelyCause: string;
  details: string;
}): Error =>
  new Error(
    [
      `Error time (UTC): ${new Date().toISOString()}`,
      "Flow: playwright-env-bootstrap",
      `Failed step: ${step}`,
      `What to inspect: ${inspect}`,
      `Likely cause: ${likelyCause}`,
      `Target environment: ${targetEnv || "unknown"}`,
      `PLAYWRIGHT_BASE_URL: ${baseUrl || "unset"}`,
      `PLAYWRIGHT_API_URL: ${apiUrl || "unset"}`,
      details,
    ].join("\n"),
  );

// this does what it can to prevent the app from starting with mismatched target env and url variable assignments
if (!baseUrl || !apiUrl) {
  throw buildPlaywrightEnvError({
    step: "validate-playwright-target-urls",
    inspect:
      "PLAYWRIGHT_BASE_URL, PLAYWRIGHT_API_URL, and target-specific CI inputs",
    likelyCause:
      "target environment URLs were not set before Playwright environment bootstrap",
    details:
      "PLAYWRIGHT_BASE_URL and PLAYWRIGHT_API_URL must be set for the selected PLAYWRIGHT_TARGET_ENV.",
  });
}

if (SUPPORTED_ENVS.indexOf(targetEnv as SupportedEnvs) === -1) {
  throw buildPlaywrightEnvError({
    step: "validate-playwright-target-env",
    inspect: "PLAYWRIGHT_TARGET_ENV value provided by workflow or local shell",
    likelyCause: "unsupported target environment was passed to Playwright",
    details: `Unsupported PLAYWRIGHT_TARGET_ENV: ${targetEnv}. Allowed values: ${SUPPORTED_ENVS.join(", ")}`,
  });
}

// Environment for web server
const webServerEnv: Record<string, string> = Object.fromEntries(
  Object.entries({
    ...process.env,
    NEW_RELIC_ENABLED: "false", // disable New Relic for E2E
  }).filter(([, value]) => typeof value === "string"),
);

const playwrightEnv = {
  webServerEnv,
  baseUrl,
  apiUrl,
  targetEnv,
  isCi: process.env.CI,
  totalShards: process.env.TOTAL_SHARDS,
  currentShard: process.env.CURRENT_SHARD,
  // Comma separated list of Playwright project (browser) names to run (e.g.
  // "Chrome"). Blank means run every project defined for the target.
  playwrightProjects: process.env.PLAYWRIGHT_PROJECTS || "",
  clientSessionSecret:
    process.env.SESSION_SECRET_OVERRIDE || process.env.SESSION_SECRET,
  // A single API-key variable drives auth in both environments:
  // local uses it for JWT fetch; staging uses it in the API-key modal.
  // Direct API key for the seeded E2E test user.
  // local uses this key with GET /v1/internal/api-jwt to build a spoofed
  // session cookie; staging uses the same key in the UI API-key login modal.
  // STAGING_TEST_USER_API_KEY is accepted as a fallback for CI compatibility.
  testUserApiKey:
    process.env.TEST_USER_API_KEY ||
    process.env.STAGING_TEST_USER_API_KEY ||
    "",
  // Legacy manager key retained for older flows and rollback references. This is
  // not used by the supported direct API-key E2E login flow.
  testUserManagerApiKey: process.env.TEST_USER_MANAGER_API_KEY || "",
  // Flag indicating if the E2E environment has a virus scanner for infected file testing.
  // Enabled by default in all environments as the scan currently works in both local and Staging env;
  // can be explicitly disabled via E2E_INFECTED_FILE_SCANNER=false.
  hasInfectedFileScanner: process.env.E2E_INFECTED_FILE_SCANNER !== "false",
};

export default playwrightEnv;
