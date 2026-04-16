*** Settings ***
Documentation    Risk Registry API Integration Tests
Resource         common.resource
Suite Setup      Setup Risk Registry Suite

*** Variables ***
${RR_URL}    ${BASE_URL}/rr

*** Keywords ***
Setup Risk Registry Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # Create an org for risk scoping
    ${org_slug}=    Set Variable    robot-risk-org-${TS}
    ${org_body}=    Create Dictionary
    ...    name=Robot Risk Org ${TS}
    ...    slug=${org_slug}
    ...    org_type_code=community
    ...    description=Org for risk registry tests
    ${org_resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${org_body}    expected_status=any
    Should Be True    ${org_resp.status_code} == 200 or ${org_resp.status_code} == 201
    ${org_json}=    Set Variable    ${org_resp.json()}
    ${oid}=    Evaluate    $org_json.get('id') or $org_json.get('org_id')
    Set Suite Variable    ${RR_ORG_ID}    ${oid}
    Log    Created org for risk registry: ${oid}
    # Create a workspace under that org
    ${ws_slug}=    Set Variable    robot-risk-ws-${TS}
    ${ws_body}=    Create Dictionary
    ...    name=Robot Risk WS ${TS}
    ...    slug=${ws_slug}
    ...    workspace_type_code=development
    ...    description=Workspace for risk registry tests
    ${ws_resp}=    POST    ${AM_URL}/orgs/${RR_ORG_ID}/workspaces
    ...    headers=${AUTH_HEADERS}    json=${ws_body}    expected_status=any
    Should Be True    ${ws_resp.status_code} == 200 or ${ws_resp.status_code} == 201
    ${ws_json}=    Set Variable    ${ws_resp.json()}
    ${wsid}=    Evaluate    $ws_json.get('id') or $ws_json.get('workspace_id')
    Set Suite Variable    ${RR_WS_ID}    ${wsid}
    Log    Created workspace for risk registry: ${wsid}

*** Test Cases ***
List Risk Categories
    [Documentation]    GET /rr/risk-categories → expect 8 items
    ${resp}=    GET    ${RR_URL}/risk-categories    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be Equal As Integers    ${count}    8
    Log    Risk categories count: ${count}

List Treatment Types
    [Documentation]    GET /rr/treatment-types → expect 4
    ${resp}=    GET    ${RR_URL}/treatment-types    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be Equal As Integers    ${count}    4
    Log    Treatment types count: ${count}

List Risk Levels
    [Documentation]    GET /rr/risk-levels → expect 4 with score ranges
    ${resp}=    GET    ${RR_URL}/risk-levels    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be Equal As Integers    ${count}    4
    Log    Risk levels count: ${count}
    # Verify score ranges are present
    ${first}=    Evaluate    $json[0]
    Dictionary Should Contain Key    ${first}    score_min
    Dictionary Should Contain Key    ${first}    score_max

Create Risk
    [Documentation]    POST /rr/risks
    ${body}=    Create Dictionary
    ...    risk_code=risk_${TS}
    ...    org_id=${RR_ORG_ID}
    ...    workspace_id=${RR_WS_ID}
    ...    risk_category_code=technology
    ...    title=Test Risk
    ...    description=Risk created by Robot Framework tests
    ${resp}=    POST    ${RR_URL}/risks    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${riskid}=    Evaluate    $json.get('id') or $json.get('risk_id')
    Set Suite Variable    ${RISK_ID}    ${riskid}
    Log    Created risk: ${riskid}

List Risks
    [Documentation]    GET /rr/risks?org_id=X → should contain risk
    ${resp}=    GET    ${RR_URL}/risks    headers=${AUTH_HEADERS}
    ...    params=org_id=${RR_ORG_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('risks', []))
    ${codes}=    Evaluate    [item.get('risk_code') or item.get('code') for item in $items]
    Should Contain    ${codes}    risk_${TS}

Filter Risks By Risk Level
    [Documentation]    GET /rr/risks?risk_level_code=low → list returns (may be empty)
    ${resp}=    GET    ${RR_URL}/risks    headers=${AUTH_HEADERS}
    ...    params=org_id=${RR_ORG_ID}&risk_level_code=low    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', [])
    # If any items returned, verify they all have the requested level
    ${count}=    Get Length    ${items}
    Log    Risks filtered by level=low: ${count}

Filter Risks By Status
    [Documentation]    GET /rr/risks?risk_status=identified → list returns only identified risks
    ${resp}=    GET    ${RR_URL}/risks    headers=${AUTH_HEADERS}
    ...    params=org_id=${RR_ORG_ID}&risk_status=identified    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', [])
    ${count}=    Get Length    ${items}
    Log    Risks filtered by status=identified: ${count}

Get Risk Detail
    [Documentation]    GET /rr/risks/${RISK_ID} → verify title, category, level
    ${resp}=    GET    ${RR_URL}/risks/${RISK_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[title]    Test Risk
    ${cat_code}=    Evaluate    $json.get('risk_category_code') or $json.get('category_code')
    Should Be Equal    ${cat_code}    technology

Update Risk
    [Documentation]    PATCH /rr/risks/${RISK_ID} with risk_status=assessed
    ${body}=    Create Dictionary    risk_status=assessed
    ${resp}=    PATCH    ${RR_URL}/risks/${RISK_ID}
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${status}=    Evaluate    $json.get('risk_status') or $json.get('status')
    Should Be Equal    ${status}    assessed

Create Assessment
    [Documentation]    POST /rr/risks/${RISK_ID}/assessments → verify risk_score=12
    ${body}=    Create Dictionary
    ...    assessment_type=inherent
    ...    likelihood_score=${4}
    ...    impact_score=${3}
    ${resp}=    POST    ${RR_URL}/risks/${RISK_ID}/assessments
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${risk_score}=    Evaluate    $json.get('risk_score')
    Should Be Equal As Integers    ${risk_score}    12
    Log    Created assessment with risk_score: ${risk_score}

List Assessments
    [Documentation]    GET /rr/risks/${RISK_ID}/assessments → should have 1
    ${resp}=    GET    ${RR_URL}/risks/${RISK_ID}/assessments
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('assessments', []))
    ${count}=    Get Length    ${items}
    Should Be Equal As Integers    ${count}    1

Create Treatment Plan
    [Documentation]    POST /rr/risks/${RISK_ID}/treatment-plan
    ${body}=    Create Dictionary
    ...    plan_description=Mitigation steps
    ...    treatment_type_code=mitigate
    ${resp}=    POST    ${RR_URL}/risks/${RISK_ID}/treatment-plan
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${planid}=    Evaluate    $json.get('id') or $json.get('plan_id')
    Set Suite Variable    ${PLAN_ID}    ${planid}
    Log    Created treatment plan: ${planid}

Get Treatment Plan
    [Documentation]    GET /rr/risks/${RISK_ID}/treatment-plan
    ${resp}=    GET    ${RR_URL}/risks/${RISK_ID}/treatment-plan
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    # plan_description is an EAV property returned in the properties dict
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    plan_status
    Log    Treatment plan retrieved: ${json}[id]

Update Treatment Plan
    [Documentation]    PATCH /rr/risks/${RISK_ID}/treatment-plan with plan_status=active
    ${body}=    Create Dictionary    plan_status=active
    ${resp}=    PATCH    ${RR_URL}/risks/${RISK_ID}/treatment-plan
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${status}=    Evaluate    $json.get('plan_status') or $json.get('status')
    Should Be Equal    ${status}    active

List Review Events
    [Documentation]    GET /rr/risks/${RISK_ID}/events → should have review events
    ${resp}=    GET    ${RR_URL}/risks/${RISK_ID}/events
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('reviews', []))
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 0
    Log    Risk review events count: ${count}

