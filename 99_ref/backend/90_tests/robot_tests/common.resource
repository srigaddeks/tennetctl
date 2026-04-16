*** Settings ***
Library    RequestsLibrary
Library    Collections
Library    String
Library    Process

*** Variables ***
${BASE_URL}              http://localhost:8000/api/v1
${AUTH_URL}              ${BASE_URL}/auth/local
${AM_URL}                ${BASE_URL}/am
${ADMIN_EMAIL}           testuser_1773423062@example.com
${ADMIN_PASSWORD}        NewSecurePassword456!
${ACCESS_TOKEN}          ${EMPTY}
${USER_ID}               ${EMPTY}

*** Keywords ***
Login As Admin
    [Documentation]    Logs in as the admin user and stores token
    ${body}=    Create Dictionary    login=${ADMIN_EMAIL}    password=${ADMIN_PASSWORD}
    ${resp}=    POST    ${AUTH_URL}/login    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${token}=    Get From Dictionary    ${json}    access_token
    Set Suite Variable    ${ACCESS_TOKEN}    ${token}
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    Set Suite Variable    ${AUTH_HEADERS}    ${headers}
    # Get user_id from /me
    ${me_resp}=    GET    ${AUTH_URL}/me    headers=${headers}    expected_status=200
    ${me_json}=    Set Variable    ${me_resp.json()}
    ${uid}=    Get From Dictionary    ${me_json}    user_id
    Set Suite Variable    ${USER_ID}    ${uid}
    # Grant platform_super_admin membership so API key and permission-gated tests pass
    Grant Super Admin    ${uid}

Get Timestamp
    [Documentation]    Returns current epoch timestamp for unique test data
    ${ts}=    Evaluate    str(int(__import__('time').time()))
    RETURN    ${ts}

Register Test User
    [Documentation]    Registers a new test user and returns the user_id
    [Arguments]    ${email}    ${password}=TestPass123!
    ${body}=    Create Dictionary    email=${email}    password=${password}
    ${resp}=    POST    ${AUTH_URL}/register    json=${body}    expected_status=any
    IF    ${resp.status_code} == 200 or ${resp.status_code} == 201
        ${json}=    Set Variable    ${resp.json()}
        ${uid}=    Get From Dictionary    ${json}    user_id
        RETURN    ${uid}
    ELSE
        Log    Registration failed: ${resp.text}    WARN
        RETURN    ${EMPTY}
    END

Grant Super Admin
    [Documentation]    Adds user to platform_super_admin group via direct DB insert
    [Arguments]    ${user_id}
    ${result}=    Run Process    python3
    ...    ${CURDIR}/_grant_super_admin.py    ${user_id}
    Log    Grant super admin result: ${result.stdout}
    Run Keyword If    ${result.rc} != 0    Log    Grant super admin stderr: ${result.stderr}    WARN
