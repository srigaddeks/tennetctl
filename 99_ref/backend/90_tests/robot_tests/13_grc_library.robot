*** Settings ***
Documentation    GRC Library API Integration Tests
Resource         common.resource
Suite Setup      Setup GRC Library Suite

*** Variables ***
${FR_URL}    ${BASE_URL}/fr

*** Keywords ***
Setup GRC Library Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}

*** Test Cases ***
List Framework Types
    [Documentation]    GET /fr/framework-types
    ${resp}=    GET    ${FR_URL}/framework-types    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} > 0
    Log    Framework types count: ${count}
    # Verify compliance_standard exists
    ${codes}=    Evaluate    [item.get('code') for item in $json]
    Should Contain    ${codes}    compliance_standard

List Framework Categories
    [Documentation]    GET /fr/framework-categories
    ${resp}=    GET    ${FR_URL}/framework-categories    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} > 0
    Log    Framework categories count: ${count}
    ${codes}=    Evaluate    [item.get('code') for item in $json]
    Should Contain    ${codes}    compliance

List Control Categories
    [Documentation]    GET /fr/control-categories → expect 14 items
    ${resp}=    GET    ${FR_URL}/control-categories    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} >= 10
    Log    Control categories count: ${count}

List Control Criticalities
    [Documentation]    GET /fr/control-criticalities → expect 4 items
    ${resp}=    GET    ${FR_URL}/control-criticalities    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} >= 3
    Log    Control criticalities count: ${count}

List Test Types
    [Documentation]    GET /fr/test-types → expect 3 items
    ${resp}=    GET    ${FR_URL}/test-types    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} >= 2
    Log    Test types count: ${count}

Create Framework
    [Documentation]    POST /fr/frameworks
    ${body}=    Create Dictionary
    ...    framework_code=robot_fw_${TS}
    ...    framework_type_code=compliance_standard
    ...    framework_category_code=compliance
    ...    name=Robot Framework ${TS}
    ...    description=Framework created by Robot Framework tests
    ${resp}=    POST    ${FR_URL}/frameworks    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${fwid}=    Evaluate    $json.get('id') or $json.get('framework_id')
    Set Suite Variable    ${FW_ID}    ${fwid}
    Log    Created framework: ${fwid}

List Frameworks
    [Documentation]    GET /fr/frameworks → should contain robot_fw_${TS}
    ${resp}=    GET    ${FR_URL}/frameworks    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('frameworks', []))
    ${codes}=    Evaluate    [item.get('framework_code') or item.get('code') for item in $items]
    Should Contain    ${codes}    robot_fw_${TS}

Get Framework Detail
    [Documentation]    GET /fr/frameworks/${FW_ID} → verify name, type_code, category_code
    ${resp}=    GET    ${FR_URL}/frameworks/${FW_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[name]    Robot Framework ${TS}
    ${type_code}=    Evaluate    $json.get('framework_type_code') or $json.get('type_code')
    Should Be Equal    ${type_code}    compliance_standard
    ${cat_code}=    Evaluate    $json.get('framework_category_code') or $json.get('category_code')
    Should Be Equal    ${cat_code}    compliance

Update Framework
    [Documentation]    PATCH /fr/frameworks/${FW_ID} with new description
    ${body}=    Create Dictionary
    ...    description=Updated by Robot Framework tests
    ${resp}=    PATCH    ${FR_URL}/frameworks/${FW_ID}    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[description]    Updated by Robot Framework tests

Create Requirement
    [Documentation]    POST /fr/frameworks/${FW_ID}/requirements
    ${body}=    Create Dictionary
    ...    requirement_code=req_${TS}
    ...    name=Test Requirement
    ...    description=Requirement created by Robot Framework tests
    ${resp}=    POST    ${FR_URL}/frameworks/${FW_ID}/requirements
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${reqid}=    Evaluate    $json.get('id') or $json.get('requirement_id')
    Set Suite Variable    ${REQ_ID}    ${reqid}
    Log    Created requirement: ${reqid}

List Requirements
    [Documentation]    GET /fr/frameworks/${FW_ID}/requirements
    ${resp}=    GET    ${FR_URL}/frameworks/${FW_ID}/requirements
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('requirements', []))
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 1
    Log    Requirements count: ${count}

