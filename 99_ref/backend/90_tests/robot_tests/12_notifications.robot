*** Settings ***
Documentation    Notification System Integration Tests — 35 endpoints (config, preferences, templates, rules, broadcasts, releases, incidents)
Resource         common.resource
Suite Setup      Login As Admin
Suite Teardown   Delete Test Template

*** Variables ***
${NOTIF_URL}              ${BASE_URL}/notifications
${TEST_QUEUE_ITEM_ID}     ${EMPTY}

*** Test Cases ***
# ------------------------------------------------------------------ #
# 1. GET /config — dimension data
# ------------------------------------------------------------------ #

Get Notification Config
    [Documentation]    GET /notifications/config — returns channels, categories, types, variable_keys
    ${resp}=    GET    ${NOTIF_URL}/config    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    channels
    Dictionary Should Contain Key    ${json}    categories
    Dictionary Should Contain Key    ${json}    types
    Dictionary Should Contain Key    ${json}    variable_keys
    # Verify we have seeded data
    ${ch_len}=    Get Length    ${json}[channels]
    Should Be True    ${ch_len} >= 2    Expected at least 2 channels (email, web_push)
    ${cat_len}=    Get Length    ${json}[categories]
    Should Be True    ${cat_len} >= 4    Expected at least 4 categories
    ${type_len}=    Get Length    ${json}[types]
    Should Be True    ${type_len} >= 10    Expected at least 10 notification types
    ${var_len}=    Get Length    ${json}[variable_keys]
    Should Be True    ${var_len} >= 20    Expected at least 20 template variable keys
    # Verify channel structure
    ${first_ch}=    Get From List    ${json}[channels]    0
    Dictionary Should Contain Key    ${first_ch}    code
    Dictionary Should Contain Key    ${first_ch}    name
    Dictionary Should Contain Key    ${first_ch}    is_available
    # Verify variable key has resolution fields
    ${first_var}=    Get From List    ${json}[variable_keys]    0
    Dictionary Should Contain Key    ${first_var}    resolution_source
    Dictionary Should Contain Key    ${first_var}    resolution_key

Config Contains Group And Tenant Variables
    [Documentation]    Verify group-level and tenant-level variables are in config
    ${resp}=    GET    ${NOTIF_URL}/config    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${found_group}=    Set Variable    ${FALSE}
    ${found_tenant}=    Set Variable    ${FALSE}
    FOR    ${var}    IN    @{json}[variable_keys]
        IF    '${var}[resolution_source]' == 'user_group'
            ${found_group}=    Set Variable    ${TRUE}
        END
        IF    '${var}[resolution_source]' == 'tenant'
            ${found_tenant}=    Set Variable    ${TRUE}
        END
    END
    Should Be True    ${found_group}    No user_group resolution source found
    Should Be True    ${found_tenant}    No tenant resolution source found

# ------------------------------------------------------------------ #
# 2-4. Preferences CRUD
# ------------------------------------------------------------------ #

Set Notification Preference Global Disable
    [Documentation]    PUT /notifications/preferences — set a global disable preference
    ${body}=    Create Dictionary    scope_level=global    is_enabled=${FALSE}
    ${resp}=    PUT    ${NOTIF_URL}/preferences    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal    ${json}[scope_level]    global
    Should Be Equal    ${json}[is_enabled]    ${FALSE}
    Set Suite Variable    ${PREF_GLOBAL_ID}    ${json}[id]

Set Notification Preference Type Level
    [Documentation]    PUT /notifications/preferences — set a type-level preference
    ${body}=    Create Dictionary
    ...    scope_level=type
    ...    channel_code=email
    ...    notification_type_code=org_member_added
    ...    is_enabled=${FALSE}
    ${resp}=    PUT    ${NOTIF_URL}/preferences    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[scope_level]    type
    Should Be Equal    ${json}[channel_code]    email
    Should Be Equal    ${json}[notification_type_code]    org_member_added
    Set Suite Variable    ${PREF_TYPE_ID}    ${json}[id]

List Notification Preferences
    [Documentation]    GET /notifications/preferences — list all user preferences
    ${resp}=    GET    ${NOTIF_URL}/preferences    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    ${pref_count}=    Get Length    ${json}[items]
    Should Be True    ${pref_count} >= 2    Expected at least 2 preferences

Delete Notification Preference
    [Documentation]    DELETE /notifications/preferences/{id} — delete a preference
    ${resp}=    DELETE    ${NOTIF_URL}/preferences/${PREF_TYPE_ID}    headers=${AUTH_HEADERS}    expected_status=204

Delete Preference Not Found
    [Documentation]    DELETE non-existent preference returns 404
    ${resp}=    DELETE    ${NOTIF_URL}/preferences/00000000-0000-0000-0000-000000000000    headers=${AUTH_HEADERS}    expected_status=404

Cleanup Global Preference
    [Documentation]    Clean up the global preference we created
    ${resp}=    DELETE    ${NOTIF_URL}/preferences/${PREF_GLOBAL_ID}    headers=${AUTH_HEADERS}    expected_status=204

# ------------------------------------------------------------------ #
# 5. Notification history
# ------------------------------------------------------------------ #

Get Notification History Empty
    [Documentation]    GET /notifications/history — returns empty for fresh user
    ${resp}=    GET    ${NOTIF_URL}/history    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total

Get Notification History With Params
    [Documentation]    GET /notifications/history?limit=10&offset=0
    ${params}=    Create Dictionary    limit=10    offset=0
    ${resp}=    GET    url=${NOTIF_URL}/history    params=${params}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    ${json}[total] >= 0

# ------------------------------------------------------------------ #
# 6-7. Web push subscriptions
# ------------------------------------------------------------------ #

Subscribe Web Push
    [Documentation]    POST /notifications/web-push/subscribe — create subscription
    ${body}=    Create Dictionary
    ...    endpoint=https://fcm.googleapis.com/fcm/send/robot-test-endpoint
    ...    p256dh_key=BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTBOO
    ...    auth_key=tBHItqI5SvFUqFXgk5DweA
    ...    user_agent=RobotFramework/1.0
    ${resp}=    POST    ${NOTIF_URL}/web-push/subscribe    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal    ${json}[is_active]    ${TRUE}
    Set Suite Variable    ${WEB_PUSH_SUB_ID}    ${json}[id]

Subscribe Web Push Upsert
    [Documentation]    POST same endpoint again — should upsert (update keys)
    ${body}=    Create Dictionary
    ...    endpoint=https://fcm.googleapis.com/fcm/send/robot-test-endpoint
    ...    p256dh_key=UPDATED_KEY_VALUE_12345678901234567890
    ...    auth_key=UPDATED_AUTH_KEY_123
    ...    user_agent=RobotFramework/2.0
    ${resp}=    POST    ${NOTIF_URL}/web-push/subscribe    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[is_active]    ${TRUE}

Unsubscribe Web Push
    [Documentation]    DELETE /notifications/web-push/{subscription_id}
    ${resp}=    DELETE    ${NOTIF_URL}/web-push/${WEB_PUSH_SUB_ID}    headers=${AUTH_HEADERS}    expected_status=204

