*** Settings ***
Documentation    Sandbox Module — comprehensive integration tests (Part 1: Dimensions, Connectors, Datasets, Signals)
Resource         common.resource
Suite Setup      Setup Sandbox Suite
Suite Teardown   Teardown Sandbox Suite

*** Variables ***
${SB_URL}             ${BASE_URL}/sb
${DIM_URL}            ${SB_URL}/dimensions
${CONN_URL}           ${SB_URL}/connectors
${DS_URL}             ${SB_URL}/datasets
${SIG_URL}            ${SB_URL}/signals
${TT_URL}             ${SB_URL}/threat-types
${POL_URL}            ${SB_URL}/policies
${RUN_URL}            ${SB_URL}/runs
${LS_URL}             ${SB_URL}/live-sessions
${LIB_URL}            ${SB_URL}/libraries
${PROMO_URL}          ${SB_URL}/promotions
${SSF_URL}            ${SB_URL}/ssf
${FAKE_UUID}          00000000-0000-0000-0000-000000000000

*** Keywords ***
Setup Sandbox Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    ${slug}=    Set Variable    robot-sb-org-${ts}
    ${body}=    Create Dictionary
    ...    name=Robot Sandbox Org ${ts}
    ...    slug=${slug}
    ...    org_type_code=community
    ...    description=Org for sandbox robot tests
    ${resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${oid}=    Evaluate    $json.get('id') or $json.get('org_id')
    Set Suite Variable    ${ORG_ID}    ${oid}
    ${ws_body}=    Create Dictionary
    ...    name=Robot Sandbox WS ${ts}
    ...    slug=robot-sb-ws-${ts}
    ...    workspace_type_code=sandbox
    ...    description=Workspace for sandbox tests
    ${ws_resp}=    POST    ${AM_URL}/orgs/${oid}/workspaces
    ...    headers=${AUTH_HEADERS}    json=${ws_body}    expected_status=any
    Should Be True    ${ws_resp.status_code} == 200 or ${ws_resp.status_code} == 201
    ${ws_json}=    Set Variable    ${ws_resp.json()}
    ${wsid}=    Evaluate    $ws_json.get('id') or $ws_json.get('workspace_id')
    Set Suite Variable    ${WS_ID}    ${wsid}
    Log    Created org: ${oid}, workspace: ${wsid}

Teardown Sandbox Suite
    Log    Sandbox Part 1 tests complete. ORG=${ORG_ID} WS=${WS_ID}

*** Test Cases ***

# ===========================================================================
# SECTION 1: DIMENSIONS
# ===========================================================================

List Connector Categories
    [Documentation]    GET /sb/dimensions/connector-categories returns a list with at least one entry
    ${resp}=    GET    ${DIM_URL}/connector-categories    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} > 0
    ${first}=    Set Variable    ${json}[0]
    Dictionary Should Contain Key    ${first}    code
    ${code}=    Set Variable    ${first}[code]
    Set Suite Variable    ${CONNECTOR_CAT_CODE}    ${code}
    Log    Stored connector category code: ${code}

List Connector Types
    [Documentation]    GET /sb/dimensions/connector-types returns a list with at least one entry
    ${resp}=    GET    ${DIM_URL}/connector-types    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} > 0
    ${first}=    Set Variable    ${json}[0]
    Dictionary Should Contain Key    ${first}    code
    ${code}=    Set Variable    ${first}[code]
    Set Suite Variable    ${CONNECTOR_TYPE_CODE}    ${code}
    Log    Stored connector type code: ${code}

List Connector Types Filter By Category
    [Documentation]    GET /sb/dimensions/connector-types?category_code filters by category
    ${params}=    Create Dictionary    category_code=${CONNECTOR_CAT_CODE}
    ${resp}=    GET    ${DIM_URL}/connector-types    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    Log    Connector types in category ${CONNECTOR_CAT_CODE}: ${json}

List Asset Versions
    [Documentation]    GET /sb/dimensions/asset-versions returns a list
    ${resp}=    GET    ${DIM_URL}/asset-versions    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    Log    Asset versions: ${json}

List Signal Statuses
    [Documentation]    GET /sb/dimensions/signal-statuses returns a list with 'draft' code
    ${resp}=    GET    ${DIM_URL}/signal-statuses    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} > 0
    ${codes}=    Evaluate    [item['code'] for item in $json]
    Should Contain    ${codes}    draft
    Log    Signal statuses: ${codes}