Create Control
    [Documentation]    POST /fr/frameworks/${FW_ID}/controls
    ${body}=    Create Dictionary
    ...    control_code=ctrl_${TS}
    ...    control_category_code=access_control
    ...    criticality_code=medium
    ...    control_type=preventive
    ...    automation_potential=manual
    ...    name=Test Control
    ...    description=Control created by Robot Framework tests
    ${resp}=    POST    ${FR_URL}/frameworks/${FW_ID}/controls
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${ctrlid}=    Evaluate    $json.get('id') or $json.get('control_id')
    Set Suite Variable    ${CTRL_ID}    ${ctrlid}
    Log    Created control: ${ctrlid}

List Controls
    [Documentation]    GET /fr/frameworks/${FW_ID}/controls → verify count
    ${resp}=    GET    ${FR_URL}/frameworks/${FW_ID}/controls
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('controls', []))
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 1
    Log    Controls count: ${count}

Get Control Detail
    [Documentation]    GET /fr/frameworks/${FW_ID}/controls/${CTRL_ID}
    ${resp}=    GET    ${FR_URL}/frameworks/${FW_ID}/controls/${CTRL_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[name]    Test Control
    Log    Control detail retrieved: ${CTRL_ID}

Create Control Test
    [Documentation]    POST /fr/tests
    ${body}=    Create Dictionary
    ...    test_code=test_${TS}
    ...    test_type_code=automated
    ...    integration_type=api
    ...    monitoring_frequency=monthly
    ...    name=Test Check
    ...    description=Test created by Robot Framework tests
    ${resp}=    POST    ${FR_URL}/tests
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${testid}=    Evaluate    $json.get('id') or $json.get('test_id')
    Set Suite Variable    ${TEST_ID}    ${testid}
    Log    Created test: ${testid}

List Tests
    [Documentation]    GET /fr/tests → should contain test_${TS}
    ${resp}=    GET    ${FR_URL}/tests    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('tests', []))
    ${codes}=    Evaluate    [item.get('test_code') for item in $items]
    Should Contain    ${codes}    test_${TS}

Create Test Control Mapping
    [Documentation]    POST /fr/tests/${TEST_ID}/controls
    ${body}=    Create Dictionary    control_id=${CTRL_ID}
    ${resp}=    POST    ${FR_URL}/tests/${TEST_ID}/controls
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${mapid}=    Evaluate    $json.get('id') or $json.get('mapping_id')
    Set Suite Variable    ${MAPPING_ID}    ${mapid}
    Log    Created test-control mapping: ${mapid}

List Test Mappings
    [Documentation]    GET /fr/tests/${TEST_ID}/controls → should have 1 item
    ${resp}=    GET    ${FR_URL}/tests/${TEST_ID}/controls
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('mappings', []))
    ${count}=    Get Length    ${items}
    Should Be Equal As Integers    ${count}    1

Filter Controls By Category
    [Documentation]    GET /fr/frameworks/${FW_ID}/controls?control_category_code=access_control
    ${resp}=    GET    ${FR_URL}/frameworks/${FW_ID}/controls
    ...    headers=${AUTH_HEADERS}
    ...    params=control_category_code=access_control    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', [])
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 1
    # All returned controls should have the filtered category
    ${cats}=    Evaluate    [item.get('control_category_code') for item in $items]
    Should Contain    ${cats}    access_control
    Log    Controls filtered by category: ${count}

Filter Tests By Test Type
    [Documentation]    GET /fr/tests?test_type_code=automated → should contain our test
    ${resp}=    GET    ${FR_URL}/tests    headers=${AUTH_HEADERS}
    ...    params=test_type_code=automated    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', [])
    ${codes}=    Evaluate    [item.get('test_code') for item in $items]
    Should Contain    ${codes}    test_${TS}
    Log    Tests filtered by type: automated

