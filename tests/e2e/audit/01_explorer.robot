*** Settings ***
Documentation    Audit Explorer — navigation, filtering, detail drawer, stats.
...              Drives live backend (51734) + frontend (51735). Creates a test
...              user via API, seeds audit events for that user's org, signs in
...              via UI, navigates /audit, verifies filter + detail drawer.
Library     Browser
Library     Collections
Resource    ../keywords/audit.resource
Resource    ../keywords/auth.resource
Suite Setup       Launch Audit Suite
Suite Teardown    Teardown Audit Suite

*** Variables ***
${TS}           ${EMPTY}
${TEST_EMAIL}   ${EMPTY}
${TEST_PASS}    pass-audit-E2E-1234!
${PREFIX}       ${EMPTY}

*** Keywords ***
Launch Audit Suite
    ${ts}=    Get Time    epoch
    Set Suite Variable    ${TS}        ${ts}
    Set Suite Variable    ${PREFIX}    e2e-audit-${ts}
    Set Suite Variable    ${TEST_EMAIL}    e2e-audit-${ts}@tennetctl.test
    ${signup}=    API Create Audit User    ${TEST_EMAIL}    ${TEST_PASS}    Audit E2E
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

Teardown Audit Suite
    Cleanup Seeded Audit    ${PREFIX}
    Close Browser    ALL

Sign In UI
    Go To    ${FRONTEND_URL}/auth/signin
    Wait For Elements State    [data-testid="signin-form"]    visible    timeout=10s
    Fill Text    [data-testid="signin-email"]    ${TEST_EMAIL}
    Fill Text    [data-testid="signin-password"]    ${TEST_PASS}
    Click    [data-testid="signin-submit"]
    Wait For Load State    networkidle

*** Test Cases ***
Audit Explorer Renders Rows And Stats
    [Documentation]    Sign in, navigate /audit, apply prefix filter, verify filter bar, stats panel,
    ...                and events table all show seeded events (12 total).
    Sign In UI
    Open Audit Explorer
    Filter By Event Key Glob    ${PREFIX}.evt*
    Wait For Load State    networkidle    timeout=10s
    Assert Events Table Has Rows
    Assert Totals Equals    12

Filter By Event Key Glob Reduces Set
    [Documentation]    Narrow the glob to .alpha only — 4 rows (12 / 3 event types).
    Filter By Event Key Glob    ${PREFIX}.evt.alpha
    Wait For Load State    networkidle    timeout=10s
    Assert Totals Equals    4

Detail Drawer Opens On Row Click
    [Documentation]    Click the first event row, verify the drawer opens with
    ...                the metadata block rendered, then close it.
    Fill Text    [data-testid="audit-filter-event-key"]    ${EMPTY}
    Sleep    500ms
    Click First Event Row
    Assert Detail Drawer Open
    Close Detail Drawer
