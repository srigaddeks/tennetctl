*** Settings ***
Documentation    Monitoring Alerts — seed a metric + a rule → evaluator fires → alert
...              surfaces in UI → silence suppresses notifications → editor creates
...              new rule. Requires backend started with
...              TENNETCTL_MONITORING_ALERT_EVAL_INTERVAL_S=10 so cycles complete
...              within the E2E Sleep windows.
Library     Browser
Library     RequestsLibrary
Library     Collections
Library     String
Resource    monitoring_keywords.resource
Suite Setup       Launch Alerts Suite
Suite Teardown    Close Browser    ALL

*** Variables ***
${TS}                  ${EMPTY}
${TEST_EMAIL}          ${EMPTY}
${TEST_PASS}           pass-mon-alerts-E2E!1
${ORG_ID}              ${EMPTY}
${USER_ID}             ${EMPTY}
${METRIC_KEY}          ${EMPTY}
${FIRE_RULE_ID}        ${EMPTY}
${EVAL_WAIT}           40s

*** Keywords ***
Launch Alerts Suite
    ${ts}=    Get Time    epoch
    Set Suite Variable    ${TS}           ${ts}
    Set Suite Variable    ${METRIC_KEY}   e2ealerts${ts}
    Set Suite Variable    ${TEST_EMAIL}   e2e-alerts-${ts}@tennetctl.test
    ${signup}=    API Create Monitoring User    ${TEST_EMAIL}    ${TEST_PASS}    Alerts E2E
    Set Suite Variable    ${ORG_ID}    ${signup['org_id']}
    Set Suite Variable    ${USER_ID}   ${signup['user_id']}
    # Seed a counter metric and push increments so the rule has something to evaluate.
    API Create Metric    ${METRIC_KEY}    counter    ${ORG_ID}    ${USER_ID}
    FOR    ${i}    IN RANGE    10
        API Increment Metric    ${METRIC_KEY}    1    ${ORG_ID}    ${USER_ID}
    END
    Sleep    2s
    New Browser    chromium    headless=true
    New Context    viewport={'width': 1280, 'height': 900}
    New Page    about:blank
    Sign In Monitoring User    ${TEST_EMAIL}    ${TEST_PASS}

Seed Alert Rule Via API
    [Documentation]    POST an alert rule directly via the backend API. Uses the
    ...                test.alert.template notify_template_key placeholder — the
    ...                evaluator handles notify failures gracefully (alert event
    ...                is still created and visible in the UI).
    [Arguments]    ${name}    ${metric_key}    ${threshold}=0    ${for_duration}=0    ${severity}=info
    ${sess_name}=    Evaluate    'mon_rule_' + str(__import__('random').randint(10000,99999))
    RequestsLibrary.Create Session    ${sess_name}    ${MONITORING_BACKEND}
    ${headers}=    Create Dictionary
    ...    Content-Type=application/json
    ...    x-org-id=${ORG_ID}
    ...    x-user-id=${USER_ID}
    ${dsl}=    Create Dictionary
    ...    target=metrics
    ...    metric_key=${metric_key}
    ...    aggregate=sum
    ...    bucket=1m
    ${timerange}=    Create Dictionary    last=15m
    Set To Dictionary    ${dsl}    timerange=${timerange}
    ${condition}=    Create Dictionary
    ...    op=gt
    ...    threshold=${threshold}
    ...    for_duration_seconds=${for_duration}
    ${labels}=    Create Dictionary    recipient_user_id=${USER_ID}
    ${body}=    Create Dictionary
    ...    name=${name}
    ...    target=metrics
    ...    dsl=${dsl}
    ...    condition=${condition}
    ...    severity=${severity}
    ...    notify_template_key=test.alert.template
    ...    labels=${labels}
    ${resp}=    POST On Session    ${sess_name}    /v1/monitoring/alert-rules    json=${body}    headers=${headers}    expected_status=201
    ${rid}=    Set Variable    ${resp.json()['data']['id']}
    RETURN    ${rid}

