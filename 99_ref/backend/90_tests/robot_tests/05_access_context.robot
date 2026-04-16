*** Settings ***
Documentation    Access Context API Integration Tests
Resource         common.resource
Suite Setup      Login As Admin

*** Test Cases ***
Get Access Context
    [Documentation]    GET /am/access
    ${resp}=    GET    ${AM_URL}/access    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    user_id
    Dictionary Should Contain Key    ${json}    tenant_key
    Dictionary Should Contain Key    ${json}    platform
    Log    Access context keys: ${{list($json.keys())}}

Access Context Has Platform Actions
    [Documentation]    Verify platform section contains actions
    ${resp}=    GET    ${AM_URL}/access    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${platform}=    Get From Dictionary    ${json}    platform
    Dictionary Should Contain Key    ${platform}    actions
    ${actions}=    Get From Dictionary    ${platform}    actions
    ${count}=    Get Length    ${actions}
    Should Be True    ${count} > 0
    Log    Platform actions count: ${count}

Access Context User ID Matches
    [Documentation]    Verify the user_id in context matches the logged-in user
    ${resp}=    GET    ${AM_URL}/access    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[user_id]    ${USER_ID}

Access Context Without Auth Returns Error
    [Documentation]    GET /am/access without authentication
    ${resp}=    GET    ${AM_URL}/access    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403
