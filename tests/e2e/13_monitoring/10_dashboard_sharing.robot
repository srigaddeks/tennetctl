*** Settings ***
Documentation     Dashboard Sharing E2E Tests
Library           Browser
Library           Collections
Library           DateTime

Suite Setup       Start Browser
Suite Teardown    Close Browser


*** Variables ***
${BASE_URL}       http://localhost:51735
${API_URL}        http://localhost:51734
${ADMIN_EMAIL}    admin@example.com
${ADMIN_PASSWORD}    password123
${USER2_EMAIL}    user2@example.com
${USER2_PASSWORD}    password123


*** Keywords ***
Start Browser
    [Documentation]    Launch browser and navigate to app
    New Browser    chromium    headless=false
    New Page      ${BASE_URL}

Close Browser
    [Documentation]    Close browser and cleanup
    Close Browser

Login As Admin
    [Documentation]    Log in as admin user
    Fill Text    css=input[name="email"]    ${ADMIN_EMAIL}
    Fill Text    css=input[name="password"]    ${ADMIN_PASSWORD}
    Click    css=button:has-text("Sign In")
    Wait For Load State    networkidle

Login As User2
    [Documentation]    Log in as second user
    Fill Text    css=input[name="email"]    ${USER2_EMAIL}
    Fill Text    css=input[name="password"]    ${USER2_PASSWORD}
    Click    css=button:has-text("Sign In")
    Wait For Load State    networkidle

Navigate To Dashboards
    [Documentation]    Navigate to monitoring dashboards page
    Click    css=a:has-text("Monitoring")
    Click    css=a:has-text("Dashboards")
    Wait For Load State    networkidle

Navigate To Dashboard Detail
    [Arguments]    ${dashboard_name}
    [Documentation]    Navigate to a specific dashboard
    Click    text=${dashboard_name}
    Wait For Load State    networkidle

Open Share Dialog
    [Documentation]    Open the share dialog
    Click    css=button:has-text("Share")
    Wait For Load State    networkidle

Create Internal Share
    [Arguments]    ${granted_user_email}
    [Documentation]    Create an internal user share
    Open Share Dialog
    Select Options By    css=select[name="scope"]    value    internal_user
    Fill Text    css=input[name="granted_to_user"]    ${granted_user_email}
    Click    css=button:has-text("Grant Access")
    Wait For Load State    networkidle

Verify Share Token Displayed
    [Documentation]    Verify plaintext token is displayed once
    ${token_visible}    Get Text    css=textarea[name="share_token"]
    Should Not Be Empty    ${token_visible}
    Should Contain    ${token_visible}    v1.

Copy Share Token
    [Documentation]    Copy share token to clipboard
    Click    css=button:has-text("Copy Token")
    Wait For Load State    networkidle

Create Public Token Share
    [Arguments]    ${days_to_expire}    ${passphrase}    ${recipient_email}
    [Documentation]    Create a public token share
    Open Share Dialog
    Select Options By    css=select[name="scope"]    value    public_token
    Fill Text    css=input[name="days_to_expire"]    ${days_to_expire}
    Fill Text    css=input[name="passphrase"]    ${passphrase}
    Fill Text    css=input[name="recipient_email"]    ${recipient_email}
    Click    css=button:has-text("Create Token")
    Wait For Load State    networkidle
    Verify Share Token Displayed

View Share Via Token
    [Arguments]    ${token}
    [Documentation]    View a shared dashboard via token
    Go To    ${BASE_URL}/share/dashboard/${token}
    Wait For Load State    networkidle

Enter Passphrase
    [Arguments]    ${passphrase}
    [Documentation]    Enter passphrase on protected share
    Fill Text    css=input[name="passphrase"]    ${passphrase}
    Click    css=button:has-text("Unlock")
    Wait For Load State    networkidle

Attempt Wrong Passphrase
    [Arguments]    ${wrong_passphrase}
    [Documentation]    Attempt to unlock with wrong passphrase
    Fill Text    css=input[name="passphrase"]    ${wrong_passphrase}
    Click    css=button:has-text("Unlock")
    Wait For Load State    networkidle
    Expect Response    status    401

Verify Access Denied
    [Documentation]    Verify access denied message
    ${error_text}    Get Text    css=[role="alert"]
    Should Contain    ${error_text}    Access Denied

Open Share Events Timeline
    [Documentation]    Open the events timeline for a share
    Click    css=button:has-text("View Events")
    Wait For Load State    networkidle

Verify Event In Timeline
    [Arguments]    ${event_kind}
    [Documentation]    Verify event appears in timeline
    ${event_row}    Get Element    xpath=//tr[contains(td, '${event_kind}')]
    Should Not Be Empty    ${event_row}


*** Test Cases ***
Test Internal Share Access
    [Documentation]    Admin creates internal share, user2 gains access
    Login As Admin
    Navigate To Dashboards
    Navigate To Dashboard Detail    Test Dashboard
    Create Internal Share    ${USER2_EMAIL}

    # Switch to user2
    Go To    ${BASE_URL}/logout
    Wait For Load State    networkidle
    Login As User2
    Navigate To Dashboards
    Navigate To Dashboard Detail    Test Dashboard
    # Should succeed now


Test Public Token Share Creation
    [Documentation]    Create public token share and verify token format
    Login As Admin
    Navigate To Dashboards
    Navigate To Dashboard Detail    Test Dashboard
    Create Public Token Share    7    hunter2    recipient@example.com
    Verify Share Token Displayed
    Copy Share Token


Test Passphrase Protected Share
    [Documentation]    Access passphrase-protected share
    Login As Admin
    Navigate To Dashboards
    Navigate To Dashboard Detail    Test Dashboard
    Create Public Token Share    7    hunter2    recipient@example.com
    ${token}    Get Text    css=textarea[name="share_token"]
    Copy Share Token

    # View in incognito
    New Context
    New Page    ${BASE_URL}
    View Share Via Token    ${token}

    # Should require passphrase
    Expect Response    status    401

    # Enter wrong passphrase
    Attempt Wrong Passphrase    wrongpass

    # Enter correct passphrase
    Enter Passphrase    hunter2
    Wait For Load State    networkidle


Test Share Events Timeline
    [Documentation]    Verify share events are recorded
    Login As Admin
    Navigate To Dashboards
    Navigate To Dashboard Detail    Test Dashboard
    Create Internal Share    ${USER2_EMAIL}
    Open Share Events Timeline
    Verify Event In Timeline    Share Granted


Test Revoke Share
    [Documentation]    Revoke share and verify access denied
    Login As Admin
    Navigate To Dashboards
    Navigate To Dashboard Detail    Test Dashboard
    Create Internal Share    ${USER2_EMAIL}

    # Find the share row and click revoke
    Click    css=button[data-action="revoke"]
    Wait For Load State    networkidle

    # Switch to user2
    Go To    ${BASE_URL}/logout
    Wait For Load State    networkidle
    Login As User2
    Navigate To Dashboards
    Navigate To Dashboard Detail    Test Dashboard

    # Should get access denied
    Verify Access Denied
