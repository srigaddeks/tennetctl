*** Settings ***
Library    Browser
Resource   api.resource

*** Variables ***
${UI_URL}    http://localhost:51735

*** Keywords ***
Open Vault Secrets Page
    [Documentation]    Opens /vault/secrets; waits for networkidle.
    New Page    ${UI_URL}/vault/secrets
    Wait For Load State    networkidle

Open Vault Configs Page
    [Documentation]    Opens /vault/configs; waits for networkidle.
    New Page    ${UI_URL}/vault/configs
    Wait For Load State    networkidle

Open Vault Page
    [Documentation]    Alias kept for backwards compatibility — opens /vault/secrets.
    Open Vault Secrets Page

# ── Secrets ───────────────────────────────────────────────────────────

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

# ── Configs ───────────────────────────────────────────────────────────

Create Config Via UI
    [Documentation]    Creates a config through the create-config dialog.
    ...                value_type defaults to string; description is optional.
    [Arguments]    ${key}    ${value}    ${value_type}=string    ${description}=${EMPTY}
    Click    [data-testid="open-create-config"]
    Wait For Elements State    [data-testid="create-config-form"]    visible
    Fill Text    [data-testid="new-config-key"]    ${key}
    Select Options By    [data-testid="new-config-type"]    value    ${value_type}
    Fill Text    [data-testid="new-config-value"]    ${value}
    IF    '${description}' != ''
        Fill Text    [data-testid="new-config-description"]    ${description}
    END
    Click    [data-testid="new-config-submit"]
    Wait For Elements State    [data-testid="create-config-form"]    detached    timeout=10s

Edit Config Value Via UI
    [Documentation]    Opens the Edit dialog for the config at ${key} and saves a new value.
    ...                Uses CSS prefix selectors since edit form testids include the config UUID.
    [Arguments]    ${key}    ${new_value}
    Click    [data-testid="config-row-edit-${key}"]
    Wait For Elements State    [data-testid^="edit-config-value-"]    visible    timeout=5s
    Fill Text    [data-testid^="edit-config-value-"]    ${new_value}
    Click    [data-testid^="edit-config-submit-"]
    Wait For Elements State    [data-testid^="edit-config-form-"]    detached    timeout=10s

Delete Config Via UI
    [Arguments]    ${key}
    Click    [data-testid="config-row-delete-${key}"]
    Wait For Elements State    [data-testid="config-delete-confirm-${key}"]    visible
    Click    [data-testid="config-delete-confirm-yes-${key}"]
    Wait For Elements State    [data-testid="config-row-${key}"]    detached    timeout=10s