Unsubscribe Web Push Not Found
    [Documentation]    DELETE non-existent subscription returns 404
    ${resp}=    DELETE    ${NOTIF_URL}/web-push/00000000-0000-0000-0000-000000000000    headers=${AUTH_HEADERS}    expected_status=404

# ------------------------------------------------------------------ #
# 8-13. Templates CRUD
# ------------------------------------------------------------------ #

Create Template
    [Documentation]    POST /notifications/templates — create a notification template
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TEMPLATE_CODE}    robot_test_template_${ts}
    ${body}=    Create Dictionary
    ...    code=${TEMPLATE_CODE}
    ...    name=Robot Test Template
    ...    description=Template created by Robot Framework tests
    ...    notification_type_code=password_reset
    ...    channel_code=email
    ${resp}=    POST    ${NOTIF_URL}/templates    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal    ${json}[code]    ${TEMPLATE_CODE}
    Should Be Equal    ${json}[is_active]    ${TRUE}
    Set Suite Variable    ${TEMPLATE_ID}    ${json}[id]

Create Template Duplicate Code Fails
    [Documentation]    POST with duplicate code returns 409
    ${body}=    Create Dictionary
    ...    code=${TEMPLATE_CODE}
    ...    name=Duplicate Template
    ...    notification_type_code=password_reset
    ...    channel_code=email
    ${resp}=    POST    ${NOTIF_URL}/templates    json=${body}    headers=${AUTH_HEADERS}    expected_status=409

List Templates
    [Documentation]    GET /notifications/templates — list all templates
    ${resp}=    GET    ${NOTIF_URL}/templates    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    Should Be True    ${json}[total] >= 1

