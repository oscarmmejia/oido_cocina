Feature: Schedule and work shift management (HU-HOR-02)

  Background:
    Given an authenticated manager with the schedule:manage permission

  Scenario: Create a schedule in draft
    Given an active employee responsible for the schedule
    When the manager creates a schedule with a coherent period
    Then the response status is 201
    And the schedule status is borrador
    And the responsible employee is stored

  Scenario: Reject an inverted schedule period
    When the manager creates a schedule whose end date is before its start date
    Then the response status is 422
    And no schedule is saved

  Scenario: List only schedules from the manager's restaurant
    Given schedules exist in the manager's restaurant and in another restaurant
    When the manager requests GET /api/v1/schedules
    Then the response status is 200 with only the manager's schedules

  Scenario: Update a schedule in draft
    Given a schedule in borrador
    When the manager changes its period and responsible employee
    Then the response status is 200 with the new values

  Scenario: Delete a schedule in draft
    Given a schedule in borrador
    When the manager deletes it
    Then the response status is 204
    And the schedule and its shifts no longer exist

  Scenario: Reject deleting a published schedule
    Given a published schedule
    When the manager deletes it
    Then the response status is 409
    And the schedule still exists

  Scenario: Publish a schedule once
    Given a schedule in borrador
    When the manager publishes it
    Then the response status is 200 with status publicado
    And publishing it again returns 409

  Scenario: Reject schedule operations without permission
    Given a user without the schedule:manage permission
    When the user calls any schedule or shift endpoint
    Then the response status is 403

  Scenario: Create a night shift that crosses midnight
    Given an active employee without shifts that night
    When the manager assigns a shift from 22:00 to 02:00 the next day
    Then the response status is 201
    And the shift keeps its type and scheduled status

  Scenario: Represent a split shift as two intervals
    Given an active employee
    When the manager assigns 12:00-16:00 and 20:00-23:00 on the same day
    Then both shifts are saved
    And the total duration is 7 hours

  Scenario: Reject an inactive employee
    Given an inactive employee
    When the manager assigns a shift to that employee
    Then the response status is 422
    And the shift is not saved

  Scenario: Update a shift in draft
    Given a schedule in borrador with a shift
    When the manager changes the shift times and type
    Then the response status is 200 with the updated values
    And the shift does not conflict with itself

  Scenario: Reject updating a shift in a published schedule
    Given a published schedule with a shift
    When the manager updates the shift
    Then the response status is 409

  Scenario: Delete a shift in draft
    Given a schedule in borrador with a shift
    When the manager deletes the shift
    Then the response status is 204
    And the shift no longer exists

  Scenario: Reject deleting a shift in a published schedule
    Given a published schedule with a shift
    When the manager deletes the shift
    Then the response status is 409
    And the shift still exists
