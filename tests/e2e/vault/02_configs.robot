*** Settings ***
Documentation    Vault Configs UI — create / edit / delete happy path.
...              Drives a live backend (51734) + frontend (51735).
...              Suite teardown cleans any pw-cfg-* configs via the API.
Library     Browser
Resource    ../keywords/vault.resource
Resource    ../keywords/api.resource
Suite Setup       Launch Config Suite
Suite Teardown    Close Config Suite
Test Teardown     Cleanup Test Configs

*** Variables ***
${KEY_PREFIX}    pw-cfg

*** Keywords ***
Launch Config Suite
    New Browser    chromium    headless=true
    New Context
    Open Vault Configs Page

Close Config Suite
    API Cleanup Vault Config Prefix    ${KEY_PREFIX}
    Close Browser    ALL

Cleanup Test Configs
    API Cleanup Vault Config Prefix    ${KEY_PREFIX}
    Reload
    Wait For Load State    networkidle

*** Test Cases ***
Create String Config Shows In List
    [Documentation]    Create a string config; row appears in table with correct key + value.
    ${ts}=    Get Time    epoch
    ${key}=    Set Variable    ${KEY_PREFIX}-str-${ts}
    ${val}=    Set Variable    hello-${ts}
    Create Config Via UI    ${key}    ${val}    string    e2e smoke
    Wait For Elements State    [data-testid="config-row-${key}"]    visible    timeout=10s
    Get Text    [data-testid="config-value-${key}"]    equal    ${val}

Create Number Config Shows Value
    [Documentation]    Create a number config; value appears as numeric text in the table.
    ${ts}=    Get Time    epoch
    ${key}=    Set Variable    ${KEY_PREFIX}-num-${ts}
    Create Config Via UI    ${key}    60    number
    Wait For Elements State    [data-testid="config-row-${key}"]    visible    timeout=10s
    Get Text    [data-testid="config-value-${key}"]    equal    60

Edit Config Updates Value
    [Documentation]    Create a number config, edit it to a new value, verify the table updates.
    ${ts}=    Get Time    epoch
    ${key}=    Set Variable    ${KEY_PREFIX}-edit-${ts}
    Create Config Via UI    ${key}    60    number
    Wait For Elements State    [data-testid="config-row-${key}"]    visible    timeout=10s
    Edit Config Value Via UI    ${key}    120
    Wait For Load State    networkidle
    Get Text    [data-testid="config-value-${key}"]    equal    120

Delete Config Removes Row
    [Documentation]    Delete via confirm dialog; row detaches from DOM and is absent from API.
    ${ts}=    Get Time    epoch
    ${key}=    Set Variable    ${KEY_PREFIX}-del-${ts}
    Create Config Via UI    ${key}    to-be-deleted    string
    Wait For Elements State    [data-testid="config-row-${key}"]    visible    timeout=10s
    Delete Config Via UI    ${key}
    Wait For Elements State    [data-testid="config-row-${key}"]    detached    timeout=5s
    ${configs}=    API List Vault Configs
    FOR    ${entry}    IN    @{configs}
        Should Not Be Equal    ${entry}[key]    ${key}
    END
