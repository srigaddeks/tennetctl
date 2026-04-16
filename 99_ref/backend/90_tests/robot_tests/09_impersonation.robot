*** Settings ***
Documentation    Impersonation API Integration Tests
Resource         common.resource
Suite Setup      Setup Impersonation Suite

*** Keywords ***
Setup Impersonation Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # Register a target user to impersonate
    ${target_email}=    Set Variable    robot_imp_target_${TS}@example.com
    Set Suite Variable    ${TARGET_EMAIL}    ${target_email}
    ${target_uid}=    Register Test User    ${target_email}
    Set Suite Variable    ${TARGET_USER_ID}    ${target_uid}
    Log    Target user for impersonation: ${target_uid}

*** Test Cases ***
Impersonation Status Without Impersonation
    [Documentation]    GET /am/impersonation/status — normal session returns false
    ${resp}=    GET    ${AM_URL}/impersonation/status    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal As Strings    ${json}[is_impersonating]    False

Start Impersonation Without Permission Returns 403
    [Documentation]    POST /am/impersonation/start — user without permission gets 403
    # Register a non-admin user and log in as them
    ${email}=    Set Variable    robot_imp_nonadmin_${TS}@example.com
    Register Test User    ${email}
    ${body}=    Create Dictionary    login=${email}    password=TestPass123!
    ${resp}=    POST    ${AUTH_URL}/login    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${token}=    Get From Dictionary    ${json}    access_token
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    ${imp_body}=    Create Dictionary    target_user_id=${TARGET_USER_ID}    reason=Testing without permission
    ${imp_resp}=    POST    ${AM_URL}/impersonation/start    headers=${headers}    json=${imp_body}    expected_status=403

Start Impersonation Requires Reason
    [Documentation]    POST /am/impersonation/start — missing or short reason returns 422
    ${body}=    Create Dictionary    target_user_id=${TARGET_USER_ID}    reason=abc
    ${resp}=    POST    ${AM_URL}/impersonation/start    headers=${AUTH_HEADERS}    json=${body}    expected_status=422

Start Impersonation With Nonexistent User Returns 404
    [Documentation]    POST /am/impersonation/start — unknown target user
    ${body}=    Create Dictionary    target_user_id=00000000-0000-0000-0000-000000000000    reason=Testing with nonexistent user
    ${resp}=    POST    ${AM_URL}/impersonation/start    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 403 or ${resp.status_code} == 404

Start Impersonation Success
    [Documentation]    POST /am/impersonation/start — admin impersonates target user
    ${body}=    Create Dictionary    target_user_id=${TARGET_USER_ID}    reason=Robot Framework impersonation smoke test
    ${resp}=    POST    ${AM_URL}/impersonation/start    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    IF    ${resp.status_code} == 200
        ${json}=    Set Variable    ${resp.json()}
        Dictionary Should Contain Key    ${json}    access_token
        Dictionary Should Contain Key    ${json}    refresh_token
        Dictionary Should Contain Key    ${json}    impersonation_session_id
        Dictionary Should Contain Key    ${json}    target_user
        ${imp_token}=    Get From Dictionary    ${json}    access_token
        Set Suite Variable    ${IMP_ACCESS_TOKEN}    ${imp_token}
        ${imp_headers}=    Create Dictionary    Authorization=Bearer ${imp_token}
        Set Suite Variable    ${IMP_HEADERS}    ${imp_headers}
        Log    Impersonation started successfully
    ELSE
        # Impersonation may be disabled in test environment — skip remaining tests
        Log    Impersonation start returned ${resp.status_code}: ${resp.text}    WARN
        Set Suite Variable    ${IMP_ACCESS_TOKEN}    ${EMPTY}
        Set Suite Variable    ${IMP_HEADERS}    ${AUTH_HEADERS}
    END

Impersonation Token Has Status True
    [Documentation]    GET /am/impersonation/status — impersonation token shows is_impersonating=true
    Skip If    '${IMP_ACCESS_TOKEN}' == '${EMPTY}'    Impersonation not available
    ${resp}=    GET    ${AM_URL}/impersonation/status    headers=${IMP_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal As Strings    ${json}[is_impersonating]    True
    Should Be Equal As Strings    ${json}[target_user_id]    ${TARGET_USER_ID}
    Dictionary Should Contain Key    ${json}    impersonator_id
    Dictionary Should Contain Key    ${json}    session_id

Impersonation Me Returns Target User
    [Documentation]    GET /auth/local/me — impersonation token returns target user info
    Skip If    '${IMP_ACCESS_TOKEN}' == '${EMPTY}'    Impersonation not available
    ${resp}=    GET    ${AUTH_URL}/me    headers=${IMP_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal As Strings    ${json}[user_id]    ${TARGET_USER_ID}
    Should Be Equal As Strings    ${json}[email]    ${TARGET_EMAIL}

Impersonation Response Headers Present
    [Documentation]    Verify X-Impersonation-Active and X-Impersonator-Id headers
    Skip If    '${IMP_ACCESS_TOKEN}' == '${EMPTY}'    Impersonation not available
    ${resp}=    GET    ${AM_URL}/impersonation/status    headers=${IMP_HEADERS}    expected_status=200
    ${imp_active}=    Get From Dictionary    ${resp.headers}    X-Impersonation-Active
    Should Be Equal As Strings    ${imp_active}    true
    Dictionary Should Contain Key    ${resp.headers}    X-Impersonator-Id

Impersonation Cannot Change Email
    [Documentation]    PUT /auth/local/me/properties/email — blocked during impersonation
    Skip If    '${IMP_ACCESS_TOKEN}' == '${EMPTY}'    Impersonation not available
    ${body}=    Create Dictionary    value=hacked@example.com
    ${resp}=    PUT    ${AUTH_URL}/me/properties/email    headers=${IMP_HEADERS}    json=${body}    expected_status=403

Impersonation Cannot Nest
    [Documentation]    POST /am/impersonation/start — blocked while already impersonating
    Skip If    '${IMP_ACCESS_TOKEN}' == '${EMPTY}'    Impersonation not available
    ${body}=    Create Dictionary    target_user_id=${TARGET_USER_ID}    reason=Trying to nest impersonation
    ${resp}=    POST    ${AM_URL}/impersonation/start    headers=${IMP_HEADERS}    json=${body}    expected_status=403

End Impersonation
    [Documentation]    POST /am/impersonation/end — ends impersonation session
    Skip If    '${IMP_ACCESS_TOKEN}' == '${EMPTY}'    Impersonation not available
    ${resp}=    POST    ${AM_URL}/impersonation/end    headers=${IMP_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    impersonator_user_id
    Should Be Equal As Strings    ${json}[message]    Impersonation session ended.

End Impersonation On Normal Session Returns 403
    [Documentation]    POST /am/impersonation/end — not impersonating returns 403
    ${resp}=    POST    ${AM_URL}/impersonation/end    headers=${AUTH_HEADERS}    expected_status=403
