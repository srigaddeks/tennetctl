*** Settings ***
Documentation    Roles API Integration Tests
Resource         common.resource
Suite Setup      Setup Roles Suite

*** Keywords ***
Setup Roles Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    Set Suite Variable    ${PERM_ID}    ${EMPTY}

*** Test Cases ***
List Roles
    [Documentation]    GET /am/roles
    ${resp}=    GET    ${AM_URL}/roles    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, (list, dict))
    Log    Roles response type: ${{type($json).__name__}}

Create Role
    [Documentation]    POST /am/roles
    ${body}=    Create Dictionary
    ...    code=robot_role_${TS}
    ...    name=Robot Role ${TS}
    ...    description=Role created by Robot Framework
    ...    role_level_code=platform
    ${resp}=    POST    ${AM_URL}/roles    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${rid}=    Evaluate    $json.get('id') or $json.get('role_id')
    Set Suite Variable    ${ROLE_ID}    ${rid}
    Log    Created role: ${rid}

Update Role
    [Documentation]    PATCH /am/roles/{role_id}
    ${body}=    Create Dictionary
    ...    name=Robot Role ${TS} Updated
    ...    description=Updated by Robot Framework
    ${resp}=    PATCH    ${AM_URL}/roles/${ROLE_ID}    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[name]    Robot Role ${TS} Updated

Assign Permission To Role
    [Documentation]    POST /am/roles/{role_id}/permissions
    # First get available permissions
    ${resp}=    GET    ${AM_URL}/features    headers=${AUTH_HEADERS}    expected_status=200
    ${flags}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $flags.get('flags', []) if isinstance($flags, dict) else $flags
    IF    len($items) > 0
        ${flag}=    Evaluate    $items[0]
        ${perms}=    Evaluate    $flag.get('permissions', [])
        IF    len($perms) > 0
            ${perm_id}=    Evaluate    $perms[0].get('id')
            ${body}=    Create Dictionary    feature_permission_id=${perm_id}
            ${resp}=    POST    ${AM_URL}/roles/${ROLE_ID}/permissions
            ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
            Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201 or ${resp.status_code} == 409
            Log    Assign permission result: ${resp.status_code}
            IF    ${resp.status_code} == 200 or ${resp.status_code} == 201
                Set Suite Variable    ${PERM_ID}    ${perm_id}
            END
        ELSE
            Log    No permissions found on first flag, skipping    WARN
            Pass Execution    No permissions available to assign
        END
    ELSE
        Log    No feature flags found, skipping    WARN
        Pass Execution    No feature flags available
    END

Revoke Permission From Role
    [Documentation]    DELETE /am/roles/{role_id}/permissions/{permission_id}
    ${has_perm}=    Evaluate    hasattr(type('', (), {}), '') or '${PERM_ID}' != '${EMPTY}'
    IF    '${PERM_ID}' != '${EMPTY}'
        ${resp}=    DELETE    ${AM_URL}/roles/${ROLE_ID}/permissions/${PERM_ID}
        ...    headers=${AUTH_HEADERS}    expected_status=any
        Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
        Log    Revoke permission result: ${resp.status_code}
    ELSE
        Pass Execution    No permission was assigned to revoke
    END

Create Role Without Auth Returns Error
    [Documentation]    POST /am/roles without authentication
    ${body}=    Create Dictionary
    ...    code=noauth_role
    ...    name=No Auth Role
    ...    description=Should fail
    ...    role_level_code=platform
    ${resp}=    POST    ${AM_URL}/roles    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403