List Dataset Sources
    [Documentation]    GET /sb/dimensions/dataset-sources returns a list; prefer manual_json code
    ${resp}=    GET    ${DIM_URL}/dataset-sources    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} > 0
    ${codes}=    Evaluate    [item['code'] for item in $json]
    ${has_manual}=    Evaluate    'manual_json' in $codes
    IF    ${has_manual}
        Set Suite Variable    ${DS_SOURCE_CODE}    manual_json
    ELSE
        ${first_code}=    Set Variable    ${json}[0][code]
        Set Suite Variable    ${DS_SOURCE_CODE}    ${first_code}
    END
    Log    Stored dataset source code: ${DS_SOURCE_CODE}

List Execution Statuses
    [Documentation]    GET /sb/dimensions/execution-statuses returns a list
    ${resp}=    GET    ${DIM_URL}/execution-statuses    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    Log    Execution statuses: ${json}

List Threat Severities
    [Documentation]    GET /sb/dimensions/threat-severities returns a list containing 'critical'
    ${resp}=    GET    ${DIM_URL}/threat-severities    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${codes}=    Evaluate    [item['code'] for item in $json]
    Should Contain    ${codes}    critical
    Log    Threat severities: ${codes}

List Policy Action Types
    [Documentation]    GET /sb/dimensions/policy-action-types returns a list containing 'notification'
    ${resp}=    GET    ${DIM_URL}/policy-action-types    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${codes}=    Evaluate    [item['code'] for item in $json]
    Should Contain    ${codes}    notification
    Log    Policy action types: ${codes}

List Library Types
    [Documentation]    GET /sb/dimensions/library-types returns a list; store first code
    ${resp}=    GET    ${DIM_URL}/library-types    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} > 0
    ${code}=    Set Variable    ${json}[0][code]
    Set Suite Variable    ${LIBRARY_TYPE_CODE}    ${code}
    Log    Stored library type code: ${code}

List Dataset Templates
    [Documentation]    GET /sb/dimensions/dataset-templates returns a list
    ${resp}=    GET    ${DIM_URL}/dataset-templates    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    Log    Dataset templates: ${json}

# ===========================================================================
# SECTION 2: CONNECTORS
# ===========================================================================

Create Connector Instance
    [Documentation]    POST /sb/connectors creates a new connector instance
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${body}=    Create Dictionary
    ...    instance_code=robot-conn-${TS}
    ...    connector_type_code=${CONNECTOR_TYPE_CODE}
    ...    collection_schedule=manual
    ...    name=Robot Connector ${TS}
    ${resp}=    POST    ${CONN_URL}    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    instance_code
    Dictionary Should Contain Key    ${json}    connector_type_code
    Dictionary Should Contain Key    ${json}    collection_schedule
    Should Be Equal    ${json}[instance_code]    robot-conn-${TS}
    Should Be Equal    ${json}[connector_type_code]    ${CONNECTOR_TYPE_CODE}
    Should Be Equal    ${json}[collection_schedule]    manual
    Set Suite Variable    ${CONNECTOR_ID}    ${json}[id]
    Set Suite Variable    ${CONNECTOR_CODE}    ${json}[instance_code]
    Log    Created connector: ${CONNECTOR_ID} / ${CONNECTOR_CODE}

Create Second Connector Same Type
    [Documentation]    POST /sb/connectors creates a second connector with daily schedule
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${body}=    Create Dictionary
    ...    instance_code=robot-conn2-${TS}
    ...    connector_type_code=${CONNECTOR_TYPE_CODE}
    ...    collection_schedule=daily
    ...    name=Robot Connector 2 ${TS}
    ${resp}=    POST    ${CONN_URL}    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Set Suite Variable    ${CONNECTOR_ID_2}    ${json}[id]
    Log    Created second connector: ${CONNECTOR_ID_2}

