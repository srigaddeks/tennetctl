*** Settings ***
Documentation    Template Designer UI — create template, open designer, add variable, preview.
...              Requires live backend (51734) + frontend (51735).
Library     Browser
Resource    ../keywords/api.resource
Suite Setup       Launch Suite
Suite Teardown    Close Suite

*** Variables ***
${BASE}          http://localhost:51735
${API_BASE}      http://localhost:51734
${KEY_PREFIX}    pw-tmpl

*** Keywords ***
Launch Suite
    New Browser    chromium    headless=true
    New Context    baseURL=${BASE}
    New Page    ${BASE}

Close Suite
    Close Browser    ALL

Open Templates Page
    Go To    ${BASE}/notify/templates
    Wait For Load State    networkidle
    Wait For Elements State    [data-testid="heading-notify-templates"]    visible    timeout=10s

*** Test Cases ***
Templates page loads and nav entry is visible
    [Documentation]    /notify/templates renders and the sidebar nav link is present.
    Open Templates Page
    Get Element    [data-testid="heading-notify-templates"]
    Get Element    [data-testid="nav-notify-templates"]

New template dialog opens
    [Documentation]    Clicking "+ New template" opens the dialog with required fields.
    Open Templates Page
    Click    [data-testid="btn-new-template"]
    Wait For Elements State    [data-testid="input-template-key"]    visible    timeout=5s
    Wait For Elements State    [data-testid="select-template-group"]    visible
    Wait For Elements State    [data-testid="input-template-subject"]    visible
    Wait For Elements State    [data-testid="btn-create-template"]    visible