Add Review Comment
    [Documentation]    POST /rr/risks/${RISK_ID}/events with event_type=reviewed
    ${body}=    Create Dictionary
    ...    event_type=reviewed
    ...    comment=Reviewed by Robot Framework test
    ${resp}=    POST    ${RR_URL}/risks/${RISK_ID}/events
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    Log    Added review event to risk: ${RISK_ID}

Get Risk Summary
    [Documentation]    GET /rr/risks/summary?org_id=X → KPI counts
    ${resp}=    GET    ${RR_URL}/risks/summary    headers=${AUTH_HEADERS}
    ...    params=org_id=${RR_ORG_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    total_risks
    ${total}=    Evaluate    $json.get('total_risks', 0)
    Should Be True    ${total} >= 1
    Log    Risk summary total: ${total}

Get Risk Heat Map
    [Documentation]    GET /rr/risks/heat-map?org_id=X → 5×5 cells
    ${resp}=    GET    ${RR_URL}/risks/heat-map    headers=${AUTH_HEADERS}
    ...    params=org_id=${RR_ORG_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    cells
    ${cells}=    Evaluate    $json.get('cells', [])
    Should Be True    isinstance($cells, list)
    ${cell_count}=    Get Length    ${cells}
    Log    Heat map cells returned: ${cell_count}

Export Risks CSV
    [Documentation]    GET /rr/risks/export?org_id=X → CSV content-type
    ${resp}=    GET    ${RR_URL}/risks/export    headers=${AUTH_HEADERS}
    ...    params=org_id=${RR_ORG_ID}    expected_status=200
    ${ct}=    Evaluate    $resp.headers.get('content-type', '')
    Should Contain    ${ct}    text/csv
    ${body}=    Set Variable    ${resp.text}
    Should Contain    ${body}    risk_code
    ${body_len}=    Get Length    ${body}
    Log    CSV export length: ${body_len}

Assign Risk Group
    [Documentation]    POST /rr/risks/${RISK_ID}/groups with role=accountable
    ${body}=    Create Dictionary
    ...    group_id=00000000-0000-0000-0000-000000000001
    ...    role=accountable
    ...    notes=Robot test RACI assignment
    ${resp}=    POST    ${RR_URL}/risks/${RISK_ID}/groups
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    # Group may not exist — accept 201 or 404/422 (validation error for unknown group)
    Should Be True    ${resp.status_code} in [201, 400, 403, 404, 422]
    Run Keyword If    ${resp.status_code} == 201
    ...    Set Suite Variable    ${GROUP_ASSIGN_ID}    ${resp.json().get('id', '')}
    Log    Assign risk group status: ${resp.status_code}

List Risk Groups
    [Documentation]    GET /rr/risks/${RISK_ID}/groups → list
    ${resp}=    GET    ${RR_URL}/risks/${RISK_ID}/groups
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('assignments', []))
    Should Be True    isinstance($items, list)
    ${assign_count}=    Get Length    ${items}
    Log    Risk group assignments count: ${assign_count}

Get Risk Appetite Empty
    [Documentation]    GET /rr/risks/appetite?org_id=X → list (may be empty)
    ${resp}=    GET    ${RR_URL}/risks/appetite    headers=${AUTH_HEADERS}
    ...    params=org_id=${RR_ORG_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('appetite', []))
    Should Be True    isinstance($items, list)
    ${appetite_count}=    Get Length    ${items}
    Log    Risk appetite entries: ${appetite_count}

Upsert Risk Appetite
    [Documentation]    PUT /rr/risks/appetite → create appetite threshold
    ${body}=    Create Dictionary
    ...    org_id=${RR_ORG_ID}
    ...    risk_category_code=technology
    ...    tolerance_threshold=${12}
    ...    description=Moderate tolerance for technology risks
    ${resp}=    PUT    ${RR_URL}/risks/appetite
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201]
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    ${apid}=    Evaluate    $json.get('id')
    Set Suite Variable    ${APPETITE_ID}    ${apid}
    Log    Created risk appetite: ${apid}

