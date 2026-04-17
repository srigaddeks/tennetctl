*** Settings ***
Library    Browser
Library    RequestsLibrary
Library    Collections
Library    String

*** Variables ***
${MONITORING_FRONTEND}    http://localhost:51735
${MONITORING_BACKEND}     http://localhost:51734

*** Keywords ***
# ── Auth ──────────────────────────────────────────────────────────────

API Create Monitoring User
    [Documentation]    Sign up and return a dict with keys: token, org_id, user_id.
    [Arguments]    ${email}    ${password}    ${display_name}
    ${body}=    Create Dictionary    email=${email}    password=${password}    display_name=${display_name}
    ${session}=    RequestsLibrary.Create Session    mon_auth    ${MONITORING_BACKEND}
    ${resp}=    POST On Session    mon_auth    /v1/auth/signup    json=${body}    expected_status=201
    ${d}=    Set Variable    ${resp.json()['data']}
    ${result}=    Create Dictionary
    ...    token=${d}[token]
    ...    org_id=${d}[session][org_id]
    ...    user_id=${d}[session][user_id]
    RETURN    ${result}

Sign In Monitoring User
    [Arguments]    ${email}    ${password}
    Go To    ${MONITORING_FRONTEND}/auth/signin
    Wait For Elements State    [data-testid="signin-form"]    visible    timeout=10s
    Fill Text    [data-testid="signin-email"]    ${email}
    Fill Text    [data-testid="signin-password"]    ${password}
    Click    [data-testid="signin-submit"]
    Wait For Load State    networkidle    timeout=15s

Open Monitoring Page
    [Arguments]    ${path}
    Go To    ${MONITORING_FRONTEND}${path}
    Wait For Load State    networkidle    timeout=15s

# ── OTLP Log Seeding ──────────────────────────────────────────────────

Post OTLP Log
    [Documentation]    POST a single log record via OTLP endpoint.
    ...                severity: 9=INFO, 13=WARN, 17=ERROR
    [Arguments]    ${service}    ${severity}    ${body_text}    ${trace_id}=${EMPTY}    ${org_id}=${EMPTY}    ${user_id}=${EMPTY}
    ${sess_name}=    Evaluate    'mon_otlp_' + str(__import__('random').randint(10000,99999))
    RequestsLibrary.Create Session    ${sess_name}    ${MONITORING_BACKEND}
    ${headers}=    Create Dictionary
    ...    Content-Type=application/json
    ...    x-org-id=${org_id}
    ...    x-user-id=${user_id}
    ${now_ns}=    Evaluate    int(__import__('time').time() * 1e9)
    ${trace_field}=    Set Variable If    '${trace_id}' != ''
    ...    ,"traceId":"${trace_id}"
    ...    ${EMPTY}
    ${payload}=    Evaluate
    ...    {"resourceLogs":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"${service}"}}]},"scopeLogs":[{"scope":{"name":"e2e"},"logRecords":[{"timeUnixNano":"${now_ns}","severityNumber":${severity},"severityText":"SEV${severity}","body":{"stringValue":"${body_text}"}${trace_field}}]}]}]}
    ${resp}=    POST On Session    ${sess_name}    /v1/monitoring/otlp/v1/logs    json=${payload}    headers=${headers}    expected_status=any
    RETURN    ${resp.status_code}

# ── OTLP Trace Seeding ────────────────────────────────────────────────

