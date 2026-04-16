*** Settings ***
Library    Browser
Suite Setup    Open TennetCTL Frontend
Suite Teardown    Close Browser    ALL

*** Variables ***
${FRONTEND_URL}    http://localhost:51735

*** Keywords ***
Open TennetCTL Frontend
    New Browser    chromium    headless=true
    New Page    ${FRONTEND_URL}
    Wait For Load State    networkidle

*** Test Cases ***
Frontend Loads Successfully
    [Documentation]    Verify the frontend shell loads and renders the TennetCTL heading.
    Get Title    contains    TennetCTL

Page Has TennetCTL Heading
    [Documentation]    Verify the h1 heading contains TennetCTL.
    Get Text    [data-testid="heading"]    contains    TennetCTL

Page Has Developer Platform Subtitle
    [Documentation]    Verify the subtitle text is present.
    Get Text    css=main p.text-lg    contains    Developer Platform
