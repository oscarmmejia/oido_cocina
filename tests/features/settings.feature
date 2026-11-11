Feature: Authenticated restaurant settings
  Settings belong to the restaurant resolved from the authenticated user.

  Scenario: Read restaurant settings
    Given an active authenticated user associated with a restaurant
    When the user requests GET /api/v1/settings
    Then the response status is 200
    And the response contains the user's restaurant settings

  Scenario: Persist a partial update
    Given an authenticated user with the settings:update permission
    When the user changes courtesy_minutes to 10
    Then the response status is 200
    And the change is persisted
    And omitted fields are preserved

  Scenario: Reject an update without permission
    Given an authenticated user without the settings:update permission
    When the user requests PATCH /api/v1/settings
    Then the response status is 403
    And no settings are changed

  Scenario: Validate the complete resulting schedule
    Given a restaurant closing at 23:00 with kitchen closing at 22:00
    When an authorized user changes closing to 21:00 and courtesy_minutes to 10
    Then the response status is 422
    And neither change is persisted

  Scenario: Allow an overnight schedule
    Given an authenticated user with the settings:update permission
    When the user sets opening to 20:00, kitchen closing to 02:00 and closing to 03:00
    Then the response status is 200

  Scenario: Reject continuous 24-hour operation
    Given an authenticated user with the settings:update permission
    When the user sets opening and closing to the same time
    Then the response status is 422
    And no settings are changed

  Scenario: Ignore a client-selected restaurant
    Given an active authenticated user associated with restaurant A
    When the user supplies restaurant B in a query parameter
    Then settings are resolved for restaurant A
    And restaurant B is unchanged

  Scenario: Reject an anonymous request
    Given a request without valid authentication
    When the request accesses restaurant settings
    Then the response status is 401