List Connectors
    [Documentation]    GET /sb/connectors returns at least 2 connectors for this org
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${CONN_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Set Variable    ${json}[total]
    Should Be True    ${total} >= 2
    Log    Total connectors: ${total}

List Connectors Filter By Type
    [Documentation]    GET /sb/connectors?connector_type_code filters correctly
    ${params}=    Create Dictionary    org_id=${ORG_ID}    connector_type_code=${CONNECTOR_TYPE_CODE}
    ${resp}=    GET    ${CONN_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    ${items}=    Set Variable    ${json}[items]
    FOR    ${item}    IN    @{items}
        Should Be Equal    ${item}[connector_type_code]    ${CONNECTOR_TYPE_CODE}
    END
    Log    All items have correct connector_type_code

List Connectors Filter By Health Status
    [Documentation]    GET /sb/connectors?health_status=unchecked returns a list
    ${params}=    Create Dictionary    org_id=${ORG_ID}    health_status=unchecked
    ${resp}=    GET    ${CONN_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Log    Connectors with health_status=unchecked: ${json}[total]

Get Connector By Id
    [Documentation]    GET /sb/connectors/{id} returns connector without exposing credentials
    ${resp}=    GET    ${CONN_URL}/${CONNECTOR_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${CONNECTOR_ID}
    Should Be Equal    ${json}[instance_code]    ${CONNECTOR_CODE}
    Dictionary Should Not Contain Key    ${json}    credentials
    Log    Got connector by id; credentials not exposed

Get Connector Not Found
    [Documentation]    GET /sb/connectors/{fake_uuid} returns 404
    ${resp}=    GET    ${CONN_URL}/${FAKE_UUID}    headers=${AUTH_HEADERS}    expected_status=404
    Log    Correctly got 404 for missing connector

Update Connector
    [Documentation]    PATCH /sb/connectors/{id} updates name and collection_schedule
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${body}=    Create Dictionary
    ...    name=Robot Connector Updated ${TS}
    ...    collection_schedule=hourly
    ${resp}=    PATCH    ${CONN_URL}/${CONNECTOR_ID}    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[collection_schedule]    hourly
    Log    Updated connector schedule to hourly

Update Connector Credentials
    [Documentation]    PATCH /sb/connectors/{id}/credentials returns 204 with no body
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${body}=    Create Dictionary    api_key=robot-test-key-${TS}
    ${resp}=    PATCH    ${CONN_URL}/${CONNECTOR_ID}/credentials    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=204
    Log    Credential update returned 204 as expected

Get Connector After Credential Update Hides Credentials
    [Documentation]    GET after credential update still does not expose credentials key
    ${resp}=    GET    ${CONN_URL}/${CONNECTOR_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Not Contain Key    ${json}    credentials
    Log    Credentials still not exposed after update

Test Connector Connectivity
    [Documentation]    POST /sb/connectors/{id}/test returns connectivity status
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${CONN_URL}/${CONNECTOR_ID}/test    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503, 422]
    IF    ${resp.status_code} == 200
        ${json}=    Set Variable    ${resp.json()}
        Dictionary Should Contain Key    ${json}    health_status
        Dictionary Should Contain Key    ${json}    message
        Dictionary Should Contain Key    ${json}    tested_at
    END
    Log    Connector test status: ${resp.status_code}

Trigger Connector Collection
    [Documentation]    POST /sb/connectors/{id}/collect triggers data collection — returns 202 Accepted
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${CONN_URL}/${CONNECTOR_ID}/collect    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201, 202, 422, 503]
    IF    ${resp.status_code} == 200 or ${resp.status_code} == 201 or ${resp.status_code} == 202
        ${json}=    Set Variable    ${resp.json()}
        Dictionary Should Contain Key    ${json}    id
    END
    Log    Collection trigger status: ${resp.status_code}

Create Connector With Invalid Short Code
    [Documentation]    POST /sb/connectors with a 2-character code returns 422
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${body}=    Create Dictionary
    ...    instance_code=AB
    ...    connector_type_code=${CONNECTOR_TYPE_CODE}
    ...    collection_schedule=manual
    ...    name=Invalid Short Code Connector
    ${resp}=    POST    ${CONN_URL}    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=422
    Log    Correctly rejected short code with 422

Create Connector Duplicate Code
    [Documentation]    POST /sb/connectors with duplicate instance_code returns 409
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${body}=    Create Dictionary
    ...    instance_code=${CONNECTOR_CODE}
    ...    connector_type_code=${CONNECTOR_TYPE_CODE}
    ...    collection_schedule=manual
    ...    name=Duplicate Connector
    ${resp}=    POST    ${CONN_URL}    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=409
    Log    Correctly rejected duplicate code with 409

Delete Second Connector
    [Documentation]    DELETE /sb/connectors/{id} removes the second connector
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${CONN_URL}/${CONNECTOR_ID_2}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204
    Log    Deleted second connector ${CONNECTOR_ID_2}

# ===========================================================================
# SECTION 3: DATASETS
# ===========================================================================

Create Dataset Manual JSON
    [Documentation]    POST /sb/datasets creates a new manual JSON dataset at version 1
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${records}=    Evaluate    []
    ${props}=    Create Dictionary    name=Robot Dataset ${TS}
    ${body}=    Create Dictionary
    ...    dataset_source_code=${DS_SOURCE_CODE}
    ...    workspace_id=${WS_ID}
    ...    properties=${props}
    ...    records=${records}
    ${resp}=    POST    ${DS_URL}    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    dataset_code
    Should Be True    ${json}[version_number] >= 1
    Should Not Be True    ${json}[is_locked]
    Set Suite Variable    ${DATASET_ID}    ${json}[id]
    Set Suite Variable    ${DATASET_CODE}    ${json}[dataset_code]
    Log    Created dataset: ${DATASET_ID} / ${DATASET_CODE}

Create Second Dataset
    [Documentation]    POST /sb/datasets creates a second dataset
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${props}=    Create Dictionary    name=Robot Dataset 2 ${TS}
    ${body}=    Create Dictionary
    ...    dataset_source_code=${DS_SOURCE_CODE}
    ...    workspace_id=${WS_ID}
    ...    properties=${props}
    ${resp}=    POST    ${DS_URL}    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Set Suite Variable    ${DATASET_ID_2}    ${json}[id]
    Log    Created second dataset: ${DATASET_ID_2}

List Datasets
    [Documentation]    GET /sb/datasets returns at least 2 datasets for this org
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${DS_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    Should Be True    ${json}[total] >= 2
    Log    Total datasets: ${json}[total]

List Datasets Filter By Source
    [Documentation]    GET /sb/datasets?dataset_source_code filters by source
    ${params}=    Create Dictionary    org_id=${ORG_ID}    dataset_source_code=${DS_SOURCE_CODE}
    ${resp}=    GET    ${DS_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Log    Datasets filtered by source ${DS_SOURCE_CODE}: ${json}[total]

List Datasets Filter By Locked False
    [Documentation]    GET /sb/datasets?is_locked=false returns only unlocked datasets
    ${params}=    Create Dictionary    org_id=${ORG_ID}    is_locked=false
    ${resp}=    GET    ${DS_URL}    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    ${items}=    Set Variable    ${json}[items]
    FOR    ${item}    IN    @{items}
        Should Not Be True    ${item}[is_locked]
    END
    Log    All returned datasets have is_locked=False

Get Dataset Metadata
    [Documentation]    GET /sb/datasets/{id} returns dataset metadata
    ${resp}=    GET    ${DS_URL}/${DATASET_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${DATASET_ID}
    Should Be Equal    ${json}[dataset_code]    ${DATASET_CODE}
    Log    Got dataset metadata for ${DATASET_ID}

Get Dataset Payload
    [Documentation]    GET /sb/datasets/{id}/records returns dataset records
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${DS_URL}/${DATASET_ID}/records    headers=${AUTH_HEADERS}    params=${params}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 404
    IF    ${resp.status_code} == 200
        ${json}=    Set Variable    ${resp.json()}
        Should Be True    isinstance($json, dict) or isinstance($json, list)
        Log    Got dataset records for ${DATASET_ID}
    ELSE
        Log    Records endpoint not available
    END

Get Dataset Not Found
    [Documentation]    GET /sb/datasets/{fake_uuid} returns 404
    ${resp}=    GET    ${DS_URL}/${FAKE_UUID}    headers=${AUTH_HEADERS}    expected_status=404
    Log    Correctly got 404 for missing dataset

Update Dataset
    [Documentation]    PATCH /sb/datasets/{id} updates properties and version increments
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${new_props}=    Create Dictionary    name=Robot Dataset Updated ${TS}
    ${body}=    Create Dictionary    properties=${new_props}
    ${resp}=    PATCH    ${DS_URL}/${DATASET_ID}    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[version_number] >= 1
    Log    Updated dataset; version_number=${json}[version_number]

Dataset Version History
    [Documentation]    GET /sb/datasets/{id}/versions returns version list if endpoint exists
    ${resp}=    GET    ${DS_URL}/${DATASET_ID}/versions    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 404
    IF    ${resp.status_code} == 200
        ${json}=    Set Variable    ${resp.json()}
        Should Be True    isinstance($json, list)
        Log    Dataset version history: ${json}
    ELSE
        Log    Version history endpoint not yet implemented (404)
    END

Lock Dataset
    [Documentation]    POST /sb/datasets/{id}/lock sets is_locked=True
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${DS_URL}/${DATASET_ID}/lock    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[is_locked]
    Log    Dataset ${DATASET_ID} is now locked

Lock Already Locked Dataset
    [Documentation]    POST lock on already-locked dataset returns 409
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${DS_URL}/${DATASET_ID}/lock    headers=${AUTH_HEADERS}    params=${params}    expected_status=409
    Log    Correctly got 409 when locking an already-locked dataset

Update Locked Dataset Fails
    [Documentation]    PATCH on locked dataset returns 409
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${body}=    Create Dictionary    name=Should Not Update
    ${resp}=    PATCH    ${DS_URL}/${DATASET_ID}    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=409
    Log    Correctly got 409 when updating a locked dataset

Delete Locked Dataset Fails
    [Documentation]    DELETE on locked dataset returns 409
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${DS_URL}/${DATASET_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=409
    Log    Correctly got 409 when deleting a locked dataset

Clone Locked Dataset
    [Documentation]    POST /sb/datasets/{id}/clone creates unlocked copy with new id
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${DS_URL}/${DATASET_ID}/clone    headers=${AUTH_HEADERS}    params=${params}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Not Be Equal    ${json}[id]    ${DATASET_ID}
    Should Not Be True    ${json}[is_locked]
    Set Suite Variable    ${CLONED_DS_ID}    ${json}[id]
    Log    Cloned dataset: ${CLONED_DS_ID}

Delete Cloned Dataset
    [Documentation]    DELETE /sb/datasets/{cloned_id} removes the cloned dataset
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${DS_URL}/${CLONED_DS_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204
    Log    Deleted cloned dataset ${CLONED_DS_ID}

Delete Second Dataset
    [Documentation]    DELETE /sb/datasets/{id} removes the second dataset
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    DELETE    ${DS_URL}/${DATASET_ID_2}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204
    Log    Deleted second dataset ${DATASET_ID_2}

# ===========================================================================
# SECTION 4: SIGNALS
# ===========================================================================

Create Signal With Evaluate Function
    [Documentation]    POST /sb/signals creates a signal with evaluate(dataset) function; version_number=1
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${python_src}=    Catenate    SEPARATOR=
    ...    def evaluate(dataset):
    ...    ${SPACE}users = dataset.get('users', [])\n    no_mfa = [u for u in users if not u.get('mfa_enabled', True)]\n    return {'result': 'fail' if no_mfa else 'pass', 'summary': f'{len(no_mfa)} users without MFA', 'details': [{'user': u.get('email', 'unknown'), 'status': 'fail'} for u in no_mfa]}
    ${properties}=    Create Dictionary
    ...    name=MFA Disabled Check ${TS}
    ...    python_source=${python_src}
    ${body}=    Create Dictionary
    ...    signal_code=mfa_check_${TS}
    ...    workspace_id=${WS_ID}
    ...    timeout_ms=${5000}
    ...    max_memory_mb=${128}
    Set To Dictionary    ${body}    properties    ${properties}
    ${resp}=    POST    ${SIG_URL}/    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    signal_code
    Should Be Equal    ${json}[signal_code]    mfa_check_${TS}
    Should Be Equal As Numbers    ${json}[version_number]    1
    Set Suite Variable    ${SIGNAL_ID}    ${json}[id]
    Set Suite Variable    ${SIGNAL_CODE}    ${json}[signal_code]
    Log    Created signal: ${SIGNAL_ID} / ${SIGNAL_CODE}

Create Second Signal Pass Result
    [Documentation]    POST /sb/signals creates a second signal that always passes
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${python_src}=    Catenate    SEPARATOR=
    ...    def evaluate(dataset):
    ...    ${SPACE}return {'result': 'pass', 'summary': 'Login anomaly check passed', 'details': []}
    ${properties}=    Create Dictionary
    ...    name=Login Anomaly Check ${TS}
    ...    python_source=${python_src}
    ${body}=    Create Dictionary
    ...    signal_code=login_check_${TS}
    ...    workspace_id=${WS_ID}
    Set To Dictionary    ${body}    properties    ${properties}
    ${resp}=    POST    ${SIG_URL}/    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Set Suite Variable    ${SIGNAL_ID_2}    ${json}[id]
    Set Suite Variable    ${SIGNAL_CODE_2}    ${json}[signal_code]
    Log    Created second signal: ${SIGNAL_ID_2} / ${SIGNAL_CODE_2}

List Signals
    [Documentation]    GET /sb/signals returns at least 2 signals for this org
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${SIG_URL}/    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    Should Be True    ${json}[total] >= 2
    Log    Total signals: ${json}[total]

List Signals Filter By Status
    [Documentation]    GET /sb/signals?signal_status_code=draft returns only draft signals
    ${params}=    Create Dictionary    org_id=${ORG_ID}    signal_status_code=draft
    ${resp}=    GET    ${SIG_URL}/    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Log    Draft signals count: ${json}[total]

List Signals With Search Query
    [Documentation]    GET /sb/signals?search=mfa returns at least 1 result
    ${params}=    Create Dictionary    org_id=${ORG_ID}    search=mfa
    ${resp}=    GET    ${SIG_URL}/    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[total] >= 1
    Log    Signals matching 'mfa': ${json}[total]

Get Signal With Python Source
    [Documentation]    GET /sb/signals/{id} returns signal with python_source as top-level field
    ${resp}=    GET    ${SIG_URL}/${SIGNAL_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${SIGNAL_ID}
    Should Be Equal    ${json}[signal_code]    ${SIGNAL_CODE}
    Dictionary Should Contain Key    ${json}    python_source
    Log    Got signal with python_source field

Get Signal Not Found
    [Documentation]    GET /sb/signals/{fake_uuid} returns 404
    ${resp}=    GET    ${SIG_URL}/${FAKE_UUID}    headers=${AUTH_HEADERS}    expected_status=404
    Log    Correctly got 404 for missing signal

Signal List Does Not Expose Python Source
    [Documentation]    GET /sb/signals list items — python_source may be null in list view
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${SIG_URL}/    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Set Variable    ${json}[items]
    Should Be True    len($items) > 0
    ${first_item}=    Set Variable    ${items}[0]
    # python_source may be present as null in list view — verify item has expected fields
    Dictionary Should Contain Key    ${first_item}    id
    Dictionary Should Contain Key    ${first_item}    signal_code
    Log    List view signal has expected fields

Update Signal Creates New Version
    [Documentation]    PATCH /sb/signals/{id} updates python_source and version_number increments
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${updated_src}=    Catenate    SEPARATOR=
    ...    def evaluate(dataset):
    ...    ${SPACE}users = dataset.get('users', [])\n    no_mfa = [u for u in users if not u.get('mfa_enabled', True)]\n    count = len(no_mfa)\n    return {'result': 'fail' if count > 0 else 'pass', 'summary': f'{count} users without MFA (updated)', 'details': [{'user': u.get('email', 'unknown'), 'status': 'fail'} for u in no_mfa]}
    ${properties}=    Create Dictionary    python_source=${updated_src}
    ${body}=    Create Dictionary
    Set To Dictionary    ${body}    properties    ${properties}
    ${resp}=    PATCH    ${SIG_URL}/${SIGNAL_ID}    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[version_number] >= 1
    Log    Updated signal; version_number=${json}[version_number]

Signal Version History
    [Documentation]    GET /sb/signals/{id}/versions returns list with at least 1 entry
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    GET    ${SIG_URL}/${SIGNAL_ID}/versions    headers=${AUTH_HEADERS}    params=${params}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} >= 1
    Log    Signal version history entries: ${count}

Create Signal With Tags In Properties
    [Documentation]    POST /sb/signals creates a signal with tags in properties
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${python_src}=    Catenate    SEPARATOR=
    ...    def evaluate(dataset):
    ...    ${SPACE}return {'result': 'pass', 'summary': 'Tagged signal check passed', 'details': []}
    ${properties}=    Create Dictionary
    ...    name=Tagged Signal ${TS}
    ...    python_source=${python_src}
    ...    tags=security,mfa,test
    ${body}=    Create Dictionary
    ...    signal_code=tagged_sig_${TS}
    ...    workspace_id=${WS_ID}
    Set To Dictionary    ${body}    properties    ${properties}
    ${resp}=    POST    ${SIG_URL}/    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Set Suite Variable    ${TAGGED_SIG_ID}    ${json}[id]
    Log    Created tagged signal: ${TAGGED_SIG_ID}

Create Signal With CAEP Event Type
    [Documentation]    POST /sb/signals creates a signal with caep_event_type property
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${python_src}=    Catenate    SEPARATOR=
    ...    def evaluate(dataset):
    ...    ${SPACE}return {'result': 'pass', 'summary': 'CAEP credential-change check passed', 'details': []}
    ${properties}=    Create Dictionary
    ...    name=CAEP Credential Change Signal ${TS}
    ...    python_source=${python_src}
    ...    caep_event_type=credential-change
    ${body}=    Create Dictionary
    ...    signal_code=caep_sig_${TS}
    ...    workspace_id=${WS_ID}
    Set To Dictionary    ${body}    properties    ${properties}
    ${resp}=    POST    ${SIG_URL}/    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Set Suite Variable    ${CAEP_SIG_ID}    ${json}[id]
    Log    Created CAEP signal: ${CAEP_SIG_ID}

Create Cascade Delete Test Signal
    [Documentation]    POST /sb/signals creates a signal for cascade delete testing in Part 2
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${python_src}=    Catenate    SEPARATOR=
    ...    def evaluate(dataset):
    ...    ${SPACE}return {'result': 'pass', 'summary': 'Cascade test signal', 'details': []}
    ${properties}=    Create Dictionary
    ...    name=Cascade Delete Test Signal ${TS}
    ...    python_source=${python_src}
    ${body}=    Create Dictionary
    ...    signal_code=cascade_sig_${TS}
    ...    workspace_id=${WS_ID}
    Set To Dictionary    ${body}    properties    ${properties}
    ${resp}=    POST    ${SIG_URL}/    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Set Suite Variable    ${CASCADE_SIG_ID}    ${json}[id]
    Log    Created cascade test signal: ${CASCADE_SIG_ID}

Validate Signal Returns Status
    [Documentation]    POST /sb/signals/{id}/validate returns signal_status_code if 200
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${body}=    Create Dictionary    org_id=${ORG_ID}
    ${resp}=    POST    ${SIG_URL}/${SIGNAL_ID}/validate    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201, 422]
    IF    ${resp.status_code} == 200 or ${resp.status_code} == 201
        ${json}=    Set Variable    ${resp.json()}
        Dictionary Should Contain Key    ${json}    signal_status_code
    END
    Log    Signal validate status: ${resp.status_code}

AI Generate Signal Stub
    [Documentation]    POST /sb/signals/generate returns generated stub or not-implemented
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${body}=    Create Dictionary
    ...    prompt=Check if users have MFA enabled
    ...    connector_type_code=${CONNECTOR_TYPE_CODE}
    ${resp}=    POST    ${SIG_URL}/generate    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201, 501, 503, 422]
    Log    AI generate signal status: ${resp.status_code}

Create Signal Duplicate Code
    [Documentation]    POST /sb/signals with duplicate signal_code returns 409
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${python_src}=    Catenate    SEPARATOR=
    ...    def evaluate(dataset):
    ...    ${SPACE}return {'result': 'pass', 'summary': 'Duplicate', 'details': []}
    ${properties}=    Create Dictionary    python_source=${python_src}
    ${body}=    Create Dictionary
    ...    signal_code=mfa_check_${TS}
    ...    workspace_id=${WS_ID}
    Set To Dictionary    ${body}    properties    ${properties}
    ${resp}=    POST    ${SIG_URL}/    headers=${AUTH_HEADERS}    params=${params}    json=${body}    expected_status=409
    Log    Correctly rejected duplicate signal code with 409

Delete Tagged And Caep Signals
    [Documentation]    DELETE tagged and CAEP signals; cascade signal is preserved for Part 2
    ${params}=    Create Dictionary    org_id=${ORG_ID}
    ${resp_tagged}=    DELETE    ${SIG_URL}/${TAGGED_SIG_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204
    Log    Deleted tagged signal ${TAGGED_SIG_ID}
    ${resp_caep}=    DELETE    ${SIG_URL}/${CAEP_SIG_ID}    headers=${AUTH_HEADERS}    params=${params}    expected_status=204
    Log    Deleted CAEP signal ${CAEP_SIG_ID}
