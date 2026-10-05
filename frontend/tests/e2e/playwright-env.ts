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

// this does what it can to prevent the app from starting with mismatched target env and url variable assignments
if (!baseUrl || !apiUrl) {
  throw new Error(
    `PLAYWRIGHT_BASE_URL and PLAYWRIGHT_API_URL must be set when PLAYWRIGHT_TARGET_ENV=${targetEnv}`,
  );
}

if (SUPPORTED_ENVS.indexOf(targetEnv as SupportedEnvs) === -1) {
  throw new Error(
    `Unsupported PLAYWRIGHT_TARGET_ENV: ${targetEnv}. Allowed values: ${SUPPORTED_ENVS.join(", ")}`,
  );
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
  testUserEmail: process.env.STAGING_TEST_USER_EMAIL || "",
  testUserPassword: process.env.STAGING_TEST_USER_PASSWORD || "",
  testUserAuthKey: process.env.STAGING_TEST_USER_MFA_KEY || "",
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