Get Template Detail With Versions
    [Documentation]    GET /notifications/templates/{id} — returns template with embedded versions
    ${resp}=    GET    ${NOTIF_URL}/templates/${TEMPLATE_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${TEMPLATE_ID}
    Dictionary Should Contain Key    ${json}    versions
    ${version_count}=    Get Length    ${json}[versions]
    Should Be True    ${version_count} == 0    New template should have 0 versions

Create Template Version
    [Documentation]    POST /notifications/templates/{id}/versions — create a version
    ${body}=    Create Dictionary
    ...    subject_line=Hello {{user.display_name}} from {{platform.name}}
    ...    body_html=<h1>Hello {{user.display_name}}</h1><p>Token: {{token}}</p>
    ...    body_text=Hello {{user.display_name}}, Token: {{token}}
    ...    body_short=Token: {{token}}
    ...    change_notes=Initial version from Robot tests
    ${resp}=    POST    ${NOTIF_URL}/templates/${TEMPLATE_ID}/versions    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal As Integers    ${json}[version_number]    1
    Should Be Equal    ${json}[is_active]    ${TRUE}
    Set Suite Variable    ${VERSION_1_ID}    ${json}[id]

Create Template Second Version
    [Documentation]    POST another version — auto-activated
    ${body}=    Create Dictionary
    ...    subject_line=Updated: Hello {{user.display_name}}
    ...    body_html=<h1>Updated Hello {{user.display_name}}</h1>
    ...    body_text=Updated Hello {{user.display_name}}
    ...    change_notes=Second version with updated subject
    ${resp}=    POST    ${NOTIF_URL}/templates/${TEMPLATE_ID}/versions    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal As Integers    ${json}[version_number]    2
    Set Suite Variable    ${VERSION_2_ID}    ${json}[id]

Get Template Shows Versions Embedded
    [Documentation]    GET /templates/{id} — should now show 2 versions
    ${resp}=    GET    ${NOTIF_URL}/templates/${TEMPLATE_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${version_count}=    Get Length    ${json}[versions]
    Should Be True    ${version_count} == 2    Should have 2 versions
    Should Be Equal    ${json}[active_version_id]    ${VERSION_2_ID}

Update Template Name
    [Documentation]    PATCH /notifications/templates/{id} — update name
    ${body}=    Create Dictionary    name=Updated Robot Template Name
    ${resp}=    PATCH    ${NOTIF_URL}/templates/${TEMPLATE_ID}    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[name]    Updated Robot Template Name

Activate Previous Version Via PATCH
    [Documentation]    PATCH /templates/{id} with active_version_id — rollback to v1
    ${body}=    Create Dictionary    active_version_id=${VERSION_1_ID}
    ${resp}=    PATCH    ${NOTIF_URL}/templates/${TEMPLATE_ID}    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[active_version_id]    ${VERSION_1_ID}

Activate Invalid Version Fails
    [Documentation]    PATCH with non-existent version_id returns 404
    ${body}=    Create Dictionary    active_version_id=00000000-0000-0000-0000-000000000000
    ${resp}=    PATCH    ${NOTIF_URL}/templates/${TEMPLATE_ID}    json=${body}    headers=${AUTH_HEADERS}    expected_status=404

Preview Template
    [Documentation]    POST /notifications/templates/{id}/preview — render with variables
    ${variables}=    Create Dictionary
    ...    user.display_name=Robot User
    ...    platform.name=kcontrol
    ...    token=ABC123
    ${body}=    Create Dictionary    variables=${variables}
    ${resp}=    POST    ${NOTIF_URL}/templates/${TEMPLATE_ID}/preview    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    rendered_subject
    Dictionary Should Contain Key    ${json}    rendered_body_html
    Should Contain    ${json}[rendered_subject]    Robot User
    Should Contain    ${json}[rendered_body_html]    Robot User
    Should Contain    ${json}[rendered_body_html]    ABC123

Get Template Not Found
    [Documentation]    GET non-existent template returns 404
    ${resp}=    GET    ${NOTIF_URL}/templates/00000000-0000-0000-0000-000000000000    headers=${AUTH_HEADERS}    expected_status=404

# ------------------------------------------------------------------ #
# 14-15. Tracking endpoints (public, no auth)
# ------------------------------------------------------------------ #

Track Open Returns Pixel
    [Documentation]    GET /notifications/track/open/{id} — returns GIF pixel
    ${resp}=    GET    ${NOTIF_URL}/track/open/00000000-0000-0000-0000-000000000000    expected_status=200
    Should Be Equal    ${resp.headers}[Content-Type]    image/gif

Track Click Redirects
    [Documentation]    GET /notifications/track/click/{id}?url=... — 302 redirect
    ${params}=    Create Dictionary    url=https://example.com
    ${resp}=    GET
    ...    url=${NOTIF_URL}/track/click/00000000-0000-0000-0000-000000000000
    ...    params=${params}
    ...    expected_status=any
    ...    allow_redirects=${FALSE}
    Should Be True    ${resp.status_code} == 307 or ${resp.status_code} == 302 or ${resp.status_code} == 200

# ------------------------------------------------------------------ #
# 16-18. Broadcasts
# ------------------------------------------------------------------ #

Create Broadcast
    [Documentation]    POST /notifications/broadcasts — create a broadcast
    ${body}=    Create Dictionary
    ...    title=Robot Test Broadcast
    ...    body_text=This is a test broadcast from Robot Framework
    ...    scope=global
    ...    priority_code=normal
    ${resp}=    POST    ${NOTIF_URL}/broadcasts    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal    ${json}[title]    Robot Test Broadcast
    Should Be Equal    ${json}[scope]    global
    Should Be Equal    ${json}[is_active]    ${TRUE}
    Should Be Equal    ${json}[is_critical]    ${FALSE}
    Set Suite Variable    ${BROADCAST_ID}    ${json}[id]

Create Critical Broadcast With Severity
    [Documentation]    POST /notifications/broadcasts — create a critical broadcast with severity
    ${body}=    Create Dictionary
    ...    title=URGENT: Service Degradation
    ...    body_text=We are investigating issues with the API
    ...    scope=global
    ...    severity=critical
    ...    is_critical=${TRUE}
    ...    notification_type_code=platform_incident
    ${resp}=    POST    ${NOTIF_URL}/broadcasts    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[severity]    critical
    Should Be Equal    ${json}[is_critical]    ${TRUE}
    Should Be Equal    ${json}[notification_type_code]    platform_incident
    # Critical broadcasts auto-escalate priority
    Should Be True    '${json}[priority_code]' == 'critical' or '${json}[priority_code]' == 'high'

List Broadcasts
    [Documentation]    GET /notifications/broadcasts — list all broadcasts
    ${resp}=    GET    ${NOTIF_URL}/broadcasts    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${broadcast_count}=    Get Length    ${json}
    Should Be True    ${broadcast_count} >= 1

Send Broadcast
    [Documentation]    POST /notifications/broadcasts/{id}/send — trigger send
    ${resp}=    POST    ${NOTIF_URL}/broadcasts/${BROADCAST_ID}/send    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Equal    ${json}[sent_at]    ${None}

# ------------------------------------------------------------------ #
# 19-25. Rules CRUD with embedded sub-resources
# ------------------------------------------------------------------ #

Create Rule
    [Documentation]    POST /notifications/rules — create a notification rule
    ${ts}=    Get Timestamp
    Set Suite Variable    ${RULE_CODE}    robot_rule_${ts}
    ${body}=    Create Dictionary
    ...    code=${RULE_CODE}
    ...    name=Robot Test Rule
    ...    description=Rule created by Robot Framework tests
    ...    source_event_type=login_succeeded
    ...    source_event_category=auth
    ...    notification_type_code=login_from_new_device
    ...    recipient_strategy=actor
    ...    priority_code=normal
    ...    delay_seconds=${0}
    ${resp}=    POST    ${NOTIF_URL}/rules    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal    ${json}[code]    ${RULE_CODE}
    Should Be Equal    ${json}[is_active]    ${TRUE}
    Should Be Equal    ${json}[recipient_strategy]    actor
    Set Suite Variable    ${RULE_ID}    ${json}[id]

Create Rule Duplicate Code Fails
    [Documentation]    POST with duplicate code returns 409
    ${body}=    Create Dictionary
    ...    code=${RULE_CODE}
    ...    name=Duplicate Rule
    ...    source_event_type=login_succeeded
    ...    notification_type_code=login_from_new_device
    ...    recipient_strategy=actor
    ${resp}=    POST    ${NOTIF_URL}/rules    json=${body}    headers=${AUTH_HEADERS}    expected_status=409

List Rules
    [Documentation]    GET /notifications/rules — list all rules
    ${resp}=    GET    ${NOTIF_URL}/rules    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${rule_count}=    Get Length    ${json}
    Should Be True    ${rule_count} >= 1

Get Rule Detail With Sub Resources
    [Documentation]    GET /notifications/rules/{id} — returns rule with channels, conditions, runs
    ${resp}=    GET    ${NOTIF_URL}/rules/${RULE_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${RULE_ID}
    Dictionary Should Contain Key    ${json}    channels
    Dictionary Should Contain Key    ${json}    conditions
    Dictionary Should Contain Key    ${json}    recent_runs
    # Initially empty
    ${ch_len}=    Get Length    ${json}[channels]
    Should Be True    ${ch_len} == 0
    ${cond_len}=    Get Length    ${json}[conditions]
    Should Be True    ${cond_len} == 0

Get Rule Not Found
    [Documentation]    GET non-existent rule returns 404
    ${resp}=    GET    ${NOTIF_URL}/rules/00000000-0000-0000-0000-000000000000    headers=${AUTH_HEADERS}    expected_status=404

Update Rule
    [Documentation]    PATCH /notifications/rules/{id} — update rule properties
    ${body}=    Create Dictionary    name=Updated Robot Rule    priority_code=high    delay_seconds=${30}
    ${resp}=    PATCH    ${NOTIF_URL}/rules/${RULE_ID}    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[name]    Updated Robot Rule
    Should Be Equal    ${json}[priority_code]    high
    Should Be Equal As Integers    ${json}[delay_seconds]    30

Disable Rule
    [Documentation]    PATCH /notifications/rules/{id} — disable the rule
    ${body}=    Create Dictionary    is_disabled=${TRUE}
    ${resp}=    PATCH    ${NOTIF_URL}/rules/${RULE_ID}    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[is_active]    ${FALSE}

Enable Rule
    [Documentation]    PATCH /notifications/rules/{id} — re-enable the rule
    ${body}=    Create Dictionary    is_disabled=${FALSE}
    ${resp}=    PATCH    ${NOTIF_URL}/rules/${RULE_ID}    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[is_active]    ${TRUE}

Set Rule Channel Email
    [Documentation]    PUT /notifications/rules/{id}/channels/email — configure email channel
    ${body}=    Create Dictionary    template_code=${TEMPLATE_CODE}    is_active=${TRUE}
    ${resp}=    PUT    ${NOTIF_URL}/rules/${RULE_ID}/channels/email    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[channel_code]    email
    Should Be Equal    ${json}[template_code]    ${TEMPLATE_CODE}
    Should Be Equal    ${json}[is_active]    ${TRUE}

Set Rule Channel Web Push
    [Documentation]    PUT /notifications/rules/{id}/channels/web_push — configure web push
    ${body}=    Create Dictionary    is_active=${TRUE}
    ${resp}=    PUT    ${NOTIF_URL}/rules/${RULE_ID}/channels/web_push    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[channel_code]    web_push
    Should Be Equal    ${json}[is_active]    ${TRUE}

Verify Rule Detail Has Channels
    [Documentation]    GET /rules/{id} — verify channels are now embedded
    ${resp}=    GET    ${NOTIF_URL}/rules/${RULE_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${ch_len}=    Get Length    ${json}[channels]
    Should Be True    ${ch_len} == 2    Should have 2 channels configured

Create Rule Condition Inactivity
    [Documentation]    POST /notifications/rules/{id}/conditions — add inactivity condition
    ${body}=    Create Dictionary
    ...    condition_type=inactivity
    ...    field_key=inactivity_days
    ...    operator=gte
    ...    value=7
    ...    value_type=integer
    ...    logical_group=${0}
    ...    sort_order=${0}
    ${resp}=    POST    ${NOTIF_URL}/rules/${RULE_ID}/conditions    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal    ${json}[condition_type]    inactivity
    Should Be Equal    ${json}[field_key]    inactivity_days
    Should Be Equal    ${json}[operator]    gte
    Should Be Equal    ${json}[value]    7
    Should Be Equal    ${json}[is_active]    ${TRUE}
    Set Suite Variable    ${CONDITION_ID}    ${json}[id]

Create Rule Condition Engagement
    [Documentation]    POST /notifications/rules/{id}/conditions — add engagement condition
    ${body}=    Create Dictionary
    ...    condition_type=engagement
    ...    field_key=notification_type:org_invite_received
    ...    operator=not_in
    ...    value=48
    ...    value_type=integer
    ...    logical_group=${1}
    ...    sort_order=${0}
    ${resp}=    POST    ${NOTIF_URL}/rules/${RULE_ID}/conditions    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[condition_type]    engagement
    Set Suite Variable    ${CONDITION_2_ID}    ${json}[id]

Verify Rule Detail Has Conditions
    [Documentation]    GET /rules/{id} — verify conditions are now embedded
    ${resp}=    GET    ${NOTIF_URL}/rules/${RULE_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${cond_len}=    Get Length    ${json}[conditions]
    Should Be True    ${cond_len} == 2    Should have 2 conditions

Delete Rule Condition
    [Documentation]    DELETE /notifications/rules/{id}/conditions/{condition_id}
    ${resp}=    DELETE    ${NOTIF_URL}/rules/${RULE_ID}/conditions/${CONDITION_2_ID}    headers=${AUTH_HEADERS}    expected_status=204

Delete Rule Condition Not Found
    [Documentation]    DELETE non-existent condition returns 404
    ${resp}=    DELETE    ${NOTIF_URL}/rules/${RULE_ID}/conditions/00000000-0000-0000-0000-000000000000    headers=${AUTH_HEADERS}    expected_status=404

Verify Rule Detail After Condition Delete
    [Documentation]    GET /rules/{id} — verify only 1 condition remains
    ${resp}=    GET    ${NOTIF_URL}/rules/${RULE_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${cond_len}=    Get Length    ${json}[conditions]
    Should Be True    ${cond_len} == 1    Should have 1 condition after delete

# ------------------------------------------------------------------ #
# Auth enforcement — endpoints require Bearer token
# ------------------------------------------------------------------ #

Preferences Without Auth Fails
    [Documentation]    GET /notifications/preferences without token returns 401/403
    ${resp}=    GET    ${NOTIF_URL}/preferences    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

Templates Without Auth Fails
    [Documentation]    GET /notifications/templates without token returns 401/403
    ${resp}=    GET    ${NOTIF_URL}/templates    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

Rules Without Auth Fails
    [Documentation]    GET /notifications/rules without token returns 401/403
    ${resp}=    GET    ${NOTIF_URL}/rules    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

Broadcasts Without Auth Fails
    [Documentation]    GET /notifications/broadcasts without token returns 401/403
    ${resp}=    GET    ${NOTIF_URL}/broadcasts    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

# ------------------------------------------------------------------ #
# Releases CRUD
# ------------------------------------------------------------------ #

Create Release
    [Documentation]    POST /notifications/releases — create a draft release
    ${ts}=    Get Timestamp
    Set Suite Variable    ${RELEASE_VERSION}    v1.0.${ts}
    ${body}=    Create Dictionary
    ...    version=${RELEASE_VERSION}
    ...    title=Robot Test Release
    ...    summary=Automated test release with new features and bug fixes
    ...    body_markdown=## What's New\n- Feature A\n- Bug fix B
    ...    changelog_url=https://docs.example.com/changelog
    ${resp}=    POST    ${NOTIF_URL}/releases    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal    ${json}[version]    ${RELEASE_VERSION}
    Should Be Equal    ${json}[title]    Robot Test Release
    Should Be Equal    ${json}[status]    draft
    Should Be Equal    ${json}[is_active]    ${TRUE}
    Set Suite Variable    ${RELEASE_ID}    ${json}[id]

Get Release By ID
    [Documentation]    GET /notifications/releases/{id} — get single release
    ${resp}=    GET    ${NOTIF_URL}/releases/${RELEASE_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${RELEASE_ID}
    Should Be Equal    ${json}[version]    ${RELEASE_VERSION}

List Releases
    [Documentation]    GET /notifications/releases — list all releases
    ${resp}=    GET    ${NOTIF_URL}/releases    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${release_count}=    Get Length    ${json}[items]
    Should Be True    ${release_count} >= 1

List Releases With Status Filter
    [Documentation]    GET /notifications/releases?status=draft — filter by status
    ${params}=    Create Dictionary    status=draft
    ${resp}=    GET    ${NOTIF_URL}/releases    params=${params}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    FOR    ${release}    IN    @{json}[items]
        Should Be Equal    ${release}[status]    draft
    END

Update Release
    [Documentation]    PATCH /notifications/releases/{id} — update release details
    ${body}=    Create Dictionary
    ...    title=Robot Test Release Updated
    ...    summary=Updated summary with more details
    ${resp}=    PATCH    ${NOTIF_URL}/releases/${RELEASE_ID}    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[title]    Robot Test Release Updated
    Should Be Equal    ${json}[summary]    Updated summary with more details

Publish Release
    [Documentation]    POST /notifications/releases/{id}/publish — publish and optionally broadcast
    ${params}=    Create Dictionary    notify=false
    ${resp}=    POST    ${NOTIF_URL}/releases/${RELEASE_ID}/publish    params=${params}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[status]    published
    Should Not Be Equal    ${json}[published_at]    ${None}

Publish Already Published Release Fails
    [Documentation]    Publishing an already published release returns 409 Conflict
    ${params}=    Create Dictionary    notify=false
    ${resp}=    POST    ${NOTIF_URL}/releases/${RELEASE_ID}/publish    params=${params}    headers=${AUTH_HEADERS}    expected_status=409

Archive Release
    [Documentation]    POST /notifications/releases/{id}/archive — archive a release
    ${resp}=    POST    ${NOTIF_URL}/releases/${RELEASE_ID}/archive    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[status]    archived

Get Release Not Found
    [Documentation]    GET non-existent release returns 404
    ${resp}=    GET    ${NOTIF_URL}/releases/00000000-0000-0000-0000-000000000000    headers=${AUTH_HEADERS}    expected_status=404

Releases Without Auth Fails
    [Documentation]    GET /notifications/releases without token returns 401/403
    ${resp}=    GET    ${NOTIF_URL}/releases    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

# ------------------------------------------------------------------ #
# Incidents CRUD
# ------------------------------------------------------------------ #

Create Incident
    [Documentation]    POST /notifications/incidents — create an incident
    ${body}=    Create Dictionary
    ...    title=API Latency Degradation
    ...    description=Users experiencing increased response times on API endpoints
    ...    severity=major
    ...    affected_components=API, Dashboard
    ...    notify_users=${FALSE}
    ${resp}=    POST    ${NOTIF_URL}/incidents    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal    ${json}[title]    API Latency Degradation
    Should Be Equal    ${json}[severity]    major
    Should Be Equal    ${json}[status]    investigating
    Should Be Equal    ${json}[is_active]    ${TRUE}
    Set Suite Variable    ${INCIDENT_ID}    ${json}[id]

Create Critical Incident With Auto Broadcast
    [Documentation]    POST /notifications/incidents — critical incident auto-creates broadcast
    ${body}=    Create Dictionary
    ...    title=Complete Service Outage
    ...    description=All services are currently unavailable
    ...    severity=critical
    ...    notify_users=${TRUE}
    ${resp}=    POST    ${NOTIF_URL}/incidents    json=${body}    headers=${AUTH_HEADERS}    expected_status=201
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[severity]    critical
    Should Not Be Equal    ${json}[broadcast_id]    ${None}
    Set Suite Variable    ${CRITICAL_INCIDENT_ID}    ${json}[id]

Get Incident By ID
    [Documentation]    GET /notifications/incidents/{id} — get single incident with updates
    ${resp}=    GET    ${NOTIF_URL}/incidents/${INCIDENT_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${INCIDENT_ID}
    Dictionary Should Contain Key    ${json}    updates

List Incidents
    [Documentation]    GET /notifications/incidents — list all incidents
    ${resp}=    GET    ${NOTIF_URL}/incidents    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${incident_count}=    Get Length    ${json}[items]
    Should Be True    ${incident_count} >= 1

List Incidents With Status Filter
    [Documentation]    GET /notifications/incidents?status=investigating — filter by status
    ${params}=    Create Dictionary    status=investigating
    ${resp}=    GET    ${NOTIF_URL}/incidents    params=${params}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    FOR    ${incident}    IN    @{json}[items]
        Should Be Equal    ${incident}[status]    investigating
    END

Update Incident
    [Documentation]    PATCH /notifications/incidents/{id} — update incident details
    ${body}=    Create Dictionary
    ...    title=API Latency Degradation - Root Cause Identified
    ...    severity=minor
    ${resp}=    PATCH    ${NOTIF_URL}/incidents/${INCIDENT_ID}    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[title]    API Latency Degradation - Root Cause Identified
    Should Be Equal    ${json}[severity]    minor

Post Incident Update Identified
    [Documentation]    POST /notifications/incidents/{id}/updates — post status update
    ${body}=    Create Dictionary
    ...    status=identified
    ...    message=Root cause identified: database connection pool exhaustion
    ...    is_public=${TRUE}
    ...    notify_users=${FALSE}
    ${resp}=    POST    ${NOTIF_URL}/incidents/${INCIDENT_ID}/updates    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[status]    identified
    ${update_count}=    Get Length    ${json}[updates]
    Should Be True    ${update_count} >= 1

Post Incident Update Resolved
    [Documentation]    POST /notifications/incidents/{id}/updates — resolve incident
    ${body}=    Create Dictionary
    ...    status=resolved
    ...    message=Issue resolved. Connection pool size increased and monitoring enhanced.
    ...    is_public=${TRUE}
    ...    notify_users=${FALSE}
    ${resp}=    POST    ${NOTIF_URL}/incidents/${INCIDENT_ID}/updates    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[status]    resolved
    Should Not Be Equal    ${json}[resolved_at]    ${None}

Get Incident Not Found
    [Documentation]    GET non-existent incident returns 404
    ${resp}=    GET    ${NOTIF_URL}/incidents/00000000-0000-0000-0000-000000000000    headers=${AUTH_HEADERS}    expected_status=404

Incidents Without Auth Fails
    [Documentation]    GET /notifications/incidents without token returns 401/403
    ${resp}=    GET    ${NOTIF_URL}/incidents    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

# ------------------------------------------------------------------ #
# Config validates new notification types
# ------------------------------------------------------------------ #

Config Contains Platform Notification Types
    [Documentation]    Verify platform_release, platform_incident, platform_maintenance are in config
    ${resp}=    GET    ${NOTIF_URL}/config    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${found_release}=    Set Variable    ${FALSE}
    ${found_incident}=    Set Variable    ${FALSE}
    ${found_maintenance}=    Set Variable    ${FALSE}
    FOR    ${t}    IN    @{json}[types]
        IF    '${t}[code]' == 'platform_release'
            ${found_release}=    Set Variable    ${TRUE}
        END
        IF    '${t}[code]' == 'platform_incident'
            ${found_incident}=    Set Variable    ${TRUE}
        END
        IF    '${t}[code]' == 'platform_maintenance'
            ${found_maintenance}=    Set Variable    ${TRUE}
        END
    END
    Should Be True    ${found_release}    platform_release type not found in config
    Should Be True    ${found_incident}    platform_incident type not found in config
    Should Be True    ${found_maintenance}    platform_maintenance type not found in config

# ------------------------------------------------------------------ #
# Admin: SMTP configuration
# ------------------------------------------------------------------ #

Get SMTP Config
    [Documentation]    GET /notifications/smtp/config — returns current SMTP settings
    ${resp}=    GET    ${NOTIF_URL}/smtp/config    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    host
    Dictionary Should Contain Key    ${json}    port
    Dictionary Should Contain Key    ${json}    username
    Dictionary Should Contain Key    ${json}    from_email
    Dictionary Should Contain Key    ${json}    from_name
    Dictionary Should Contain Key    ${json}    use_tls
    Dictionary Should Contain Key    ${json}    start_tls
    Dictionary Should Contain Key    ${json}    is_configured
    # Values must be the right types
    Should Be True    isinstance(${json}[port], int)
    Should Be True    isinstance(${json}[use_tls], bool)
    Should Be True    isinstance(${json}[start_tls], bool)
    Should Be True    isinstance(${json}[is_configured], bool)
    Log    SMTP configured: ${json}[is_configured]    INFO
    Log    SMTP host: ${json}[host]    INFO

Get SMTP Config Without Auth Fails
    [Documentation]    GET /notifications/smtp/config without token returns 401/403
    ${resp}=    GET    ${NOTIF_URL}/smtp/config    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

# ------------------------------------------------------------------ #
# Admin: SMTP test connection
# ------------------------------------------------------------------ #

Test SMTP Connection Uses Configured Settings
    [Documentation]    POST /notifications/smtp/test — test with no overrides (uses .env config)
    # We only run the actual send if SMTP is configured; otherwise verify the error is descriptive
    ${config_resp}=    GET    ${NOTIF_URL}/smtp/config    headers=${AUTH_HEADERS}    expected_status=200
    ${config}=    Set Variable    ${config_resp.json()}
    ${body}=    Create Dictionary    to_email=robot-test@example.com
    ${resp}=    POST    ${NOTIF_URL}/smtp/test    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    success
    Dictionary Should Contain Key    ${json}    message
    # If SMTP not configured, success=false with a descriptive message
    IF    not ${config}[is_configured]
        Should Be Equal    ${json}[success]    ${FALSE}
        Should Contain    ${json}[message]    not configured
    END
    Log    SMTP test result: success=${json}[success], message=${json}[message]    INFO

Test SMTP Connection With Missing Host Fails Gracefully
    [Documentation]    POST /notifications/smtp/test with empty host override — returns error
    ${body}=    Create Dictionary
    ...    to_email=robot-test@example.com
    ...    host=${EMPTY}
    ${resp}=    POST    ${NOTIF_URL}/smtp/test    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    # Empty host overrides to None; falls back to configured or returns not configured
    Dictionary Should Contain Key    ${json}    success
    Dictionary Should Contain Key    ${json}    message

Test SMTP Connection Without Auth Fails
    [Documentation]    POST /notifications/smtp/test without token returns 401/403
    ${body}=    Create Dictionary    to_email=robot-test@example.com
    ${resp}=    POST    ${NOTIF_URL}/smtp/test    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

# ------------------------------------------------------------------ #
# Admin: send test notification
# ------------------------------------------------------------------ #

Send Test Notification Email Channel
    [Documentation]    POST /notifications/send-test — send a test email notification
    ${body}=    Create Dictionary
    ...    to_email=robot-test@example.com
    ...    notification_type_code=password_reset
    ...    channel_code=email
    ${resp}=    POST    ${NOTIF_URL}/send-test    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    success
    Dictionary Should Contain Key    ${json}    message
    Log    Send test result: success=${json}[success], message=${json}[message]    INFO

Send Test Notification With Custom Subject And Body
    [Documentation]    POST /notifications/send-test with custom subject/body override
    ${body}=    Create Dictionary
    ...    to_email=robot-test@example.com
    ...    notification_type_code=org_invite_received
    ...    channel_code=email
    ...    subject=Robot Framework Test Notification
    ...    body=<h1>Test</h1><p>This was sent from the Robot Framework test suite.</p>
    ${resp}=    POST    ${NOTIF_URL}/send-test    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    success

Send Test Notification Unsupported Channel
    [Documentation]    POST /notifications/send-test with web_push returns success=false (not supported via this endpoint)
    ${body}=    Create Dictionary
    ...    to_email=robot-test@example.com
    ...    notification_type_code=org_invite_received
    ...    channel_code=web_push
    ${resp}=    POST    ${NOTIF_URL}/send-test    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[success]    ${FALSE}
    Should Contain    ${json}[message]    not supported

Send Test Notification Without Auth Fails
    [Documentation]    POST /notifications/send-test without token returns 401/403
    ${body}=    Create Dictionary
    ...    to_email=robot-test@example.com
    ...    notification_type_code=password_reset
    ...    channel_code=email
    ${resp}=    POST    ${NOTIF_URL}/send-test    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

# ------------------------------------------------------------------ #
# Admin: delivery queue monitor
# ------------------------------------------------------------------ #

Get Queue Admin Default
    [Documentation]    GET /notifications/queue — returns queue stats + items
    ${resp}=    GET    ${NOTIF_URL}/queue    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    stats
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    # Verify stats structure
    ${stats}=    Set Variable    ${json}[stats]
    Dictionary Should Contain Key    ${stats}    queued
    Dictionary Should Contain Key    ${stats}    processing
    Dictionary Should Contain Key    ${stats}    sent
    Dictionary Should Contain Key    ${stats}    delivered
    Dictionary Should Contain Key    ${stats}    failed
    Dictionary Should Contain Key    ${stats}    dead_letter
    Dictionary Should Contain Key    ${stats}    suppressed
    Should Be True    ${json}[total] >= 0
    Log    Queue stats: queued=${stats}[queued], sent=${stats}[sent], failed=${stats}[failed]    INFO

Get Queue Admin With Status Filter
    [Documentation]    GET /notifications/queue?status_code=sent — filter by status
    ${params}=    Create Dictionary    status_code=sent
    ${resp}=    GET    url=${NOTIF_URL}/queue    params=${params}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    FOR    ${item}    IN    @{json}[items]
        Should Be Equal    ${item}[status_code]    sent
    END

Get Queue Admin With Channel Filter
    [Documentation]    GET /notifications/queue?channel_code=email — filter by channel
    ${params}=    Create Dictionary    channel_code=email
    ${resp}=    GET    url=${NOTIF_URL}/queue    params=${params}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    FOR    ${item}    IN    @{json}[items]
        Should Be Equal    ${item}[channel_code]    email
    END

Get Queue Admin With Pagination
    [Documentation]    GET /notifications/queue?limit=5&offset=0 — pagination works
    ${params}=    Create Dictionary    limit=5    offset=0
    ${resp}=    GET    url=${NOTIF_URL}/queue    params=${params}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${item_count}=    Get Length    ${json}[items]
    Should Be True    ${item_count} <= 5

Get Queue Admin Without Auth Fails
    [Documentation]    GET /notifications/queue without token returns 401/403
    ${resp}=    GET    ${NOTIF_URL}/queue    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

# ------------------------------------------------------------------ #
# Admin: delivery reports
# ------------------------------------------------------------------ #

Get Delivery Report Default Period
    [Documentation]    GET /notifications/reports/delivery — 24h period default
    ${resp}=    GET    ${NOTIF_URL}/reports/delivery    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    funnel
    Dictionary Should Contain Key    ${json}    rows
    Dictionary Should Contain Key    ${json}    period_hours
    Should Be Equal As Integers    ${json}[period_hours]    24
    # Verify funnel structure
    ${funnel}=    Set Variable    ${json}[funnel]
    Dictionary Should Contain Key    ${funnel}    queued
    Dictionary Should Contain Key    ${funnel}    sent
    Dictionary Should Contain Key    ${funnel}    delivered
    Dictionary Should Contain Key    ${funnel}    opened
    Dictionary Should Contain Key    ${funnel}    clicked
    Dictionary Should Contain Key    ${funnel}    failed
    Dictionary Should Contain Key    ${funnel}    dead_letter
    Dictionary Should Contain Key    ${funnel}    suppressed
    Dictionary Should Contain Key    ${funnel}    delivery_rate
    Dictionary Should Contain Key    ${funnel}    open_rate
    Dictionary Should Contain Key    ${funnel}    click_rate
    # Rates must be numeric and within 0-100
    Should Be True    ${funnel}[delivery_rate] >= 0 and ${funnel}[delivery_rate] <= 100
    Should Be True    ${funnel}[open_rate] >= 0 and ${funnel}[open_rate] <= 100
    Should Be True    ${funnel}[click_rate] >= 0 and ${funnel}[click_rate] <= 100

Get Delivery Report Short Period
    [Documentation]    GET /notifications/reports/delivery?period_hours=1 — 1h period
    ${params}=    Create Dictionary    period_hours=1
    ${resp}=    GET    url=${NOTIF_URL}/reports/delivery    params=${params}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal As Integers    ${json}[period_hours]    1

Get Delivery Report Long Period
    [Documentation]    GET /notifications/reports/delivery?period_hours=720 — 30d period (max)
    ${params}=    Create Dictionary    period_hours=720
    ${resp}=    GET    url=${NOTIF_URL}/reports/delivery    params=${params}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal As Integers    ${json}[period_hours]    720

Get Delivery Report Invalid Period Fails
    [Documentation]    GET /notifications/reports/delivery?period_hours=0 — below minimum
    ${params}=    Create Dictionary    period_hours=0
    ${resp}=    GET    url=${NOTIF_URL}/reports/delivery    params=${params}    headers=${AUTH_HEADERS}    expected_status=422

Get Delivery Report Without Auth Fails
    [Documentation]    GET /notifications/reports/delivery without token returns 401/403
    ${resp}=    GET    ${NOTIF_URL}/reports/delivery    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

# ------------------------------------------------------------------ #
# Admin: queue item detail + retry/dead-letter with real queue entry
# ------------------------------------------------------------------ #

Insert Queue Item For Testing
    [Documentation]    Directly inserts a test notification into the queue via the broadcast→send flow
    # Use the broadcast we already created and get any item from the queue, or create a fresh one
    ${params}=    Create Dictionary    status_code=failed    limit=1
    ${resp}=    GET    url=${NOTIF_URL}/queue    params=${params}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${has_failed}=    Evaluate    len(${json}[items]) > 0
    IF    ${has_failed}
        ${first_item}=    Get From List    ${json}[items]    0
        Set Suite Variable    ${TEST_QUEUE_ITEM_ID}    ${first_item}[id]
        Log    Using existing failed item: ${TEST_QUEUE_ITEM_ID}    INFO
    ELSE
        # Try dead_letter
        ${params2}=    Create Dictionary    status_code=dead_letter    limit=1
        ${resp2}=    GET    url=${NOTIF_URL}/queue    params=${params2}    headers=${AUTH_HEADERS}    expected_status=200
        ${json2}=    Set Variable    ${resp2.json()}
        ${has_dl}=    Evaluate    len(${json2}[items]) > 0
        IF    ${has_dl}
            ${first_item2}=    Get From List    ${json2}[items]    0
            Set Suite Variable    ${TEST_QUEUE_ITEM_ID}    ${first_item2}[id]
            Log    Using existing dead_letter item: ${TEST_QUEUE_ITEM_ID}    INFO
        ELSE
            Set Suite Variable    ${TEST_QUEUE_ITEM_ID}    ${EMPTY}
            Log    No failed/dead_letter items available for queue detail test    WARN
        END
    END

Get Queue Item Detail
    [Documentation]    GET /notifications/queue/{id} — returns full notification detail with logs + tracking events
    IF    '${TEST_QUEUE_ITEM_ID}' == '${EMPTY}'
        Log    Skipping: no test queue item available    WARN
        Skip    No failed/dead_letter queue item available for this test
    END
    ${resp}=    GET    ${NOTIF_URL}/queue/${TEST_QUEUE_ITEM_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    notification
    Dictionary Should Contain Key    ${json}    delivery_logs
    Dictionary Should Contain Key    ${json}    tracking_events
    # Verify notification structure
    ${notif}=    Set Variable    ${json}[notification]
    Dictionary Should Contain Key    ${notif}    id
    Dictionary Should Contain Key    ${notif}    status_code
    Dictionary Should Contain Key    ${notif}    channel_code
    Dictionary Should Contain Key    ${notif}    attempt_count
    Should Be Equal    ${notif}[id]    ${TEST_QUEUE_ITEM_ID}
    # Delivery logs may be empty or populated
    ${log_count}=    Get Length    ${json}[delivery_logs]
    Should Be True    ${log_count} >= 0
    Log    Queue item detail: status=${notif}[status_code], logs=${log_count}    INFO

Get Queue Item Detail Not Found
    [Documentation]    GET /notifications/queue/{non-existent-id} — returns 404
    ${resp}=    GET    ${NOTIF_URL}/queue/00000000-0000-0000-0000-000000000000    headers=${AUTH_HEADERS}    expected_status=404

Get Queue Item Detail Without Auth Fails
    [Documentation]    GET /notifications/queue/{id} without token returns 401/403
    ${resp}=    GET    ${NOTIF_URL}/queue/00000000-0000-0000-0000-000000000000    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

Retry Queue Item
    [Documentation]    POST /notifications/queue/{id}/retry — requeue a failed notification
    IF    '${TEST_QUEUE_ITEM_ID}' == '${EMPTY}'
        Log    Skipping: no test queue item available    WARN
        Skip    No failed/dead_letter queue item available for this test
    END
    ${resp}=    POST    ${NOTIF_URL}/queue/${TEST_QUEUE_ITEM_ID}/retry    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    success
    Dictionary Should Contain Key    ${json}    message
    Log    Retry result: success=${json}[success], message=${json}[message]    INFO
    # After retry the item should be in queued state
    IF    ${json}[success]
        ${detail_resp}=    GET    ${NOTIF_URL}/queue/${TEST_QUEUE_ITEM_ID}    headers=${AUTH_HEADERS}    expected_status=200
        ${detail}=    Set Variable    ${detail_resp.json()}
        Should Be Equal    ${detail}[notification][status_code]    queued
    END

Dead Letter Queue Item
    [Documentation]    POST /notifications/queue/{id}/dead-letter — move item to dead_letter
    IF    '${TEST_QUEUE_ITEM_ID}' == '${EMPTY}'
        Log    Skipping: no test queue item available    WARN
        Skip    No failed/dead_letter queue item available for this test
    END
    # The item may already be back in queued after retry above — dead-letter it
    ${body}=    Create Dictionary    reason=Robot Framework test: intentional dead-letter
    ${resp}=    POST    ${NOTIF_URL}/queue/${TEST_QUEUE_ITEM_ID}/dead-letter    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    success
    Dictionary Should Contain Key    ${json}    message
    Log    Dead-letter result: success=${json}[success], message=${json}[message]    INFO

Retry Queue Item Not Found
    [Documentation]    POST /notifications/queue/{non-existent}/retry — returns success=false
    ${resp}=    POST    ${NOTIF_URL}/queue/00000000-0000-0000-0000-000000000000/retry    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[success]    ${FALSE}

Dead Letter Queue Item Not Found
    [Documentation]    POST /notifications/queue/{non-existent}/dead-letter — returns success=false
    ${body}=    Create Dictionary    reason=test
    ${resp}=    POST    ${NOTIF_URL}/queue/00000000-0000-0000-0000-000000000000/dead-letter    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[success]    ${FALSE}

Retry Without Auth Fails
    [Documentation]    POST /notifications/queue/{id}/retry without token returns 401/403
    ${resp}=    POST    ${NOTIF_URL}/queue/00000000-0000-0000-0000-000000000000/retry    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

Dead Letter Without Auth Fails
    [Documentation]    POST /notifications/queue/{id}/dead-letter without token returns 401/403
    ${body}=    Create Dictionary    reason=test
    ${resp}=    POST    ${NOTIF_URL}/queue/00000000-0000-0000-0000-000000000000/dead-letter    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 401 or ${resp.status_code} == 403

# ------------------------------------------------------------------ #
# Tracking endpoints — end-to-end: send → track open → track click
# ------------------------------------------------------------------ #

Track Open Valid Notification ID Returns GIF Pixel
    [Documentation]    GET /notifications/track/open/{id} — returns 1x1 GIF regardless of notification existence
    # Tracking pixel always returns 200 + GIF (even for unknown IDs — silently ignores)
    ${resp}=    GET    ${NOTIF_URL}/track/open/00000000-0000-0000-0000-000000000001    expected_status=200
    Should Be Equal    ${resp.headers}[Content-Type]    image/gif
    # Verify response body is non-empty by checking Content-Length or response length
    ${body_len}=    Get Length    ${resp.text}
    Should Be True    ${body_len} > 0

Track Open With Real Notification ID
    [Documentation]    GET /notifications/track/open/{id} with real queue item — records tracking event
    IF    '${TEST_QUEUE_ITEM_ID}' == '${EMPTY}'
        Log    Skipping: no test queue item available    WARN
        Skip    No queue item available for tracking test
    END
    # Dead-letter item above — status is terminal, but open tracking should still record the event
    ${resp}=    GET    ${NOTIF_URL}/track/open/${TEST_QUEUE_ITEM_ID}    expected_status=200
    Should Be Equal    ${resp.headers}[Content-Type]    image/gif
    # Check tracking event was recorded via queue detail
    ${detail_resp}=    GET    ${NOTIF_URL}/queue/${TEST_QUEUE_ITEM_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${detail}=    Set Variable    ${detail_resp.json()}
    ${event_count}=    Get Length    ${detail}[tracking_events]
    Should Be True    ${event_count} >= 1
    ${first_event}=    Get From List    ${detail}[tracking_events]    0
    Should Be Equal    ${first_event}[tracking_event_type_code]    opened
    Dictionary Should Contain Key    ${first_event}    occurred_at
    Log    Tracking open recorded: ${event_count} events    INFO

Track Click Returns Redirect
    [Documentation]    GET /notifications/track/click/{id}?url=... — 307 redirect to destination URL
    ${params}=    Create Dictionary    url=https://example.com/destination
    ${resp}=    GET
    ...    url=${NOTIF_URL}/track/click/00000000-0000-0000-0000-000000000001
    ...    params=${params}
    ...    expected_status=any
    ...    allow_redirects=${FALSE}
    Should Be True    ${resp.status_code} == 307 or ${resp.status_code} == 302
    # Verify Location header points to the target URL
    Dictionary Should Contain Key    ${resp.headers}    location
    Should Contain    ${resp.headers}[location]    example.com

Track Click With Real Notification ID
    [Documentation]    GET /notifications/track/click/{id}?url=... with real queue item — records click event
    IF    '${TEST_QUEUE_ITEM_ID}' == '${EMPTY}'
        Log    Skipping: no test queue item available    WARN
        Skip    No queue item available for tracking test
    END
    ${params}=    Create Dictionary    url=https://example.com/robot-click-test
    ${resp}=    GET
    ...    url=${NOTIF_URL}/track/click/${TEST_QUEUE_ITEM_ID}
    ...    params=${params}
    ...    expected_status=any
    ...    allow_redirects=${FALSE}
    Should Be True    ${resp.status_code} == 307 or ${resp.status_code} == 302
    # Check click event was recorded
    ${detail_resp}=    GET    ${NOTIF_URL}/queue/${TEST_QUEUE_ITEM_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${detail}=    Set Variable    ${detail_resp.json()}
    ${has_click}=    Set Variable    ${FALSE}
    FOR    ${event}    IN    @{detail}[tracking_events]
        IF    '${event}[tracking_event_type_code]' == 'clicked'
            ${has_click}=    Set Variable    ${TRUE}
        END
    END
    Should Be True    ${has_click}    Click tracking event not recorded

Track Click Missing URL Param Fails
    [Documentation]    GET /notifications/track/click/{id} without url param returns 422
    ${resp}=    GET    ${NOTIF_URL}/track/click/00000000-0000-0000-0000-000000000001    expected_status=422

Track Open No Auth Required
    [Documentation]    GET /notifications/track/open/{id} — no authentication required (public endpoint)
    ${resp}=    GET    ${NOTIF_URL}/track/open/00000000-0000-0000-0000-000000000002    expected_status=200
    Should Be Equal    ${resp.headers}[Content-Type]    image/gif

Track Click No Auth Required
    [Documentation]    GET /notifications/track/click/{id}?url=... — no authentication required (public endpoint)
    ${params}=    Create Dictionary    url=https://example.com
    ${resp}=    GET
    ...    url=${NOTIF_URL}/track/click/00000000-0000-0000-0000-000000000002
    ...    params=${params}
    ...    expected_status=any
    ...    allow_redirects=${FALSE}
    Should Be True    ${resp.status_code} == 307 or ${resp.status_code} == 302

# ------------------------------------------------------------------ #
# Delivery log structure validation
# ------------------------------------------------------------------ #

Delivery Log Fields Are Complete
    [Documentation]    GET /notifications/queue/{id} — verify each delivery log has required fields
    IF    '${TEST_QUEUE_ITEM_ID}' == '${EMPTY}'
        Log    Skipping: no test queue item    WARN
        Skip    No queue item available
    END
    ${resp}=    GET    ${NOTIF_URL}/queue/${TEST_QUEUE_ITEM_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    FOR    ${log}    IN    @{json}[delivery_logs]
        Dictionary Should Contain Key    ${log}    id
        Dictionary Should Contain Key    ${log}    notification_id
        Dictionary Should Contain Key    ${log}    channel_code
        Dictionary Should Contain Key    ${log}    attempt_number
        Dictionary Should Contain Key    ${log}    status
        Dictionary Should Contain Key    ${log}    occurred_at
        Dictionary Should Contain Key    ${log}    created_at
    END

Tracking Event Fields Are Complete
    [Documentation]    GET /notifications/queue/{id} — verify each tracking event has required fields
    IF    '${TEST_QUEUE_ITEM_ID}' == '${EMPTY}'
        Log    Skipping: no test queue item    WARN
        Skip    No queue item available
    END
    ${resp}=    GET    ${NOTIF_URL}/queue/${TEST_QUEUE_ITEM_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    FOR    ${event}    IN    @{json}[tracking_events]
        Dictionary Should Contain Key    ${event}    id
        Dictionary Should Contain Key    ${event}    notification_id
        Dictionary Should Contain Key    ${event}    tracking_event_type_code
        Dictionary Should Contain Key    ${event}    channel_code
        Dictionary Should Contain Key    ${event}    occurred_at
        Dictionary Should Contain Key    ${event}    created_at
    END


*** Keywords ***
Delete Test Template
    [Documentation]    Suite teardown — soft-delete the test template created during this run
    IF    '${TEMPLATE_ID}' != '${EMPTY}'
        DELETE    ${NOTIF_URL}/templates/${TEMPLATE_ID}    headers=${AUTH_HEADERS}    expected_status=204
    END
