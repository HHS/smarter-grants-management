import { BrowserContext } from "@playwright/test";
import { SignJWT } from "jose";
import playwrightEnv from "tests/e2e/playwright-env";

/*

  This file creates the client-side session cookie used by Playwright to spoof a
  logged-in user in local/dev E2E runs.

  The app validates the spoofed session exactly as it does for the real server
  session, so this helper intentionally mirrors the app's session semantics
  without depending on the full browser login flow.

  Most of this logic is copied from src/services/auth/session so the app logic
  and test logic remain intentionally separate.

*/

const CLIENT_JWT_ENCRYPTION_ALGORITHM = "HS256";

let clientJwtKey: Uint8Array;

const encodeText = (valueToEncode: string) =>
  new TextEncoder().encode(valueToEncode);

const createSpoofLoginError = ({
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
      "Flow: local-spoofed-session",
      `Failed step: ${step}`,
      `What to inspect: ${inspect}`,
      `Likely cause: ${likelyCause}`,
      `Target environment: ${playwrightEnv.targetEnv || "unknown"}`,
      `Base URL: ${playwrightEnv.baseUrl || "unset"}`,
      details,
    ].join("\n"),
  );

export const initializePlaywrightSessionSecrets = () => {
  if (!playwrightEnv.clientSessionSecret) {
    // eslint-disable-next-line
    console.debug("Api session key not present, cannot spoof login");
    return;
  }
  // eslint-disable-next-line
  console.debug("Initializing TESTING Session Secrets");
  clientJwtKey = encodeText(playwrightEnv.clientSessionSecret);
};

// 12 hour expiration for test tokens to avoid expiration issues
export const newExpirationDate = () =>
  new Date(Date.now() + 12 * 60 * 60 * 1000);

/*
  Encrypts a server session token (fetched from GET /v1/internal/api-jwt in the
  local/dev auth flow) into a fake client token.
*/
export const generateSpoofedSession = async (
  serverToken: string,
): Promise<string> => {
  if (!clientJwtKey) {
    throw createSpoofLoginError({
      step: "generate-spoofed-session-signing-key",
      inspect:
        "SESSION_SECRET / SESSION_SECRET_OVERRIDE used for test cookie signing",
      likelyCause:
        "client session secret was not loaded before spoofed session generation",
      details: "Unable to spoof login because auth signing key is missing.",
    });
  }

  if (!serverToken) {
    throw createSpoofLoginError({
      step: "generate-spoofed-session-server-token",
      inspect: "JWT token returned by GET /v1/internal/api-jwt",
      likelyCause:
        "upstream token fetch returned an empty value before cookie generation",
      details: "Unable to spoof login because server token is missing.",
    });
  }

  const fakeToken = await new SignJWT({
    token: serverToken,
  })
    .setProtectedHeader({ alg: CLIENT_JWT_ENCRYPTION_ALGORITHM })
    .setIssuedAt()
    .setExpirationTime(newExpirationDate())
    .sign(clientJwtKey);

  return fakeToken;
};

// For bypassing login in E2E test runs: encodes the server session token into a
// spoofed client session cookie so tests skip the login process.
export const createSpoofedSessionCookie = async (
  context: BrowserContext,
  serverToken: string,
) => {
  const token = await generateSpoofedSession(serverToken);
  // Mirror the attributes the app sets on the real session cookie
  // (see createSession in src/services/auth/session.ts). In particular:
  //  - sameSite "Lax": addCookies otherwise defaults to SameSite=None, which
  //    Webkit/Firefox reject over plain HTTP.
  //  - expires: without it the cookie is a session cookie, which Webkit will
  //    not replay on the client-side fetch to /api/auth/session, silently
  //    logging the spoofed user out on the client.
  await context.addCookies([
    {
      name: "sgm-session",
      value: token,
      url: playwrightEnv.baseUrl,
      httpOnly: true,
      sameSite: "Lax",
      expires: Math.floor(newExpirationDate().getTime() / 1000),
    },
  ]);
};

initializePlaywrightSessionSecrets();
