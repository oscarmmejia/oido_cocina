Feature: Administrative user listing and creation (OICO-61)

  Background:
    Given an authenticated administrator associated with a restaurant

  Scenario: Create a staff member with a role from the restaurant
    Given the administrator has the user:manage permission
    And a waiter role exists for their restaurant
    When they request user creation with valid data and that role_id
    Then the response status is 201 with the public user fields
    And the password is stored only as a hash
    And the response contains no passwords, hashes or tokens

  Scenario: Reject a duplicate email
    Given the administrator has the user:manage permission
    And a user already exists with the email ana@example.com
    When they request another user with the email ANA@example.com
    Then the response status is 409
    And no additional user is saved

  Scenario Outline: Reject requests without permission
    Given the administrator does not have the user:manage permission
    When they request <method> on /api/v1/users
    Then the response status is 403
    And users remain unchanged

    Examples:
      | method |
      | GET    |
      | POST   |

  Scenario: List only restaurant users with pagination
    Given the administrator has the user:manage permission
    And users exist in their restaurant and another restaurant
    When they request GET /api/v1/users with page 2 and page_size 1
    Then the response status is 200 with the second page ordered by user ID
    And the total and results only include users from their restaurant
    And the response contains no hashes or tokens

  Scenario: Reject invalid creation data
    Given the administrator has the user:manage permission
    When they request user creation with an invalid email
    Then the response status is 422
    And the user is not saved

  Scenario: Prevent client-selected restaurant identifiers
    Given the administrator has the user:manage permission
    When they send restaurant_id in the creation request body
    Then the response status is 422
    And the user is not saved

  Scenario: Reject a role from another restaurant
    Given the administrator has the user:manage permission
    When they request user creation with a role_id from another restaurant
    Then the response status is 404
    And the user is not saved

  Scenario: Prevent superadministrator creation
    Given the administrator has the user:manage permission
    When they request user creation with the superadministrator role
    Then the response status is 403
    And the user is not saved
