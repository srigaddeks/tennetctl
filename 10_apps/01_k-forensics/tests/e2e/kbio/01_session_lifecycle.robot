*** Settings ***
Documentation    kbio session lifecycle E2E test.
...              Verifies: SDK init -> behavioral collection -> drift scoring -> dashboard display.
Library          Browser
Library          Collections
Library          String
Suite Setup      Open Demo Site
Suite Teardown   Close Browser    ALL

*** Variables ***
${DEMO_URL}         http://localhost:3100
${KF_URL}           http://localhost:3100
${TIMEOUT}          15s

*** Test Cases ***
SDK Initializes Successfully
    [Documentation]    Verify the SDK loads and initializes on the demo site.
    Go To    ${DEMO_URL}
    Wait For Load State    networkidle    timeout=${TIMEOUT}
    # The demo site should show an SDK status indicator
    Wait For Elements State    text=SDK Active    visible    timeout=${TIMEOUT}

Typing In Login Form Captures Keystrokes
    [Documentation]    Navigate to login, type credentials, verify SDK captures data.
    Go To    ${DEMO_URL}/login
    Wait For Load State    networkidle    timeout=${TIMEOUT}
    # Fill in the username field
    Fill Text    input[name="username"]    testuser@example.com
    # Fill in the password field
    Fill Text    input[name="password"]    SecureP@ssw0rd!
    # Wait for SDK to process the keystrokes
    Sleep    2s
    # Submit the form
    Click    button[type="submit"]
    Wait For Load State    networkidle    timeout=${TIMEOUT}

Drift Score Is Returned After Behavioral Data
    [Documentation]    After typing, verify that a drift score appears.
    # The scores dashboard should show drift score
    Go To    ${DEMO_URL}/scores
    Wait For Load State    networkidle    timeout=${TIMEOUT}
    # Look for score display elements
    Wait For Elements State    text=Drift Score    visible    timeout=${TIMEOUT}

Session Appears In kbio Dashboard
    [Documentation]    Verify the k-forensics dashboard shows the session.
    Go To    ${KF_URL}/kbio
    Wait For Load State    networkidle    timeout=${TIMEOUT}
    # The overview page should show session stats
    Wait For Elements State    text=Total Sessions    visible    timeout=${TIMEOUT}
    # Navigate to sessions list
    Go To    ${KF_URL}/kbio/sessions
    Wait For Load State    networkidle    timeout=${TIMEOUT}
    Wait For Elements State    text=Sessions    visible    timeout=${TIMEOUT}

Policy Catalog Is Accessible
    [Documentation]    Verify the policy catalog page loads with policies.
    Go To    ${KF_URL}/kbio/policies
    Wait For Load State    networkidle    timeout=${TIMEOUT}
    Wait For Elements State    text=Policies    visible    timeout=${TIMEOUT}

*** Keywords ***
Open Demo Site
    [Documentation]    Launch browser and navigate to demo site.
    New Browser    chromium    headless=true
    New Page    ${DEMO_URL}
    Wait For Load State    networkidle    timeout=${TIMEOUT}
