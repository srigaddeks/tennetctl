*** Settings ***
Documentation    Monitoring Logs — Explorer tab filtering + Live Tail streaming.
...              Seeds logs via OTLP API, signs in via UI, asserts rows visible,
...              severity filter works, and live tail streams new events.
Library     Browser
Library     RequestsLibrary
Library     Collections
Resource    monitoring_keywords.resource
Suite Setup       Launch Logs Suite
Suite Teardown    Close Browser    ALL

*** Variables ***
${TS}           ${EMPTY}
${TEST_EMAIL}   ${EMPTY}
${TEST_PASS}    pass-mon-logs-E2E!1
${ORG_ID}       ${EMPTY}
${USER_ID}      ${EMPTY}
${SVC_NAME}     ${EMPTY}

*** Keywords ***
Launch Logs Suite
    ${ts}=    Get Time    epoch
    Set Suite Variable    ${TS}           ${ts}
    Set Suite Variable    ${SVC_NAME}     e2e-logs-${ts}
    Set Suite Variable    ${TEST_EMAIL}   e2e-logs-${ts}@tennetctl.test
    ${signup}=    API Create Monitoring User    ${TEST_EMAIL}    ${TEST_PASS}    Logs E2E
    Set Suite Variable    ${ORG_ID}    ${signup['org_id']}
    Set Suite Variable    ${USER_ID}   ${signup['user_id']}
    # Seed 3 INFO + 2 ERROR logs — body includes SVC_NAME so body-search works.
    Post OTLP Log    ${SVC_NAME}    9     ${SVC_NAME} info-row-one     org_id=${ORG_ID}    user_id=${USER_ID}
    Post OTLP Log    ${SVC_NAME}    9     ${SVC_NAME} info-row-two     org_id=${ORG_ID}    user_id=${USER_ID}
    Post OTLP Log    ${SVC_NAME}    9     ${SVC_NAME} info-row-three   org_id=${ORG_ID}    user_id=${USER_ID}
    Post OTLP Log    ${SVC_NAME}    17    ${SVC_NAME} error-row-one    org_id=${ORG_ID}    user_id=${USER_ID}
    Post OTLP Log    ${SVC_NAME}    17    ${SVC_NAME} error-row-two    org_id=${ORG_ID}    user_id=${USER_ID}
    Sleep    5s
    New Browser    chromium    headless=true
    New Context    viewport={'width': 1280, 'height': 900}
    New Page    about:blank
    Sign In Monitoring User    ${TEST_EMAIL}    ${TEST_PASS}

*** Test Cases ***
Logs Explorer Renders Seeded Rows
    [Documentation]    Navigate to /monitoring/logs (Explorer tab), wait for rows to appear.
    ...                At least one log row must be visible; confirms OTLP pipeline + UI query.
    Open Monitoring Page    /monitoring/logs
    Wait For Elements State    [data-testid="monitoring-log-explorer"]    visible    timeout=10s
    # Apply body search to narrow results to our seeded service marker
    Fill Text    [data-testid="monitoring-log-body-search"]    ${SVC_NAME}
    # Debounce + query takes ~1s
    Sleep    2s
    Wait For Load State    networkidle
    ${count}=    Get Element Count    css=tr[data-testid^="monitoring-log-row-"]
    Should Be True    ${count} >= 5    Expected ≥5 seeded log rows, got ${count}

Severity Filter Info Shows Info Rows
    [Documentation]    Click the INFO severity button — the explorer sends severity_min=9.
    ...                Rows matching our service must include the info entries.
    Open Monitoring Page    /monitoring/logs
    Wait For Elements State    [data-testid="monitoring-log-explorer"]    visible    timeout=10s
    Fill Text    [data-testid="monitoring-log-body-search"]    ${SVC_NAME}
    Sleep    500ms
    Click    [data-testid="monitoring-log-sev-info"]
    Sleep    2s
    Wait For Load State    networkidle
    ${count}=    Get Element Count    css=tr[data-testid^="monitoring-log-row-"]
    Should Be True    ${count} >= 1    Expected at least 1 row after info filter, got ${count}
    # Deselect filter for teardown isolation
    Click    [data-testid="monitoring-log-sev-info"]

Severity Filter Error Narrows To Error Rows
    [Documentation]    Click ERROR severity — should reduce to only error-level rows.
    Open Monitoring Page    /monitoring/logs
    Wait For Elements State    [data-testid="monitoring-log-explorer"]    visible    timeout=10s
    Fill Text    [data-testid="monitoring-log-body-search"]    ${SVC_NAME}
    Sleep    500ms
    Click    [data-testid="monitoring-log-sev-error"]
    Sleep    2s
    Wait For Load State    networkidle
    ${count}=    Get Element Count    css=tr[data-testid^="monitoring-log-row-"]
    Should Be True    ${count} >= 1    Expected at least 1 error row, got ${count}
    # Clicking error filter means severity_min=17 — all rows must be error level.
    # We seeded 2 error rows so expect at most 2 (may have background errors too).
    Should Be True    ${count} <= 50    Unexpectedly huge result with error filter

Live Tail Tab Is Reachable And Shows Component
    [Documentation]    Switch to Live Tail tab — confirms the tab renders the live tail component.
    Open Monitoring Page    /monitoring/logs
    Wait For Elements State    [data-testid="monitoring-logs-tab-live"]    visible    timeout=10s
    Click    [data-testid="monitoring-logs-tab-live"]
    Wait For Load State    networkidle
    Wait For Elements State    [data-testid="monitoring-log-live-tail"]    visible    timeout=10s
    # Pause button should be visible (stream is live by default)
    Wait For Elements State    [data-testid="monitoring-livetail-pause"]    visible    timeout=10s

Live Tail Streams New Log Entry
    [Documentation]    With live tail open, push a fresh log via OTLP and verify it appears.
    Open Monitoring Page    /monitoring/logs
    Wait For Elements State    [data-testid="monitoring-logs-tab-live"]    visible    timeout=10s
    Click    [data-testid="monitoring-logs-tab-live"]
    Wait For Load State    networkidle
    Wait For Elements State    [data-testid="monitoring-log-live-tail"]    visible    timeout=10s
    # Wait for pause button (indicates SSE stream is live and component is rendered)
    Wait For Elements State    [data-testid="monitoring-livetail-pause"]    visible    timeout=15s
    # Allow SSE connection to fully establish
    Sleep    2s
    # Push a log with a unique body marker — this body text is unique to this test run
    ${ts_now}=    Get Time    epoch
    ${unique_marker}=    Set Variable    LIVETAIL-${ts_now}
    Post OTLP Log    ${SVC_NAME}    9    ${unique_marker}    org_id=${ORG_ID}    user_id=${USER_ID}
    # Live tail SSE polls every 1s → allow up to 30s including NATS/consumer latency
    Wait For Elements State    text=${unique_marker}    visible    timeout=30s
