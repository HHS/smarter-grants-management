enum validFeatureTags {
  GRANTOR = "@grantor",
  STATIC = "@static",
  AUTH = "@auth",
  USER_MANAGEMENT = "@user-management",
}

enum validExecutionTags {
  SMOKE = "@smoke",
  CORE_REGRESSION = "@core-regression",
  FULL_REGRESSION = "@full-regression",
  EXTENDED = "@extended",
}

export const VALID_TAGS = { ...validExecutionTags, ...validFeatureTags };
