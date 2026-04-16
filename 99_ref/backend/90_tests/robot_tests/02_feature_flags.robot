*** Settings ***
Documentation    Feature Flags API Integration Tests
Resource         common.resource
Suite Setup      Setup Feature Flags Suite

*** Keywords ***
Setup Feature Flags Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}

*** Test Cases ***
List Feature Flag Categories
    [Documentation]    GET /am/features should return feature flags list
    ${resp}=    GET    ${AM_URL}/features    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, (list, dict))
    Log    Feature flags response type: ${{type($json).__name__}}

Create Feature Flag
    [Documentation]    POST /am/features
    ${body}=    Create Dictionary
    ...    code=robot_flag_${TS}
    ...    name=Robot Flag ${TS}
    ...    description=Robot Framework test flag
    ...    category_code=auth
    ...    access_mode=permissioned
    ${resp}=    POST    ${AM_URL}/features    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    Log    Created flag: ${json}
    ${code}=    Get From Dictionary    ${json}    code
    Set Suite Variable    ${FLAG_CODE}    ${code}

Update Feature Flag
    [Documentation]    PATCH /am/features/{code}
    ${body}=    Create Dictionary
    ...    name=Robot Flag ${TS} Updated
    ...    description=Updated by Robot Framework
    ${resp}=    PATCH    ${AM_URL}/features/${FLAG_CODE}    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[name]    Robot Flag ${TS} Updated

List Features After Create
    [Documentation]    Verify the created flag appears in the list
    ${resp}=    GET    ${AM_URL}/features    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json.get('flags', []) if isinstance($json, dict) else $json
    ${codes}=    Evaluate    [f.get('code') for f in $items]
    Should Contain    ${codes}    robot_flag_${TS}

Create Feature Flag With Missing Fields Returns 422
    [Documentation]    POST /am/features with incomplete data
    ${body}=    Create Dictionary    code=incomplete_flag
    ${resp}=    POST    ${AM_URL}/features    headers=${AUTH_HEADERS}    json=${body}    expected_status=422

Create Feature Flag Without Auth Returns 401
    [Documentation]    POST /am/features without authentication
    ${body}=    Create Dictionary
    ...    code=no_auth_flag
    ...    name=No Auth Flag
    ...    description=Should fail
    ...    category_code=auth
    ...    access_mode=public
    ${resp}=    POST    ${AM_URL}/features    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403
