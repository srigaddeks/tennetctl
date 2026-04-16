*** Settings ***
Documentation    API Key Management Integration Tests
Resource         common.resource
Suite Setup      Login As Admin

*** Variables ***
${API_KEYS_URL}    ${AM_URL}/api-keys

*** Test Cases ***
Create API Key
    [Documentation]    POST /am/api-keys — create a new API key
    ${body}=    Create Dictionary    name=Robot Test Key
    ${resp}=    POST    ${API_KEYS_URL}    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    api_key
    Dictionary Should Contain Key    ${json}    key_prefix
    Dictionary Should Contain Key    ${json}    name
    Should Start With    ${json}[api_key]    kctl_
    Should Be Equal    ${json}[name]    Robot Test Key
    Set Suite Variable    ${API_KEY_ID}    ${json}[id]
    Set Suite Variable    ${API_KEY_FULL}    ${json}[api_key]
    Set Suite Variable    ${API_KEY_PREFIX}    ${json}[key_prefix]
    Log    Created API key: ${json}[key_prefix]

List API Keys
    [Documentation]    GET /am/api-keys — list user's API keys
    ${resp}=    GET    ${API_KEYS_URL}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    Should Be True    ${json}[total] >= 1

Get API Key By ID
    [Documentation]    GET /am/api-keys/{key_id} — get key details
    ${resp}=    GET    ${API_KEYS_URL}/${API_KEY_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${API_KEY_ID}
    Should Be Equal    ${json}[status]    active
    Should Be Equal    ${json}[key_prefix]    ${API_KEY_PREFIX}

Authenticate With API Key To Get Me
    [Documentation]    Use API key as Bearer token to access GET /auth/local/me
    ${api_headers}=    Create Dictionary    Authorization=Bearer ${API_KEY_FULL}
    ${resp}=    GET    ${AUTH_URL}/me    headers=${api_headers}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    user_id
    Should Be Equal    ${json}[user_id]    ${USER_ID}
    # Verify API key response headers
    Should Be Equal    ${resp.headers}[X-Auth-Type]    api_key

API Key To Get Properties Works
    [Documentation]    API key can access GET /auth/local/me/properties
    ${api_headers}=    Create Dictionary    Authorization=Bearer ${API_KEY_FULL}
    ${resp}=    GET    ${AUTH_URL}/me/properties    headers=${api_headers}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    properties

API Key To Logout Is Blocked
    [Documentation]    API key cannot access POST /auth/local/logout
    ${api_headers}=    Create Dictionary    Authorization=Bearer ${API_KEY_FULL}
    ${body}=    Create Dictionary    refresh_token=dummy
    ${resp}=    POST    ${AUTH_URL}/logout    json=${body}    headers=${api_headers}    expected_status=403

API Key To Change Password Is Blocked
    [Documentation]    API key cannot access PUT /auth/local/me/password
    ${api_headers}=    Create Dictionary    Authorization=Bearer ${API_KEY_FULL}
    ${body}=    Create Dictionary    current_password=x    new_password=y
    ${resp}=    PUT    ${AUTH_URL}/me/password    json=${body}    headers=${api_headers}    expected_status=403

API Key To Impersonation Start Is Blocked
    [Documentation]    API key cannot access POST /am/impersonation/start
    ${api_headers}=    Create Dictionary    Authorization=Bearer ${API_KEY_FULL}
    ${body}=    Create Dictionary    target_user_id=${USER_ID}
    ${resp}=    POST    ${AM_URL}/impersonation/start    json=${body}    headers=${api_headers}    expected_status=403

API Key To Create API Key Is Blocked
    [Documentation]    API key cannot create another API key (no key-creating-keys)
    ${api_headers}=    Create Dictionary    Authorization=Bearer ${API_KEY_FULL}
    ${body}=    Create Dictionary    name=Nested Key
    ${resp}=    POST    ${API_KEYS_URL}    json=${body}    headers=${api_headers}    expected_status=403

Create API Key With Expiry
    [Documentation]    POST /am/api-keys — create with expires_in_days
    ${body}=    Create Dictionary    name=Expiring Key    expires_in_days=${30}
    ${resp}=    POST    ${API_KEYS_URL}    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Equal    ${json}[expires_at]    ${None}
    Set Suite Variable    ${EXPIRING_KEY_ID}    ${json}[id]

Rotate API Key
    [Documentation]    POST /am/api-keys/{key_id}/rotate — rotate returns new key
    ${resp}=    POST    ${API_KEYS_URL}/${EXPIRING_KEY_ID}/rotate    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    api_key
    Should Start With    ${json}[api_key]    kctl_
    Should Not Be Equal    ${json}[id]    ${EXPIRING_KEY_ID}
    Set Suite Variable    ${ROTATED_KEY_ID}    ${json}[id]
    Set Suite Variable    ${ROTATED_KEY_FULL}    ${json}[api_key]

Rotated Key Old Key Is Revoked
    [Documentation]    After rotation, old key should be revoked
    ${resp}=    GET    ${API_KEYS_URL}/${EXPIRING_KEY_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[status]    revoked

Rotated Key New Key Works
    [Documentation]    New rotated key should authenticate
    ${api_headers}=    Create Dictionary    Authorization=Bearer ${ROTATED_KEY_FULL}
    ${resp}=    GET    ${AUTH_URL}/me    headers=${api_headers}    expected_status=200

Revoke API Key
    [Documentation]    PATCH /am/api-keys/{key_id}/revoke — revoke a key
    ${body}=    Create Dictionary    reason=Testing revocation
    ${resp}=    PATCH    ${API_KEYS_URL}/${API_KEY_ID}/revoke    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[status]    revoked
    Should Be Equal    ${json}[revoke_reason]    Testing revocation

Revoked Key Cannot Authenticate
    [Documentation]    Revoked API key returns 401
    ${api_headers}=    Create Dictionary    Authorization=Bearer ${API_KEY_FULL}
    ${resp}=    GET    ${AUTH_URL}/me    headers=${api_headers}    expected_status=401

Delete API Key
    [Documentation]    DELETE /am/api-keys/{key_id} — soft delete
    ${resp}=    DELETE    ${API_KEYS_URL}/${ROTATED_KEY_ID}    headers=${AUTH_HEADERS}    expected_status=204

Deleted Key Not Found
    [Documentation]    Deleted key returns 404
    ${resp}=    GET    ${API_KEYS_URL}/${ROTATED_KEY_ID}    headers=${AUTH_HEADERS}    expected_status=404

API Key Audit Trail
    [Documentation]    Verify audit events contain api_key entries
    ${resp}=    GET    ${AM_URL}/admin/audit    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    # Verify at least one api_key audit event exists
    ${events}=    Get From Dictionary    ${json}    events
    ${found}=    Set Variable    ${FALSE}
    FOR    ${event}    IN    @{events}
        IF    '${event}[entity_type]' == 'api_key'
            ${found}=    Set Variable    ${TRUE}
            BREAK
        END
    END
    Should Be True    ${found}    No api_key audit events found
