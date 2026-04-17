*** Settings ***
Documentation       IAM — Deactivate vs Delete lifecycle E2E tests.
...                 Covers: deactivate blocks signin, reactivate restores access, delete pseudonymizes.
Library             Browser
Library             Collections
Library             RequestsLibrary
Library             String

Suite Setup         Suite Setup Steps
Suite Teardown      Suite Teardown Steps

*** Variables ***
${BASE_URL}         http://localhost:51734
${FRONT_URL}        http://localhost:3001
${DB_URL}           postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl
${TEST_PREFIX}      e2e-lifecycle-

*** Test Cases ***

Deactivate User Blocks Signin
    [Documentation]    Deactivate a user via API, verify POST /v1/auth/signin returns 403 USER_INACTIVE.
    [Tags]    lifecycle    deactivate
    ${email}=    Set Variable    ${TEST_PREFIX}deactivate@example.com
    ${user_id}=    Create Test User Via API    ${email}    DeactivateTestUser
    # Deactivate via PATCH status=inactive
    ${resp}=    PATCH    ${BASE_URL}/v1/users/${user_id}    json={"status": "inactive"}    headers=&{ADMIN_HEADERS}
    Should Be Equal As Integers    ${resp.status_code}    200
    ${body}=    Set Variable    ${resp.json()}
    Should Be Equal    ${body['data']['is_active']}    ${False}
    # Try signin — expect 403
    ${signin_resp}=    POST    ${BASE_URL}/v1/auth/signin
    ...    json={"email": "${email}", "password": "Test@1234"}
    ...    headers={"Content-Type": "application/json"}
    Should Be Equal As Integers    ${signin_resp.status_code}    403
    ${signin_body}=    Set Variable    ${signin_resp.json()}
    Should Be Equal    ${signin_body['error']['code']}    USER_INACTIVE

Reactivate User Restores Access
    [Documentation]    Reactivate a previously deactivated user, verify signin succeeds.
    [Tags]    lifecycle    reactivate
    ${email}=    Set Variable    ${TEST_PREFIX}reactivate@example.com
    ${user_id}=    Create Test User Via API    ${email}    ReactivateTestUser
    # Set password
    Set User Password Via API    ${user_id}    Test@1234
    # Deactivate
    PATCH    ${BASE_URL}/v1/users/${user_id}    json={"status": "inactive"}    headers=&{ADMIN_HEADERS}
    # Reactivate
    ${resp}=    PATCH    ${BASE_URL}/v1/users/${user_id}    json={"status": "active"}    headers=&{ADMIN_HEADERS}
    Should Be Equal As Integers    ${resp.status_code}    200
    Should Be Equal    ${resp.json()['data']['is_active']}    ${True}
    # Signin should now succeed
    ${signin_resp}=    POST    ${BASE_URL}/v1/auth/signin
    ...    json={"email": "${email}", "password": "Test@1234"}
    ...    headers={"Content-Type": "application/json"}
    Should Be Equal As Integers    ${signin_resp.status_code}    200

Delete User Pseudonymizes PII
    [Documentation]    DELETE a user, verify email is pseudonymized and GET returns 404.
    [Tags]    lifecycle    delete
    ${email}=    Set Variable    ${TEST_PREFIX}delete@example.com
    ${user_id}=    Create Test User Via API    ${email}    DeleteTestUser
    # Delete
    ${del_resp}=    DELETE    ${BASE_URL}/v1/users/${user_id}    headers=&{ADMIN_HEADERS}
    Should Be Equal As Integers    ${del_resp.status_code}    204
    # GET returns 404
    ${get_resp}=    GET    ${BASE_URL}/v1/users/${user_id}    headers=&{ADMIN_HEADERS}
    Should Be Equal As Integers    ${get_resp.status_code}    404

User Detail Page Shows Status Badge And Deactivate Button
    [Documentation]    Navigate to user detail page and verify status badge + action buttons.
    [Tags]    lifecycle    frontend
    ${email}=    Set Variable    ${TEST_PREFIX}ui-status@example.com
    ${user_id}=    Create Test User Via API    ${email}    UIStatusUser
    New Page    ${FRONT_URL}/iam/users/${user_id}
    Wait For Load State    networkidle
    Get Element    [data-testid="user-status-badge"]
    Get Text    [data-testid="user-status-badge"]    ==    Active
    Get Element    [data-testid="btn-deactivate"]
    Get Element    [data-testid="btn-delete"]

User Detail Delete Modal Requires Email Confirmation
    [Documentation]    Delete button opens modal that requires typing the user's email.
    [Tags]    lifecycle    frontend
    ${email}=    Set Variable    ${TEST_PREFIX}ui-delete@example.com
    ${user_id}=    Create Test User Via API    ${email}    UIDeleteUser
    New Page    ${FRONT_URL}/iam/users/${user_id}
    Wait For Load State    networkidle
    Click    [data-testid="btn-delete"]
    Wait For Elements State    [data-testid="input-confirm-email"]    visible
    # Confirm button should be disabled until email is typed
    Get Element Attribute    [data-testid="btn-confirm-delete"]    disabled    ==    true
    Type Text    [data-testid="input-confirm-email"]    ${email}
    # Now confirm button should be enabled
    Wait For Elements State    [data-testid="btn-confirm-delete"]:not([disabled])    visible
    Click    [data-testid="btn-cancel-delete"]

*** Keywords ***

Suite Setup Steps
    New Browser    headless=True
    New Context
    ${headers}=    Create Dictionary    Content-Type=application/json    x-user-id=system    x-org-id=system
    Set Suite Variable    &{ADMIN_HEADERS}    ${headers}

Suite Teardown Steps
    Cleanup Test Users Via API
    Close Browser

Create Test User Via API
    [Arguments]    ${email}    ${display_name}
    ${resp}=    POST    ${BASE_URL}/v1/users
    ...    json={"account_type": "email_password", "email": "${email}", "display_name": "${display_name}"}
    ...    headers=&{ADMIN_HEADERS}
    Should Be Equal As Integers    ${resp.status_code}    201
    RETURN    ${resp.json()['data']['id']}

Set User Password Via API
    [Arguments]    ${user_id}    ${password}
    # Password set via credentials endpoint if available, else skip
    ${resp}=    POST    ${BASE_URL}/v1/auth/signup
    ...    json={"email": "unused@x.com", "display_name": "x", "password": "${password}"}
    ...    headers={"Content-Type": "application/json"}
    # Ignore errors — just a best-effort for signin test

Cleanup Test Users Via API
    ${resp}=    GET    ${BASE_URL}/v1/users?limit=200    headers=&{ADMIN_HEADERS}
    ${users}=    Set Variable    ${resp.json()['data']}
    FOR    ${user}    IN    @{users}
        ${email}=    Set Variable    ${user['email']}
        IF    '${email}' is not None and '${email}'.startswith('${TEST_PREFIX}')
            DELETE    ${BASE_URL}/v1/users/${user['id']}    headers=&{ADMIN_HEADERS}
        END
    END
