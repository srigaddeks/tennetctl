*** Settings ***
Library    RequestsLibrary
Library    Collections

*** Variables ***
${API_URL}    http://localhost:51734

# ── Vault Secrets ─────────────────────────────────────────────────────

*** Keywords ***
API List Vault Keys
    [Documentation]    GET /v1/vault → list of VaultSecretMeta. Returns just the data array.
    Create Session    vault_api    ${API_URL}
    ${r}=    GET On Session    vault_api    /v1/vault
    Should Be Equal As Integers    ${r.status_code}    200
    ${body}=    Set Variable    ${r.json()}
    Should Be True    ${body}[ok]
    RETURN    ${body}[data]

API Delete Vault Key
    [Documentation]    DELETE /v1/vault/{key}. Tolerates 404 (key already gone).
    [Arguments]    ${key}
    Create Session    vault_api    ${API_URL}
    ${r}=    DELETE On Session    vault_api    /v1/vault/${key}
    ...    expected_status=any
    Should Be True    ${r.status_code} in (204, 404)

API Cleanup Vault Prefix
    [Documentation]    Delete every vault secret whose key starts with the given prefix.
    [Arguments]    ${prefix}
    ${keys}=    API List Vault Keys
    FOR    ${entry}    IN    @{keys}
        IF    $entry['key'].startswith('${prefix}')
            API Delete Vault Key    ${entry}[key]
        END
    END

# ── Vault Configs ─────────────────────────────────────────────────────

API List Vault Configs
    [Documentation]    GET /v1/vault-configs → list of VaultConfigMeta. Returns data array.
    Create Session    vault_configs_api    ${API_URL}
    ${r}=    GET On Session    vault_configs_api    /v1/vault-configs
    Should Be Equal As Integers    ${r.status_code}    200
    ${body}=    Set Variable    ${r.json()}
    Should Be True    ${body}[ok]
    RETURN    ${body}[data]

API Delete Vault Config
    [Documentation]    DELETE /v1/vault-configs/{id}. Tolerates 404.
    [Arguments]    ${config_id}
    Create Session    vault_configs_api    ${API_URL}
    ${r}=    DELETE On Session    vault_configs_api    /v1/vault-configs/${config_id}
    ...    expected_status=any
    Should Be True    ${r.status_code} in (204, 404)

API Cleanup Vault Config Prefix
    [Documentation]    Delete every config whose key starts with the given prefix.
    [Arguments]    ${prefix}
    ${configs}=    API List Vault Configs
    FOR    ${entry}    IN    @{configs}
        IF    $entry['key'].startswith('${prefix}')
            API Delete Vault Config    ${entry}[id]
        END
    END
