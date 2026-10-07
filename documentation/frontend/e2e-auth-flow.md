# E2E auth flow: local vs staging

This is a visual guide to the Playwright E2E login flow for local and staging CI runs.

![E2E auth flow diagram](./e2e-auth-flow.svg)

## Mermaid source (saved)

```mermaid
flowchart TD
   T["Start E2E test"] --> P["Playwright loads target environment config"]
   P -. "Target env config failed" .-> E0["Error: target environment config failed\nCheck: PLAYWRIGHT_TARGET_ENV, base URL, API URL, and env file\nLikely cause: wrong env selected or missing config values"]
   P --> C{"Target environment?"}

   C -->|Local environment| L1["Read local environment config"]
   C -->|Staging environment| S1["Target staging frontend + API URL"]

   L1 --> L2["Fetch JWT from /v1/internal/api-jwt"]
   L2 --> L3["Backend issues JWT for seeded local test user"]
   L3 --> L4["Create spoofed session cookie"]
   L4 --> L5["Navigate app with same BrowserContext"]
   L5 --> L6["Rest of the local test reuses authenticated session"]

   S1 --> S2["Lookup staging API key in GitHub secret / env"]
   S2 --> S3["TEST_USER_API_KEY or STAGING_TEST_USER_API_KEY"]
   S3 --> S4["Open sign-in UI"]
   S4 --> S5["Complete staging login flow using API key"]
   S5 --> S6["Navigate app with same BrowserContext"]
   S6 --> S7["Rest of the staging test reuses authenticated session"]

   L1 -. "Missing config" .-> E1["Error: missing local env values or secrets\nCheck: .env.local, frontend env values, SESSION_SECRET\nLikely cause: stale local config or missing secret"]
   L2 -. "JWT request failed" .-> E2["Error: unable to fetch e2e user token\nCheck: backend API URL and API key\nLikely cause: wrong URL, invalid key, or backend unavailable"]
   L3 -. "JWT not issued" .-> E3["Error: invalid or inactive API key\nCheck: seeded local key and backend auth config\nLikely cause: key expired, not seeded, or backend rejected it"]
   L4 -. "Spoofed cookie not created" .-> E8["Error: create spoofed session cookie failed\nCheck: JWT value, cookie domain, and app session secret\nLikely cause: JWT invalid or session secret mismatch"]
   S1 -. "Wrong staging URL" .-> E9["Error: target staging frontend + API URL invalid\nCheck: PLAYWRIGHT_BASE_URL, PLAYWRIGHT_API_URL, and deployment target\nLikely cause: wrong deployed URL or API host selected"]
   S2 -. "Staging secret missing" .-> E4["Error: missing staging API key in GitHub secret\nCheck: GitHub Actions secret / environment variables\nLikely cause: secret not created or not passed to workflow"]
   S3 -. "API key value missing" .-> E10["Error: TEST_USER_API_KEY or STAGING_TEST_USER_API_KEY not resolved\nCheck: workflow env, local .env values, and CI secret mapping\nLikely cause: env var not set or fallback mapping failed"]
   S4 -. "Login modal not ready" .-> E11["Error: open sign-in UI failed\nCheck: page load, sign-in modal selector, and deployed frontend state\nLikely cause: page did not finish loading or app UI changed"]
   S5 -. "Staging sign-in failed" .-> E5["Error: staging login flow failed / invalid API key (Check with infra team) and update in GitHub secret\nCheck: deployed URL, workflow env, secret value\nLikely cause: stale secret, wrong deployment env, or auth mismatch"]
   L5 -. "Local session not ready" .-> E6["Error: app did not load authenticated local session\nCheck: local base URL, cookie write, app startup\nLikely cause: cookie missing or redirect before auth completed"]
   S6 -. "Staging session not ready" .-> E7["Error: app did not load authenticated staging session\nCheck: deployed URL, sign-in flow, BrowserContext state\nLikely cause: session cookie not persisted or page loaded before auth finished"]
   S7 -. "Session not reused" .-> E12["Error: rest of the staging test reuses authenticated session failed\nCheck: BrowserContext persistence and page lifetime\nLikely cause: new context created or auth state lost mid-test"]

   L6 --> E["Continue test actions against authenticated app"]
   S7 --> E

   E -. "Test actions failed after auth" .-> E13["Error: continue test actions against authenticated app failed\nCheck: authenticated page state, app route, and session validity\nLikely cause: session expired or app state was not ready"]
   E --> Shared["Shared environment model\nTEST_USER_API_KEY = environment-specific value\n(local or staging)"]
   Shared -. "Env mismatch" .-> E14["Error: shared environment model mismatch\nCheck: target env, TEST_USER_API_KEY value, and config mapping\nLikely cause: wrong environment selected or stale variable value"]

   classDef error fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d,stroke-width:2px;
   class E0,E1,E2,E3,E4,E5,E6,E7,E8,E9,E10,E11,E12,E13,E14 error;
```

## One quick picture

```text
Spec runs
   |
   v
authenticateE2eUser
   |
   +--> PLAYWRIGHT_TARGET_ENV == "local" ?
   |         |
   |         +--> fetch JWT from /v1/internal/api-jwt
   |                 |
   |                 +--> create spoofed session cookie
   |                         |
   |                         +--> open app
   |
   +--> PLAYWRIGHT_TARGET_ENV == "staging" ?
             |
             +--> open staging frontend
                     |
                     +--> click Sign in
                     |
                     +--> fill API key modal
                     |
                     +--> continue test as signed-in user
```

## Local CI flow

```text
GitHub workflow
   |
   v
CI job sets target = local
   |
   v
Composite action sets:
- PLAYWRIGHT_TARGET_ENV=local
- PLAYWRIGHT_BASE_URL
- PLAYWRIGHT_API_URL
   |
   v
Playwright spec calls authenticateE2eUser
   |
   v
Fetch JWT from /v1/internal/api-jwt
   |
   v
Create spoofed session cookie
   |
   v
Open local app and run test
```

## Staging CI flow

```text
GitHub workflow
   |
   v
CI job sets target = staging
   |
   v
Composite action sets:
- PLAYWRIGHT_TARGET_ENV=staging
- PLAYWRIGHT_BASE_URL
- PLAYWRIGHT_API_URL
   |
   v
Playwright spec calls authenticateE2eUser
   |
   v
Open deployed staging frontend
   |
   v
Click Sign in
   |
   v
Fill API key in modal
   |
   v
Wait for authenticated state
   |
   v
Run test
```

## The decision point

The branching logic lives here:

- [frontend/tests/e2e/utils/auth/authenticate-e2e-user-utils.ts](../tests/e2e/utils/auth/authenticate-e2e-user-utils.ts)

The decision is straightforward:

- if the target is `staging`, use the real frontend API-key modal flow
- otherwise, use the local JWT spoof flow

## Related files

- [frontend/tests/e2e/playwright-env.ts](../tests/e2e/playwright-env.ts)
- [.github/actions/e2e/action.yml](../../.github/actions/e2e/action.yml)
- [.github/workflows/e2e-staging.yml](../../.github/workflows/e2e-staging.yml)
- [.github/workflows/ci-frontend-e2e.yml](../../.github/workflows/ci-frontend-e2e.yml)
