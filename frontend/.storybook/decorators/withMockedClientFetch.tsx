/**
 * @file Storybook decorator for components that call useClientFetch.
 * Provides a logged in user (useClientFetch reads its auth helpers from UserContext,
 * which is empty outside of the app's UserProvider) and answers requests to
 * `parameters.mockFetch.url` with a canned response, so stories never call a real API.
 * @see https://storybook.js.org/docs/writing-stories/decorators
 */
import { Decorator } from "@storybook/react";
import { UserContext } from "src/services/auth/useUser";
import { UserProviderState } from "src/types/authTypes";

import React, { PropsWithChildren, useEffect } from "react";

export type MockFetchParameters = {
  url: string;
  responseBody?: unknown;
  status?: number;
  delayMs?: number;
};

const mockUserState: UserProviderState = {
  user: { token: "storybook-token", user_id: "storybook-user" },
  isLoading: false,
  refreshUser: () => Promise.resolve(),
  hasBeenLoggedOut: false,
  logoutLocalUser: () => undefined,
  resetHasBeenLoggedOut: () => undefined,
  refreshIfExpired: () => Promise.resolve(false),
  refreshIfExpiring: () => Promise.resolve(false),
  featureFlags: {},
  userFeatureFlags: {},
  defaultFeatureFlags: {},
};

const requestUrl = (input: RequestInfo | URL) => {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.href;
  return input.url;
};

const MockFetch = ({
  mockFetch,
  children,
}: PropsWithChildren<{ mockFetch: MockFetchParameters }>) => {
  useEffect(() => {
    const originalFetch = window.fetch;
    window.fetch = async (input, init) => {
      if (requestUrl(input) !== mockFetch.url) {
        return originalFetch(input, init);
      }
      await new Promise((resolve) =>
        setTimeout(resolve, mockFetch.delayMs ?? 0),
      );
      return new Response(JSON.stringify(mockFetch.responseBody ?? {}), {
        status: mockFetch.status ?? 200,
        headers: { "Content-Type": "application/json" },
      });
    };
    return () => {
      window.fetch = originalFetch;
    };
  }, [mockFetch]);

  return <>{children}</>;
};

// registered globally in preview.tsx, but only takes effect for stories that set
// `parameters.mockFetch`, so other stories keep the default (empty) user context
const withMockedClientFetch: Decorator = (Story, context) => {
  const mockFetch = context.parameters.mockFetch as
    MockFetchParameters | undefined;
  if (!mockFetch) return <Story />;
  return (
    <UserContext.Provider value={mockUserState}>
      <MockFetch mockFetch={mockFetch}>
        <Story />
      </MockFetch>
    </UserContext.Provider>
  );
};

export default withMockedClientFetch;
