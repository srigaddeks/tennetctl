*** Settings ***
Documentation    Notify UI smoke tests — campaigns, deliveries, send API, preferences pages all render.
...              Requires live backend (51734) + frontend (51735).
Library     Browser
Resource    ../keywords/api.resource
Suite Setup       Launch Suite
Suite Teardown    Close Suite

*** Variables ***
${BASE}    http://localhost:51735

*** Keywords ***
Launch Suite
    New Browser    chromium    headless=true
    New Context    baseURL=${BASE}
    New Page    ${BASE}

Close Suite
    Close Browser    ALL

Open Page And Wait
    [Arguments]    ${path}    ${testid}
    Go To    ${BASE}${path}
    Wait For Load State    networkidle
    Wait For Elements State    [data-testid="${testid}"]    visible    timeout=10s

*** Test Cases ***
Campaigns page loads
    [Documentation]    /notify/campaigns renders heading and new campaign button.
    Open Page And Wait    /notify/campaigns    heading-notify-campaigns
    Get Element    [data-testid="nav-notify-campaigns"]
    Get Element    [data-testid="btn-new-campaign"]

Deliveries page loads with filters
    [Documentation]    /notify/deliveries renders heading and status/channel filter controls.
    Open Page And Wait    /notify/deliveries    heading-notify-deliveries
    Get Element    [data-testid="nav-notify-deliveries"]
    Get Element    [data-testid="select-delivery-status"]
    Get Element    [data-testid="select-delivery-channel"]

Send API page loads
    [Documentation]    /notify/send renders heading and the test-send form.
    Open Page And Wait    /notify/send    heading-notify-send
    Get Element    [data-testid="nav-notify-send"]
    Get Element    [data-testid="input-send-template-key"]
    Get Element    [data-testid="input-send-recipient"]
    Get Element    [data-testid="select-send-channel"]
    Get Element    [data-testid="btn-send"]

Preferences page loads
    [Documentation]    /notify/preferences renders the preferences heading and preference grid.
    Open Page And Wait    /notify/preferences    heading-notify-preferences
    Get Element    [data-testid="nav-notify-preferences"]