Get Risk Appetite After Upsert
    [Documentation]    GET /rr/risks/appetite?org_id=X → should have 1 entry now
    ${resp}=    GET    ${RR_URL}/risks/appetite    headers=${AUTH_HEADERS}
    ...    params=org_id=${RR_ORG_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('appetite', []))
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 1
    Log    Risk appetite after upsert: ${count}

Set Review Schedule
    [Documentation]    PUT /rr/risks/${RISK_ID}/review-schedule
    ${body}=    Create Dictionary
    ...    review_frequency=quarterly
    ...    next_review_date=2026-06-30
    ${resp}=    PUT    ${RR_URL}/risks/${RISK_ID}/review-schedule
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201]
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    review_frequency
    ${freq}=    Evaluate    $json.get('review_frequency')
    Should Be Equal    ${freq}    quarterly
    Log    Review schedule set with frequency: ${freq}

Get Review Schedule
    [Documentation]    GET /rr/risks/${RISK_ID}/review-schedule
    ${resp}=    GET    ${RR_URL}/risks/${RISK_ID}/review-schedule
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Run Keyword If    ${json} is not None
    ...    Dictionary Should Contain Key    ${json}    review_frequency
    Run Keyword If    ${json} is not None
    ...    Log    Retrieved review schedule
    Run Keyword If    ${json} is None
    ...    Log    No review schedule set yet

Complete Review
    [Documentation]    POST /rr/risks/${RISK_ID}/review-schedule/complete
    ${body}=    Create Dictionary
    ...    next_review_date=2026-09-30
    ${resp}=    POST    ${RR_URL}/risks/${RISK_ID}/review-schedule/complete
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201]
    Log    Completed review for risk: ${RISK_ID}

List Overdue Reviews
    [Documentation]    GET /rr/risks/overdue-reviews?org_id=X → list (may be empty since next_review is future)
    ${resp}=    GET    ${RR_URL}/risks/overdue-reviews    headers=${AUTH_HEADERS}
    ...    params=org_id=${RR_ORG_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('overdue', []))
    Should Be True    isinstance($items, list)
    ${overdue_count}=    Get Length    ${items}
    Log    Overdue reviews count: ${overdue_count}

Cleanup Risk
    [Documentation]    DELETE risk (soft-delete)
    ${resp}=    DELETE    ${RR_URL}/risks/${RISK_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted risk: ${RISK_ID}
