locals {
  # Each environment has its own VPC in its own AWS account. The account_name
  # here resolves to an account id via the matching
  # infra/accounts/<account_name>.<account_id>.s3.tfbackend file, which is what
  # the provider's allowed_account_ids guard and the CI/CD role lookup both read.
  network_configs = {
    # dev — AWS account 135002447353
    dev = {
      account_name                 = "dev"
      database_subnet_group_name   = "dev"
      vpc_name                     = "dev"
      second_octet                 = 0               # The second octet of the VPC CIDR block (10.0.0.0/20)
      grants_gov_oracle_cidr_block = "10.220.0.0/16" # Unused while enable_dms = false, but still read by the api/database layer
      enable_dms                   = false           # does not peer with the Grants.gov Oracle DMS network

      domain_config = {
        # A hosted zone represents a domain and all of its subdomains. For example, a
        # hosted zone of foo.domain.com includes foo.domain.com, bar.foo.domain.com, etc.
        manage_dns  = false
        hosted_zone = null # DNS is managed externally; set once a Route53 hosted zone is created

        certificate_configs = {
          # Example certificate configuration for a certificate that is managed by the project
          # "sub.domain.com" = {
          #   source = "issued"
          # }

          # Example certificate configuration for a certificate that is issued elsewhere and imported into the project
          # "platform-test-dev.navateam.com" = {
          #   source = "imported"
          #   private_key_ssm_name = "/certificates/sub.domain.com/private-key"
          #   certificate_body_ssm_name = "/certificates/sub.domain.com/certificate-body"
          # }
        }
      }
    }

    # staging — AWS account 530702498822
    staging = {
      account_name                 = "staging"
      database_subnet_group_name   = "staging"
      vpc_name                     = "staging"
      second_octet                 = 1               # The second octet of the VPC CIDR block (10.1.0.0/20)
      grants_gov_oracle_cidr_block = "10.220.0.0/16" # Unused while enable_dms = false, but still read by the api/database layer
      enable_dms                   = false           # does not peer with the Grants.gov Oracle DMS network

      domain_config = {
        manage_dns  = false
        hosted_zone = null # DNS is managed externally; set once a Route53 hosted zone is created

        certificate_configs = {}
      }
    }
  }
}
