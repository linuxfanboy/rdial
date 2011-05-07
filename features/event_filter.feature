Feature: Filter database events
    In order to support operate on subsets of events
    As a user
    We'll implement basic filtering methods

    Scenario: Fetch events for specific project
        Given I have the database test.txt
        When I process it with Events.read
        When I check return value for calling for_project on result with project=project2
        Then I see 1 events

    Scenario: Fetch events for specific year
        Given I have the database date_filtering.txt
        When I process it with Events.read
        When I check return value for calling for_year on result with year=2011
        Then I see 2 events

    Scenario: Fetch events for specific month
        Given I have the database date_filtering.txt
        When I process it with Events.read
        When I check return value for calling for_month on result with year=2011, month=1
        Then I see 1 events

    Scenario: Fetch events for specific day
        Given I have the database date_filtering.txt
        When I process it with Events.read
        When I check return value for calling for_day on result with year=2011, month=3, day=1
        Then I see 1 events