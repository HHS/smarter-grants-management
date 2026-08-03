# bin

Shell scripts that back the [root `Makefile`](../Makefile) targets and the
[GitHub Actions workflows](../.github/workflows). Most of them wrap `terraform`
or the AWS CLI. Prefer the Make targets over calling these directly.

Run them from the repository root — several resolve paths like `infra/...` and
`./bin/...` relative to the current working directory.

## Terraform plumbing

| Script | Purpose |
| --- | --- |
| `terraform-init` | `terraform init` for a root module using `<config_name>.s3.tfbackend` |
| `terraform-apply` | `terraform apply` for a root module, picking up `<config_name>.tfvars` if present |
| `terraform-init-and-apply` | The two above, in sequence |
| `create-tfbackend` | Generate a `.tfbackend` file from `infra/example.s3.tfbackend` |
| `account-ids-by-name` | Print a JSON map of account name to account id, read from the `infra/accounts/*.s3.tfbackend` filenames. Called by terraform as an `external` data source |

## Account bootstrap

| Script | Purpose |
| --- | --- |
| `set-up-current-account` | Bootstrap a brand new AWS account: create the state bucket, create the **GitHub OIDC provider** (via AWS CLI — terraform only reads it), create placeholder monitoring SSM params/secrets, then apply the account layer and write the `infra/accounts/<name>.<id>.s3.tfbackend` file |
| `check-github-actions-auth` | Trigger `check-ci-cd-auth.yml` and watch it, to verify this repo's OIDC role works |

## AWS context

| Script | Purpose |
| --- | --- |
| `current-account-id` | Account id of the active credentials |
| `current-account-alias` | Account alias of the active credentials |
| `current-account-config-name` | The `<account name>.<account id>` config name matching the active credentials |
| `current-region` | The configured AWS region |

## Release path

These are what CD runs, via `make release-*`:

| Script | Purpose |
| --- | --- |
| `is-image-published` | Print `true`/`false` for whether a commit's image is already in ECR |
| `publish-release` | Tag and push a built image to the app's ECR repository |
| `run-database-migrations` | Roll the task definition forward, then run `db-migrate` as a one-off ECS task |
| `run-command` | Run an arbitrary command as a one-off ECS task using the service's task definition |
| `deploy-release` | Apply the service module with a new `image_tag` and wait for ECS to stabilize |

## Database

| Script | Purpose |
| --- | --- |
| `create-or-update-database-roles` | Invoke the role-manager Lambda to create/update Postgres roles and schemas |
| `check-database-roles` | Invoke the role-manager Lambda to verify roles were configured correctly |
| `run-setup-foreign-tables` | Run `setup-foreign-tables` as the migrator role, creating the Oracle FDW tables |

## Certificates and DNS

| Script | Purpose |
| --- | --- |
| `create-csr` | Generate a certificate signing request for a domain |
| `import-certificate` | Import an externally issued certificate into ACM |

## Operations

| Script | Purpose |
| --- | --- |
| `configure-monitoring-secret` | Store an incident-management integration URL (PagerDuty/VictorOps) in SSM |
| `invalidate-cloudfront-cache` | Invalidate all paths on the frontend's CloudFront distribution |
| `cleanup-ecr` | Delete unused images from the project's ECR repositories. Supports `--dry-run` |
| `run-step-function` | Start a step function execution for an app/environment |
| `util.sh` | Shared helper functions |
