locals {
  # app_name is the name of the application, which by convention should match the name of
  # the folder under /infra that corresponds to the application
  app_name = regex("/infra/([^/]+)/app-config$", abspath(path.module))[0]

  environments = ["dev", "staging"]
  project_name = module.project_config.project_name

  # Whether or not the application has a database
  # If enabled:
  # 1. The networks associated with this application's environments will have
  #    VPC endpoints needed by the database layer
  # 2. Each environment's config will have a database_config property that is used to
  #    pass db_vars into the infra/modules/service module, which provides the necessary
  #    configuration for the service to access the database
  has_database = true

  # Whether or not the application depends on external non-AWS services.
  # If enabled, the networks associated with this application's environments
  # will have NAT gateways, which allows the service in the private subnet to
  # make calls to the internet.
  has_external_non_aws_service = true

  has_incident_management_service = false

  # Whether or not the application should deploy an identity provider
  # If enabled:
  # 1. Creates a Cognito user pool
  # 2. Creates a Cognito user pool app client
  # 3. Adds environment variables for the app client to the service
  enable_identity_provider = false

  # Whether or not the application should deploy a notification service.
  #
  # To use this in a particular environment, domain_name must also be set.
  # The domain name is set in infra/<APP_NAME>/app-config/<ENVIRONMENT>.tf
  # The domain name is the same domain as, or a subdomain of, the hosted zone in that environment.
  # The hosted zone is set in infra/project-config/networks.tf
  # If either (domain name or hosted zone) is not set in an environment, notifications will not actually be enabled.
  #
  # If enabled:
  # 1. Creates an AWS Pinpoint application
  # 2. Configures email notifications using AWS SES
  enable_notifications = true

  # Whether or not to deploy the ClamAV file scanner (infra/modules/clamav) against
  # the file-scan S3 bucket.
  #
  # Disabled: the module needs three things that do not exist yet in either
  # account, and each one fails at PLAN time, not apply time:
  #   1. The /api/<environment>/file-scan-api-key SSM parameter, read through a
  #      plain data.aws_ssm_parameter the same way every other manual secret is.
  #   2. infra/modules/clamav/layer.zip built for the target architecture — the
  #      committed artifact is a starting point, but ./infra/modules/clamav/build-layer.sh
  #      should be re-run so the binaries match what gets deployed.
  #   3. The API's POST /v1/files/<file_id> scan-result callback, which api/src does
  #      not implement yet. Without it the scanner's callback fails, the event
  #      retries, and every scan ends up on the DLQ.
  #
  # To enable: create the SSM parameter (a SecureString whose value matches the
  # key_id on the internal scanner user's user_api_key row), build the layer, land
  # the callback endpoint, then flip this to true and re-apply the service layer.
  enable_file_scanning = false

  environment_configs = {
    dev     = module.dev_config
    staging = module.staging_config
  }

  # Map from environment name to the account name for the AWS account that
  # contains the resources for that environment. Every environment is
  # self-contained, so there is no cross-environment "shared" key.
  # The list of configured AWS accounts can be found in /infra/account
  # by looking for the backend config files of the form:
  #   <ACCOUNT_NAME>.<ACCOUNT_ID>.s3.tfbackend
  #
  # Projects/applications that use the same AWS account for all environments
  # will refer to the same account for all environments. For example, if the
  # project has a single account named "myaccount", then infra/accounts will
  # have one tfbackend file myaccount.XXXXX.s3.tfbackend, and the
  # account_names_by_environment map will look like:
  #
  #   account_names_by_environment = {
  #     dev     = "myaccount"
  #     staging = "myaccount"
  #     prod    = "myaccount"
  #   }
  #
  # This app has no "shared" entry: every environment, including its build
  # repository, is self-contained in that environment's own AWS account.
  account_names_by_environment = {
    dev     = "dev"     # AWS account 135002447353
    staging = "staging" # AWS account 530702498822
  }
}

module "project_config" {
  source = "../../project-config"
}
