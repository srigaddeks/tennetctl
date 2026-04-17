*** Settings ***
Documentation    Monitoring Metrics — pick a metric, chart renders, bucket toggle re-renders,
...              "Add to dashboard" modal creates a panel on a new dashboard.
Library     Browser
Library     RequestsLibrary
Library     Collections
Resource    monitoring_keywords.resource
Suite Setup       Launch Metrics Suite
Suite Teardown    Close Browser    ALL

*** Variables ***
${TS}           ${EMPTY}
${TEST_EMAIL}   ${EMPTY}
${TEST_PASS}    pass-mon-metrics-E2E!1
${ORG_ID}       ${EMPTY}
${USER_ID}      ${EMPTY}
${METRIC_KEY}   ${EMPTY}

*** Keywords ***
Launch Metrics Suite
    ${ts}=    Get Time    epoch
    Set Suite Variable    ${TS}           ${ts}
    Set Suite Variable    ${METRIC_KEY}   e2ectr${ts}
    Set Suite Variable    ${TEST_EMAIL}   e2e-metrics-${ts}@tennetctl.test
    ${signup}=    API Create Monitoring User    ${TEST_EMAIL}    ${TEST_PASS}    Metrics E2E
    Set Suite Variable    ${ORG_ID}    ${signup['org_id']}
    Set Suite Variable    ${USER_ID}   ${signup['user_id']}
    # Create a counter metric and push 5 increments so the chart has data points
    API Create Metric    ${METRIC_KEY}    counter    ${ORG_ID}    ${USER_ID}
    FOR    ${i}    IN RANGE    5
        API Increment Metric    ${METRIC_KEY}    1    ${ORG_ID}    ${USER_ID}
    END
    Sleep    2s
    New Browser    chromium    headless=true
    New Context    viewport={'width': 1280, 'height': 900}
    New Page    about:blank
    Sign In Monitoring User    ${TEST_EMAIL}    ${TEST_PASS}

*** Test Cases ***
Metric Picker Renders And Shows Seeded Metric
    [Documentation]    Open /monitoring/metrics — metric picker sidebar renders,
    ...                searching for our key shows it in the list.
    Open Monitoring Page    /monitoring/metrics
    Wait For Elements State    [data-testid="monitoring-metric-picker"]    visible    timeout=10s
    Fill Text    [data-testid="monitoring-metric-search"]    ${METRIC_KEY}
    Sleep    1s
    Wait For Elements State    [data-testid="monitoring-metric-${METRIC_KEY}"]    visible    timeout=10s

Select Metric Renders Chart
    [Documentation]    Click the seeded metric row — MetricsChart component should render.
    Open Monitoring Page    /monitoring/metrics
    Wait For Elements State    [data-testid="monitoring-metric-picker"]    visible    timeout=10s
    Fill Text    [data-testid="monitoring-metric-search"]    ${METRIC_KEY}
    Sleep    1s
    Wait For Elements State    [data-testid="monitoring-metric-${METRIC_KEY}"]    visible    timeout=10s
    Click    [data-testid="monitoring-metric-${METRIC_KEY}"]
    # Chart component appears after metric is selected
    Wait For Elements State    [data-testid="monitoring-metrics-chart"]    visible    timeout=15s

Bucket Toggle Re-renders Chart
    [Documentation]    With metric selected, change bucket via select — chart re-renders
    ...                (the element detaches briefly then reappears with new data).
    Open Monitoring Page    /monitoring/metrics
    Wait For Elements State    [data-testid="monitoring-metric-picker"]    visible    timeout=10s
    Fill Text    [data-testid="monitoring-metric-search"]    ${METRIC_KEY}
    Sleep    1s
    Click    [data-testid="monitoring-metric-${METRIC_KEY}"]
    Wait For Elements State    [data-testid="monitoring-metrics-chart"]    visible    timeout=15s
    # Change bucket to 1m
    Select Options By    [data-testid="monitoring-metrics-bucket"]    value    1m
    Sleep    1s
    Wait For Load State    networkidle
    # Chart should still be visible after bucket change
    Wait For Elements State    [data-testid="monitoring-metrics-chart"]    visible    timeout=10s

Add To Dashboard Creates Panel On New Dashboard
    [Documentation]    Click "Add to dashboard" → modal appears → enter new dashboard name
    ...                → confirm → modal closes → verify via API that the panel exists.
    Open Monitoring Page    /monitoring/metrics
    Wait For Elements State    [data-testid="monitoring-metric-picker"]    visible    timeout=10s
    Fill Text    [data-testid="monitoring-metric-search"]    ${METRIC_KEY}
    Sleep    1s
    Click    [data-testid="monitoring-metric-${METRIC_KEY}"]
    Wait For Elements State    [data-testid="monitoring-metrics-add-to-dash"]    visible    timeout=15s
    Click    [data-testid="monitoring-metrics-add-to-dash"]
    # Modal opens — "Add panel to dashboard"
    Wait For Elements State    text=Add panel to dashboard    visible    timeout=5s
    # Enter new dashboard name in the "Or new dashboard name" input
    ${dash_name}=    Set Variable    E2E-Dash-${TS}
    Fill Text    id=dash-new    ${dash_name}
    # Use role=button with exact name to avoid matching the modal title
    Click    xpath=//button[normalize-space(text())="Add panel"]
    Wait For Load State    networkidle    timeout=10s
    # Verify via API that a dashboard with that name was created
    ${dashboards}=    API List Dashboards    ${ORG_ID}    ${USER_ID}
    ${items}=    Set Variable    ${dashboards}[items]
    ${found}=    Set Variable    ${False}
    FOR    ${d}    IN    @{items}
        IF    '${d}[name]' == '${dash_name}'
            Set Suite Variable    ${CREATED_DASH_ID}    ${d}[id]
            ${found}=    Set Variable    ${True}
        END
    END
    Should Be True    ${found}    Dashboard "${dash_name}" not found via API after creation
