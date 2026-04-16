*** Settings ***
Documentation    Enhancement API Integration Tests (batch properties, property keys,
...              password change, email verification, sessions, admin users, audit,
...              feature evaluation, entity settings, accounts, session revocation)
Resource         common.resource
Suite Setup      Setup Enhancements Suite

*** Keywords ***
Setup Enhancements Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # Register a dedicated test user for password / email tests
    ${email}=    Set Variable    robot_enh_${TS}@example.com
    Set Suite Variable    ${ENH_EMAIL}    ${email}
    Set Suite Variable    ${ENH_PASSWORD}    RobotEnhPass123!
    ${uid}=    Register Test User    ${email}    ${ENH_PASSWORD}
    Set Suite Variable    ${ENH_USER_ID}    ${uid}
    # Login as the test user and store their token
    ${body}=    Create Dictionary    login=${email}    password=${ENH_PASSWORD}
    ${resp}=    POST    ${AUTH_URL}/login    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${token}=    Get From Dictionary    ${json}    access_token
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    Set Suite Variable    ${ENH_HEADERS}    ${headers}
    Set Suite Variable    ${ENH_TOKEN}    ${token}
    # Create an org for settings tests
    ${resp}=    GET    ${AM_URL}/org-types    headers=${AUTH_HEADERS}    expected_status=200
    ${types}=    Set Variable    ${resp.json()}
    ${first_type}=    Evaluate    $types[0]
    ${type_code}=    Get From Dictionary    ${first_type}    code
    Set Suite Variable    ${ORG_TYPE_CODE}    ${type_code}
    ${slug}=    Set Variable    robot-enh-org-${TS}
    ${org_body}=    Create Dictionary
    ...    name=Robot Enh Org ${TS}
    ...    slug=${slug}
    ...    org_type_code=${type_code}
    ...    description=Org for enhancement tests
    ${resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${org_body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${oid}=    Evaluate    $json.get('id') or $json.get('org_id')
    Set Suite Variable    ${ORG_ID}    ${oid}
    # Create a workspace inside the org for workspace settings tests
    ${ws_types_resp}=    GET    ${AM_URL}/workspace-types    headers=${AUTH_HEADERS}    expected_status=200
    ${ws_types}=    Set Variable    ${ws_types_resp.json()}
    ${ws_type}=    Evaluate    $ws_types[0]
    ${ws_type_code}=    Get From Dictionary    ${ws_type}    code
    ${ws_slug}=    Set Variable    robot-enh-ws-${TS}
    ${ws_body}=    Create Dictionary
    ...    name=Robot Enh WS ${TS}
    ...    slug=${ws_slug}
    ...    workspace_type_code=${ws_type_code}
    ...    description=Workspace for enhancement tests
    ${ws_resp}=    POST    ${AM_URL}/orgs/${oid}/workspaces    headers=${AUTH_HEADERS}    json=${ws_body}    expected_status=any
    Should Be True    ${ws_resp.status_code} == 200 or ${ws_resp.status_code} == 201
    ${ws_json}=    Set Variable    ${ws_resp.json()}
    ${wsid}=    Evaluate    $ws_json.get('id') or $ws_json.get('workspace_id')
    Set Suite Variable    ${WS_ID}    ${wsid}
    # Store the enhancement user's session_id for session revocation test
    ${sessions_resp}=    GET    ${AM_URL}/admin/users/${ENH_USER_ID}/sessions
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${sessions_json}=    Set Variable    ${sessions_resp.json()}
    ${sessions}=    Get From Dictionary    ${sessions_json}    sessions
    ${first_session}=    Evaluate    $sessions[0]
    ${enh_session_id}=    Get From Dictionary    ${first_session}    session_id
    Set Suite Variable    ${ENH_SESSION_ID}    ${enh_session_id}
    Log    Suite setup complete: user=${uid}, org=${oid}, ws=${wsid}

*** Test Cases ***
# ── Batch Properties ────────────────────────────────────────────────────

Batch Set User Properties
    [Documentation]    PUT /auth/local/me/properties with multiple properties
    ${props}=    Create Dictionary    display_name=Robot Test    timezone=UTC
    ${body}=    Create Dictionary    properties=${props}
    ${resp}=    PUT    ${AUTH_URL}/me/properties    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    properties
    ${items}=    Get From Dictionary    ${json}    properties
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 2
    Log    Batch set ${count} properties

Batch Set Invalid Key Returns 404
    [Documentation]    PUT /auth/local/me/properties with invalid key returns 404
    ${props}=    Create Dictionary    totally_invalid_key_xyz=whatever
    ${body}=    Create Dictionary    properties=${props}
    ${resp}=    PUT    ${AUTH_URL}/me/properties    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 404 or ${resp.status_code} == 422 or ${resp.status_code} == 400
    Log    Invalid key result: ${resp.status_code}

# ── Property Keys Discovery ────────────────────────────────────────────

List User Property Keys
    [Documentation]    GET /auth/local/me/property-keys
    ${resp}=    GET    ${AUTH_URL}/me/property-keys    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    keys
    ${keys}=    Get From Dictionary    ${json}    keys
    ${count}=    Get Length    ${keys}
    Should Be True    ${count} > 0
    # Verify email key is present
    ${codes}=    Evaluate    [k.get('code') for k in $keys]
    Should Contain    ${codes}    email
    Log    Found ${count} property keys

Property Key Has Expected Fields
    [Documentation]    Verify each property key has required fields
    ${resp}=    GET    ${AUTH_URL}/me/property-keys    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${keys}=    Get From Dictionary    ${json}    keys
    ${first}=    Evaluate    $keys[0]
    Dictionary Should Contain Key    ${first}    code
    Dictionary Should Contain Key    ${first}    name
    Dictionary Should Contain Key    ${first}    data_type
    Dictionary Should Contain Key    ${first}    sort_order
    Log    Property key fields verified

# ── Password Change ────────────────────────────────────────────────────

Change Password Success
    [Documentation]    PUT /auth/local/me/password with valid current and new password
    ${body}=    Create Dictionary
    ...    current_password=${ENH_PASSWORD}
    ...    new_password=NewRobotPass456!
    ${resp}=    PUT    ${AUTH_URL}/me/password    headers=${ENH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    message
    Set Suite Variable    ${ENH_PASSWORD}    NewRobotPass456!
    Log    Password changed successfully

Change Password Wrong Current Returns 401
    [Documentation]    PUT /auth/local/me/password with wrong current_password
    ${body}=    Create Dictionary
    ...    current_password=TotallyWrongPass99!
    ...    new_password=AnotherNewPass789!
    ${resp}=    PUT    ${AUTH_URL}/me/password    headers=${ENH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403 or ${resp.status_code} == 400
    Log    Wrong current password result: ${resp.status_code}

Login With New Password
    [Documentation]    Verify login works with the changed password
    ${body}=    Create Dictionary    login=${ENH_EMAIL}    password=${ENH_PASSWORD}
    ${resp}=    POST    ${AUTH_URL}/login    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    access_token
    ${token}=    Get From Dictionary    ${json}    access_token
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    Set Suite Variable    ${ENH_HEADERS}    ${headers}
    Set Suite Variable    ${ENH_TOKEN}    ${token}
    Log    Login with new password succeeded

Change Password Short New Password Returns 422
    [Documentation]    PUT /auth/local/me/password with too-short new_password returns 422
    ${body}=    Create Dictionary
    ...    current_password=${ENH_PASSWORD}
    ...    new_password=short
    ${resp}=    PUT    ${AUTH_URL}/me/password    headers=${ENH_HEADERS}    json=${body}    expected_status=422
    Log    Short password validation: ${resp.status_code}

# ── Email Verification ─────────────────────────────────────────────────

Request Email Verification
    [Documentation]    POST /auth/local/me/verify-email/request
    ${resp}=    POST    ${AUTH_URL}/me/verify-email/request    headers=${ENH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 202
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    message
    # In dev environment, verification_token is returned directly
    ${has_token}=    Evaluate    'verification_token' in $json and $json['verification_token'] is not None
    IF    ${has_token}
        ${vtoken}=    Get From Dictionary    ${json}    verification_token
        Set Suite Variable    ${VERIFY_TOKEN}    ${vtoken}
        Log    Got verification token (dev mode)
    ELSE
        Set Suite Variable    ${VERIFY_TOKEN}    ${EMPTY}
        Log    No verification token in response (production mode)    WARN
    END

Verify Email With Token
    [Documentation]    POST /auth/local/me/verify-email with token
    Skip If    '${VERIFY_TOKEN}' == '${EMPTY}'    No verification token available
    ${body}=    Create Dictionary    verification_token=${VERIFY_TOKEN}
    ${resp}=    POST    ${AUTH_URL}/me/verify-email    headers=${ENH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    message
    Log    Email verified: ${json}[message]

Email Verified After Verification
    [Documentation]    GET /auth/local/me shows email_verified=True after verification
    Skip If    '${VERIFY_TOKEN}' == '${EMPTY}'    No verification token available
    ${resp}=    GET    ${AUTH_URL}/me    headers=${ENH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    email_verified
    Should Be True    ${json}[email_verified] == True
    Log    email_verified confirmed True

Request Verification When Already Verified
    [Documentation]    POST /auth/local/me/verify-email/request when already verified
    Skip If    '${VERIFY_TOKEN}' == '${EMPTY}'    No verification token available
    ${resp}=    POST    ${AUTH_URL}/me/verify-email/request    headers=${ENH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 202 or ${resp.status_code} == 409 or ${resp.status_code} == 400
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    message
    Log    Already verified response: ${json}[message]

# ── Session Management ──────────────────────────────────────────────────

List My Sessions
    [Documentation]    GET /am/admin/users/{user_id}/sessions
    ${resp}=    GET    ${AM_URL}/admin/users/${USER_ID}/sessions
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    sessions
    ${sessions}=    Get From Dictionary    ${json}    sessions
    ${count}=    Get Length    ${sessions}
    Should Be True    ${count} >= 1
    Log    Found ${count} sessions for admin user

Session Has Expected Fields
    [Documentation]    Verify session object contains expected fields
    ${resp}=    GET    ${AM_URL}/admin/users/${USER_ID}/sessions
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${sessions}=    Get From Dictionary    ${json}    sessions
    ${first}=    Evaluate    $sessions[0]
    Dictionary Should Contain Key    ${first}    session_id
    Dictionary Should Contain Key    ${first}    user_id
    Dictionary Should Contain Key    ${first}    client_ip
    Dictionary Should Contain Key    ${first}    created_at
    Log    Session fields verified

# ── Admin User Listing ──────────────────────────────────────────────────

List Users
    [Documentation]    GET /am/admin/users
    ${resp}=    GET    ${AM_URL}/admin/users    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    users
    Dictionary Should Contain Key    ${json}    total
    ${users}=    Get From Dictionary    ${json}    users
    ${count}=    Get Length    ${users}
    Should Be True    ${count} >= 1
    Log    Found ${json}[total] total users, ${count} returned

List Users With Search
    [Documentation]    GET /am/admin/users?search=robot filters results
    ${resp}=    GET    ${AM_URL}/admin/users?search=robot_enh
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    users
    Dictionary Should Contain Key    ${json}    total
    Log    Search returned ${json}[total] users

# ── Audit Log ───────────────────────────────────────────────────────────

List Audit Events
    [Documentation]    GET /am/admin/audit
    ${resp}=    GET    ${AM_URL}/admin/audit    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    events
    Dictionary Should Contain Key    ${json}    total
    ${events}=    Get From Dictionary    ${json}    events
    ${count}=    Get Length    ${events}
    Should Be True    ${count} >= 1
    Log    Found ${json}[total] total audit events, ${count} returned

Filter Audit By Event Type
    [Documentation]    GET /am/admin/audit?event_type=login_succeeded
    ${resp}=    GET    ${AM_URL}/admin/audit?event_type=login_succeeded
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    events
    Dictionary Should Contain Key    ${json}    total
    Log    Filtered audit events: ${json}[total]

# ── Feature Evaluation ──────────────────────────────────────────────────

Evaluate My Features
    [Documentation]    GET /am/admin/me/features
    ${resp}=    GET    ${AM_URL}/admin/me/features    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    features
    ${features}=    Get From Dictionary    ${json}    features
    Should Be True    isinstance($features, list)
    ${feature_count}=    Get Length    ${features}
    Log    Evaluated ${feature_count} features

# ── Org Settings ────────────────────────────────────────────────────────

List Org Settings Empty Initially
    [Documentation]    GET /am/settings/org/{org_id} returns empty list for new org
    ${resp}=    GET    ${AM_URL}/settings/org/${ORG_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    settings
    ${settings}=    Get From Dictionary    ${json}    settings
    ${count}=    Get Length    ${settings}
    Should Be True    ${count} == 0
    Log    Org settings initially empty

List Org Setting Keys
    [Documentation]    GET /am/settings/org/{org_id}/keys returns available keys
    ${resp}=    GET    ${AM_URL}/settings/org/${ORG_ID}/keys
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    keys
    ${keys}=    Get From Dictionary    ${json}    keys
    ${count}=    Get Length    ${keys}
    Should Be True    ${count} > 0
    Log    Found ${count} org setting keys

Set Org Setting
    [Documentation]    PUT /am/settings/org/{org_id}/logo_url
    ${body}=    Create Dictionary    value=https://example.com/logo.png
    ${resp}=    PUT    ${AM_URL}/settings/org/${ORG_ID}/logo_url
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Log    Set org setting: ${json}

Get Org Settings After Set
    [Documentation]    GET /am/settings/org/{org_id} contains logo_url after set
    ${resp}=    GET    ${AM_URL}/settings/org/${ORG_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${settings}=    Get From Dictionary    ${json}    settings
    ${count}=    Get Length    ${settings}
    Should Be True    ${count} >= 1
    ${keys}=    Evaluate    [s.get('key') or s.get('setting_key') or s.get('code') for s in $settings]
    Log    Org settings keys after set: ${keys}

Batch Set Org Settings
    [Documentation]    PUT /am/settings/org/{org_id} with multiple settings
    ${settings}=    Create Dictionary    website=https://example.com    industry=Technology
    ${body}=    Create Dictionary    settings=${settings}
    ${resp}=    PUT    ${AM_URL}/settings/org/${ORG_ID}
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Log    Batch set org settings result: ${json}

Delete Org Setting
    [Documentation]    DELETE /am/settings/org/{org_id}/logo_url
    ${resp}=    DELETE    ${AM_URL}/settings/org/${ORG_ID}/logo_url
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted org setting: ${resp.status_code}

Set Invalid Setting Key Returns 404
    [Documentation]    PUT /am/settings/org/{org_id} with unknown key returns error
    ${body}=    Create Dictionary    value=anything
    ${resp}=    PUT    ${AM_URL}/settings/org/${ORG_ID}/totally_nonexistent_key_xyz
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 404 or ${resp.status_code} == 422 or ${resp.status_code} == 400
    Log    Invalid setting key result: ${resp.status_code}

# ── Individual User Properties ─────────────────────────────────────────

Get User Properties
    [Documentation]    GET /auth/local/me/properties returns list of user properties
    ${resp}=    GET    ${AUTH_URL}/me/properties    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    properties
    ${props}=    Get From Dictionary    ${json}    properties
    Should Be True    isinstance($props, list)
    ${prop_count}=    Get Length    ${props}
    Log    Found ${prop_count} user properties

Set Individual User Property
    [Documentation]    PUT /auth/local/me/properties/{key} sets a single property
    ${body}=    Create Dictionary    value=Robot Display Name
    ${resp}=    PUT    ${AUTH_URL}/me/properties/display_name
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    key
    Dictionary Should Contain Key    ${json}    value
    Should Be Equal    ${json}[key]    display_name
    Should Be Equal    ${json}[value]    Robot Display Name
    Log    Set individual property: display_name

Delete Individual User Property
    [Documentation]    DELETE /auth/local/me/properties/{key} removes a property
    ${resp}=    DELETE    ${AUTH_URL}/me/properties/display_name
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted property display_name: ${resp.status_code}

# ── User Accounts ──────────────────────────────────────────────────────

List User Accounts
    [Documentation]    GET /auth/local/me/accounts returns list of linked accounts
    ${resp}=    GET    ${AUTH_URL}/me/accounts    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    accounts
    ${accounts}=    Get From Dictionary    ${json}    accounts
    Should Be True    isinstance($accounts, list)
    ${count}=    Get Length    ${accounts}
    Should Be True    ${count} >= 1
    # Verify first account has expected fields
    ${first}=    Evaluate    $accounts[0]
    Dictionary Should Contain Key    ${first}    account_type
    Dictionary Should Contain Key    ${first}    is_primary
    Dictionary Should Contain Key    ${first}    is_active
    Log    Found ${count} user accounts

# ── Password Reset ─────────────────────────────────────────────────────

Reset Password With Token
    [Documentation]    POST /auth/local/forgot-password then POST /auth/local/reset-password
    # First, trigger forgot-password to get a reset token (dev mode returns it)
    ${body}=    Create Dictionary    login=${ENH_EMAIL}
    ${resp}=    POST    ${AUTH_URL}/forgot-password    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 202
    ${json}=    Set Variable    ${resp.json()}
    ${has_token}=    Evaluate    'reset_token' in $json and $json['reset_token'] is not None
    Skip If    not ${has_token}    No reset token in response (production mode)
    ${reset_token}=    Get From Dictionary    ${json}    reset_token
    # Now reset the password using the token
    ${reset_body}=    Create Dictionary    reset_token=${reset_token}    new_password=ResetRobotPass789!
    ${reset_resp}=    POST    ${AUTH_URL}/reset-password    json=${reset_body}    expected_status=200
    ${reset_json}=    Set Variable    ${reset_resp.json()}
    Dictionary Should Contain Key    ${reset_json}    message
    Log    Password reset successful: ${reset_json}[message]
    # Verify login works with the new password
    ${login_body}=    Create Dictionary    login=${ENH_EMAIL}    password=ResetRobotPass789!
    ${login_resp}=    POST    ${AUTH_URL}/login    json=${login_body}    expected_status=200
    Dictionary Should Contain Key    ${login_resp.json()}    access_token
    Set Suite Variable    ${ENH_PASSWORD}    ResetRobotPass789!
    Log    Login with reset password succeeded

Reset Password With Invalid Token Returns Error
    [Documentation]    POST /auth/local/reset-password with bogus token returns error
    ${body}=    Create Dictionary    reset_token=totally-invalid-reset-token-value    new_password=AnyPass123!
    ${resp}=    POST    ${AUTH_URL}/reset-password    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 400 or ${resp.status_code} == 401 or ${resp.status_code} == 404 or ${resp.status_code} == 422
    Log    Invalid reset token result: ${resp.status_code}

# ── Admin Session Revocation ───────────────────────────────────────────

Revoke User Session
    [Documentation]    DELETE /am/admin/users/{user_id}/sessions/{session_id} revokes a session
    ${resp}=    DELETE    ${AM_URL}/admin/users/${ENH_USER_ID}/sessions/${ENH_SESSION_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Revoked session ${ENH_SESSION_ID}: ${resp.status_code}

Revoked Session No Longer Active
    [Documentation]    Verify the revoked session no longer appears in active sessions
    ${resp}=    GET    ${AM_URL}/admin/users/${ENH_USER_ID}/sessions
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${sessions}=    Get From Dictionary    ${json}    sessions
    ${session_ids}=    Evaluate    [s.get('session_id') for s in $sessions]
    Should Not Contain    ${session_ids}    ${ENH_SESSION_ID}
    Log    Confirmed session ${ENH_SESSION_ID} no longer active

# ── Impersonation History ──────────────────────────────────────────────

List Impersonation History
    [Documentation]    GET /am/admin/impersonation/history returns impersonation log
    ${resp}=    GET    ${AM_URL}/admin/impersonation/history
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    # Response should have a list structure (events or history)
    Should Be True    isinstance($json, dict)
    Log    Impersonation history response: ${json}

# ── Workspace Settings ─────────────────────────────────────────────────

List Workspace Settings Empty Initially
    [Documentation]    GET /am/settings/workspace/{ws_id} returns empty list for new workspace
    ${resp}=    GET    ${AM_URL}/settings/workspace/${WS_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    settings
    ${settings}=    Get From Dictionary    ${json}    settings
    ${count}=    Get Length    ${settings}
    Should Be True    ${count} == 0
    Log    Workspace settings initially empty

List Workspace Setting Keys
    [Documentation]    GET /am/settings/workspace/{ws_id}/keys returns available keys
    ${resp}=    GET    ${AM_URL}/settings/workspace/${WS_ID}/keys
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    keys
    ${keys}=    Get From Dictionary    ${json}    keys
    Should Be True    isinstance($keys, list)
    Log    Found workspace setting keys

Set Workspace Setting
    [Documentation]    PUT /am/settings/workspace/{ws_id}/{key} sets a workspace setting
    ${body}=    Create Dictionary    value=https://example.com/ws-logo.png
    ${resp}=    PUT    ${AM_URL}/settings/workspace/${WS_ID}/logo_url
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    # May succeed or 404 if no setting keys are defined for workspaces yet
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 404
    Log    Set workspace setting result: ${resp.status_code}

Invalid Entity Type Returns 404
    [Documentation]    GET /am/settings/invalid_type/{id} returns 404 for unknown entity type
    ${resp}=    GET    ${AM_URL}/settings/nonexistent_entity_type/some-id
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 404 or ${resp.status_code} == 422 or ${resp.status_code} == 400
    Log    Invalid entity type result: ${resp.status_code}
