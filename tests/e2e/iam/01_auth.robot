*** Settings ***
Documentation    IAM Auth UI — signin / signout / redirect E2E.
...              Drives live backend (51734) + frontend (51735).
...              Creates a test user via API, signs in via UI, checks topbar,
...              signs out, and verifies redirect to signin page.
Library     Browser
Resource    ../keywords/auth.resource
Suite Setup       Launch Suite
Suite Teardown    Close Browser    ALL

*** Variables ***
${TS}           ${EMPTY}
${TEST_EMAIL}   ${EMPTY}
${TEST_PASS}    pass-E2E-1234!

*** Keywords ***
Launch Suite
    ${ts}=    Get Time    epoch
    Set Suite Variable    ${TS}    ${ts}
    Set Suite Variable    ${TEST_EMAIL}    ${AUTH_PREFIX}-${ts}@tennetctl.test
    API Create Test User    ${TEST_EMAIL}    ${TEST_PASS}    E2E User
    New Browser    chromium    headless=True
    New Context
    New Page    about:blank

*** Test Cases ***
Signin Shows User In Topbar
    [Documentation]    Navigate to /auth/signin, fill credentials, submit,
    ...                verify topbar displays the user's display name.
    Open Signin Page
    Signin Via UI    ${TEST_EMAIL}    ${TEST_PASS}
    Assert Topbar Shows User    E2E User

Signout Redirects To Signin
    [Documentation]    Click Sign Out in topbar, verify page goes to /auth/signin
    ...                and the sign-in form is visible (user is logged out).
    Signout Via Topbar
    Wait For Elements State    [data-testid="signin-form"]    visible    timeout=10s
    ${url}=    Get Url
    Should Contain    ${url}    /auth/signin

Protected Page Redirects Unauthenticated User
    [Documentation]    Navigate directly to /vault without a session.
    ...                The app should redirect to /auth/signin.
    Go To    ${FRONTEND_URL}/vault
    Wait For Load State    networkidle
    ${url}=    Get Url
    Should Contain    ${url}    /auth/signin
