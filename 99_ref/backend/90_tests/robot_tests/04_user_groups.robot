*** Settings ***
Documentation    User Groups API Integration Tests
Resource         common.resource
Suite Setup      Setup Groups Suite

*** Keywords ***
Setup Groups Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # Register a member user for membership tests
    ${member_email}=    Set Variable    robot_member_${TS}@example.com
    ${member_id}=    Register Test User    ${member_email}
    Set Suite Variable    ${MEMBER_ID}    ${member_id}

*** Test Cases ***
List Groups
    [Documentation]    GET /am/groups
    ${resp}=    GET    ${AM_URL}/groups    headers=${AUTH_HEADERS}    expected_status=200

Create Group
    [Documentation]    POST /am/groups
    ${body}=    Create Dictionary
    ...    code=robot_group_${TS}
    ...    name=Robot Group ${TS}
    ...    description=Group created by Robot Framework
    ...    role_level_code=platform
    ${resp}=    POST    ${AM_URL}/groups    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${gid}=    Evaluate    $json.get('id') or $json.get('group_id')
    Set Suite Variable    ${GROUP_ID}    ${gid}
    Log    Created group: ${gid}

Update Group
    [Documentation]    PATCH /am/groups/{group_id}
    ${body}=    Create Dictionary
    ...    name=Robot Group ${TS} Updated
    ...    description=Updated by Robot Framework
    ${resp}=    PATCH    ${AM_URL}/groups/${GROUP_ID}    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[name]    Robot Group ${TS} Updated

Add Member To Group
    [Documentation]    POST /am/groups/{group_id}/members
    IF    '${MEMBER_ID}' != '${EMPTY}'
        ${body}=    Create Dictionary    user_id=${MEMBER_ID}
        ${resp}=    POST    ${AM_URL}/groups/${GROUP_ID}/members
        ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
        Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
        Log    Added member: ${MEMBER_ID}
    ELSE
        Pass Execution    No member user available
    END

Assign Role To Group
    [Documentation]    POST /am/groups/{group_id}/roles
    # Create a role to assign
    ${body}=    Create Dictionary
    ...    code=robot_grp_role_${TS}
    ...    name=Robot Group Role ${TS}
    ...    description=Role for group assignment test
    ...    role_level_code=platform
    ${resp}=    POST    ${AM_URL}/roles    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${rid}=    Evaluate    $json.get('id') or $json.get('role_id')
    Set Suite Variable    ${ASSIGN_ROLE_ID}    ${rid}
    # Assign to group
    ${assign_body}=    Create Dictionary    role_id=${rid}
    ${resp}=    POST    ${AM_URL}/groups/${GROUP_ID}/roles
    ...    headers=${AUTH_HEADERS}    json=${assign_body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201

Revoke Role From Group
    [Documentation]    DELETE /am/groups/{group_id}/roles/{role_id}
    ${resp}=    DELETE    ${AM_URL}/groups/${GROUP_ID}/roles/${ASSIGN_ROLE_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Revoked role: ${resp.status_code}

Remove Member From Group
    [Documentation]    DELETE /am/groups/{group_id}/members/{user_id}
    IF    '${MEMBER_ID}' != '${EMPTY}'
        ${resp}=    DELETE    ${AM_URL}/groups/${GROUP_ID}/members/${MEMBER_ID}
        ...    headers=${AUTH_HEADERS}    expected_status=any
        Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
        Log    Removed member: ${resp.status_code}
    ELSE
        Pass Execution    No member user to remove
    END

List Groups After Mutations
    [Documentation]    GET /am/groups — verify list still works after all mutations
    ${resp}=    GET    ${AM_URL}/groups    headers=${AUTH_HEADERS}    expected_status=200
