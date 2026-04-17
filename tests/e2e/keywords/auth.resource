*** Settings ***
Library     Browser
Library     Collections
Library     RequestsLibrary

*** Variables ***
${FRONTEND_URL}    http://localhost:51735
${BACKEND_URL}     http://localhost:51734
${AUTH_PREFIX}     e2e-auth

*** Keywords ***
Open Signin Page
    Go To    ${FRONTEND_URL}/auth/signin
    Wait For Elements State    [data-testid="signin-form"]    visible    timeout=10s

Signin Via UI
    [Arguments]    ${email}    ${password}
    Fill Text    [data-testid="signin-email"]    ${email}
    Fill Text    [data-testid="signin-password"]    ${password}
    Click    [data-testid="signin-submit"]
    Wait For Load State    networkidle

Assert Topbar Shows User
    [Arguments]    ${expected_text}
    Wait For Elements State    [data-testid="topbar-user-name"]    visible    timeout=8s
    ${text}=    Get Text    [data-testid="topbar-user-name"]
    Should Contain    ${text}    ${expected_text}

Assert Topbar Shows Signin Link
    Wait For Elements State    [data-testid="topbar-signin"]    visible    timeout=8s

Signout Via Topbar
    Wait For Elements State    [data-testid="topbar-signout"]    visible    timeout=8s
    Click    [data-testid="topbar-signout"]
    Wait For Load State    networkidle

API Create Test User
    [Arguments]    ${email}    ${password}    ${display_name}
    ${body}=    Create Dictionary    email=${email}    password=${password}    display_name=${display_name}
    ${session}=    RequestsLibrary.Create Session    backend    ${BACKEND_URL}
    ${resp}=    POST On Session    backend    /v1/auth/signup    json=${body}    expected_status=201
    RETURN    ${resp.json()['data']}
