*** Settings ***
Library     Browser
Library     Collections
Library     RequestsLibrary
Library     DatabaseLibrary

*** Variables ***
${FRONTEND_URL}        http://localhost:51735
${BACKEND_URL}         http://localhost:51734
${AUDIT_PREFIX}        e2e-audit
${DB_HOST}             localhost
${DB_PORT}             5434
${DB_NAME}             tennetctl
${DB_USER}             tennetctl
${DB_PASS}             tennetctl_dev

*** Keywords ***
Open Audit Explorer
    Go To    ${FRONTEND_URL}/audit
    Wait For Load State    networkidle    timeout=20s
    Wait For Elements State    [data-testid="audit-filter-bar"]    visible    timeout=10s
    Wait For Elements State    [data-testid="audit-stats-panel"]   visible    timeout=10s

Assert Events Table Has Rows
    ${count}=    Get Element Count    css=tr[data-testid^="audit-row-"]
    Should Be True    ${count} > 0    Expected at least one audit row; got ${count}

Assert Totals Equals
    [Arguments]    ${expected}
    Wait For Elements State    [data-testid="audit-stats-total"]    visible    timeout=15s
    Wait Until Keyword Succeeds    15s    500ms    _Check Total Value    ${expected}

_Check Total Value
    [Arguments]    ${expected}
    ${text}=    Get Text    [data-testid="audit-stats-total"]
    Should Be Equal As Strings    ${text}    ${expected}

Filter By Event Key Glob
    [Arguments]    ${pattern}
    Fill Text    [data-testid="audit-filter-event-key"]    ${pattern}

Click First Event Row
    ${count}=    Get Element Count    css=tr[data-testid^="audit-row-"]
    Should Be True    ${count} > 0    Expected at least one audit row
    Click    css=tbody > tr:first-child

Assert Detail Drawer Open
    Wait For Elements State    [data-testid="audit-detail-drawer"]    visible    timeout=5s
    Wait For Elements State    [data-testid="detail-metadata"]        visible    timeout=5s

Close Detail Drawer
    Click    [data-testid="audit-detail-close"]
    Wait For Elements State    [data-testid="audit-detail-drawer"]    hidden    timeout=5s

API Create Audit User
    [Arguments]    ${email}    ${password}    ${display_name}
    ${body}=    Create Dictionary    email=${email}    password=${password}    display_name=${display_name}
    ${session}=    RequestsLibrary.Create Session    backend    ${BACKEND_URL}
    ${resp}=    POST On Session    backend    /v1/auth/signup    json=${body}    expected_status=201
    RETURN    ${resp.json()['data']}

API Fetch Me
    [Arguments]    ${token}
    ${headers}=    Create Dictionary    Cookie=tennetctl_session=${token}
    ${session}=    RequestsLibrary.Create Session    backend    ${BACKEND_URL}
    ${resp}=    GET On Session    backend    /v1/auth/me    headers=${headers}    expected_status=200
    RETURN    ${resp.json()['data']}

Seed Audit Events Into Org
    [Documentation]    Insert 12 demo audit events for the given user/org via raw SQL.
    ...                Uses category='setup' to bypass scope CHECK when workspace_id missing.
    ...                Generates 36-char UUID v7 ids via gen_random_uuid().
    [Arguments]    ${user_id}    ${session_id}    ${org_id}    ${workspace_id}    ${prefix}
    Connect To Database    psycopg2    ${DB_NAME}    ${DB_USER}    ${DB_PASS}    ${DB_HOST}    ${DB_PORT}
    ${sql}=    Catenate    SEPARATOR=\n
    ...    INSERT INTO "04_audit"."60_evt_audit"
    ...      (id, event_key, actor_user_id, actor_session_id, org_id, workspace_id, trace_id, span_id, audit_category, outcome, metadata)
    ...    SELECT
    ...      gen_random_uuid()::text,
    ...      CASE i % 3 WHEN 0 THEN '${prefix}.evt.alpha' WHEN 1 THEN '${prefix}.evt.beta' ELSE '${prefix}.evt.gamma' END,
    ...      '${user_id}', '${session_id}', '${org_id}',
    ...      COALESCE('${workspace_id}'::text, '${org_id}'),
    ...      gen_random_uuid()::text,
    ...      gen_random_uuid()::text,
    ...      'setup', CASE i % 4 WHEN 3 THEN 'failure' ELSE 'success' END,
    ...      jsonb_build_object('i', i, 'tag', '${prefix}')
    ...    FROM generate_series(0, 11) i;
    Execute Sql String    ${sql}
    Disconnect From Database

Cleanup Seeded Audit
    [Arguments]    ${prefix}
    Connect To Database    psycopg2    ${DB_NAME}    ${DB_USER}    ${DB_PASS}    ${DB_HOST}    ${DB_PORT}
    Execute Sql String    DELETE FROM "04_audit"."60_evt_audit" WHERE event_key LIKE '${prefix}.%' OR metadata->>'tag' = '${prefix}';
    Disconnect From Database

Open Analytics Tab
    Go To    ${FRONTEND_URL}/audit
    Wait For Load State    networkidle    timeout=20s
    Click    [data-testid="audit-tab-analytics"]
    Wait For Elements State    [data-testid="audit-funnel-builder"]    visible    timeout=10s

Run Funnel
    [Arguments]    ${step1}    ${step2}
    Fill Text    [data-testid="audit-funnel-step-0"]    ${step1}
    Fill Text    [data-testid="audit-funnel-step-1"]    ${step2}
    Click    [data-testid="audit-funnel-run"]
    Wait For Elements State    [data-testid="audit-funnel-result"]    visible    timeout=15s

Create Saved View
    [Arguments]    ${name}
    Click    [data-testid="audit-saved-views-new"]
    Wait For Elements State    [data-testid="audit-saved-views-name-input"]    visible    timeout=5s
    Fill Text    [data-testid="audit-saved-views-name-input"]    ${name}
    Click    [data-testid="audit-saved-views-save"]
    Wait For Elements State    [data-testid="audit-saved-views-list"]    visible    timeout=10s
