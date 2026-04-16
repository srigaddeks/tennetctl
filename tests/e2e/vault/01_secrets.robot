*** Settings ***
Documentation    Vault UI — CRUD happy path + reveal-once enforcement.
...              Drives a live backend (51734) + frontend (51735). Suite teardown
...              cleans any pw-vault-* keys via the API.
Library     Browser
Resource    ../keywords/vault.resource
Resource    ../keywords/api.resource
Suite Setup       Launch Suite
Suite Teardown    Close Suite
Test Teardown     Cleanup Test Secrets

*** Variables ***
${KEY_PREFIX}    pw-vault

*** Keywords ***
Launch Suite
    New Browser    chromium    headless=true
    New Context
    Open Vault Page

Close Suite
    API Cleanup Vault Prefix    ${KEY_PREFIX}
    Close Browser    ALL

Cleanup Test Secrets
    API Cleanup Vault Prefix    ${KEY_PREFIX}
    # Reload so stale dialogs / cached rows don't leak between tests.
    Reload
    Wait For Load State    networkidle

Body Should Not Contain
    [Documentation]    Assert the page body text does NOT contain the given sentinel.
    [Arguments]    ${sentinel}
    ${count}=    Get Element Count    body >> text=${sentinel}
    Should Be Equal As Integers    ${count}    0
    ...    msg=sentinel ${sentinel} still present in DOM (count=${count})

*** Test Cases ***
Create Secret Shows Value Once
    [Documentation]    POST via UI, reveal-once shows the plaintext, dismiss unmounts it,
    ...                the value is absent from the DOM, and the new row is visible.
    ${ts}=     Get Time    epoch
    ${key}=    Set Variable    ${KEY_PREFIX}-${ts}
    ${val}=    Set Variable    hunter-${ts}
    Create Secret Via UI    ${key}    ${val}    e2e smoke
    Get Text    [data-testid="reveal-once-value"]    equal    ${val}
    Dismiss Reveal Once
    Wait For Load State    networkidle
    Body Should Not Contain    ${val}
    Wait For Elements State    [data-testid="secret-row-${key}"]    visible

Rotate Secret Bumps Version
    [Documentation]    Create at v1, rotate to v2, reveal-once shows the new value once,
    ...                and the row shows v2 after dismiss.
    ${ts}=     Get Time    epoch
    ${key}=    Set Variable    ${KEY_PREFIX}-rot-${ts}
    ${v1}=     Set Variable    v1-${ts}
    ${v2}=     Set Variable    v2-${ts}
    Create Secret Via UI    ${key}    ${v1}
    Dismiss Reveal Once
    Rotate Secret Via UI    ${key}    ${v2}
    Get Text    [data-testid="reveal-once-value"]    equal    ${v2}
    Dismiss Reveal Once
    Wait For Load State    networkidle
    # The row sits in a tr — v2 badge appears next to the key.
    Get Text    xpath=//tr[.//*[@data-testid="secret-row-${key}"]]    contains    v2
    Body Should Not Contain    ${v1}
    Body Should Not Contain    ${v2}

Delete Secret Removes Row
    [Documentation]    Delete via confirm dialog; row detaches and API no longer returns it.
    ${ts}=     Get Time    epoch
    ${key}=    Set Variable    ${KEY_PREFIX}-del-${ts}
    Create Secret Via UI    ${key}    bye-${ts}
    Dismiss Reveal Once
    Delete Secret Via UI    ${key}
    Wait For Elements State    [data-testid="secret-row-${key}"]    detached    timeout=5s
    ${keys}=    API List Vault Keys
    FOR    ${entry}    IN    @{keys}
        Should Not Be Equal    ${entry}[key]    ${key}
    END

Reveal Once Is Truly Once
    [Documentation]    After dismiss + full page reload, the sentinel must not reappear
    ...                and the list API must never carry 'value' / 'ciphertext' fields.
    ${ts}=     Set Variable    ${{int(time.time() * 1000)}}
    ${key}=    Set Variable    ${KEY_PREFIX}-rev-${ts}
    ${sentinel}=    Set Variable    sentinel-${ts}
    Create Secret Via UI    ${key}    ${sentinel}
    Dismiss Reveal Once
    Reload
    Wait For Load State    networkidle
    Body Should Not Contain    ${sentinel}
    ${keys}=    API List Vault Keys
    FOR    ${entry}    IN    @{keys}
        Dictionary Should Not Contain Key    ${entry}    value
        Dictionary Should Not Contain Key    ${entry}    ciphertext
        Dictionary Should Not Contain Key    ${entry}    wrapped_dek
        Dictionary Should Not Contain Key    ${entry}    nonce
    END
