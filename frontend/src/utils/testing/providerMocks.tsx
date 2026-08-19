import { FeatureFlags } from "src/constants/defaultFeatureFlags";

export const createFakeUserContext = (featureFlags?: FeatureFlags) => {
  return {
    user: undefined,
    error: undefined,
    isLoading: false,
    refreshUser: function (): Promise<void> {
      throw new Error("Function not implemented.");
    },
    hasBeenLoggedOut: false,
    logoutLocalUser: function (): void {
      throw new Error("Function not implemented.");
    },
    resetHasBeenLoggedOut: function (): void {
      throw new Error("Function not implemented.");
    },
    refreshIfExpired: function (): Promise<boolean | undefined> {
      throw new Error("Function not implemented.");
    },
    refreshIfExpiring: function (): Promise<boolean | undefined> {
      throw new Error("Function not implemented.");
    },
    featureFlags: {
      ...featureFlags,
    },
    userFeatureFlags: {},
    defaultFeatureFlags: {},
  };
};
