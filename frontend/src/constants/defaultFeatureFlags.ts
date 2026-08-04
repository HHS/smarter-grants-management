export type FeatureFlags = { [name: string]: boolean };

export const defaultFeatureFlags: FeatureFlags = {
  featureFlagAdminOff: false,
  maintenanceBannerEnabled: false,
  maintenanceMode: false,
};
