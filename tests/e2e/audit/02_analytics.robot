*** Settings ***
Documentation    Audit Analytics — funnel, retention, saved views, CSV export.
...              Shares the same seed pattern as 01_explorer.robot (12 events per
...              prefix, 3 event types: .evt.alpha / .evt.beta / .evt.gamma).
...              Each test case builds on the one before within the suite.
Library     Browser
Library     Collections
Library     RequestsLibrary
Library     DatabaseLibrary
Resource    ../keywords/audit.resource
Resource    ../keywords/auth.resource
Suite Setup       Launch Analytics Suite
Suite Teardown    Teardown Analytics Suite

*** Variables ***
${TS}           ${EMPTY}
${TEST_EMAIL}   ${EMPTY}
${TEST_PASS}    pass-analytics-E2E-1234!
${PREFIX}       ${EMPTY}

*** Keywords ***
Launch Analytics Suite
    ${ts}=    Get Time    epoch
    Set Suite Variable    ${TS}        ${ts}
    Set Suite Variable    ${PREFIX}    e2e-analytics-${ts}
    Set Suite Variable    ${TEST_EMAIL}    e2e-analytics-${ts}@tennetctl.test
    ${signup}=    API Create Audit User    ${TEST_EMAIL}    ${TEST_PASS}    Analytics E2E
    ${me}=        API Fetch Me    ${signup['token']}
    Set Suite Variable    ${USER_ID}         ${me['user']['id']}
    Set Suite Variable    ${SESSION_ID}      ${me['session']['id']}
    Set Suite Variable    ${ORG_ID}          ${me['session']['org_id']}
    ${ws_id}=    Evaluate    $me['session']['workspace_id'] or $me['session']['org_id']
    Set Suite Variable    ${WORKSPACE_ID}    ${ws_id}
    Seed Audit Events Into Org    ${USER_ID}    ${SESSION_ID}    ${ORG_ID}    ${WORKSPACE_ID}    ${PREFIX}
    New Browser    chromium    headless=True
    New Context
    New Page    about:blank
    # Sign in once for the whole suite
    Go To    ${FRONTEND_URL}/auth/signin
    Wait For Elements State    [data-testid="signin-form"]    visible    timeout=10s
    Fill Text    [data-testid="signin-email"]    ${TEST_EMAIL}
    Fill Text    [data-testid="signin-password"]    ${TEST_PASS}
    Click    [data-testid="signin-submit"]
    Wait For Load State    networkidle

Teardown Analytics Suite
    Cleanup Seeded Audit    ${PREFIX}
    Cleanup Seeded Audit    e2e-analytics-${TS}
    # Clean up saved views via DB
    Connect To Database    psycopg2    ${DB_NAME}    ${DB_USER}    ${DB_PASS}    ${DB_HOST}    ${DB_PORT}
    Execute Sql String    DELETE FROM "04_audit"."10_fct_audit_saved_views" WHERE org_id = '${ORG_ID}';
    Disconnect From Database
    Close Browser    ALL

_Assert No Saved Views
    ${vis}=    Run Keyword And Return Status    Get Element    [data-testid="audit-saved-views-list"]
    IF    ${vis}
        ${count}=    Get Element Count    css=[data-testid="audit-saved-views-list"] > li
        Should Be Equal As Integers    ${count}    0
    END

*** Test Cases ***
Analytics Tab Renders All Panels
    [Documentation]    Navigate to the Analytics tab; verify funnel builder,
    ...                retention grid, and saved views panel all render.
    Open Analytics Tab
    Wait For Elements State    [data-testid="audit-funnel-builder"]     visible    timeout=10s
    Wait For Elements State    [data-testid="audit-retention-grid"]     visible    timeout=10s
    Wait For Elements State    [data-testid="audit-saved-views-panel"]  visible    timeout=10s

Funnel Returns Steps For Seeded Events
    [Documentation]    Run a 2-step funnel with the seeded event keys; verify
    ...                the result panel appears and both steps are listed.
    Run Funnel    ${PREFIX}.evt.alpha    ${PREFIX}.evt.beta
    ${items}=    Get Element Count    css=[data-testid="audit-funnel-result"] > *
    Should Be True    ${items} >= 2    Expected at least 2 funnel step rows; got ${items}

Saved View Create And Delete
    [Documentation]    Save current filter as a named view, verify it appears
    ...                in the list, then delete it and verify list is empty again.
    Create Saved View    My E2E Test View
    # Verify the view appears in the list
    ${count}=    Get Element Count    css=[data-testid="audit-saved-views-list"] > li
    Should Be True    ${count} >= 1    Expected at least 1 saved view in list; got ${count}
    # Delete the first view
    ${items}=    Get Elements    css=[data-testid^="audit-saved-views-delete-"]
    Click    ${items}[0]
    # List should disappear or show empty message
    Wait Until Keyword Succeeds    10s    500ms    _Assert No Saved Views

CSV Export Link Present
    [Documentation]    Verify the Export CSV link is rendered in the page header
    ...                and points to the backend CSV endpoint.
    Go To    ${FRONTEND_URL}/audit
    Wait For Load State    networkidle    timeout=15s
    Wait For Elements State    [data-testid="audit-export-csv"]    visible    timeout=10s
    ${href}=    Get Attribute    [data-testid="audit-export-csv"]    href
    Should Contain    ${href}    format=csv
