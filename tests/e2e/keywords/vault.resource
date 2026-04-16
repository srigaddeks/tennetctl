*** Settings ***
Library    Browser
Resource   api.resource

*** Variables ***
${UI_URL}    http://localhost:51735

*** Keywords ***
Open Vault Page
    [Documentation]    Opens /vault in a new page; returns after networkidle.
    New Page    ${UI_URL}/vault
    Wait For Load State    networkidle

Create Secret Via UI
    [Documentation]    Drives the create-secret dialog end-to-end up to the reveal-once show.
    [Arguments]    ${key}    ${value}    ${description}=${EMPTY}
    Click    [data-testid="open-create-secret"]
    Wait For Elements State    [data-testid="create-secret-form"]    visible
    Fill Text    [data-testid="new-secret-key"]       ${key}
    Fill Text    [data-testid="new-secret-value"]     ${value}
    IF    '${description}' != ''
        Fill Text    [data-testid="new-secret-description"]    ${description}
    END
    Click    [data-testid="new-secret-submit"]
    Wait For Elements State    [data-testid="reveal-once"]    visible    timeout=10s

Dismiss Reveal Once
    Click    [data-testid="reveal-once-dismiss"]
    Wait For Elements State    [data-testid="reveal-once"]    detached    timeout=5s

Rotate Secret Via UI
    [Arguments]    ${key}    ${new_value}
    Click    [data-testid="secret-row-rotate-${key}"]
    Wait For Elements State    [data-testid="rotate-secret-form-${key}"]    visible
    Fill Text    [data-testid="rotate-secret-value-${key}"]    ${new_value}
    Click    [data-testid="rotate-secret-submit-${key}"]
    Wait For Elements State    [data-testid="reveal-once"]    visible    timeout=10s

Delete Secret Via UI
    [Arguments]    ${key}
    Click    [data-testid="secret-row-delete-${key}"]
    Wait For Elements State    [data-testid="delete-confirm-${key}"]    visible
    Click    [data-testid="delete-confirm-yes-${key}"]
    Wait For Elements State    [data-testid="secret-row-${key}"]    detached    timeout=10s
