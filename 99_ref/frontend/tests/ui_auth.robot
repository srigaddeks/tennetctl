*** Settings ***
Documentation       Full UI auth flow tests — register, login, dashboard guard, profile, logout.
...                 Uses Robot Framework Browser library (Playwright / Chromium).
...                 Requires backend (port 8000) and frontend (port 3000) running.

Library             Browser    auto_closing_level=TEST
Library             String

Suite Setup         Suite Init

*** Variables ***
${FRONTEND_URL}     http://localhost:3000
${TIMEOUT}          25s
${TEST_EMAIL}       ${EMPTY}
${TEST_PASSWORD}    UITestPass123!
${ERROR_CSS}        css=.text-red-500

*** Keywords ***

Suite Init
    ${ts}=    Evaluate    str(int(__import__('time').time()))
    Set Suite Variable    ${TEST_EMAIL}    uitest_${ts}@kreesalis.io
    Log    Test run email: ${TEST_EMAIL}

Open Chrome
    New Browser    browser=chromium    headless=False    slowMo=0:00:00.350
    New Context    viewport={'width': 1280, 'height': 800}

Wait For Dashboard
    # Dashboard layout: auth guard fetches /me, then renders sidebar
    Wait For Elements State    css=[data-sidebar="sidebar"]    visible    timeout=${TIMEOUT}
    ${url}=    Get Url
    Should Contain    ${url}    /dashboard

Login Via UI
    [Arguments]    ${email}    ${password}
    New Page    ${FRONTEND_URL}/login
    Wait For Elements State    css=input[type="email"]    visible    timeout=${TIMEOUT}
    Fill Text    css=input[type="email"]    ${email}
    # Login page has only 1 password field — use first/only occurrence
    Fill Text    css=input[placeholder="Password"]    ${password}
    Click    css=button[type="submit"]

Screenshot
    [Arguments]    ${name}
    Take Screenshot    filename=/tmp/robot_screenshots/${name}.png

*** Test Cases ***

# ─────────────────────────────────────────────────────────────────────────────
# 1. Unauthenticated redirect — /dashboard → /login
# ─────────────────────────────────────────────────────────────────────────────

TC01 Unauthenticated Dashboard Access Redirects To Login
    [Documentation]    /dashboard without session must redirect to /login
    [Tags]    auth    guard
    Open Chrome
    New Page    ${FRONTEND_URL}/dashboard
    Wait For Elements State    css=input[type="email"]    visible    timeout=${TIMEOUT}
    ${url}=    Get Url
    Should Contain    ${url}    /login
    Screenshot    01_redirect_to_login

# ─────────────────────────────────────────────────────────────────────────────
# 2. Register a new account
# ─────────────────────────────────────────────────────────────────────────────

TC02 User Can Register A New Account
    [Documentation]    Registration form → auto-login → /dashboard with sidebar
    [Tags]    auth    register
    Open Chrome
    New Page    ${FRONTEND_URL}/register
    Wait For Elements State    css=input[type="email"]    visible    timeout=${TIMEOUT}

    Fill Text    css=input[type="email"]    ${TEST_EMAIL}
    # Register page has 2 password fields — target by placeholder
    Fill Text    css=input[placeholder="Password"]    ${TEST_PASSWORD}
    Fill Text    css=input[placeholder="Confirm Password"]    ${TEST_PASSWORD}
    Screenshot    02_register_form_filled

    Click    css=button[type="submit"]
    Screenshot    03_register_submitted

    Wait For Dashboard
    Screenshot    04_register_landed_dashboard

# ─────────────────────────────────────────────────────────────────────────────
# 3. Short password rejected client-side
# ─────────────────────────────────────────────────────────────────────────────

TC03 Register With Short Password Shows Error
    [Documentation]    Password < 12 chars → error div visible, stay on /register
    [Tags]    auth    register    validation
    Open Chrome
    New Page    ${FRONTEND_URL}/register
    Wait For Elements State    css=input[type="email"]    visible    timeout=${TIMEOUT}

    Fill Text    css=input[type="email"]    short_${TEST_EMAIL}
    Fill Text    css=input[placeholder="Password"]    short1!
    Fill Text    css=input[placeholder="Confirm Password"]    short1!
    Screenshot    05_short_pw_before_submit
    Click    css=button[type="submit"]

    Wait For Elements State    ${ERROR_CSS}    visible    timeout=${TIMEOUT}
    Screenshot    06_short_password_error

    ${url}=    Get Url
    Should Contain    ${url}    /register

