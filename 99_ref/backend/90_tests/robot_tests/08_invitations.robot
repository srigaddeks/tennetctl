*** Settings ***
Documentation    Invitations API Integration Tests
Resource         common.resource
Suite Setup      Setup Invitations Suite

*** Keywords ***
Setup Invitations Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # Create an org for scoped invitation tests
    ${slug}=    Set Variable    robot-inv-org-${TS}
    ${body}=    Create Dictionary
    ...    name=Robot Inv Org ${TS}
    ...    slug=${slug}
    ...    org_type_code=community
    ...    description=Org for invitation tests
    ${resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${oid}=    Evaluate    $json.get('id') or $json.get('org_id')
    Set Suite Variable    ${INV_ORG_ID}    ${oid}
    Log    Created org for invitations: ${oid}
    # Create a workspace for workspace-scoped invitation tests
    ${ws_slug}=    Set Variable    robot-inv-ws-${TS}
    ${ws_body}=    Create Dictionary
    ...    name=Robot Inv WS ${TS}
    ...    slug=${ws_slug}
    ...    workspace_type_code=project
    ...    description=Workspace for invitation tests
    ${ws_resp}=    POST    ${AM_URL}/orgs/${INV_ORG_ID}/workspaces
    ...    headers=${AUTH_HEADERS}    json=${ws_body}    expected_status=any
    Should Be True    ${ws_resp.status_code} == 200 or ${ws_resp.status_code} == 201
    ${ws_json}=    Set Variable    ${ws_resp.json()}
    ${wsid}=    Evaluate    $ws_json.get('id') or $ws_json.get('workspace_id')
    Set Suite Variable    ${INV_WS_ID}    ${wsid}
    Log    Created workspace for invitations: ${wsid}

*** Test Cases ***
Create Platform Invitation
    [Documentation]    POST /am/invitations — platform scope
    ${email}=    Set Variable    platform_invite_${TS}@example.com
    ${body}=    Create Dictionary
    ...    email=${email}
    ...    scope=platform
    ${resp}=    POST    ${AM_URL}/invitations    headers=${AUTH_HEADERS}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[email]    ${email}
    Should Be Equal    ${json}[scope]    platform
    Should Be Equal    ${json}[status]    pending
    Dictionary Should Contain Key    ${json}    invite_token
    Set Suite Variable    ${PLATFORM_INVITE_ID}    ${json}[id]
    Log    Created platform invitation: ${json}[id]

Create Organization Invitation
    [Documentation]    POST /am/invitations — organization scope with role
    ${email}=    Set Variable    org_invite_${TS}@example.com
    ${body}=    Create Dictionary
    ...    email=${email}
    ...    scope=organization
    ...    org_id=${INV_ORG_ID}
    ...    role=member
    ${resp}=    POST    ${AM_URL}/invitations    headers=${AUTH_HEADERS}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[email]    ${email}
    Should Be Equal    ${json}[scope]    organization
    Should Be Equal    ${json}[role]    member
    Set Suite Variable    ${ORG_INVITE_ID}    ${json}[id]
    Log    Created org invitation: ${json}[id]

Create Workspace Invitation
    [Documentation]    POST /am/invitations — workspace scope with role
    ${email}=    Set Variable    ws_invite_${TS}@example.com
    ${body}=    Create Dictionary
    ...    email=${email}
    ...    scope=workspace
    ...    org_id=${INV_ORG_ID}
    ...    workspace_id=${INV_WS_ID}
    ...    role=contributor
    ${resp}=    POST    ${AM_URL}/invitations    headers=${AUTH_HEADERS}    json=${body}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[email]    ${email}
    Should Be Equal    ${json}[scope]    workspace
    Should Be Equal    ${json}[role]    contributor
    Set Suite Variable    ${WS_INVITE_ID}    ${json}[id]
    Set Suite Variable    ${WS_INVITE_TOKEN}    ${json}[invite_token]
    Log    Created workspace invitation: ${json}[id]

List Invitations
    [Documentation]    GET /am/invitations
    ${resp}=    GET    ${AM_URL}/invitations    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    Should Be True    ${json}[total] >= 3
    Log    Total invitations: ${json}[total]

List Invitations Filtered By Status
    [Documentation]    GET /am/invitations?status=pending
    ${resp}=    GET    ${AM_URL}/invitations?status=pending
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[total] >= 3

Get Invitation Stats
    [Documentation]    GET /am/invitations/stats
    ${resp}=    GET    ${AM_URL}/invitations/stats    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    total
    Dictionary Should Contain Key    ${json}    pending
    Dictionary Should Contain Key    ${json}    accepted
    Should Be True    ${json}[pending] >= 3
    Log    Stats - Total: ${json}[total], Pending: ${json}[pending]

Get Invitation Detail
    [Documentation]    GET /am/invitations/{invitation_id}
    ${resp}=    GET    ${AM_URL}/invitations/${PLATFORM_INVITE_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${PLATFORM_INVITE_ID}
    Should Be Equal    ${json}[scope]    platform

Revoke Invitation
    [Documentation]    PATCH /am/invitations/{invitation_id}/revoke
    ${resp}=    PATCH    ${AM_URL}/invitations/${ORG_INVITE_ID}/revoke
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[status]    revoked
    Log    Revoked invitation: ${ORG_INVITE_ID}

Accept Invitation
    [Documentation]    POST /am/invitations/accept — public endpoint
    ${body}=    Create Dictionary    invite_token=${WS_INVITE_TOKEN}
    ${resp}=    POST    ${AM_URL}/invitations/accept    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    message
    Should Be Equal    ${json}[scope]    workspace
    Log    Accepted invitation with role: ${json}[role]

Accept Invitation Public Without Auth
    [Documentation]    POST /am/invitations/accept-public — public endpoint, no JWT
    ${body}=    Create Dictionary    invite_token=${ORG_INVITE_TOKEN}
    ${resp}=    POST    ${AM_URL}/invitations/accept-public    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 404
    Run Keyword If    ${resp.status_code} == 200
    ...    Log    Public accept succeeded for existing user
    Run Keyword If    ${resp.status_code} == 404
    ...    Log    Public accept returned user_not_found (no matching account)

Create Duplicate Invitation Returns Error
    [Documentation]    POST /am/invitations — duplicate pending invite
    ${email}=    Set Variable    platform_invite_${TS}@example.com
    ${body}=    Create Dictionary
    ...    email=${email}
    ...    scope=platform
    ${resp}=    POST    ${AM_URL}/invitations    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 409 or ${resp.status_code} == 400
    Log    Duplicate invite rejected: ${resp.status_code}

Create Invitation With Invalid Scope Returns 422
    [Documentation]    POST /am/invitations — org scope without org_id
    ${body}=    Create Dictionary
    ...    email=bad_scope_${TS}@example.com
    ...    scope=organization
    ${resp}=    POST    ${AM_URL}/invitations    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 422 or ${resp.status_code} == 400
    Log    Invalid scope rejected: ${resp.status_code}

Create Invitation With Invalid Role Returns Error
    [Documentation]    POST /am/invitations — org scope with invalid role
    ${body}=    Create Dictionary
    ...    email=bad_role_${TS}@example.com
    ...    scope=organization
    ...    org_id=${INV_ORG_ID}
    ...    role=superadmin
    ${resp}=    POST    ${AM_URL}/invitations    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 422 or ${resp.status_code} == 400
    Log    Invalid role rejected: ${resp.status_code}

Create Invitation Without Auth Returns Error
    [Documentation]    POST /am/invitations without authentication
    ${body}=    Create Dictionary
    ...    email=noauth_${TS}@example.com
    ...    scope=platform
    ${resp}=    POST    ${AM_URL}/invitations    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

Accept Invalid Token Returns Error
    [Documentation]    POST /am/invitations/accept with bad token
    ${body}=    Create Dictionary    invite_token=00000000-0000-0000-0000-000000000000.fakesecret
    ${resp}=    POST    ${AM_URL}/invitations/accept    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 404 or ${resp.status_code} == 400
    Log    Invalid token rejected: ${resp.status_code}
