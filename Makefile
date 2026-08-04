PROJECT_ROOT ?= $(notdir $(PWD))

# Use `=` instead of `:=` so that we only execute `./bin/current-account-alias` when needed
# See https://www.gnu.org/software/make/manual/html_node/Flavors.html#Flavors
CURRENT_ACCOUNT_ALIAS = `./bin/current-account-alias`

CURRENT_ACCOUNT_ID = $(./bin/current-account-id)

# Backend config name for an app's build repository, matching
# <app>/build-repository/<name>.s3.tfbackend.
#
# api has one build repository per environment, each in that environment's own AWS
# account, so passing ENVIRONMENT selects it (dev.s3.tfbackend, staging.s3.tfbackend).
# frontend still has a single repository shared across environments, which is what
# the "shared" fallback is for.
BUILD_REPOSITORY_CONFIG_NAME ?= $(if $(ENVIRONMENT),$(ENVIRONMENT),shared)

# Get the list of reusable terraform modules by getting out all the modules
# in infra/modules and then stripping out the "infra/modules/" prefix
MODULES := $(notdir $(wildcard infra/modules/*))

# Root deployment layers, validated separately from MODULES. Without this nothing
# ever type-checks a root layer, which is how a missing file referenced by
# filebase64sha256 in infra/accounts reached main-adjacent code: it only failed on a
# clean checkout, never in CI.
ROOT_LAYERS := accounts networks project-config \
               api/app-config api/build-repository api/database api/service \
               frontend/app-config frontend/build-repository frontend/service

# Check that given variables are set and all have non-empty values,
# die with an error otherwise.
#
# Params:
#   1. Variable name(s) to test.
#   2. (optional) Error message to print.
# Based off of https://stackoverflow.com/questions/10858261/how-to-abort-makefile-if-variable-not-set
check_defined = \
	$(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
	$(if $(value $1),, \
		$(error Undefined $1$(if $2, ($2))$(if $(value @), \
			required by target '$@')))


.PHONY : \
	dump-env \
	help \
	infra-check-app-database-roles \
	infra-check-github-actions-auth \
	infra-configure-app-build-repository \
	infra-configure-monitoring-secrets \
	infra-create-csr \
	infra-import-certificate \
	infra-set-up-account \
	infra-update-app-database-roles \
	infra-configure-app-database \
	infra-configure-app-service \
	infra-configure-network \
	infra-format \
	infra-lint \
	infra-lint-scripts \
	infra-lint-terraform \
	infra-test-modules \
	infra-validate \
	infra-validate-root-layers \
	infra-update-app-build-repository \
	infra-update-app-database \
	infra-update-app-service \
	infra-update-current-account \
	infra-update-network \
	infra-validate-modules \
	cleanup-ecr \
	invalidate-cloudfront-cache \
	release-build \
	release-deploy \
	release-image-name \
	release-image-tag \
	release-publish \
	release-run-database-migrations \
	release-run-setup-foreign-tables

###########
## Infra ##
###########

infra-set-up-account: ## Configure and create resources for current AWS profile and save tfbackend file to infra/accounts/$ACCOUNT_NAME.ACCOUNT_ID.s3.tfbackend. Optionally pass AWS_PROFILE=<profile> to target a specific AWS SSO profile.
	@:$(call check_defined, ACCOUNT_NAME, human readable name for account e.g. "dev" or "staging")
	$(if $(AWS_PROFILE),AWS_PROFILE=$(AWS_PROFILE)) ./bin/set-up-current-account $(ACCOUNT_NAME)

infra-check-github-actions-auth: ## Check that GitHub Actions in this repo can authenticate with $ACCOUNT_NAME
	@:$(call check_defined, ACCOUNT_NAME, the name of the account in /infra/accounts)
	./bin/check-github-actions-auth $(ACCOUNT_NAME)

infra-configure-network: ## Configure network $NETWORK_NAME
	@:$(call check_defined, NETWORK_NAME, the name of the network in /infra/networks)
	./bin/create-tfbackend infra/networks $(NETWORK_NAME)

infra-configure-app-build-repository: ## Configure infra/$APP_NAME/build-repository tfbackend and tfvars files
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	./bin/create-tfbackend "infra/$(APP_NAME)/build-repository" $(BUILD_REPOSITORY_CONFIG_NAME)

infra-configure-app-database: ## Configure infra/$APP_NAME/database module's tfbackend and tfvars files for $ENVIRONMENT
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	./bin/create-tfbackend "infra/$(APP_NAME)/database" "$(ENVIRONMENT)"

infra-configure-app-service: ## Configure infra/$APP_NAME/service module's tfbackend and tfvars files for $ENVIRONMENT
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	./bin/create-tfbackend "infra/$(APP_NAME)/service" "$(ENVIRONMENT)"

infra-update-current-account: ## Update infra resources for current AWS profile
	TF_VAR_account_name="$$(./bin/current-account-config-name | cut -d. -f1)" \
	./bin/terraform-init-and-apply infra/accounts "$$(./bin/current-account-config-name)"

infra-update-network: ## Update network
	@:$(call check_defined, NETWORK_NAME, the name of the network in /infra/networks)
	terraform -chdir="infra/networks" init -input=false -reconfigure -backend-config="$(NETWORK_NAME).s3.tfbackend"
	terraform -chdir="infra/networks" apply -var="network_name=$(NETWORK_NAME)" -var="environment_name=$(NETWORK_NAME)"

infra-update-app-build-repository: ## Create or update $APP_NAME's build repository
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	./bin/terraform-init-and-apply infra/$(APP_NAME)/build-repository $(BUILD_REPOSITORY_CONFIG_NAME)

infra-update-app-database: ## Create or update $APP_NAME's database module for $ENVIRONMENT
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	terraform -chdir="infra/$(APP_NAME)/database" init -input=false -reconfigure -backend-config="$(ENVIRONMENT).s3.tfbackend"
	terraform -chdir="infra/$(APP_NAME)/database" apply -var="environment_name=$(ENVIRONMENT)"

infra-update-app-service: ## Create or update $APP_NAME's web service module
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	terraform -chdir="infra/$(APP_NAME)/service" init -input=false -reconfigure -backend-config="$(ENVIRONMENT).s3.tfbackend"
	terraform -chdir="infra/$(APP_NAME)/service" apply -var="environment_name=$(ENVIRONMENT)"

infra-update-app-database-roles: ## Create or update database roles and schemas for $APP_NAME's database in $ENVIRONMENT
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	./bin/create-or-update-database-roles $(APP_NAME) $(ENVIRONMENT)

infra-check-app-database-roles: ## Check that database roles for $APP_NAME in $ENVIRONMENT were configured properly
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	./bin/check-database-roles $(APP_NAME) $(ENVIRONMENT)

infra-configure-monitoring-secrets: ## Set $APP_NAME's incident management service integration URL for $ENVIRONMENT
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	@:$(call check_defined, URL, incident management service (PagerDuty or VictorOps) integration URL)
	./bin/configure-monitoring-secret $(APP_NAME) $(ENVIRONMENT) $(URL)

infra-create-csr: ## Create a certificate signing request for $DOMAIN_NAME
	@:$(call check_defined, DOMAIN_NAME, the domain name to create a certificate signing request for)
	./bin/create-csr $(DOMAIN_NAME)

infra-import-certificate: ## Import a certificate for $DOMAIN_NAME into ACM
	@:$(call check_defined, DOMAIN_NAME, the domain name of the certificate to import)
	./bin/import-certificate $(DOMAIN_NAME)

invalidate-cloudfront-cache: ## Invalidate CloudFront cache for $ENVIRONMENT
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	./bin/invalidate-cloudfront-cache $(ENVIRONMENT)

cleanup-ecr: ## Delete untagged/unused images from the project's ECR repositories. Pass DRY_RUN=--dry-run to preview.
	./bin/cleanup-ecr $(DRY_RUN)

infra-format: ## Format infrastructure as code files
	terraform fmt -recursive infra

infra-lint: ## Lint infrastructure as code files and shell scripts
infra-lint: infra-lint-terraform infra-lint-scripts

infra-lint-terraform: ## Lint Terraform code
	terraform fmt -check -recursive infra

infra-lint-scripts: ## Lint shell scripts
	# Excludes non-shell files (bin/README.md) so shellcheck isn't handed a
	# document it can't parse.
	find bin -type f ! -name '*.md' -print0 | xargs -0 shellcheck

# The prerequisite for this rule is obtained by
# prefixing each module with the string "infra-validate-module-"
infra-validate-modules: ## Run terraform validate on reusable child modules
infra-validate-modules: $(patsubst %, infra-validate-module-%, $(MODULES))

infra-validate-module-%:
	@echo "Validate library module: $*"
	terraform -chdir=infra/modules/$* init -backend=false
	terraform -chdir=infra/modules/$* validate

# A shell loop rather than the per-item pattern rule used for MODULES above: make's
# `%` pattern rules do not match targets containing a "/", so a generated target
# like "infra-validate-root-layer-api/app-config" is never resolved.
infra-validate-root-layers: ## Run terraform validate on the root deployment layers
	@set -e; for layer in $(ROOT_LAYERS); do \
		echo "Validate root layer: $$layer"; \
		terraform -chdir=infra/$$layer init -backend=false; \
		terraform -chdir=infra/$$layer validate; \
	done

infra-validate: ## Run terraform validate on both the child modules and the root layers
infra-validate: infra-validate-modules infra-validate-root-layers

# The prerequisite for this rule is obtained by
# prefixing each module with the string "infra-test-module-"
infra-test-modules: ## Run native Terraform unit tests for reusable child modules
infra-test-modules: $(patsubst %, infra-test-module-%, $(MODULES))

infra-test-module-%:
	@echo "Test module: $*"
	terraform -chdir=infra/modules/$* init -backend=false
	terraform -chdir=infra/modules/$* test

########################
## Release Management ##
########################

# Include project name in image name so that image name
# does not conflict with other images during local development
IMAGE_NAME := $(PROJECT_ROOT)-$(APP_NAME)

GIT_REPO_AVAILABLE := $(shell git rev-parse --is-inside-work-tree 2>/dev/null)

ROOT_REV := $(shell git rev-parse HEAD)

# Generate a unique tag based solely on the git hash.
# This will be the identifier used for deployment via terraform.

ifdef APP_NAME
	APP_NAME_ARG := ${APP_NAME}
else
	APP_NAME_ARG := "."
endif

ifeq ($(origin IMAGE_TAG),undefined)
	ifdef GIT_REPO_AVAILABLE
		IMAGE_TAG := $(shell git log --pretty=format:'%H' -n 1 "${ROOT_REV}" -- "${APP_NAME_ARG}")
	else
		IMAGE_TAG := "unknown-dev.$(DATE)"
	endif
endif

# Generate an informational tag so we can see where every image comes from.
DATE := $(shell date -u '+%Y%m%d.%H%M%S')
INFO_TAG := $(DATE).$(USER)

release-build: ## Build release for $APP_NAME and tag it with current git hash
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	cd $(APP_NAME) && $(MAKE) release-build \
		OPTS="--tag $(IMAGE_NAME):latest --tag $(IMAGE_NAME):$(IMAGE_TAG) --load -t $(IMAGE_NAME):$(IMAGE_TAG) $(OPTIONAL_BUILD_FLAGS)"

release-publish: ## Publish release to $APP_NAME's build repository
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	./bin/publish-release $(APP_NAME) $(IMAGE_NAME) $(IMAGE_TAG)

release-run-database-migrations: ## Run $APP_NAME's database migrations in $ENVIRONMENT
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	./bin/run-database-migrations "$(APP_NAME)" "$(IMAGE_TAG)" "$(ENVIRONMENT)"

release-run-setup-foreign-tables: ## Run setup-foreign-tables for $APP_NAME in $ENVIRONMENT
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	./bin/run-setup-foreign-tables $(APP_NAME) $(ENVIRONMENT)

release-deploy: ## Deploy release to $APP_NAME's web service in $ENVIRONMENT
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@:$(call check_defined, ENVIRONMENT, the name of the application environment e.g. "dev" or "staging")
	./bin/deploy-release "$(APP_NAME)" "$(IMAGE_TAG)" "$(ENVIRONMENT)"

release-image-name: ## Prints the image name of the release image
	@:$(call check_defined, APP_NAME, the name of subdirectory of /infra that holds the application's infrastructure code)
	@echo $(IMAGE_NAME)

release-image-tag: ## Prints the image tag of the release image
	@echo $(IMAGE_TAG)

dump-env: ## Prints the release-related variables, for debugging CI runs
	@echo "APP_NAME=$(APP_NAME)"
	@echo "ENVIRONMENT=$(ENVIRONMENT)"
	@echo "IMAGE_NAME=$(IMAGE_NAME)"
	@echo "IMAGE_TAG=$(IMAGE_TAG)"
	@echo "INFO_TAG=$(INFO_TAG)"
	@echo "GIT_REPO_AVAILABLE=$(GIT_REPO_AVAILABLE)"

########################
## Scripts and Helper ##
########################

help: ## Prints the help documentation and info about each command
	@grep -Eh '^[[:print:]]+:.*?##' $(MAKEFILE_LIST) | \
	sort -d | \
	awk -F':.*?## ' '{printf "\033[36m%s\033[0m\t%s\n", $$1, $$2}' | \
	expand -t20
