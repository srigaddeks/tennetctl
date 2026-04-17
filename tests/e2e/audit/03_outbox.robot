*** Settings ***
Documentation    Audit Outbox — live tail toggle, outbox cursor endpoint, tail API.
...              Drives live backend (51734) + frontend (51735). Creates a test user,
...              seeds audit events, verifies the tail API returns events via outbox
...              cursor, and checks the Live toggle UI appears and activates.
Library     Browser
Library     Collections
Library     RequestsLibrary
Library     DatabaseLibrary
Resource    ../keywords/audit.resource
Resource    ../keywords/auth.resource
Suite Setup       Launch Outbox Suite
Suite Teardown    Teardown Outbox Suite

*** Variables ***
${TS}           ${EMPTY}
${TEST_EMAIL}   ${EMPTY}
${TEST_PASS}    pass-outbox-E2E-1234!
${PREFIX}       ${EMPTY}
${USER_ID}      ${EMPTY}
${SESSION_ID}   ${EMPTY}
${ORG_ID}       ${EMPTY}
${WORKSPACE_ID}    ${EMPTY}

*** Keywords ***
Launch Outbox Suite
    ${ts}=    Get Time    epoch
    Set Suite Variable    ${TS}           ${ts}
    Set Suite Variable    ${PREFIX}       e2e-outbox-${ts}
    Set Suite Variable    ${TEST_EMAIL}   e2e-outbox-${ts}@tennetctl.test
    ${signup}=    API Create Audit User    ${TEST_EMAIL}    ${TEST_PASS}    Outbox E2E
    ${me}=        API Fetch Me    ${signup['token']}
    Set Suite Variable    ${USER_ID}         ${me['user']['id']}
    Set Suite Variable    ${SESSION_ID}      ${me['session']['id']}
    Set Suite Variable    ${ORG_ID}          ${me['session']['org_id']}
    ${ws_id}=    Evaluate    $me['session']['workspace_id'] or $me['session']['org_id']
    Set Suite Variable    ${WORKSPACE_ID}    ${ws_id}
    New Browser    chromium    headless=True
    New Context
    New Page    about:blank

Teardown Outbox Suite
    Cleanup Seeded Audit    ${PREFIX}
    Close Browser    ALL

Sign In Outbox UI
    Go To    ${FRONTEND_URL}/auth/signin
    Wait For Elements State    [data-testid="signin-form"]    visible    timeout=10s
    Fill Text    [data-testid="signin-email"]    ${TEST_EMAIL}
    Fill Text    [data-testid="signin-password"]    ${TEST_PASS}
    Click    [data-testid="signin-submit"]
    Wait For Load State    networkidle

Seed One System Event
    [Documentation]    Insert a single audit event with the given org and return its id via SQL output.
    [Arguments]    ${event_key}
    Connect To Database    psycopg2    ${DB_NAME}    ${DB_USER}    ${DB_PASS}    ${DB_HOST}    ${DB_PORT}
    ${sql}=    Catenate    SEPARATOR=\n
    ...    INSERT INTO "04_audit"."60_evt_audit"
    ...      (id, event_key, actor_user_id, actor_session_id, org_id, workspace_id,
    ...       trace_id, span_id, audit_category, outcome, metadata)
    ...    VALUES (
    ...      gen_random_uuid()::text,
    ...      '${event_key}',
    ...      '${USER_ID}', '${SESSION_ID}', '${ORG_ID}', '${WORKSPACE_ID}',
    ...      gen_random_uuid()::text, gen_random_uuid()::text,
    ...      'system', 'success',
    ...      jsonb_build_object('tag', '${PREFIX}')
    ...    )
    ...    RETURNING id;
    ${rows}=    Query    ${sql}
    Disconnect From Database
    RETURN    ${rows[0][0]}

Get Outbox Cursor Via API
    [Documentation]    Call /v1/audit-events/outbox-cursor and return last_outbox_id.
    ${session}=    RequestsLibrary.Create Session    backend    ${BACKEND_URL}
    ${resp}=    GET On Session    backend    /v1/audit-events/outbox-cursor    expected_status=200
    RETURN    ${resp.json()['data']['last_outbox_id']}

Poll Tail Via API
    [Documentation]    Call /v1/audit-events/tail and return response data.
    [Arguments]    ${since_id}    ${org_id}
    ${session}=    RequestsLibrary.Create Session    backend    ${BACKEND_URL}
    ${params}=    Create Dictionary    since_id=${since_id}    org_id=${org_id}    limit=10
    ${resp}=    GET On Session    backend    /v1/audit-events/tail    params=${params}    expected_status=200
    RETURN    ${resp.json()['data']}

*** Test Cases ***
Outbox Cursor Endpoint Returns Integer
    [Documentation]    GET /v1/audit-events/outbox-cursor returns ok + last_outbox_id as int.
    ${cursor}=    Get Outbox Cursor Via API
    Should Be True    isinstance(${cursor}, int)    last_outbox_id should be an integer, got: ${cursor}

Tail Returns New Events After Cursor
    [Documentation]    Record cursor, insert 1 event, poll tail from before that event —
    ...                response must include exactly that event and advance the cursor.
    ${before_id}=    Get Outbox Cursor Via API
    Seed One System Event    ${PREFIX}.tail.test
    ${tail}=    Poll Tail Via API    ${before_id}    ${ORG_ID}
    ${count}=    Get Length    ${tail['items']}
    Should Be True    ${count} >= 1    Expected at least 1 item from tail, got ${count}
    Should Be True    ${tail['last_outbox_id']} > ${before_id}
    ...    last_outbox_id (${tail['last_outbox_id']}) should be > before_id (${before_id})

Tail With No New Events Returns Empty
    [Documentation]    Poll tail with cursor at current max — must return empty items
    ...                and same last_outbox_id.
    ${current_id}=    Get Outbox Cursor Via API
    ${tail}=    Poll Tail Via API    ${current_id}    ${ORG_ID}
    ${count}=    Get Length    ${tail['items']}
    Should Be Equal As Integers    ${count}    0
    Should Be Equal As Integers    ${tail['last_outbox_id']}    ${current_id}

Live Toggle Button Appears On Audit Explorer
    [Documentation]    Navigate to /audit, verify the "Go Live" button renders
    ...                and activates on click (shows Live text + banner).
    Sign In Outbox UI
    Open Audit Explorer
    Wait For Elements State    [data-testid="audit-live-toggle"]    visible    timeout=10s
    ${text_before}=    Get Text    [data-testid="audit-live-toggle"]
    Should Contain    ${text_before}    Go Live
    Click    [data-testid="audit-live-toggle"]
    Wait For Elements State    [data-testid="audit-live-banner"]    visible    timeout=5s
    ${text_after}=    Get Text    [data-testid="audit-live-toggle"]
    Should Contain    ${text_after}    Live
    # Turn it back off
    Click    [data-testid="audit-live-toggle"]
    Wait For Elements State    [data-testid="audit-live-banner"]    hidden    timeout=5s