# ─────────────────────────────────────────────────────────────────────────────
# 4. Login with valid credentials
# ─────────────────────────────────────────────────────────────────────────────

TC04 User Can Login With Registered Credentials
    [Documentation]    Valid login → /dashboard with sidebar visible
    [Tags]    auth    login
    Open Chrome
    Login Via UI    ${TEST_EMAIL}    ${TEST_PASSWORD}
    Screenshot    07_login_submitted

    Wait For Dashboard
    Screenshot    08_login_on_dashboard

# ─────────────────────────────────────────────────────────────────────────────
# 5. Wrong password shows error
# ─────────────────────────────────────────────────────────────────────────────

TC05 Login With Wrong Password Shows Error
    [Documentation]    Bad credentials → error text visible, stay on /login
    [Tags]    auth    login    validation
    Open Chrome
    Login Via UI    ${TEST_EMAIL}    WrongPassword999!

    Wait For Elements State    ${ERROR_CSS}    visible    timeout=${TIMEOUT}
    Screenshot    09_wrong_password_error

    ${url}=    Get Url
    Should Contain    ${url}    /login

# ─────────────────────────────────────────────────────────────────────────────
# 6. Dashboard renders sidebar and content
# ─────────────────────────────────────────────────────────────────────────────

TC06 Dashboard Renders Sidebar And Main Content
    [Documentation]    Sidebar nav and page heading visible after login
    [Tags]    dashboard    ui
    Open Chrome
    Login Via UI    ${TEST_EMAIL}    ${TEST_PASSWORD}
    Wait For Dashboard
    Screenshot    10_dashboard_sidebar

    Wait For Elements State    css=main h1, main [class*="h1"]    visible    timeout=${TIMEOUT}
    Screenshot    11_dashboard_heading

# ─────────────────────────────────────────────────────────────────────────────
# 7. Profile shows real /me data
# ─────────────────────────────────────────────────────────────────────────────

TC07 Profile Page Shows Real User Email From Backend
    [Documentation]    /settings/profile displays actual email from /me endpoint
    [Tags]    settings    profile    api
    Open Chrome
    Login Via UI    ${TEST_EMAIL}    ${TEST_PASSWORD}
    Wait For Dashboard

    Go To    ${FRONTEND_URL}/settings/profile
    Wait For Elements State    css=h3:has-text("${TEST_EMAIL}")    visible    timeout=${TIMEOUT}
    Screenshot    12_profile_email_visible
    Screenshot    13_profile_full

# ─────────────────────────────────────────────────────────────────────────────
# 8. Logout → session revoked → dashboard blocked
# ─────────────────────────────────────────────────────────────────────────────

TC08 Logout Revokes Session And Blocks Dashboard Access
    [Documentation]    Sign out via sidebar → /login; direct /dashboard re-blocked
    [Tags]    auth    logout    guard
    Open Chrome
    Login Via UI    ${TEST_EMAIL}    ${TEST_PASSWORD}
    Wait For Dashboard
    Screenshot    14_pre_logout

    # Open sidebar footer user dropdown
    Wait For Elements State    css=[data-sidebar="footer"] button    visible    timeout=${TIMEOUT}
    Click    css=[data-sidebar="footer"] button
    Wait For Elements State    text=Sign out    visible    timeout=${TIMEOUT}
    Screenshot    15_user_menu_open

    Click    text=Sign out
    Screenshot    16_sign_out_clicked

    # logoutUser() calls backend revocation + clears cookie → window.location.replace("/login")
    Wait For Elements State    css=input[type="email"]    visible    timeout=${TIMEOUT}
    ${url}=    Get Url
    Should Contain    ${url}    /login
    Screenshot    17_after_logout

    # Direct /dashboard visit must be blocked — auth guard fires fetchMe() → 401 → /login
    Go To    ${FRONTEND_URL}/dashboard
    Wait For Elements State    css=input[type="email"]    visible    timeout=${TIMEOUT}
    ${url}=    Get Url
    Should Contain    ${url}    /login
    Screenshot    18_dashboard_blocked_post_logout
