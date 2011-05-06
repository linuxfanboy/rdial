Feature: Handle database events
  In order to support storing database
  As a developer
  We'll implement database reading and writing

  Scenario: Read database
    Given I have the database test.txt
    When I process it with Events.read
    Then I see 3 events

  Scenario Outline: Check events
    Given I have the database test.txt
    When I process it with Events.read
    Then I see event <n> contains <project>, <start> and <delta>

  Examples:
    | n | project  | start                     | delta   |
    | 0 | project  | 2011-05-04 08:00:00+00:00 | 1:00:00 |
    | 1 | project2 | 2011-05-04 09:15:00+00:00 | 0:15:00 |
    | 2 | project  | 2011-05-04 09:30:00+00:00 | 0:00:00 |

  Scenario: Write database
    Given I have the events from test.txt
    When I write it to a temp file
    Then I see an duplicate of test.txt

  Scenario: List projects
    Given I have the database test.txt
    When I process it with Events.read
    When I check output for calling projects on result
    Then I see the string ['project', 'project2']

  Scenario: Currently running event
    Given I have the database test.txt
    When I process it with Events.read
    When I check output for calling running on result
    Then I see the string project

  Scenario: No currently running event
    Given I have the database test_not_running.txt
    When I process it with Events.read
    When I check output for calling running on result
    Then I see the string False

  Scenario: Start event
    Given I have the database test_not_running.txt
    When I process it with Events.read
    When I call start on result with project=project2
    When I check output for calling running on result
    Then I see the string project2

  Scenario: Fail starting when currently running
    Given I have the database test.txt
    When I process it with Events.read
    When I call start on result with project=project2
    Then I receive ValueError

  Scenario: Stop event
    Given I have the database test.txt
    When I process it with Events.read
    When I call stop on result
    When I check output for calling running on result
    Then I see the string False

  Scenario: Fail stopping when not currently running
    Given I have the database test_not_running.txt
    When I process it with Events.read
    When I call stop on result
    Then I receive ValueError
