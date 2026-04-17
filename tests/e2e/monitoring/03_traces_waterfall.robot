*** Settings ***
Documentation    Monitoring Traces — seed parent+child span pair via OTLP, open trace list,
...              click trace row, navigate to waterfall detail page, verify 2 spans rendered.
Library     Browser
Library     RequestsLibrary
Library     Collections
Resource    monitoring_keywords.resource
Suite Setup       Launch Traces Suite
Suite Teardown    Close Browser    ALL

*** Variables ***
${TS}           ${EMPTY}
${TEST_EMAIL}   ${EMPTY}
${TEST_PASS}    pass-mon-traces-E2E!1
${ORG_ID}       ${EMPTY}
${USER_ID}      ${EMPTY}
${TRACE_ID}     ${EMPTY}
${SVC_NAME}     ${EMPTY}

*** Keywords ***
Launch Traces Suite
    ${ts}=    Get Time    epoch
    Set Suite Variable    ${TS}       ${ts}
    Set Suite Variable    ${SVC_NAME}    e2e-trace-svc-${ts}
    Set Suite Variable    ${TEST_EMAIL}   e2e-traces-${ts}@tennetctl.test
    ${signup}=    API Create Monitoring User    ${TEST_EMAIL}    ${TEST_PASS}    Traces E2E
    Set Suite Variable    ${ORG_ID}    ${signup['org_id']}
    Set Suite Variable    ${USER_ID}   ${signup['user_id']}
    # Seed a parent + child span pair
    ${tid}=    Post OTLP Parent Child Trace
    ...    ${SVC_NAME}    parent-span-${ts}    child-span-${ts}
    ...    ${ORG_ID}    ${USER_ID}
    Set Suite Variable    ${TRACE_ID}    ${tid}
    # Allow consumer to process
    Sleep    4s
    New Browser    chromium    headless=true
    New Context    viewport={'width': 1280, 'height': 900}
    New Page    about:blank
    Sign In Monitoring User    ${TEST_EMAIL}    ${TEST_PASS}

*** Test Cases ***
Traces List Renders Table
    [Documentation]    Navigate to /monitoring/traces — table renders with at least one row.
    Open Monitoring Page    /monitoring/traces
    Wait For Elements State    [data-testid="heading-monitoring-traces"]    visible    timeout=10s
    # Filter by our service so we only see our trace
    Fill Text    [data-testid="monitoring-traces-service"]    ${SVC_NAME}
    Sleep    2s
    Wait For Load State    networkidle
    ${count}=    Get Element Count    css=tr[data-testid^="monitoring-trace-row-"]
    Should Be True    ${count} >= 1    Expected ≥1 trace row for service ${SVC_NAME}, got ${count}

Trace Row Links To Waterfall Detail
    [Documentation]    Click the trace_id link in the traces list — navigates to /monitoring/traces/{id}
    ...                and the waterfall component renders.
    Open Monitoring Page    /monitoring/traces
    Wait For Elements State    [data-testid="heading-monitoring-traces"]    visible    timeout=10s
    Fill Text    [data-testid="monitoring-traces-service"]    ${SVC_NAME}
    Sleep    2s
    Wait For Load State    networkidle
    # Click the first anchor for this trace (multiple rows may share trace_id for child spans)
    Wait For Elements State    css=tr[data-testid="monitoring-trace-row-${TRACE_ID}"]:first-of-type a    visible    timeout=10s
    Click    css=tr[data-testid="monitoring-trace-row-${TRACE_ID}"]:first-of-type a
    Wait For Load State    networkidle    timeout=15s
    # Waterfall should render
    Wait For Elements State    [data-testid="monitoring-trace-waterfall"]    visible    timeout=10s

Waterfall Shows Parent And Child Spans
    [Documentation]    On the waterfall detail page for our seeded trace, confirm 2 span bars
    ...                are rendered — the parent and child rows.
    Go To    ${MONITORING_FRONTEND}/monitoring/traces/${TRACE_ID}
    Wait For Load State    networkidle    timeout=15s
    Wait For Elements State    [data-testid="monitoring-trace-waterfall"]    visible    timeout=15s
    ${count}=    Get Element Count    css=button[data-testid^="monitoring-trace-span-"]
    Should Be True    ${count} >= 2    Expected ≥2 span bars (parent+child) for trace ${TRACE_ID}, got ${count}

Direct URL To Trace Waterfall Works
    [Documentation]    Navigate directly to /monitoring/traces/{id} — page loads without error.
    Go To    ${MONITORING_FRONTEND}/monitoring/traces/${TRACE_ID}
    Wait For Load State    networkidle    timeout=15s
    Wait For Elements State    [data-testid="monitoring-trace-waterfall"]    visible    timeout=15s
    # Heading confirms we're on a trace detail page
    Wait For Elements State    [data-testid="heading-monitoring-trace"]    visible    timeout=5s
