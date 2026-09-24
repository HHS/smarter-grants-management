import fs from "fs";
import path from "path";
import { defineConfig, devices, Project } from "@playwright/test";

import playwrightEnv from "./e2e/playwright-env";

type DeferredTestConfig = {
  testFiles?: string[];
};

const deferredTestFilesConfigPath = path.resolve(
  __dirname,
  "e2e",
  "deferred-test-files.json",
);

const normalizeDeferredTestPath = (testPath: string): string => {
  const normalizedPath = testPath.replace(/\\/g, "/");
  if (normalizedPath.startsWith("tests/e2e/")) {
    return normalizedPath.replace("tests/e2e/", "");
  }
  if (normalizedPath.startsWith("./e2e/")) {
    return normalizedPath.replace("./e2e/", "");
  }
  if (normalizedPath.startsWith("e2e/")) {
    return normalizedPath.replace("e2e/", "");
  }
  return normalizedPath;
};

const loadDeferredTestIgnores = (): string[] => {
  if (!fs.existsSync(deferredTestFilesConfigPath)) {
    return [];
  }

  try {
    const parsedConfig = JSON.parse(
      fs.readFileSync(deferredTestFilesConfigPath, "utf-8"),
    ) as DeferredTestConfig;
    const testFiles = Array.isArray(parsedConfig.testFiles)
      ? parsedConfig.testFiles
      : [];

    return testFiles
      .filter((entry): entry is string => typeof entry === "string")
      .map((entry) => normalizeDeferredTestPath(entry));
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(
      `Failed to parse deferred test list at ${deferredTestFilesConfigPath}: ${message}`,
    );
  }
};

// Keep temporary file-level skips in JSON so flaky specs can be deferred
// without editing test code. Paths are interpreted relative to `testDir`.
const deferredTestIgnores = loadDeferredTestIgnores();

const {
  baseUrl,
  targetEnv,
  webServerEnv,
  isCi,
  totalShards,
  currentShard,
  playwrightProjects,
} = playwrightEnv;

// If playwrightProjects is set (e.g. "Chrome" on PR runs), only run the
// requested projects. Leave blank to run every project defined below.
const requestedProjectNames = playwrightProjects
  ? playwrightProjects.split(",").map((name) => name.trim())
  : null;
const filterProjects = (allProjects: Project[]): Project[] =>
  requestedProjectNames
    ? allProjects.filter(
        (project) =>
          project.name && requestedProjectNames.includes(project.name),
      )
    : allProjects;

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  timeout: targetEnv === "local" ? 75000 : 120000,
  testDir: "./e2e",
  // Files listed in tests/e2e/deferred-test-files.json are not discovered.
  testIgnore: deferredTestIgnores,
  /* Run tests in files in parallel */
  fullyParallel: targetEnv !== "staging",
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!isCi,
  /* Retry on CI only */
  retries: isCi ? 3 : 0,
  /* ci-frontend-e2e.yml — no workers passed → defaults to 10, sharding works as normal
     e2e-staging.yml — passes workers: 1 → PLAYWRIGHT_WORKERS=1, all tests run sequentially */
  workers: process.env.PLAYWRIGHT_WORKERS
    ? parseInt(process.env.PLAYWRIGHT_WORKERS)
    : 10,
  // Use 'blob' for CI to allow merging of reports. See https://playwright.dev/docs/test-reporters
  reporter: isCi ? "blob" : "html",
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: baseUrl,
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: "on-first-retry",
    screenshot: "on",
    video: "on-first-retry",
    launchOptions:
      targetEnv === "staging"
        ? {
            args: ["--disable-dev-shm-usage"],
          }
        : undefined,
  },
  // Enable test sharding for parallelization in CI.
  shard: {
    // Total number of shards is specified via env variable or defaults to 1
    total: parseInt(totalShards || "1"),
    // Specifies which shard this job should execute
    current: parseInt(currentShard || "1"),
  },
  /* Configure projects for major browsers */
  projects: filterProjects(
    targetEnv === "staging"
      ? [
          {
            name: "Chrome",
            use: {
              ...devices["Desktop Chrome"],
              permissions: ["clipboard-read", "clipboard-write"],
            },
          },
          {
            name: "Mobile chrome",
            use: {
              ...devices["Pixel 7"],
              permissions: ["clipboard-read", "clipboard-write"],
            },
          },
        ]
      : [
          {
            name: "Chrome",
            use: {
              ...devices["Desktop Chrome"],
              permissions: ["clipboard-read", "clipboard-write"],
            },
          },
          {
            name: "Firefox",
            use: {
              ...devices["Desktop Firefox"],
              permissions: [],
            },
          },
          {
            name: "Webkit",
            use: {
              ...devices["Desktop Safari"],
              permissions: ["clipboard-read"],
            },
          },
          {
            name: "Mobile chrome",
            use: {
              ...devices["Pixel 7"],
              permissions: ["clipboard-read", "clipboard-write"],
            },
          },
        ],
  ),

  //  Only start the local dev server when running in the local environment.
  webServer:
    targetEnv === "local"
      ? {
          command: "npm run start",
          url: baseUrl,
          reuseExistingServer: !isCi,
          env: webServerEnv,
          timeout: 120_000, // default is only 60s and can be too short for cold starts in CI causing webkit failures
        }
      : undefined,
});