Post OTLP Parent Child Trace
    [Documentation]    Seed a parent+child span pair using base64-encoded IDs per OTLP JSON spec.
    ...                Returns the hex trace_id (32 chars) that appears in the UI.
    [Arguments]    ${service}    ${parent_name}    ${child_name}    ${org_id}    ${user_id}
    ${sess_name}=    Evaluate    'mon_trace_' + str(__import__('random').randint(10000,99999))
    RequestsLibrary.Create Session    ${sess_name}    ${MONITORING_BACKEND}
    ${headers}=    Create Dictionary
    ...    Content-Type=application/json
    ...    x-org-id=${org_id}
    ...    x-user-id=${user_id}
    # Generate hex IDs, then base64 encode for OTLP JSON format
    ${trace_hex}=    Evaluate    __import__('os').urandom(16).hex()
    ${parent_hex}=    Evaluate    __import__('os').urandom(8).hex()
    ${child_hex}=    Evaluate    __import__('os').urandom(8).hex()
    ${trace_b64}=    Evaluate    __import__('base64').b64encode(bytes.fromhex('${trace_hex}')).decode()
    ${parent_b64}=    Evaluate    __import__('base64').b64encode(bytes.fromhex('${parent_hex}')).decode()
    ${child_b64}=    Evaluate    __import__('base64').b64encode(bytes.fromhex('${child_hex}')).decode()
    ${now_ns}=    Evaluate    int(__import__('time').time() * 1e9)
    ${end_ns}=    Evaluate    ${now_ns} + 100000000
    ${child_start}=    Evaluate    ${now_ns} + 10000000
    ${child_end}=    Evaluate    ${now_ns} + 90000000
    # Build JSON payload string — OTLP JSON uses base64 for binary fields
    ${payload_str}=    Set Variable    {"resourceSpans":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"${service}"}}]},"scopeSpans":[{"scope":{"name":"e2e"},"spans":[{"traceId":"${trace_b64}","spanId":"${parent_b64}","parentSpanId":"","name":"${parent_name}","kind":2,"startTimeUnixNano":"${now_ns}","endTimeUnixNano":"${end_ns}","status":{"code":1}},{"traceId":"${trace_b64}","spanId":"${child_b64}","parentSpanId":"${parent_b64}","name":"${child_name}","kind":2,"startTimeUnixNano":"${child_start}","endTimeUnixNano":"${child_end}","status":{"code":1}}]}]}]}
    ${resp}=    POST On Session    ${sess_name}    /v1/monitoring/otlp/v1/traces
    ...    data=${payload_str}    headers=${headers}    expected_status=any
    RETURN    ${trace_hex}

# ── Metric Seeding ────────────────────────────────────────────────────

API Create Metric
    [Arguments]    ${key}    ${kind}    ${org_id}    ${user_id}
    ${sess_name}=    Evaluate    'mon_metric_' + str(__import__('random').randint(10000,99999))
    RequestsLibrary.Create Session    ${sess_name}    ${MONITORING_BACKEND}
    ${headers}=    Create Dictionary
    ...    Content-Type=application/json
    ...    x-org-id=${org_id}
    ...    x-user-id=${user_id}
    ${body}=    Create Dictionary    key=${key}    kind=${kind}    description=E2E test metric
    ${resp}=    POST On Session    ${sess_name}    /v1/monitoring/metrics    json=${body}    headers=${headers}    expected_status=any
    RETURN    ${resp.status_code}

API Increment Metric
    [Arguments]    ${key}    ${value}    ${org_id}    ${user_id}
    ${sess_name}=    Evaluate    'mon_inc_' + str(__import__('random').randint(10000,99999))
    RequestsLibrary.Create Session    ${sess_name}    ${MONITORING_BACKEND}
    ${headers}=    Create Dictionary
    ...    Content-Type=application/json
    ...    x-org-id=${org_id}
    ...    x-user-id=${user_id}
    ${body}=    Create Dictionary    value=${value}    labels=${{{}}}
    ${resp}=    POST On Session    ${sess_name}    /v1/monitoring/metrics/${key}/increment    json=${body}    headers=${headers}    expected_status=any
    RETURN    ${resp.status_code}

# ── Dashboard API ─────────────────────────────────────────────────────

API Delete Dashboard
    [Arguments]    ${dashboard_id}    ${org_id}    ${user_id}
    ${sess_name}=    Evaluate    'mon_dash_del_' + str(__import__('random').randint(10000,99999))
    RequestsLibrary.Create Session    ${sess_name}    ${MONITORING_BACKEND}
    ${headers}=    Create Dictionary
    ...    x-org-id=${org_id}
    ...    x-user-id=${user_id}
    ${resp}=    DELETE On Session    ${sess_name}    /v1/monitoring/dashboards/${dashboard_id}    headers=${headers}    expected_status=any
    RETURN    ${resp.status_code}

API List Dashboards
    [Arguments]    ${org_id}    ${user_id}
    ${sess_name}=    Evaluate    'mon_dash_list_' + str(__import__('random').randint(10000,99999))
    RequestsLibrary.Create Session    ${sess_name}    ${MONITORING_BACKEND}
    ${headers}=    Create Dictionary
    ...    x-org-id=${org_id}
    ...    x-user-id=${user_id}
    ${resp}=    GET On Session    ${sess_name}    /v1/monitoring/dashboards    headers=${headers}    expected_status=200
    RETURN    ${resp.json()['data']}