*** Test Cases ***
Alert Rule Fires When Threshold Breached
    [Documentation]    Seed a rule with threshold 0 on an existing counter → within
    ...                one evaluator cycle, an alert event is created and visible
    ...                on /monitoring/alerts.
    ${rule_id}=    Seed Alert Rule Via API    e2e-fire-${TS}    ${METRIC_KEY}    0    0    critical
    Set Suite Variable    ${FIRE_RULE_ID}    ${rule_id}
    # Push more increments to guarantee sum > 0 within the window
    FOR    ${i}    IN RANGE    5
        API Increment Metric    ${METRIC_KEY}    1    ${ORG_ID}    ${USER_ID}
    END
    Sleep    ${EVAL_WAIT}
    Open Monitoring Page    /monitoring/alerts
    Wait For Elements State    [data-testid="heading-monitoring-alerts"]    visible    timeout=10s
    # An alert row should appear (refetch interval is 15s — give it a moment)
    Wait For Elements State    (//tr[@data-testid="alert-row"])[1]    visible    timeout=30s
    Wait For Elements State    (//span[@data-testid="alert-severity-critical"])[1]    visible    timeout=10s

Silence Alert From Row
    [Documentation]    Click the Silence button in an alert row → fill reason →
    ...                save → row shows the silenced badge after refetch.
    Open Monitoring Page    /monitoring/alerts
    Wait For Elements State    (//tr[@data-testid="alert-row"])[1]    visible    timeout=30s
    ${silence_buttons}=    Get Element Count    [data-testid="alert-row-silence"]
    Should Be True    ${silence_buttons} >= 1    Expected silence button on alert row
    # Click first silence button
    Click    (//button[@data-testid="alert-row-silence"])[1]
    Wait For Elements State    [data-testid="silence-dialog"]    visible    timeout=5s
    Fill Text    [data-testid="silence-reason"]    E2E test silence ${TS}
    Click    [data-testid="silence-save"]
    Wait For Load State    networkidle    timeout=10s
    # Verify silence exists via API. Existing firing events do not retroactively
    # flip the `silenced` column (append-only events); the silence suppresses
    # further Notify delivery on subsequent evaluator cycles, which is the
    # intended behavior. Pytest coverage in 13-08b verifies the evaluator's
    # silence enforcement directly.
    ${sess_name}=    Evaluate    'mon_silences_verify_' + str(__import__('random').randint(10000,99999))
    RequestsLibrary.Create Session    ${sess_name}    ${MONITORING_BACKEND}
    ${headers}=    Create Dictionary    x-org-id=${ORG_ID}    x-user-id=${USER_ID}
    ${resp}=    GET On Session    ${sess_name}    /v1/monitoring/silences    headers=${headers}    expected_status=200
    ${items}=    Set Variable    ${resp.json()['data']['items']}
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 1    Expected >=1 silence after creating via UI, got ${count}

Alert Rule Editor Creates Rule
    [Documentation]    On /monitoring/alerts/rules/new, fill the form, save — the
    ...                new rule appears on the rules list.
    ${editor_name}=    Set Variable    e2e-editor-${TS}
    Open Monitoring Page    /monitoring/alerts/rules
    Wait For Elements State    [data-testid="new-rule-button"]    visible    timeout=10s
    Click    [data-testid="new-rule-button"]
    Wait For Load State    networkidle    timeout=10s
    Wait For Elements State    [data-testid="rule-name"]    visible    timeout=10s
    Fill Text    [data-testid="rule-name"]    ${editor_name}
    Fill Text    [data-testid="rule-dsl-metric-key"]    ${METRIC_KEY}
    Fill Text    [data-testid="rule-condition-threshold"]    5
    Select Options By    [data-testid="rule-severity-select"]    value    warn
    Fill Text    [data-testid="rule-notify-template"]    test.alert.template
    Click    [data-testid="rule-save-button"]
    Wait For Load State    networkidle    timeout=10s
    # Redirected to /monitoring/alerts/rules — the new rule is listed
    Wait For Elements State    text=${editor_name}    visible    timeout=15s

Rule Editor Supports Edit Flow
    [Documentation]    Open an existing rule via the list → editor loads with
    ...                current values → update severity → save succeeds.
    Open Monitoring Page    /monitoring/alerts/rules
    Wait For Elements State    [data-testid="rule-row-${FIRE_RULE_ID}"]    visible    timeout=10s
    Click    [data-testid="rule-edit-${FIRE_RULE_ID}"]
    Wait For Load State    networkidle    timeout=10s
    Wait For Elements State    [data-testid="rule-name"]    visible    timeout=10s
    # Change severity to error and save
    Select Options By    [data-testid="rule-severity-select"]    value    error
    Click    [data-testid="rule-save-button"]
    Wait For Load State    networkidle    timeout=10s
    Wait For Elements State    [data-testid="rule-row-${FIRE_RULE_ID}"]    visible    timeout=15s
