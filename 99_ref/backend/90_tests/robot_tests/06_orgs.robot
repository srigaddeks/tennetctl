*** Settings ***
Documentation    Orgs API Integration Tests
Resource         common.resource
Suite Setup      Setup Orgs Suite

*** Keywords ***
Setup Orgs Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # Register a member for org membership tests
    ${member_email}=    Set Variable    robot_org_member_${TS}@example.com
    ${member_id}=    Register Test User    ${member_email}
    Set Suite Variable    ${ORG_MEMBER_ID}    ${member_id}

*** Test Cases ***
List Org Types
    [Documentation]    GET /am/org-types
    ${resp}=    GET    ${AM_URL}/org-types    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be True    ${count} > 0
    Log    Org types count: ${count}
    # Store first type code
    ${first}=    Evaluate    $json[0]
    ${code}=    Get From Dictionary    ${first}    code
    Set Suite Variable    ${ORG_TYPE_CODE}    ${code}
    Log    Using org type: ${code}

List Orgs
    [Documentation]    GET /am/orgs
    ${resp}=    GET    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    expected_status=200

Create Org
    [Documentation]    POST /am/orgs
    ${slug}=    Set Variable    robot-org-${TS}
    ${body}=    Create Dictionary
    ...    name=Robot Org ${TS}
    ...    slug=${slug}
    ...    org_type_code=${ORG_TYPE_CODE}
    ...    description=Org created by Robot Framework
    ${resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${oid}=    Evaluate    $json.get('id') or $json.get('org_id')
    Set Suite Variable    ${ORG_ID}    ${oid}
    Log    Created org: ${oid}

Update Org
    [Documentation]    PATCH /am/orgs/{org_id}
    ${body}=    Create Dictionary
    ...    name=Robot Org ${TS} Updated
    ...    description=Updated by Robot Framework
    ${resp}=    PATCH    ${AM_URL}/orgs/${ORG_ID}    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[name]    Robot Org ${TS} Updated

List Org Members
    [Documentation]    GET /am/orgs/{org_id}/members
    ${resp}=    GET    ${AM_URL}/orgs/${ORG_ID}/members    headers=${AUTH_HEADERS}    expected_status=200

Add Org Member
    [Documentation]    POST /am/orgs/{org_id}/members
    IF    '${ORG_MEMBER_ID}' != '${EMPTY}'
        ${body}=    Create Dictionary    user_id=${ORG_MEMBER_ID}    role=member
        ${resp}=    POST    ${AM_URL}/orgs/${ORG_ID}/members
        ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
        Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
        Log    Added org member: ${ORG_MEMBER_ID}
    ELSE
        Pass Execution    No member user available
    END

Remove Org Member
    [Documentation]    DELETE /am/orgs/{org_id}/members/{user_id}
    IF    '${ORG_MEMBER_ID}' != '${EMPTY}'
        ${resp}=    DELETE    ${AM_URL}/orgs/${ORG_ID}/members/${ORG_MEMBER_ID}
        ...    headers=${AUTH_HEADERS}    expected_status=any
        Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
        Log    Removed org member: ${resp.status_code}
    ELSE
        Pass Execution    No member user to remove
    END

Create Org With Duplicate Slug Returns Error
    [Documentation]    POST /am/orgs with duplicate slug
    ${slug}=    Set Variable    robot-org-${TS}
    ${body}=    Create Dictionary
    ...    name=Duplicate Org
    ...    slug=${slug}
    ...    org_type_code=${ORG_TYPE_CODE}
    ${resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 409 or ${resp.status_code} == 422 or ${resp.status_code} == 400 or ${resp.status_code} == 500
    Log    Duplicate slug result: ${resp.status_code}

Create Org Without Auth Returns Error
    [Documentation]    POST /am/orgs without authentication
    ${body}=    Create Dictionary
    ...    name=No Auth Org
    ...    slug=noauth-org
    ...    org_type_code=community
    ${resp}=    POST    ${AM_URL}/orgs    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403
