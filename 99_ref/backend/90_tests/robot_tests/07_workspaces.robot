*** Settings ***
Documentation    Workspaces API Integration Tests
Resource         common.resource
Suite Setup      Setup Workspaces Suite

*** Keywords ***
Setup Workspaces Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # Register a member for workspace membership tests
    ${member_email}=    Set Variable    robot_ws_member_${TS}@example.com
    ${member_id}=    Register Test User    ${member_email}
    Set Suite Variable    ${WS_MEMBER_ID}    ${member_id}
    # Create an org for workspace tests
    ${slug}=    Set Variable    robot-ws-org-${TS}
    ${body}=    Create Dictionary
    ...    name=Robot WS Org ${TS}
    ...    slug=${slug}
    ...    org_type_code=community
    ...    description=Org for workspace tests
    ${resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${oid}=    Evaluate    $json.get('id') or $json.get('org_id')
    Set Suite Variable    ${WS_ORG_ID}    ${oid}
    Log    Created org for workspaces: ${oid}

*** Test Cases ***
List Workspace Types
    [Documentation]    GET /am/workspace-types
    ${resp}=    GET    ${AM_URL}/workspace-types    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} > 0
    Log    Workspace types count: ${count}
    ${first}=    Evaluate    $json[0]
    ${code}=    Get From Dictionary    ${first}    code
    Set Suite Variable    ${WS_TYPE_CODE}    ${code}

List Workspaces
    [Documentation]    GET /am/orgs/{org_id}/workspaces
    ${resp}=    GET    ${AM_URL}/orgs/${WS_ORG_ID}/workspaces
    ...    headers=${AUTH_HEADERS}    expected_status=200

Create Workspace
    [Documentation]    POST /am/orgs/{org_id}/workspaces
    ${ws_slug}=    Set Variable    robot-ws-${TS}
    ${body}=    Create Dictionary
    ...    name=Robot Workspace ${TS}
    ...    slug=${ws_slug}
    ...    workspace_type_code=${WS_TYPE_CODE}
    ...    description=Workspace created by Robot Framework
    ${resp}=    POST    ${AM_URL}/orgs/${WS_ORG_ID}/workspaces
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${wsid}=    Evaluate    $json.get('id') or $json.get('workspace_id')
    Set Suite Variable    ${WS_ID}    ${wsid}
    Log    Created workspace: ${wsid}

Update Workspace
    [Documentation]    PATCH /am/orgs/{org_id}/workspaces/{workspace_id}
    ${body}=    Create Dictionary
    ...    name=Robot Workspace ${TS} Updated
    ...    description=Updated by Robot Framework
    ${resp}=    PATCH    ${AM_URL}/orgs/${WS_ORG_ID}/workspaces/${WS_ID}
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[name]    Robot Workspace ${TS} Updated

List Workspace Members
    [Documentation]    GET /am/orgs/{org_id}/workspaces/{workspace_id}/members
    ${resp}=    GET    ${AM_URL}/orgs/${WS_ORG_ID}/workspaces/${WS_ID}/members
    ...    headers=${AUTH_HEADERS}    expected_status=200

Add Workspace Member
    [Documentation]    POST /am/orgs/{org_id}/workspaces/{workspace_id}/members
    IF    '${WS_MEMBER_ID}' != '${EMPTY}'
        ${body}=    Create Dictionary    user_id=${WS_MEMBER_ID}    role=contributor
        ${resp}=    POST    ${AM_URL}/orgs/${WS_ORG_ID}/workspaces/${WS_ID}/members
        ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
        Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
        Log    Added workspace member: ${WS_MEMBER_ID}
    ELSE
        Pass Execution    No member user available
    END

Remove Workspace Member
    [Documentation]    DELETE /am/orgs/{org_id}/workspaces/{workspace_id}/members/{user_id}
    IF    '${WS_MEMBER_ID}' != '${EMPTY}'
        ${resp}=    DELETE
        ...    ${AM_URL}/orgs/${WS_ORG_ID}/workspaces/${WS_ID}/members/${WS_MEMBER_ID}
        ...    headers=${AUTH_HEADERS}    expected_status=any
        Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
        Log    Removed workspace member: ${resp.status_code}
    ELSE
        Pass Execution    No member user to remove
    END

Create Workspace Without Auth Returns Error
    [Documentation]    POST /am/orgs/{org_id}/workspaces without auth
    ${body}=    Create Dictionary
    ...    name=No Auth WS
    ...    slug=noauth-ws
    ...    workspace_type_code=development
    ${resp}=    POST    ${AM_URL}/orgs/${WS_ORG_ID}/workspaces
    ...    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

Create Workspace With Invalid Slug Returns 422
    [Documentation]    POST /am/orgs/{org_id}/workspaces with invalid slug
    ${body}=    Create Dictionary
    ...    name=Invalid Slug WS
    ...    slug=INVALID SLUG!!
    ...    workspace_type_code=${WS_TYPE_CODE}
    ${resp}=    POST    ${AM_URL}/orgs/${WS_ORG_ID}/workspaces
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=422
