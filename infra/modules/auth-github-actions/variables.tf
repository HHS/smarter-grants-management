variable "allowed_actions" {
  type        = list(string)
  description = "List of IAM actions to allow GitHub Actions to perform"
}

variable "github_actions_role_name" {
  type        = string
  description = "The name to use for the IAM role GitHub actions will assume."
}

variable "github_repository" {
  type        = string
  description = <<EOT
    The repository portion of the GitHub OIDC `sub` claim that is allowed to assume
    the role. This is whatever GitHub actually puts in the token, which is either
    the plain 'org/repo' form (e.g. 'navapbc/template-infra') or, for orgs using
    ID-based rename-proof subjects, '<owner>@<owner_id>/<repo>@<repo_id>'
    (e.g. 'HHS@1470878/smarter-grants-management@1315368029').

    It is NOT necessarily the same as the human-readable org/repo used to build
    github.com URLs. See local.github_oidc_subject_repository in
    infra/project-config/main.tf.
  EOT
}
