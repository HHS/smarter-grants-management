/**
 * @file Storybook decorator for components that call useClientFetch.
 * Provides a logged in user (components read the session from UserContext, which is
 * empty outside of the app's UserProvider) and the story's
 * `parameters.mockFetchConfiguration` response. preview.tsx replaces useClientFetch
 * with useMockedClientFetch in every story, so stories never call a real API. Each
 * story reads its response from its own context, so stories rendered together on the
 * Docs page do not share responses.
 * @see https://storybook.js.org/docs/writing-stories/decorators
 */
import { Decorator } from "@storybook/react";
import { UserContext } from "src/services/auth/useUser";
import { UserProviderState } from "src/types/authTypes";

import React, { createContext, useCallback, useContext } from "react";

export type MockFetchConfiguration = {
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

const MockFetchContext = createContext<MockFetchConfiguration | undefined>(
  undefined,
);

// stands in for useClientFetch (see preview.tsx) with the same shape: clientFetch
// resolves with the story's response body, or throws `${errorMessage}: ${status}`
// for any status other than 200, as useClientFetch does
export const useMockedClientFetch = <T,>(errorMessage: string) => {
  const mockFetchConfiguration = useContext(MockFetchContext);
  const clientFetch = useCallback(
    async (url: string): Promise<T> => {
      if (!mockFetchConfiguration || url !== mockFetchConfiguration.url) {
        throw new Error(`No mocked response for ${url} in this story`);
      }
      await new Promise((resolve) =>
        setTimeout(resolve, mockFetchConfiguration.delayMs ?? 0),
      );
      const status = mockFetchConfiguration.status ?? 200;
      if (status !== 200) {
        throw new Error(`${errorMessage}: ${status}`);
      }
      return (mockFetchConfiguration.responseBody ?? {}) as T;
    },
    [mockFetchConfiguration, errorMessage],
  );
  return { clientFetch };
};

// registered globally in preview.tsx, but only takes effect for stories that set
// `parameters.mockFetchConfiguration`, so other stories keep the default (empty)
// user context
const withMockedClientFetch: Decorator = (Story, context) => {
  const mockFetchConfiguration = context.parameters.mockFetchConfiguration as
    MockFetchConfiguration | undefined;
  if (!mockFetchConfiguration) return <Story />;
  return (
    <UserContext.Provider value={mockUserState}>
      <MockFetchContext.Provider value={mockFetchConfiguration}>
        <Story />
      </MockFetchContext.Provider>
    </UserContext.Provider>
  );
};

export default withMockedClientFetch;
