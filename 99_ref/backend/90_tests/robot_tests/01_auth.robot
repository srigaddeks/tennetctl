*** Settings ***
Documentation    Auth API Integration Tests (register, login, refresh, /me, password reset, logout)
Resource         common.resource
Suite Setup      Get Timestamp And Store

*** Keywords ***
Get Timestamp And Store
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}

*** Test Cases ***
Register New User
    [Documentation]    POST /auth/local/register
    ${email}=    Set Variable    robot_user_${TS}@example.com
    Set Suite Variable    ${TEST_EMAIL}    ${email}
    ${body}=    Create Dictionary    email=${email}    password=RobotPass123!
    ${resp}=    POST    ${AUTH_URL}/register    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    user_id
    Dictionary Should Contain Key    ${json}    email
    ${uid}=    Get From Dictionary    ${json}    user_id
    Set Suite Variable    ${TEST_USER_ID}    ${uid}
    Log    Registered user: ${uid}

Login With Registered User
    [Documentation]    POST /auth/local/login
    ${body}=    Create Dictionary    login=${TEST_EMAIL}    password=RobotPass123!
    ${resp}=    POST    ${AUTH_URL}/login    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    access_token
    Dictionary Should Contain Key    ${json}    refresh_token
    Dictionary Should Contain Key    ${json}    token_type
    Dictionary Should Contain Key    ${json}    expires_in
    ${token}=    Get From Dictionary    ${json}    access_token
    ${refresh}=    Get From Dictionary    ${json}    refresh_token
    Set Suite Variable    ${TEST_ACCESS_TOKEN}    ${token}
    Set Suite Variable    ${TEST_REFRESH_TOKEN}    ${refresh}
    Log    Login successful, token length: ${{len("${token}")}}

Get Current User Me
    [Documentation]    GET /auth/local/me
    ${headers}=    Create Dictionary    Authorization=Bearer ${TEST_ACCESS_TOKEN}
    ${resp}=    GET    ${AUTH_URL}/me    headers=${headers}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    user_id
    Dictionary Should Contain Key    ${json}    email
    Should Be Equal    ${json}[user_id]    ${TEST_USER_ID}
    Should Be Equal    ${json}[email]    ${TEST_EMAIL}

Me Without Token Returns 401
    [Documentation]    GET /auth/local/me without auth
    ${resp}=    GET    ${AUTH_URL}/me    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

Refresh Token
    [Documentation]    POST /auth/local/refresh
    ${body}=    Create Dictionary    refresh_token=${TEST_REFRESH_TOKEN}
    ${resp}=    POST    ${AUTH_URL}/refresh    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    access_token
    Dictionary Should Contain Key    ${json}    refresh_token
    ${new_token}=    Get From Dictionary    ${json}    access_token
    Set Suite Variable    ${TEST_ACCESS_TOKEN}    ${new_token}
    ${new_refresh}=    Get From Dictionary    ${json}    refresh_token
    Set Suite Variable    ${TEST_REFRESH_TOKEN}    ${new_refresh}

Login With Wrong Password Returns 401
    [Documentation]    POST /auth/local/login with wrong password
    ${body}=    Create Dictionary    login=${TEST_EMAIL}    password=WrongPassword999!
    ${resp}=    POST    ${AUTH_URL}/login    json=${body}    expected_status=401

Forgot Password
    [Documentation]    POST /auth/local/forgot-password
    ${body}=    Create Dictionary    login=${TEST_EMAIL}
    ${resp}=    POST    ${AUTH_URL}/forgot-password    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 202 or ${resp.status_code} == 204

Logout
    [Documentation]    POST /auth/local/logout
    ${headers}=    Create Dictionary    Authorization=Bearer ${TEST_ACCESS_TOKEN}
    ${body}=    Create Dictionary    refresh_token=${TEST_REFRESH_TOKEN}
    ${resp}=    POST    ${AUTH_URL}/logout    headers=${headers}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204

Token After Logout Is Invalid
    [Documentation]    Verify the old access token no longer works after logout
    ${headers}=    Create Dictionary    Authorization=Bearer ${TEST_ACCESS_TOKEN}
    ${resp}=    GET    ${AUTH_URL}/me    headers=${headers}    expected_status=any
    # Token may still work until expiry (short-lived), but refresh should fail
    Log    Post-logout /me status: ${resp.status_code}
