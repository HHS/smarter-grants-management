# @featureArea Home
# @specFile e2e/home/specs/home-page-availability.spec.ts
#
# ============== Notes for reviewer ===============================================
# - Smoke check that the deployed frontend is up and serving the home page.
# - No authentication is performed; the browser starts with a fresh session.
# - The page is considered available when it responds successfully and the
#   "Welcome to Smarter Grants Management" heading is visible.
# ================================================================================

Feature: Home page availability
  As a visitor
  I want the Smarter Grants home page to load without signing in
  So that I know the site is live

  @STATIC @SMOKE
  Scenario: Home page loads without signing in
    Given I am not signed in
    When I navigate to the home page
    Then the page responds successfully
    And I should see the "Welcome to Smarter Grants Management" heading
