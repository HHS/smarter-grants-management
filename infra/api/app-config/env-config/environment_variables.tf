locals {
  # Map from environment variable name to environment variable value
  # This is a map rather than a list so that variables can be easily
  # overridden per environment using terraform's `merge` function
  default_extra_environment_variables = {
    FLASK_APP = "src.app:create_app()"
    # Example environment variables
    # WORKER_THREADS_COUNT    = 4
    # LOG_LEVEL               = "info"
    # DB_CONNECTION_POOL_SIZE = 5

    # Login.gov OAuth
    # Default values point to the IDP integration environment
    # which all non-prod environments should use
    #
    # TODO: LOGIN_GOV_CLIENT_ID is still simpler-grants-gov's registered client.
    # It must match the client registered with login.gov exactly, so it can only be
    # changed in lockstep with registering a client for this project — deliberately
    # left alone until that exists. Login will not work against this value.
    LOGIN_GOV_CLIENT_ID       = "urn:gov:gsa:openidconnect.profiles:sp:sso:hhs-${var.environment}-simpler-grants-gov"
    LOGIN_GOV_ENDPOINT        = "https://idp.int.identitysandbox.gov/"
    LOGIN_GOV_JWK_ENDPOINT    = "https://idp.int.identitysandbox.gov/api/openid_connect/certs"
    LOGIN_GOV_AUTH_ENDPOINT   = "https://idp.int.identitysandbox.gov/openid_connect/authorize"
    LOGIN_GOV_TOKEN_ENDPOINT  = "https://idp.int.identitysandbox.gov/api/openid_connect/token"
    LOGIN_GOV_LOGOUT_ENDPOINT = "https://idp.int.identitysandbox.gov/openid_connect/logout"
    LOGIN_GOV_REDIRECT_SCHEME = var.enable_https ? "https" : "http"

    # Set now rather than later: these are baked into every token this API issues,
    # so changing them once tokens are in circulation invalidates them.
    API_JWT_ISSUER                   = "smarter-grants-management-${var.environment}"
    API_JWT_AUDIENCE                 = "smarter-grants-management-${var.environment}"
    API_JWT_TOKEN_EXPIRATION_MINUTES = 15

    TEST_AGENCY_PREFIXES = "GDIT,IVPDF,0001,FGLT,NGMS,NGMS-Sub1,SECSCAN"

    # grants.gov services/applications URI.
    # Both staging and dev environments both point to trainingws subdomain.
    GRANTS_GOV_URI  = "https://trainingws.grants.gov"
    GRANTS_GOV_PORT = 443

    # Sam.gov
    SAM_GOV_BASE_URL = "https://api-alpha.sam.gov"

    # PDF Generation Configuration
    # TODO: this project has no hosted zone yet, so this still points at the
    # simpler-grants-gov domain. Update once DNS exists for these accounts (see
    # domain_config in infra/project-config/networks.tf).
    FRONTEND_URL                         = "https://${var.environment}.simpler.grants.gov"
    DOCRAPTOR_TEST_MODE                  = "true" # Default to test mode for safety
    DOCRAPTOR_API_URL                    = "https://docraptor.com/docs"
    SHORT_LIVED_TOKEN_EXPIRATION_MINUTES = "60"
    PDF_GENERATION_USE_MOCKS             = "false"

    # DB Schemas
    ALL_DB_SCHEMAS = "grantor,staging,legacy"
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
    # entry is manage_method = "manual", which resolves through a
    # data.aws_ssm_parameter lookup, so each one MUST exist in SSM before the
    # service layer will apply.
    #
    # Pruned from the upstream simpler-grants-gov config because nothing in
    # api/src or the grants-shared library reads them: DOCRAPTOR_API_KEY,
    # DOMAIN_VERIFICATION_CONTENT, ENABLE_SIMPLER_ROUTE, FRONTEND_BASE_URL,
    # SAM_GOV_API_KEY, SAVE_SOAP_MESSAGES_TO_S3, SOAP_APPLICANTS_PATH,
    # SOAP_GRANTORS_PATH, SOAP_PARTNER_GATEWAY_AUTH_KEY,
    # SOAP_PARTNER_GATEWAY_URI, SOAP_PRIVATE_KEYS, USE_SIMPLER.
    # Re-add an entry when the feature that needs it lands.

    # NEW RELIC DISABLED — see enable_newrelic in infra/project-config/main.tf.
    # manage_method = "manual" resolves through a data.aws_ssm_parameter lookup,
    # so leaving this in would fail the service apply until
    # /api/<environment>/new-relic-license-key exists. Uncomment once the
    # parameter is created in the target account.
    # NEW_RELIC_LICENSE_KEY = {
    #   manage_method     = "manual"
    #   secret_store_name = "/api/${var.environment}/new-relic-license-key"
    # }

    LOGIN_GOV_CLIENT_ASSERTION_PRIVATE_KEY = {
      manage_method     = "manual"
      secret_store_name = "/api/${var.environment}/login-gov-client-assertion-private-key"
    }

    API_JWT_PRIVATE_KEY = {
      manage_method     = "manual"
      secret_store_name = "/api/${var.environment}/api-jwt-private-key"
    }

    API_JWT_PUBLIC_KEY = {
      manage_method     = "manual"
      secret_store_name = "/api/${var.environment}/api-jwt-public-key"
    }

    LOGIN_FINAL_DESTINATION = {
      manage_method     = "manual"
      secret_store_name = "/api/${var.environment}/frontend-login-redirect-url"
    }

    LOGOUT_FINAL_DESTINATION = {
      manage_method     = "manual"
      secret_store_name = "/api/${var.environment}/frontend-logout-redirect-url"
    }

    ENABLE_MAINTENANCE_MODE = {
      manage_method     = "manual"
      secret_store_name = "/api/${var.environment}/enable-maintenance-mode"
    }

    API_GATEWAY_DEFAULT_USAGE_PLAN_ID = {
      manage_method     = "manual"
      secret_store_name = "/api/${var.environment}/api-gateway-default-usage-plan-id"
    }
  }
}
