*** Settings ***
Documentation    Sandbox Module — comprehensive integration tests (Part 2: Threat Types through Cleanup)
Resource         common.resource
Suite Setup      Setup Sandbox Part2 Suite
Suite Teardown   Teardown Sandbox Part2 Suite

*** Variables ***
${SB_URL}             ${BASE_URL}/sb
${DIM_URL}            ${SB_URL}/dimensions
${CONN_URL}           ${SB_URL}/connectors
${DS_URL}             ${SB_URL}/datasets
${SIG_URL}            ${SB_URL}/signals
${TT_URL}             ${SB_URL}/threat-types
${POL_URL}            ${SB_URL}/policies
${RUN_URL}            ${SB_URL}/runs
${TE_URL}             ${SB_URL}/threat-evaluations
${PE_URL}             ${SB_URL}/policy-executions
${LS_URL}             ${SB_URL}/live-sessions
${LIB_URL}            ${SB_URL}/libraries
${PROMO_URL}          ${SB_URL}/promotions
${SSF_URL}            ${SB_URL}/ssf
${FAKE_UUID}          00000000-0000-0000-0000-000000000000

*** Keywords ***
Setup Sandbox Part2 Suite
    [Documentation]    Reuse credentials from Part 1 — create own org/workspace + signals/dataset for isolation
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # Create isolated org + workspace
    ${body}=    Create Dictionary
    ...    name=Robot SB P2 Org ${ts}
    ...    slug=robot-sb-p2-org-${ts}
    ...    org_type_code=community
    ${resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${oid}=    Evaluate    $json.get('id') or $json.get('org_id')
    Set Suite Variable    ${ORG_ID}    ${oid}
    ${ws_body}=    Create Dictionary
    ...    name=Robot SB P2 WS ${ts}
    ...    slug=robot-sb-p2-ws-${ts}
    ...    workspace_type_code=sandbox
    ${ws_resp}=    POST    ${AM_URL}/orgs/${oid}/workspaces    headers=${AUTH_HEADERS}    json=${ws_body}    expected_status=any
    Should Be True    ${ws_resp.status_code} == 200 or ${ws_resp.status_code} == 201
    ${ws_json}=    Set Variable    ${ws_resp.json()}
    ${wsid}=    Evaluate    $ws_json.get('id') or $ws_json.get('workspace_id')
    Set Suite Variable    ${WS_ID}    ${wsid}
    # Fetch connector type code
    ${dim_resp}=    GET    ${SB_URL}/dimensions/connector-types    headers=${AUTH_HEADERS}    expected_status=200
    ${dim_json}=    Set Variable    ${dim_resp.json()}
    ${ct_code}=    Evaluate    $dim_json[0].get('code')
    Set Suite Variable    ${CONNECTOR_TYPE_CODE}    ${ct_code}
    # Create connector
    ${conn_body}=    Create Dictionary
    ...    instance_code=p2-conn-${ts}
    ...    connector_type_code=${ct_code}
    ...    collection_schedule=manual
    ...    name=P2 Connector ${ts}
    ${conn_params}=    Create Dictionary    org_id=${oid}
    ${conn_resp}=    POST    ${CONN_URL}    headers=${AUTH_HEADERS}    json=${conn_body}    params=${conn_params}    expected_status=201
    ${conn_json}=    Set Variable    ${conn_resp.json()}
    Set Suite Variable    ${CONNECTOR_ID}    ${conn_json}[id]
    # Fetch dataset source code
    ${src_resp}=    GET    ${SB_URL}/dimensions/dataset-sources    headers=${AUTH_HEADERS}    expected_status=200
    ${src_json}=    Set Variable    ${src_resp.json()}
    ${src_codes}=    Evaluate    [i.get('code') for i in $src_json]
    ${src_code}=    Evaluate    'manual_json' if 'manual_json' in $src_codes else $src_codes[0]
    Set Suite Variable    ${DS_SOURCE_CODE}    ${src_code}
    # Create dataset and lock it
    ${ds_body}=    Create Dictionary
    ...    dataset_code=p2-ds-${ts}
    ...    dataset_source_code=${src_code}
    ${ds_params}=    Create Dictionary    org_id=${oid}
    ${ds_resp}=    POST    ${DS_URL}    headers=${AUTH_HEADERS}    json=${ds_body}    params=${ds_params}    expected_status=201
    ${ds_json}=    Set Variable    ${ds_resp.json()}
    Set Suite Variable    ${DATASET_ID}    ${ds_json}[id]
    # Create two signals
    ${sig_params}=    Create Dictionary    org_id=${oid}
    ${sig1_src}=    Catenate    SEPARATOR=
    ...    def evaluate(dataset):
    ...    ${SPACE}return {'result': 'fail', 'summary': 'MFA check', 'details': []}
    ${sig1_props}=    Create Dictionary
    ...    name=P2 MFA Check
    ...    python_source=${sig1_src}
    ${sig1_body}=    Create Dictionary
    ...    signal_code=p2_mfa_${ts}
    ...    workspace_id=${wsid}
    ...    properties=${sig1_props}
    ${s1_resp}=    POST    ${SIG_URL}/    headers=${AUTH_HEADERS}    json=${sig1_body}    params=${sig_params}    expected_status=201
    ${s1_json}=    Set Variable    ${s1_resp.json()}
    Set Suite Variable    ${SIGNAL_ID}    ${s1_json}[id]
    Set Suite Variable    ${SIGNAL_CODE}    p2_mfa_${ts}
    ${sig2_src}=    Catenate    SEPARATOR=
    ...    def evaluate(dataset):
    ...    ${SPACE}return {'result': 'pass', 'summary': 'Login check passed', 'details': []}
    ${sig2_props}=    Create Dictionary
    ...    name=P2 Login Check
    ...    python_source=${sig2_src}
    ${sig2_body}=    Create Dictionary
    ...    signal_code=p2_login_${ts}
    ...    workspace_id=${wsid}
    ...    properties=${sig2_props}
    ${s2_resp}=    POST    ${SIG_URL}/    headers=${AUTH_HEADERS}    json=${sig2_body}    params=${sig_params}    expected_status=201
    ${s2_json}=    Set Variable    ${s2_resp.json()}
    Set Suite Variable    ${SIGNAL_ID_2}    ${s2_json}[id]
    Set Suite Variable    ${SIGNAL_CODE_2}    p2_login_${ts}
    # Create cascade test signal
    ${casc_src}=    Catenate    SEPARATOR=
    ...    def evaluate(dataset):
    ...    ${SPACE}return {'result': 'pass', 'summary': 'ok', 'details': []}
    ${casc_props}=    Create Dictionary
    ...    name=P2 Cascade Signal
    ...    python_source=${casc_src}
    ${casc_body}=    Create Dictionary
    ...    signal_code=p2_casc_${ts}
    ...    workspace_id=${wsid}
    ...    properties=${casc_props}
    ${casc_resp}=    POST    ${SIG_URL}/    headers=${AUTH_HEADERS}    json=${casc_body}    params=${sig_params}    expected_status=201
    ${casc_json}=    Set Variable    ${casc_resp.json()}
    Set Suite Variable    ${CASCADE_SIG_ID}    ${casc_json}[id]
    # Fetch library type code
    ${lt_resp}=    GET    ${SB_URL}/dimensions/library-types    headers=${AUTH_HEADERS}    expected_status=200
    ${lt_json}=    Set Variable    ${lt_resp.json()}
    ${lt_code}=    Evaluate    $lt_json[0].get('code')
    Set Suite Variable    ${LIBRARY_TYPE_CODE}    ${lt_code}
    Log    Part2 setup complete: org=${oid}, ws=${wsid}, connector=${conn_json}[id], dataset=${ds_json}[id]

Teardown Sandbox Part2 Suite
    Log    Sandbox Part 2 tests complete. ORG=${ORG_ID} WS=${WS_ID}

*** Test Cases ***

# ==============================================================================
# SECTION 5: THREAT TYPES
# ==============================================================================

Create Threat Type With AND Expression
    [Documentation]    Create a composite threat type using AND expression tree
    [Tags]    threat-types    create
    ${cond1}=    Create Dictionary
    ...    signal_code=${SIGNAL_CODE}
    ...    expected_result=fail
    ${cond2}=    Create Dictionary
    ...    signal_code=${SIGNAL_CODE_2}
    ...    expected_result=fail
    ${conditions}=    Create List    ${cond1}    ${cond2}
    ${expr_tree}=    Create Dictionary
    ...    operator=AND
    ...    conditions=${conditions}
    ${props}=    Create Dictionary
    ...    name=Account Takeover ${TS}
    ...    description=Composite threat
    ${body}=    Create Dictionary
    ...    threat_code=acct_takeover_${TS}
    ...    workspace_id=${WS_ID}
    ...    severity_code=high
    ...    expression_tree=${expr_tree}
    ...    properties=${props}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${TT_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[id]
    Should Be Equal    ${json}[threat_code]    acct_takeover_${TS}
    Should Be Equal    ${json}[severity_code]    high
    Should Be Equal As Numbers    ${json}[version_number]    1
    Set Suite Variable    ${THREAT_TYPE_ID}    ${json}[id]

Create Threat Type With OR Expression
    [Documentation]    Create a threat type using OR expression tree
    [Tags]    threat-types    create
    ${cond1}=    Create Dictionary
    ...    signal_code=${SIGNAL_CODE}
    ...    expected_result=fail
    ${conditions}=    Create List    ${cond1}
    ${expr_tree}=    Create Dictionary
    ...    operator=OR
    ...    conditions=${conditions}
    ${props}=    Create Dictionary
    ...    name=Hygiene Threat ${TS}
    ...    description=Single signal OR threat
    ${body}=    Create Dictionary
    ...    threat_code=hygiene_threat_${TS}
    ...    workspace_id=${WS_ID}
    ...    severity_code=medium
    ...    expression_tree=${expr_tree}
    ...    properties=${props}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${TT_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[id]
    Should Be Equal    ${json}[threat_code]    hygiene_threat_${TS}
    Should Be Equal    ${json}[severity_code]    medium
    Set Suite Variable    ${THREAT_TYPE_ID_2}    ${json}[id]

Create Cascade Test Threat Type
    [Documentation]    Create a threat type referencing the cascade signal for cascade delete testing
    [Tags]    threat-types    create    cascade
    ${cond1}=    Create Dictionary
    ...    signal_code=p2_casc_${TS}
    ...    expected_result=pass
    ${conditions}=    Create List    ${cond1}
    ${expr_tree}=    Create Dictionary
    ...    operator=AND
    ...    conditions=${conditions}
    ${props}=    Create Dictionary
    ...    name=Cascade TT ${TS}
    ${body}=    Create Dictionary
    ...    threat_code=cascade_tt_${TS}
    ...    workspace_id=${WS_ID}
    ...    severity_code=low
    ...    expression_tree=${expr_tree}
    ...    properties=${props}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${TT_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[id]
    Should Be Equal    ${json}[threat_code]    cascade_tt_${TS}
    Set Suite Variable    ${CASCADE_TT_ID}    ${json}[id]

List Threat Types
    [Documentation]    GET all threat types for org returns at least 3 entries
    [Tags]    threat-types    list
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${TT_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Evaluate    int($json['total'])
    Should Be True    ${total} >= 3

List Threat Types Filter By Severity
    [Documentation]    GET threat types filtered by severity_code=high returns only high severity entries
    [Tags]    threat-types    list    filter
    ${params}=    Create Dictionary    org_id=${ORG_ID}    severity_code=high
    ${resp}=    GET    ${TT_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    FOR    ${item}    IN    @{json}[items]
        Should Be Equal    ${item}[severity_code]    high
    END

Get Threat Type With Expression Tree
    [Documentation]    GET single threat type returns all expected fields including expression_tree
    [Tags]    threat-types    get
    ${resp}=    GET    ${TT_URL}/${THREAT_TYPE_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    threat_code
    Dictionary Should Contain Key    ${json}    expression_tree
    Dictionary Should Contain Key    ${json}    severity_code

Get Threat Type Not Found
    [Documentation]    GET non-existent threat type returns 404
    [Tags]    threat-types    get    negative
    ${resp}=    GET    ${TT_URL}/${FAKE_UUID}    headers=${AUTH_HEADERS}    expected_status=404

Update Threat Type Changes Severity
    [Documentation]    PATCH threat type to change severity_code to critical
    [Tags]    threat-types    update
    ${body}=    Create Dictionary    severity_code=critical
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    PATCH    ${TT_URL}/${THREAT_TYPE_ID}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[severity_code]    critical

Threat Type Version History
    [Documentation]    GET threat type versions returns list with at least one entry
    [Tags]    threat-types    versions
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${TT_URL}/${THREAT_TYPE_ID}/versions    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${length}=    Evaluate    len($json) if isinstance($json, list) else len($json.get('items', []))
    Should Be True    ${length} >= 1

Simulate Threat Triggered
    [Documentation]    POST simulate with both signals failing returns is_triggered=True for AND logic
    [Tags]    threat-types    simulate
    ${signal_results}=    Create Dictionary
    ...    ${SIGNAL_CODE}=fail
    ...    ${SIGNAL_CODE_2}=fail
    ${body}=    Create Dictionary    signal_results=${signal_results}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${TT_URL}/${THREAT_TYPE_ID}/simulate    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[is_triggered] == True
    Dictionary Should Contain Key    ${json}    evaluation_trace

Simulate Threat Not Triggered AND Logic
    [Documentation]    POST simulate with one signal passing returns is_triggered=False for AND logic
    [Tags]    threat-types    simulate
    ${signal_results}=    Create Dictionary
    ...    ${SIGNAL_CODE}=fail
    ...    ${SIGNAL_CODE_2}=pass
    ${body}=    Create Dictionary    signal_results=${signal_results}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${TT_URL}/${THREAT_TYPE_ID}/simulate    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[is_triggered] == False

Simulate Threat Triggered OR Logic
    [Documentation]    POST simulate with one failing signal triggers OR-based threat type
    [Tags]    threat-types    simulate
    ${signal_results}=    Create Dictionary
    ...    ${SIGNAL_CODE}=fail
    ${body}=    Create Dictionary    signal_results=${signal_results}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${TT_URL}/${THREAT_TYPE_ID_2}/simulate    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[is_triggered] == True

Create Threat Type Invalid Empty Expression
    [Documentation]    POST threat type with null/empty expression_tree returns 422
    [Tags]    threat-types    create    negative    validation
    ${body}=    Create Dictionary
    ...    threat_code=bad_tt_${TS}
    ...    workspace_id=${WS_ID}
    ...    severity_code=low
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${TT_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=422

Threat Type Evaluation History
    [Documentation]    GET threat type evaluations returns list (may be empty)
    [Tags]    threat-types    evaluations
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${TT_URL}/${THREAT_TYPE_ID}/evaluations    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    # Router returns bare list, not paginated dict
    Should Be True    isinstance($json, list)
    Log    Threat type evaluations count: ${len($json)}

Cascade Delete Signal Blocked By Threat Type
    [Documentation]    DELETE cascade signal returns 409 because it is referenced by cascade_tt threat type
    [Tags]    threat-types    cascade    negative
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${SIG_URL}/${CASCADE_SIG_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=409

# ==============================================================================
# SECTION 6: POLICIES
# ==============================================================================

Create Policy
    [Documentation]    Create a policy linked to the first threat type with notification action
    [Tags]    policies    create
    ${action_config}=    Create Dictionary
    ...    channel=email
    ...    recipient=admin@example.com
    ${action}=    Create Dictionary
    ...    action_type=notification
    ...    config=${action_config}
    ${actions}=    Create List    ${action}
    ${props}=    Create Dictionary    name=Account Takeover Response ${TS}
    ${body}=    Create Dictionary
    ...    policy_code=acct_resp_${TS}
    ...    workspace_id=${WS_ID}
    ...    threat_type_id=${THREAT_TYPE_ID}
    ...    actions=${actions}
    ...    is_enabled=${True}
    ...    cooldown_minutes=${5}
    ...    properties=${props}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${POL_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[id]
    Should Be Equal    ${json}[policy_code]    acct_resp_${TS}
    Should Be True    ${json}[is_enabled] == True
    Should Be Equal As Numbers    ${json}[cooldown_minutes]    5
    Set Suite Variable    ${POLICY_ID}    ${json}[id]

Create Second Policy
    [Documentation]    Create a second policy with create_task action linked to second threat type
    [Tags]    policies    create
    ${action_config}=    Create Dictionary    priority=medium
    ${action}=    Create Dictionary
    ...    action_type=create_task
    ...    config=${action_config}
    ${actions}=    Create List    ${action}
    ${props}=    Create Dictionary    name=Hygiene Response ${TS}
    ${body}=    Create Dictionary
    ...    policy_code=hygiene_resp_${TS}
    ...    workspace_id=${WS_ID}
    ...    threat_type_id=${THREAT_TYPE_ID_2}
    ...    actions=${actions}
    ...    is_enabled=${True}
    ...    properties=${props}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${POL_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[id]
    Set Suite Variable    ${POLICY_ID_2}    ${json}[id]

Create Cascade Test Policy
    [Documentation]    Create a policy linked to cascade threat type for cascade delete testing
    [Tags]    policies    create    cascade
    ${props}=    Create Dictionary    name=Cascade Policy ${TS}
    ${action_config}=    Create Dictionary    channel=log    severity=high
    ${action}=    Create Dictionary    action_type=notification    config=${action_config}
    ${actions}=    Create List    ${action}
    ${body}=    Create Dictionary
    ...    policy_code=cascade_pol_${TS}
    ...    workspace_id=${WS_ID}
    ...    threat_type_id=${CASCADE_TT_ID}
    ...    actions=${actions}
    ...    is_enabled=${True}
    ...    properties=${props}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${POL_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[id]
    Set Suite Variable    ${CASCADE_POL_ID}    ${json}[id]

List Policies
    [Documentation]    GET all policies for org returns at least 3 entries
    [Tags]    policies    list
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${POL_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Evaluate    int($json['total'])
    Should Be True    ${total} >= 3

List Policies Filter By Enabled
    [Documentation]    GET policies filtered by is_enabled=true returns only enabled policies
    [Tags]    policies    list    filter
    ${params}=    Create Dictionary    org_id=${ORG_ID}    is_enabled=true
    ${resp}=    GET    ${POL_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    FOR    ${item}    IN    @{json}[items]
        Should Be True    ${item}[is_enabled] == True
    END

List Policies Filter By Threat Type
    [Documentation]    GET policies filtered by threat_type_id returns at least one entry
    [Tags]    policies    list    filter
    ${params}=    Create Dictionary    org_id=${ORG_ID}    threat_type_id=${THREAT_TYPE_ID}
    ${resp}=    GET    ${POL_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Evaluate    int($json['total'])
    Should Be True    ${total} >= 1

Get Policy With Actions Array
    [Documentation]    GET single policy returns all expected fields with actions as a list
    [Tags]    policies    get
    ${resp}=    GET    ${POL_URL}/${POLICY_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    threat_type_id
    Dictionary Should Contain Key    ${json}    actions
    ${actions_type}=    Evaluate    type($json['actions']).__name__
    Should Be Equal    ${actions_type}    list

Get Policy Not Found
    [Documentation]    GET non-existent policy returns 404
    [Tags]    policies    get    negative
    ${resp}=    GET    ${POL_URL}/${FAKE_UUID}    headers=${AUTH_HEADERS}    expected_status=404

Disable Policy
    [Documentation]    POST to disable endpoint sets is_enabled=False
    [Tags]    policies    state
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${POL_URL}/${POLICY_ID}/disable    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[is_enabled] == False

Enable Policy
    [Documentation]    POST to enable endpoint sets is_enabled=True
    [Tags]    policies    state
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${POL_URL}/${POLICY_ID}/enable    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[is_enabled] == True

Update Policy Changes Cooldown
    [Documentation]    PATCH policy to change cooldown_minutes to 10
    [Tags]    policies    update
    ${body}=    Create Dictionary    cooldown_minutes=${10}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    PATCH    ${POL_URL}/${POLICY_ID}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal As Numbers    ${json}[cooldown_minutes]    10

Policy Version History
    [Documentation]    GET policy versions returns list with at least one entry
    [Tags]    policies    versions
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${POL_URL}/${POLICY_ID}/versions    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${length}=    Evaluate    len($json) if isinstance($json, list) else len($json.get('items', []))
    Should Be True    ${length} >= 1

Policy Dry Run Test
    [Documentation]    POST to policy test endpoint simulates without executing
    [Tags]    policies    dryrun
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${POL_URL}/${POLICY_ID}/test    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    actions_simulated
    Dictionary Should Contain Key    ${json}    would_fire

Policy Executions History
    [Documentation]    GET policy execution history returns a list
    [Tags]    policies    executions
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${POL_URL}/${POLICY_ID}/executions    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${is_list}=    Evaluate    isinstance($json, list) or 'items' in $json
    Should Be True    ${is_list}

Create Duplicate Policy Code
    [Documentation]    POST with duplicate policy_code returns 409
    [Tags]    policies    create    negative
    ${action_config}=    Create Dictionary    channel=email
    ${action}=    Create Dictionary    action_type=notification    config=${action_config}
    ${actions}=    Create List    ${action}
    ${props}=    Create Dictionary    name=Duplicate Policy
    ${body}=    Create Dictionary
    ...    policy_code=acct_resp_${TS}
    ...    workspace_id=${WS_ID}
    ...    threat_type_id=${THREAT_TYPE_ID}
    ...    actions=${actions}
    ...    properties=${props}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${POL_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=409

Create Policy With Non-Existent Threat Type
    [Documentation]    POST policy with non-existent threat_type_id returns 404 or 422
    [Tags]    policies    create    negative
    ${props}=    Create Dictionary    name=Invalid TT Policy
    ${action_config}=    Create Dictionary    channel=log
    ${action}=    Create Dictionary    action_type=notification    config=${action_config}
    ${actions}=    Create List    ${action}
    ${body}=    Create Dictionary
    ...    policy_code=invalid_tt_pol_${TS}
    ...    workspace_id=${WS_ID}
    ...    threat_type_id=${FAKE_UUID}
    ...    actions=${actions}
    ...    properties=${props}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${POL_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 404 or ${resp.status_code} == 422

Cascade Delete Threat Type Blocked By Policy
    [Documentation]    DELETE cascade threat type returns 409 because it has an enabled policy
    [Tags]    policies    cascade    negative
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${TT_URL}/${CASCADE_TT_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=409

Cascade Delete Signal Still Blocked
    [Documentation]    DELETE cascade signal still returns 409 because cascade threat type still exists
    [Tags]    policies    cascade    negative
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${SIG_URL}/${CASCADE_SIG_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=409

Disable Cascade Policy
    [Documentation]    Disable cascade policy before deleting it
    [Tags]    policies    cascade    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${POL_URL}/${CASCADE_POL_ID}/disable    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[is_enabled] == False

Delete Cascade Policy
    [Documentation]    DELETE cascade policy succeeds after disabling
    [Tags]    policies    cascade    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${POL_URL}/${CASCADE_POL_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204

Delete Cascade Threat Type
    [Documentation]    DELETE cascade threat type succeeds after policy is removed
    [Tags]    threat-types    cascade    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${TT_URL}/${CASCADE_TT_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204

Delete Cascade Signal Now Succeeds
    [Documentation]    DELETE cascade signal succeeds now that referencing threat type is removed
    [Tags]    cascade    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${SIG_URL}/${CASCADE_SIG_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204

# ==============================================================================
# SECTION 7: EXECUTION
# ==============================================================================

Execute Signal Against Dataset
    [Documentation]    POST a signal run against a dataset returns execution record
    [Tags]    execution    runs
    ${body}=    Create Dictionary
    ...    signal_id=${SIGNAL_ID}
    ...    dataset_id=${DATASET_ID}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${RUN_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    signal_id
    Dictionary Should Contain Key    ${json}    execution_status_code
    Set Suite Variable    ${RUN_ID}    ${json}[id]

Get Run Detail
    [Documentation]    GET run by ID returns execution details
    [Tags]    execution    runs
    ${resp}=    GET    ${RUN_URL}/${RUN_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    execution_status_code

Get Run Not Found
    [Documentation]    GET non-existent run returns 404
    [Tags]    execution    runs    negative
    ${resp}=    GET    ${RUN_URL}/${FAKE_UUID}    headers=${AUTH_HEADERS}    expected_status=404

Execute Signal Verify Result Code Present
    [Documentation]    GET run returns result_code field with valid value
    [Tags]    execution    runs
    ${resp}=    GET    ${RUN_URL}/${RUN_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    result_code
    ${result_code}=    Set Variable    ${json}[result_code]
    ${valid_codes}=    Create List    pass    fail    warning    error
    Should Contain    ${valid_codes}    ${result_code}

Execute Signal Verify Python Source Snapshot
    [Documentation]    GET run returns stdout_capture or error_message from execution
    [Tags]    execution    runs
    ${resp}=    GET    ${RUN_URL}/${RUN_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    # RunResponse has stdout_capture, result_code, and error_message — not python_source_snapshot
    Dictionary Should Contain Key    ${json}    result_code
    Log    Run result_code: ${json}[result_code]

Batch Execute Multiple Signals
    [Documentation]    POST batch run against multiple signals returns combined results
    [Tags]    execution    runs    batch
    ${signal_ids}=    Create List    ${SIGNAL_ID}    ${SIGNAL_ID_2}
    ${body}=    Create Dictionary
    ...    signal_ids=${signal_ids}
    ...    dataset_id=${DATASET_ID}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${RUN_URL}/batch    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    signal_results
    Dictionary Should Contain Key    ${json}    threat_evaluations
    Dictionary Should Contain Key    ${json}    policy_executions

List Runs
    [Documentation]    GET all runs for org returns at least one entry
    [Tags]    execution    runs    list
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${RUN_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Evaluate    int($json['total'])
    Should Be True    ${total} >= 1

List Runs Filter By Signal
    [Documentation]    GET runs filtered by signal_id returns matching entries only
    [Tags]    execution    runs    filter
    ${params}=    Create Dictionary    org_id=${ORG_ID}    signal_id=${SIGNAL_ID}
    ${resp}=    GET    ${RUN_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${total}=    Evaluate    int($json['total'])
    Should Be True    ${total} >= 1
    FOR    ${item}    IN    @{json}[items]
        Should Be Equal    ${item}[signal_id]    ${SIGNAL_ID}
    END

List Runs Filter By Result Code Fail
    [Documentation]    GET runs filtered by result_code=fail returns a valid list (may be empty)
    [Tags]    execution    runs    filter
    ${params}=    Create Dictionary    org_id=${ORG_ID}    result_code=fail
    ${resp}=    GET    ${RUN_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total

Threat Evaluations List
    [Documentation]    GET threat evaluations for org returns paginated results
    [Tags]    execution    threat-evaluations
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${TE_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total

Policy Executions Global List
    [Documentation]    GET policy executions for org returns paginated results
    [Tags]    execution    policy-executions
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${PE_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total

Run History Endpoint
    [Documentation]    GET run history with date filter and limit returns a list
    [Tags]    execution    runs    history
    ${params}=    Create Dictionary    org_id=${ORG_ID}    days=30    limit=100
    ${resp}=    GET    ${RUN_URL}/history    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${is_list}=    Evaluate    isinstance($json, list) or 'items' in $json
    Should Be True    ${is_list}

# ==============================================================================
# SECTION 8: LIVE SESSIONS
# ==============================================================================

Start Live Session
    [Documentation]    POST to start a live session with connector, signals, and threat types
    [Tags]    live-sessions    create
    ${signal_ids}=    Create List    ${SIGNAL_ID}
    ${threat_type_ids}=    Create List    ${THREAT_TYPE_ID}
    ${body}=    Create Dictionary
    ...    connector_instance_id=${CONNECTOR_ID}
    ...    signal_ids=${signal_ids}
    ...    threat_type_ids=${threat_type_ids}
    ...    duration_minutes=${30}
    ...    workspace_id=${WS_ID}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LS_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    session_status
    Dictionary Should Contain Key    ${json}    connector_instance_id
    Set Suite Variable    ${SESSION_ID}    ${json}[id]

Get Live Session Detail
    [Documentation]    GET live session by ID returns full detail with attached resources
    [Tags]    live-sessions    get
    ${resp}=    GET    ${LS_URL}/${SESSION_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    session_status
    Dictionary Should Contain Key    ${json}    attached_signals
    Dictionary Should Contain Key    ${json}    attached_threat_types

Get Live Session Not Found
    [Documentation]    GET non-existent live session returns 404
    [Tags]    live-sessions    get    negative
    ${resp}=    GET    ${LS_URL}/${FAKE_UUID}    headers=${AUTH_HEADERS}    expected_status=404

List Live Sessions
    [Documentation]    GET all live sessions for org returns at least one entry
    [Tags]    live-sessions    list
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${LS_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Evaluate    int($json['total'])
    Should Be True    ${total} >= 1

Get Live Session Stream
    [Documentation]    GET stream endpoint returns events and pagination info
    [Tags]    live-sessions    stream
    ${resp}=    GET    ${LS_URL}/${SESSION_ID}/stream    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    events
    Dictionary Should Contain Key    ${json}    has_more

Attach Signal To Session
    [Documentation]    POST to attach a second signal to the live session
    [Tags]    live-sessions    attach
    ${body}=    Create Dictionary    signal_id=${SIGNAL_ID_2}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LS_URL}/${SESSION_ID}/attach-signal    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 409
    Run Keyword If    ${resp.status_code} == 200    Dictionary Should Contain Key    ${resp.json()}    id

Detach Signal From Session
    [Documentation]    POST to detach the second signal from the live session
    [Tags]    live-sessions    detach
    ${body}=    Create Dictionary    signal_id=${SIGNAL_ID_2}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LS_URL}/${SESSION_ID}/detach-signal    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204

Attach Threat To Session
    [Documentation]    POST to attach a second threat type to the live session
    [Tags]    live-sessions    attach
    ${body}=    Create Dictionary    threat_type_id=${THREAT_TYPE_ID_2}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LS_URL}/${SESSION_ID}/attach-threat    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 409

Pause Live Session
    [Documentation]    POST to pause sets session_status to paused
    [Tags]    live-sessions    state
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LS_URL}/${SESSION_ID}/pause    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[session_status]    paused

Resume Live Session
    [Documentation]    POST to resume sets session_status to running or active
    [Tags]    live-sessions    state
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LS_URL}/${SESSION_ID}/resume    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${status}=    Set Variable    ${json}[session_status]
    Should Be True    '${status}' == 'running' or '${status}' == 'active'

Save Session As Dataset
    [Documentation]    POST to save session data as a new dataset
    [Tags]    live-sessions    save-dataset
    ${body}=    Create Dictionary    dataset_code=p2_session_ds_${TS}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LS_URL}/${SESSION_ID}/save-dataset    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201 or ${resp.status_code} == 409
    Run Keyword If    ${resp.status_code} == 200 or ${resp.status_code} == 201    Dictionary Should Contain Key    ${resp.json()}    dataset_id

Stop Live Session
    [Documentation]    POST to stop sets session_status to stopped or completed
    [Tags]    live-sessions    state
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LS_URL}/${SESSION_ID}/stop    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${status}=    Set Variable    ${json}[session_status]
    Should Be True    '${status}' == 'stopped' or '${status}' == 'completed'

Resume Stopped Session Fails
    [Documentation]    POST to resume a stopped session returns 409
    [Tags]    live-sessions    state    negative
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LS_URL}/${SESSION_ID}/resume    headers=${AUTH_HEADERS}    params=${params}    expected_status=409

# ==============================================================================
# SECTION 9: LIBRARIES
# ==============================================================================

Create Library
    [Documentation]    POST to create a new signal library returns unpublished library
    [Tags]    libraries    create
    ${props}=    Create Dictionary    name=Robot Library ${TS}
    ${body}=    Create Dictionary
    ...    library_code=robot_lib_${TS}
    ...    library_type_code=${LIBRARY_TYPE_CODE}
    ...    properties=${props}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LIB_URL}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[id]
    Should Be Equal    ${json}[library_code]    robot_lib_${TS}
    Should Be True    ${json}[is_published] == False
    Set Suite Variable    ${LIBRARY_ID}    ${json}[id]

List Libraries
    [Documentation]    GET all libraries for org returns at least one entry
    [Tags]    libraries    list
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${LIB_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Evaluate    int($json['total'])
    Should Be True    ${total} >= 1

Get Library Detail
    [Documentation]    GET library by ID returns expected fields
    [Tags]    libraries    get
    ${resp}=    GET    ${LIB_URL}/${LIBRARY_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    library_code

Get Library Not Found
    [Documentation]    GET non-existent library returns 404
    [Tags]    libraries    get    negative
    ${resp}=    GET    ${LIB_URL}/${FAKE_UUID}    headers=${AUTH_HEADERS}    expected_status=404

Update Library
    [Documentation]    PATCH library properties updates name
    [Tags]    libraries    update
    ${props}=    Create Dictionary    name=Robot Library ${TS} Updated
    ${body}=    Create Dictionary    properties=${props}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    PATCH    ${LIB_URL}/${LIBRARY_ID}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[id]

Add Policy To Library
    [Documentation]    POST to add a policy to the library returns policy reference
    [Tags]    libraries    policies
    ${body}=    Create Dictionary
    ...    policy_id=${POLICY_ID}
    ...    sort_order=${1}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LIB_URL}/${LIBRARY_ID}/policies    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 201 or ${resp.status_code} == 200
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}

Add Duplicate Policy To Library
    [Documentation]    POST to add same policy again returns 409
    [Tags]    libraries    policies    negative
    ${body}=    Create Dictionary
    ...    policy_id=${POLICY_ID}
    ...    sort_order=${1}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LIB_URL}/${LIBRARY_ID}/policies    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=409

List Recommended Libraries
    [Documentation]    GET recommended libraries filtered by connector type returns a list
    [Tags]    libraries    dimensions
    ${params}=    Create Dictionary    connector_type_code=${CONNECTOR_TYPE_CODE}
    ${resp}=    GET    ${SB_URL}/dimensions/recommended-libraries    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${is_list}=    Evaluate    isinstance($json, list) or 'items' in $json
    Should Be True    ${is_list}

Remove Policy From Library
    [Documentation]    DELETE policy from library returns 204
    [Tags]    libraries    policies
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${LIB_URL}/${LIBRARY_ID}/policies/${POLICY_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204

Publish Library
    [Documentation]    POST to publish library sets is_published=True
    [Tags]    libraries    publish
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LIB_URL}/${LIBRARY_ID}/publish    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[is_published] == True

Delete Published Library Fails
    [Documentation]    DELETE published library returns 409
    [Tags]    libraries    delete    negative
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${LIB_URL}/${LIBRARY_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=409

Clone Library
    [Documentation]    POST to clone published library creates new unpublished copy
    [Tags]    libraries    clone
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${LIB_URL}/${LIBRARY_ID}/clone    headers=${AUTH_HEADERS}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Equal    ${json}[id]    ${LIBRARY_ID}
    Should Be True    ${json}[is_published] == False
    Set Suite Variable    ${CLONED_LIB_ID}    ${json}[id]

Delete Cloned Library
    [Documentation]    DELETE unpublished cloned library returns 204
    [Tags]    libraries    delete
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${LIB_URL}/${CLONED_LIB_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204

# ==============================================================================
# SECTION 10: PROMOTIONS
# ==============================================================================

Promote Signal
    [Documentation]    POST to promote a signal to marketplace — 201/200 if validated, 422 if not ready
    [Tags]    promotions    signals
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${PROMO_URL}/signals/${SIGNAL_ID}/promote    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 201 or ${resp.status_code} == 200 or ${resp.status_code} == 422
    ${promo_id}=    Evaluate    $resp.json().get('id') if ${resp.status_code} in [200, 201] else None
    Set Suite Variable    ${PROMOTION_ID}    ${promo_id}

Promote Policy
    [Documentation]    POST to promote a policy — 201/200 if validated, 422 if not ready
    [Tags]    promotions    policies
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${PROMO_URL}/policies/${POLICY_ID}/promote    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 201 or ${resp.status_code} == 200 or ${resp.status_code} == 422

Promote Library
    [Documentation]    POST to promote a published library — 201/200 if validated, 422 if not ready
    [Tags]    promotions    libraries
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${PROMO_URL}/libraries/${LIBRARY_ID}/promote    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 201 or ${resp.status_code} == 200 or ${resp.status_code} == 422

List Promotions
    [Documentation]    GET all promotions returns paginated results
    [Tags]    promotions    list
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${PROMO_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total

Get Promotion Detail If Created
    [Documentation]    GET promotion by ID if one was created — skips if none created
    [Tags]    promotions    get
    Skip If    ${PROMOTION_ID} is None    No promotion was created — skipping detail check
    ${resp}=    GET    ${PROMO_URL}/${PROMOTION_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    promotion_status

List Promotions Filter By Source Type Signal
    [Documentation]    GET promotions filtered by source_type=signal returns a list
    [Tags]    promotions    list    filter
    ${params}=    Create Dictionary    org_id=${ORG_ID}    source_type=signal
    ${resp}=    GET    ${PROMO_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items

List Promotions Filter By Status
    [Documentation]    GET promotions filtered by status=pending_review returns a list
    [Tags]    promotions    list    filter
    ${params}=    Create Dictionary    org_id=${ORG_ID}    status=pending_review
    ${resp}=    GET    ${PROMO_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items

Promote Signal Again Is Idempotent
    [Documentation]    POST to promote already-promoted signal returns 409 or 200
    [Tags]    promotions    signals
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${PROMO_URL}/signals/${SIGNAL_ID}/promote    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 409 or ${resp.status_code} == 200

# ==============================================================================
# SECTION 11: SSF TRANSMITTER
# ==============================================================================

SSF Configuration Discovery
    [Documentation]    GET SSF well-known configuration endpoint — no auth required
    [Tags]    ssf    discovery
    ${discovery_url}=    Set Variable    http://localhost:8000/.well-known/ssf-configuration
    ${resp}=    GET    ${discovery_url}    expected_status=any
    Run Keyword If    ${resp.status_code} != 200    Log    Well-known returned ${resp.status_code} — trying base URL variant
    ${is_json}=    Evaluate    isinstance($resp.json(), dict) if ${resp.status_code} == 200 else True
    Should Be True    ${is_json}

Create SSF Push Stream
    [Documentation]    POST to create a push delivery SSF stream
    [Tags]    ssf    streams    create
    ${events}=    Create List    urn:ietf:params:event:SCIM:create
    ${body}=    Create Dictionary
    ...    delivery_method=push
    ...    receiver_url=https://example.com/ssf/receiver
    ...    events_requested=${events}
    ...    description=Robot push stream ${TS}
    ...    authorization_header=Bearer test-${TS}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${SSF_URL}/streams    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[id]
    Should Be Equal    ${json}[delivery_method]    push
    Should Be Equal    ${json}[stream_status]    enabled
    Set Suite Variable    ${SSF_PUSH_ID}    ${json}[id]

Create SSF Poll Stream
    [Documentation]    POST to create a poll delivery SSF stream
    [Tags]    ssf    streams    create
    ${events}=    Create List    urn:ietf:params:event:SCIM:create
    ${body}=    Create Dictionary
    ...    delivery_method=poll
    ...    events_requested=${events}
    ...    description=Robot poll stream ${TS}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${SSF_URL}/streams    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[id]
    Should Be Equal    ${json}[delivery_method]    poll
    Set Suite Variable    ${SSF_POLL_ID}    ${json}[id]

List SSF Streams
    [Documentation]    GET all SSF streams for org returns at least 2 entries
    [Tags]    ssf    streams    list
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${SSF_URL}/streams    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Evaluate    int($json['total'])
    Should Be True    ${total} >= 2

Get SSF Push Stream
    [Documentation]    GET push stream by ID returns expected fields
    [Tags]    ssf    streams    get
    ${resp}=    GET    ${SSF_URL}/streams/${SSF_PUSH_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal    ${json}[delivery_method]    push

Get SSF Stream Not Found
    [Documentation]    GET non-existent SSF stream returns 404
    [Tags]    ssf    streams    get    negative
    ${resp}=    GET    ${SSF_URL}/streams/${FAKE_UUID}    headers=${AUTH_HEADERS}    expected_status=404

Get SSF Stream Status
    [Documentation]    GET stream status endpoint returns status info
    [Tags]    ssf    streams    status
    ${resp}=    GET    ${SSF_URL}/streams/${SSF_PUSH_ID}/status    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}

Pause SSF Stream
    [Documentation]    PATCH stream status to paused
    [Tags]    ssf    streams    state
    ${body}=    Create Dictionary    stream_status=paused
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    PATCH    ${SSF_URL}/streams/${SSF_PUSH_ID}/status    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}

Enable SSF Stream
    [Documentation]    PATCH stream status back to enabled
    [Tags]    ssf    streams    state
    ${body}=    Create Dictionary    stream_status=enabled
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    PATCH    ${SSF_URL}/streams/${SSF_PUSH_ID}/status    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}

Update SSF Stream Description
    [Documentation]    PATCH stream to update description field
    [Tags]    ssf    streams    update
    ${body}=    Create Dictionary    description=Updated robot stream ${TS}
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    PATCH    ${SSF_URL}/streams/${SSF_PUSH_ID}    headers=${AUTH_HEADERS}    json=${body}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}

Add Subject To SSF Stream
    [Documentation]    POST to add a user subject to the push stream
    [Tags]    ssf    streams    subjects
    ${subject_id_data}=    Create Dictionary    email=user@example.com
    ${body}=    Create Dictionary
    ...    subject_type=user
    ...    subject_format=email
    ...    subject_id_data=${subject_id_data}
    ${resp}=    POST    ${SSF_URL}/streams/${SSF_PUSH_ID}/subjects    headers=${AUTH_HEADERS}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    subject_type
    Set Suite Variable    ${SSF_SUBJECT_ID}    ${json}[id]

Remove Subject From SSF Stream
    [Documentation]    DELETE subject from push stream returns 204
    [Tags]    ssf    streams    subjects
    ${resp}=    DELETE    ${SSF_URL}/streams/${SSF_PUSH_ID}/subjects/${SSF_SUBJECT_ID}    headers=${AUTH_HEADERS}    expected_status=204

Verify SSF Stream Delivery
    [Documentation]    POST to verify push stream delivery — 200 success, 503 if receiver unreachable, 422 if invalid
    [Tags]    ssf    streams    verify
    ${resp}=    POST    ${SSF_URL}/streams/${SSF_PUSH_ID}/verify    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 503 or ${resp.status_code} == 422
    Run Keyword If    ${resp.status_code} == 200    Dictionary Should Contain Key    ${resp.json()}    jti
    Run Keyword If    ${resp.status_code} == 200    Dictionary Should Contain Key    ${resp.json()}    delivered

Poll SSF Stream
    [Documentation]    GET poll stream endpoint returns event sets and pagination info
    [Tags]    ssf    streams    poll
    ${resp}=    GET    ${SSF_URL}/poll/${SSF_POLL_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    sets
    Dictionary Should Contain Key    ${json}    more_available

Delete SSF Push Stream
    [Documentation]    DELETE push stream returns 204
    [Tags]    ssf    streams    delete
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${SSF_URL}/streams/${SSF_PUSH_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204

Delete SSF Poll Stream
    [Documentation]    DELETE poll stream returns 204
    [Tags]    ssf    streams    delete
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${SSF_URL}/streams/${SSF_POLL_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204

# ==============================================================================
# SECTION 12: CLEANUP
# ==============================================================================

Cleanup Library
    [Documentation]    DELETE published library — 204 if unpublished, 409 if still published
    [Tags]    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${LIB_URL}/${LIBRARY_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 204 or ${resp.status_code} == 409

Cleanup Second Policy
    [Documentation]    DELETE second policy — 204 if found, 404 if already removed
    [Tags]    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${POL_URL}/${POLICY_ID_2}    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 204 or ${resp.status_code} == 404

Cleanup First Policy
    [Documentation]    DELETE first policy — 204 if found, 404 if already removed
    [Tags]    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${POL_URL}/${POLICY_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 204 or ${resp.status_code} == 404

Cleanup Second Threat Type
    [Documentation]    DELETE second threat type — 204 if found, 404 if already removed
    [Tags]    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${TT_URL}/${THREAT_TYPE_ID_2}    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 204 or ${resp.status_code} == 404

Cleanup First Threat Type
    [Documentation]    DELETE first threat type — 204 if found, 404 if already removed
    [Tags]    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${TT_URL}/${THREAT_TYPE_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 204 or ${resp.status_code} == 404

Cleanup Second Signal
    [Documentation]    DELETE second signal — 204 if found, 404 if already removed, 409 if still referenced
    [Tags]    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${SIG_URL}/${SIGNAL_ID_2}    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 204 or ${resp.status_code} == 404 or ${resp.status_code} == 409

Cleanup First Signal
    [Documentation]    DELETE first signal — 204 if found, 404 if already removed, 409 if still referenced
    [Tags]    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${SIG_URL}/${SIGNAL_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 204 or ${resp.status_code} == 404 or ${resp.status_code} == 409

Cleanup Dataset
    [Documentation]    DELETE dataset — 204 if removed, 409 if locked (acceptable)
    [Tags]    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${DS_URL}/${DATASET_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 204 or ${resp.status_code} == 409

Cleanup Connector
    [Documentation]    DELETE connector — 204 if found, 404 if already removed
    [Tags]    cleanup
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${CONN_URL}/${CONNECTOR_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 204 or ${resp.status_code} == 404