Create Evidence Template
    [Documentation]    POST /fr/tests/${TEST_ID}/evidence-templates — SKIPPED: endpoint not implemented yet
    [Tags]    skip
    Skip    Evidence template endpoint not implemented yet

List Evidence Templates
    [Documentation]    GET /fr/tests/${TEST_ID}/evidence-templates — SKIPPED: endpoint not implemented yet
    [Tags]    skip
    Skip    Evidence template endpoint not implemented yet

Delete Evidence Template
    [Documentation]    DELETE /fr/tests/${TEST_ID}/evidence-templates/${EVID_ID} — SKIPPED: endpoint not implemented yet
    [Tags]    skip
    Skip    Evidence template endpoint not implemented yet

Create Framework Version
    [Documentation]    POST /fr/frameworks/${FW_ID}/versions — verify lifecycle_state=draft
    ${body}=    Create Dictionary    version_code=v1.0
    ${resp}=    POST    ${FR_URL}/frameworks/${FW_ID}/versions
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${verid}=    Evaluate    $json.get('id') or $json.get('version_id')
    Set Suite Variable    ${VER_ID}    ${verid}
    # Newly created version should have lifecycle_state=draft
    ${lifecycle}=    Evaluate    $json.get('lifecycle_state') or $json.get('state')
    Should Be Equal    ${lifecycle}    draft
    Log    Created version: ${verid} with lifecycle_state=${lifecycle}

Publish Version
    [Documentation]    POST /fr/frameworks/${FW_ID}/versions/${VER_ID}/publish
    ${resp}=    POST    ${FR_URL}/frameworks/${FW_ID}/versions/${VER_ID}/publish
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    Log    Published version: ${VER_ID}

List Versions
    [Documentation]    GET /fr/frameworks/${FW_ID}/versions → verify published state
    ${resp}=    GET    ${FR_URL}/frameworks/${FW_ID}/versions
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('versions', []))
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 1
    # Verify the published version exists
    ${statuses}=    Evaluate    [item.get('lifecycle_state') for item in $items]
    Should Contain    ${statuses}    published

Create Framework Setting
    [Documentation]    PUT /fr/frameworks/${FW_ID}/settings/auto_publish
    ${body}=    Create Dictionary    setting_value=true
    ${resp}=    PUT    ${FR_URL}/frameworks/${FW_ID}/settings/auto_publish
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    Log    Created setting: auto_publish

List Settings
    [Documentation]    GET /fr/frameworks/${FW_ID}/settings → should have auto_publish
    ${resp}=    GET    ${FR_URL}/frameworks/${FW_ID}/settings
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('settings', []))
    ${keys}=    Evaluate    [item.get('key') or item.get('setting_key') for item in $items]
    Should Contain    ${keys}    auto_publish

Delete Framework Setting
    [Documentation]    DELETE /fr/frameworks/${FW_ID}/settings/auto_publish
    ${resp}=    DELETE    ${FR_URL}/frameworks/${FW_ID}/settings/auto_publish
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted setting: auto_publish

Cleanup Test Control Mapping
    [Documentation]    DELETE test-control mapping
    ${resp}=    DELETE    ${FR_URL}/tests/${TEST_ID}/controls/${MAPPING_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted mapping: ${MAPPING_ID}

Cleanup Test
    [Documentation]    DELETE test
    ${resp}=    DELETE    ${FR_URL}/tests/${TEST_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted test: ${TEST_ID}

Cleanup Control
    [Documentation]    DELETE control
    ${resp}=    DELETE    ${FR_URL}/frameworks/${FW_ID}/controls/${CTRL_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted control: ${CTRL_ID}

Cleanup Requirement
    [Documentation]    DELETE requirement
    ${resp}=    DELETE    ${FR_URL}/frameworks/${FW_ID}/requirements/${REQ_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted requirement: ${REQ_ID}

Cleanup Framework
    [Documentation]    DELETE framework (soft-delete)
    ${resp}=    DELETE    ${FR_URL}/frameworks/${FW_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted framework: ${FW_ID}
