# Overview

This project practices infrastructure-as-code and uses the [Terraform framework](https://www.terraform.io). This directory contains the infrastructure code for this project, including infrastructure for all application resources. This terraform project uses the [AWS provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs). It is based on the [Nava platform infrastructure template](https://github.com/navapbc/template-infra).

## 📂 Directory structure

The structure for the infrastructure code looks like this:

```text
infra/                  Infrastructure code
  accounts/             [Root module] IaC and IAM resources
  [app_name]/           Application directory: infrastructure for the main application
  modules/              Reusable child modules
  networks/             [Root module] Account level network config (shared across all apps, environments, and terraform workspaces)
```

Each application directory contains the following:

```text
  app-config/         Application-level configuration for the application resources (different config for different environments)
  build-repository/   [Root module] Docker image repository for the application (shared across environments and terraform workspaces)
  database/           [Root module] Configuration for database (different config for different environments)
  service/            [Root module] Configuration for containers, such as load balancer, application service (different config for different environments)
```

Details about terraform root modules and child modules are documented in [module-architecture](../documentation/infra/module-architecture.md).

## 🏗️ Project architecture

### 🧅 Infrastructure layers

The infrastructure template is designed to operate on different layers:

- Account layer
- Network layer
- Build repository layer (per application)
- Database layer (per application)
- Service layer (per application)

### 🏜️ Application environments

This project has two AWS environments, each in its own AWS account:

| Environment | AWS account | Network / VPC | State bucket |
| --- | --- | --- | --- |
| `dev` | `135002447353` | `dev` (`10.0.0.0/20`) | `smarter-grants-management-135002447353-us-east-1-tf` |
| `staging` | `530702498822` | `staging` (`10.1.0.0/20`) | `smarter-grants-management-530702498822-us-east-1-tf` |

The environments share the same root modules but have different configurations. Backend configuration is saved as [`.tfbackend`](https://developer.hashicorp.com/terraform/language/backend#file) files named after the environment, so each environment-scoped root module (`networks`, `[app_name]/service`, `[app_name]/database`) has a `dev.s3.tfbackend` and a `staging.s3.tfbackend`.

Resources shared across environments — the build repositories — use `shared.s3.tfbackend` and live in the **dev** account, since `shared_network_name = "dev"` in each app's `app-config/main.tf`. Resources shared across an entire account (`/infra/accounts`) use `<account name>.<account id>.s3.tfbackend`:

```text
infra/accounts/dev.135002447353.s3.tfbackend
infra/accounts/staging.530702498822.s3.tfbackend
```

Each account holds its own state bucket, so state keys are plain paths and never collide across environments:

```text
infra/account.tfstate                              # per account
infra/networks/<environment>.tfstate
infra/api/database/<environment>.tfstate
infra/api/service/<environment>.tfstate
infra/api/build-repository/shared.tfstate          # dev account
infra/frontend/service/<environment>.tfstate
infra/frontend/build-repository/shared.tfstate     # dev account
```

[`bin/create-tfbackend`](../bin/create-tfbackend) generates these from [`example.s3.tfbackend`](./example.s3.tfbackend).

### 🥾 Bootstrapping a new account

A brand new AWS account has no state bucket and, importantly, no GitHub OIDC provider — and [`modules/auth-github-actions`](./modules/auth-github-actions) *reads* the OIDC provider via a data source rather than creating one (AWS permits only one per URL per account). [`bin/set-up-current-account`](../bin/set-up-current-account) creates both, then applies the account layer:

```bash
export AWS_PROFILE=<profile for the target account>
make infra-set-up-account ACCOUNT_NAME=dev      # or: staging
```

That writes the matching `infra/accounts/<name>.<id>.s3.tfbackend`. Afterwards, confirm GitHub Actions can assume the role it created:

```bash
make infra-check-github-actions-auth ACCOUNT_NAME=dev
```

> **Note:** the script refuses to bootstrap `staging` while the New Relic / alerting values are still placeholders. During initial bring-up you can waive that deliberately with `ALLOW_PLACEHOLDER_MONITORING=true`.

### 🔀 Project workflow

This project relies on Make targets in the [root Makefile](../Makefile), which in turn call shell scripts in [./bin](../bin). The shell scripts call terraform commands. Many of the shell scripts are also called by the [Github Actions CI/CD](../.github/workflows).

Generally you should use the Make targets or the underlying bin scripts, but you can call the underlying terraform commands if needed. See [making-infra-changes](../documentation/infra/making-infra-changes.md) for more details.

### 🛡️ Account safety guards

Each environment maps to an AWS account: the network config in [`project-config/networks.tf`](./project-config/networks.tf) has an `account_name`, and that name resolves to an account id via the matching `infra/accounts/<account_name>.<account_id>.s3.tfbackend` file. When environments live in different accounts, it's easy to run an apply with the wrong AWS profile/SSO role active and target the wrong account.

To prevent that, the environment-scoped root modules (`networks`, `[app_name]/service`, `[app_name]/database`) refuse to run against the wrong account, using two complementary guards:

1. **Provider `allowed_account_ids`** — each `provider "aws"` block is restricted to the account the environment/network is configured for. If the active credentials are for a different account, the AWS provider errors out before making any changes. This covers `plan`, `apply`, **and `destroy`**.
2. **`aws-account-guard` module** ([`modules/aws-account-guard`](./modules/aws-account-guard)) — a `data.aws_caller_identity` postcondition that fails during `plan` with a clear, actionable message naming the target account.

Both resolve the expected account id from the same source of truth — the provider-less [`account-id-by-name`](./modules/account-id-by-name) module, which reads the `infra/accounts/<account_name>.<account_id>.s3.tfbackend` filename. Keeping that resolver provider-less is what lets the `allowed_account_ids` provider argument reference it without creating a dependency cycle.

If you hit an error like `Wrong AWS account: the active credentials belong to account <X>, but <...> must be deployed to account <Y>`, switch to the correct AWS profile / SSO role for that environment's account (e.g. `export AWS_PROFILE=...`) and retry.

> **Note:** the `build-repository` layer is intentionally **not** guarded this way — it can be deployed to more than one account from the same code, so it has no single expected account. Its backstop is that each account has its own state bucket (`smarter-grants-management-<account_id>-<region>-tf`), so a wrong-account run fails on the S3 backend.

### 🚀 Deploys

CD lives in [`.github/workflows`](../.github/workflows). `dev` is kept current from `main`; a published release promotes to `staging`:

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `cd-api.yml` | push to `main` touching `api/**`, `infra/api/**`, or `infra/modules/**`; or manual dispatch | Runs API checks and vulnerability scans, then deploys to `dev` (scan findings report but don't block) |
| `cd-release.yml` | a published GitHub **release**, or manual dispatch | Runs API checks and vulnerability scans, then deploys the release tag to `staging` (scan findings **do** block) |
| `deploy.yml` | called by the two above | Runs database migrations, then applies the service module and waits for ECS to stabilize |
| `database-migrations.yml` | called by `deploy.yml` | Builds/publishes the image, then runs `db-migrate` as a one-off ECS task |
| `build-and-publish.yml` | called by `database-migrations.yml` | Builds the image and pushes it to ECR, skipping the build if that commit is already published |
| `check-ci-cd-auth.yml` | manual dispatch | Verifies this repo's GitHub Actions OIDC role can be assumed |

All of them authenticate through [`.github/actions/configure-aws-credentials`](../.github/actions/configure-aws-credentials/action.yml), which resolves app → environment → network → account → role from the terraform config itself, so there are no hardcoded account ids or role ARNs in the workflows. That is also why a deploy to `staging` automatically targets `530702498822` while `dev` targets `135002447353` — the only thing that changes is the environment name.

### 🔍 Scans

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `ci-infra.yml` | PR / push to `main` touching `bin/**`, `infra/**`, `.github/workflows/**` | actionlint, shellcheck, `terraform fmt`, module validate, module unit tests, Checkov, Trivy IaC scan |
| `ci-api-vulnerability-scans.yml` | PR touching the api image or scan configs | Container scans for the api |
| `ci-frontend-vulnerability-scans.yml` | PR touching the frontend image or scan configs | Container scans for the frontend (dormant until the frontend app exists) |
| `vulnerability-scans.yml` | called by the above and by CD | hadolint, Trivy, Anchore/Grype, Dockle against the built image |

Scanner ignore lists live at the repo root: `.hadolint.yaml`, `.trivyignore`, `.grype.yml`, `.dockleconfig`. IaC findings are ignored separately in [`.trivyignore.yaml`](./.trivyignore.yaml).

## 💻 Development

### 1️⃣ First time initialization

To set up this project for the first time (aka it has never been deployed to the target AWS account):

1. [Configure the project](../infra/project-config/main.tf) (These values will be used in subsequent infra setup steps to namespace resources and add infrastructure tags.)
2. [Set up infrastructure developer tools](../documentation/infra/set-up-infrastructure-tools.md)
3. [Set up AWS account](../documentation/infra/set-up-aws-account.md)
4. [Set up the virtual network (VPC)](../documentation/infra/set-up-network.md)
5. For each application:
    1. [Set up application build repository](../documentation/infra/set-up-app-build-repository.md)
    2. [Set up application database](../documentation/infra/set-up-database.md)
    3. [Set up application environment](../documentation/infra/set-up-app-env.md)

### 🆕 New developer

To get set up as a new developer to a project that has already been deployed to the target AWS account:

1. [Set up infrastructure developer tools](../documentation/infra/set-up-infrastructure-tools.md)
2. [Review how to make changes to infrastructure](../documentation/infra/making-infra-changes.md)
3. (Optional) Set up a [terraform workspace](../documentation/infra/intro-to-terraform-workspaces.md)

## 📇 Additional reading

Additional documentation can be found in the [documentation directory](../documentation/infra).
