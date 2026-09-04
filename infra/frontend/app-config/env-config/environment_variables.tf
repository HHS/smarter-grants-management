locals {
  # Map from environment variable name to environment variable value
  # This is a map rather than a list so that variables can be easily
  # overridden per environment using terraform's `merge` function
  default_extra_environment_variables = {
    # see https://docs.newrelic.com/docs/apm/agents/nodejs-agent/installation-configuration/nodejs-agent-configuration/#agent-enabled
    # Disabled: no New Relic tenant yet, and the license key secret below is
    # commented out. See enable_newrelic in infra/project-config/main.tf.
    NEW_RELIC_ENABLED = "false"
    # see https://github.com/newrelic/node-newrelic?tab=readme-ov-file#setup
    NODE_OPTIONS = "-r newrelic"
    # expose the current AWS Env to the FE Next Node Server at Runtime
    ENVIRONMENT = var.environment
    # https://docs.newrelic.com/docs/apm/agents/nodejs-agent/installation-configuration/nodejs-agent-configuration/#labels
    NEW_RELIC_LABELS = "app_name:${var.app_name};environment:${var.environment};service_name:${var.app_name}-${var.environment};serviceName:${var.app_name}-${var.environment};service.name:${var.app_name}-${var.environment};entity.name:${var.app_name}-${var.environment}"
    # https://docs.newrelic.com/docs/apm/agents/nodejs-agent/installation-configuration/nodejs-agent-configuration/#logging_config
    NEW_RELIC_LOG_ENABLED = "true"
    NEW_RELIC_LOG         = "stderr"
    # https://docs.newrelic.com/docs/apm/agents/nodejs-agent/installation-configuration/nodejs-agent-configuration/#cloud_config
    # TODO: this was simpler-grants-gov's account id. Set it to the deploying
    # account (dev 135002447353 / staging 530702498822) when New Relic is enabled.
    NEW_RELIC_CLOUD_AWS_ACCOUNT_ID = ""
    # https://docs.newrelic.com/docs/apm/agents/nodejs-agent/installation-configuration/nodejs-agent-configuration/#browser-variables
    NEW_RELIC_BROWSER_MONITORING_ATTRIBUTES_ENABLED = "true"
    # https://docs.newrelic.com/docs/apm/agents/nodejs-agent/installation-configuration/nodejs-agent-configuration/#application-logging-enabled
    # Turned off to avoid duplicate logging, and use logging from fluent bit instead
    NEW_RELIC_APPLICATION_LOGGING_ENABLED = "false"
  }

  # Configuration for secrets
  # List of configurations for defining environment variables that pull from SSM parameter
  # store. Configurations are of the format
  # {
  #   ENV_VAR_NAME = {
  #     manage_method     = "generated" # or "manual" for a secret that was created and stored in SSM manually
  #     secret_store_name = "/ssm/param/name"
  #   }
  # }
  secrets = {
    # Only the env vars this application actually reads are listed here. Every
    # manage_method = "manual" entry resolves through a data.aws_ssm_parameter
    # lookup, so each one MUST exist in SSM before the service layer will apply.
    #
    # The authoritative list of what the app reads is the destructure at the top
    # of frontend/src/constants/environments.ts — every server-side env var goes
    # through that module. frontend/.env.local.example is NOT authoritative; it
    # documents local-dev and test-only settings too.
    #
    # Pruned from the upstream simpler-grants-gov config because nothing in
    # frontend/src reads them:
    #
    #   FEATURE_APPLY_FORM_PROTOTYPE_OFF, FEATURE_OPPORTUNITIES_LIST_OFF —
    #     not destructured in environments.ts and not referenced anywhere in
    #     frontend/src. They appear only in .env.local.example, carried over
    #     with the port. The features they gate do not exist here.
    #
    #   MAILCHIMP_API_KEY, MAILCHIMP_API_URL_PREFIX, MAILCHIMP_LIST_ID —
    #     plumbed through environments.ts but no consumer: there is no
    #     /subscribe route and no newsletter code in frontend/src. Re-add all
    #     three together if the subscribe feature is ported.
    #
    # Re-add an entry when the feature that needs it lands.

    # NEW RELIC DISABLED — see enable_newrelic in infra/project-config/main.tf.
    # NEW_RELIC_APP_NAME = {
    #   manage_method     = "manual"
    #   secret_store_name = "/${var.app_name}/${var.environment}/new-relic-app-name"
    # },
    # NEW_RELIC_LICENSE_KEY = {
    #   manage_method     = "manual"
    #   secret_store_name = "/new-relic-license-key"
    # },

    # URL that the frontend uses to make fetch requests to the Grants API.
    # Read in environments.ts; also drives LOCAL_DEV detection.
    API_URL = {
      manage_method     = "manual"
      secret_store_name = "/${var.app_name}/${var.environment}/api-url"
    },

    # Sent as the X-API-KEY header on API requests.
    # See frontend/src/services/fetch/fetcherHelpers.ts.
    API_GW_AUTH = {
      manage_method     = "manual"
      secret_store_name = "/${var.app_name}/${var.environment}/X-API-KEY"
    },

    # Public half of the API's JWT signing key, used to verify session tokens.
    # See frontend/src/services/auth/session.ts. This reads the api's parameter
    # (/api/...), whose private counterpart is API_JWT_PRIVATE_KEY in
    # infra/api/app-config/env-config/environment_variables.tf.
    API_JWT_PUBLIC_KEY = {
      manage_method     = "manual"
      secret_store_name = "/api/${var.environment}/api-jwt-public-key"
    },

    # URL for the API login route.
    # See frontend/src/app/api/auth/login/route.ts.
    AUTH_LOGIN_URL = {
      manage_method     = "manual"
      secret_store_name = "/${var.app_name}/${var.environment}/auth-login-url"
    },

    # Feature flags. Each is read in environments.ts and surfaced through
    # envFeatureFlags; "true" disables the feature.
    FEATURE_AWARD_RECOMMENDATION_OFF = {
      manage_method     = "manual"
      secret_store_name = "/${var.app_name}/${var.environment}/feature-award-recommendation-off"
    },
    FEATURE_FEATURE_FLAG_ADMIN_OFF = {
      manage_method     = "manual"
      secret_store_name = "/${var.app_name}/${var.environment}/feature-feature-flag-admin-off"
    },
    FEATURE_MAINTENANCE_BANNER_ENABLED = {
      manage_method     = "manual"
      secret_store_name = "/${var.app_name}/${var.environment}/feature-maintenance-banner-enabled"
    },
    FEATURE_MAINTENANCE_MODE = {
      manage_method     = "manual"
      secret_store_name = "/${var.app_name}/${var.environment}/feature-maintenance-mode"
    },

    # Free-text message shown in the site-wide maintenance banner when
    # FEATURE_MAINTENANCE_BANNER_ENABLED is true.
    MAINTENANCE_BANNER_MESSAGE = {
      manage_method     = "manual"
      secret_store_name = "/${var.app_name}/${var.environment}/maintenance-banner-message"
    },

    # "generated" creates the SSM parameter itself rather than reading an
    # existing one, so it needs nothing pre-provisioned. Paired with
    # API_JWT_PUBLIC_KEY in session.ts — both must be set or session
    # initialization is skipped.
    SESSION_SECRET = {
      manage_method     = "generated"
      secret_store_name = "/${var.app_name}/${var.environment}/session-secret"
    },
    AUTH_LOGOUT_URL = {
      manage_method     = "manual"
      secret_store_name = "/${var.app_name}/${var.environment}/auth-logout-url"
    },
  }
}
