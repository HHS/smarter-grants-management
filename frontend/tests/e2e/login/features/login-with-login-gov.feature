# @featureArea Authentication
# @specFile e2e/login/specs/login-with-login-gov.spec.ts
# @debugNote Mirrors the current staging API-key auth flow; Login.gov credential MFA flow was removed.

Feature: Sign in to staging
  As a user
  I want to sign in to the staging site
  So that I can access my Simpler Grants account

  Background:
    Given I navigate to the Simpler Grants staging site

  @Login-StagingApiKey
  Scenario: signs in with staging auth and reaches an authenticated state
    Given the user launches the application
    When the user authenticates with the staging sign-in flow
    Then the user is successfully logged in
