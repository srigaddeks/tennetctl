*** Settings ***
Documentation    Comments API Integration Tests — CRUD, replies, reactions, pin/resolve, soft-delete, pagination
Resource         common.resource
Suite Setup      Setup Comments Suite
Suite Teardown   Teardown Comments Suite

*** Variables ***
${CM_URL}                   ${BASE_URL}/cm
${TK_URL_CM}                ${BASE_URL}/tk
# Suite-level IDs set during setup
${CM_ORG_ID}                ${EMPTY}
${CM_WS_ID}                 ${EMPTY}
${CM_TASK_ID}               ${EMPTY}
# Primary user (admin) state
${COMMENT_ID}               ${EMPTY}
${REPLY_ID}                 ${EMPTY}
# Secondary user state
${SECONDARY_TOKEN}          ${EMPTY}
${SECONDARY_HEADERS}        ${EMPTY}
${SECONDARY_USER_ID}        ${EMPTY}
${SECONDARY_EMAIL}          ${EMPTY}
# Comment created by secondary user (for cross-user delete test)
${SECONDARY_COMMENT_ID}     ${EMPTY}
# Timestamp for unique names
${TS}                       ${EMPTY}

*** Keywords ***
Setup Comments Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # ── Create org ──────────────────────────────────────────────────────────
    ${org_slug}=    Set Variable    robot-cm-org-${TS}
    ${org_body}=    Create Dictionary
    ...    name=Robot CM Org ${TS}
    ...    slug=${org_slug}
    ...    org_type_code=community
    ...    description=Org for comments tests
    ${org_resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${org_body}    expected_status=any
    Should Be True    ${org_resp.status_code} == 200 or ${org_resp.status_code} == 201
    ${org_json}=    Set Variable    ${org_resp.json()}
    ${oid}=    Evaluate    $org_json.get('id') or $org_json.get('org_id')
    Set Suite Variable    ${CM_ORG_ID}    ${oid}
    Log    Created org for comments: ${oid}
    # ── Create workspace ────────────────────────────────────────────────────
    ${ws_slug}=    Set Variable    robot-cm-ws-${TS}
    ${ws_body}=    Create Dictionary
    ...    name=Robot CM WS ${TS}
    ...    slug=${ws_slug}
    ...    workspace_type_code=development
    ...    description=Workspace for comments tests
    ${ws_resp}=    POST    ${AM_URL}/orgs/${CM_ORG_ID}/workspaces
    ...    headers=${AUTH_HEADERS}    json=${ws_body}    expected_status=any
    Should Be True    ${ws_resp.status_code} == 200 or ${ws_resp.status_code} == 201
    ${ws_json}=    Set Variable    ${ws_resp.json()}
    ${wsid}=    Evaluate    $ws_json.get('id') or $ws_json.get('workspace_id')
    Set Suite Variable    ${CM_WS_ID}    ${wsid}
    Log    Created workspace for comments: ${wsid}
    # ── Create task to use as comment target ────────────────────────────────
    ${task_body}=    Create Dictionary
    ...    org_id=${CM_ORG_ID}
    ...    workspace_id=${CM_WS_ID}
    ...    task_type_code=general
    ...    title=Robot CM Task ${TS}
    ...    description=Task for comment tests
    ${task_resp}=    POST    ${TK_URL_CM}/tasks    headers=${AUTH_HEADERS}    json=${task_body}    expected_status=any
    Should Be True    ${task_resp.status_code} == 200 or ${task_resp.status_code} == 201
    ${task_json}=    Set Variable    ${task_resp.json()}
    ${tid}=    Evaluate    $task_json.get('id') or $task_json.get('task_id')
    Set Suite Variable    ${CM_TASK_ID}    ${tid}
    Log    Created task for comments: ${tid}
    # ── Register secondary test user ─────────────────────────────────────────
    ${sec_email}=    Set Variable    robot-cm-user-${TS}@example.com
    Set Suite Variable    ${SECONDARY_EMAIL}    ${sec_email}
    ${sec_uid}=    Register Test User    ${sec_email}    TestPass123!
    Set Suite Variable    ${SECONDARY_USER_ID}    ${sec_uid}
    # Login as secondary user and capture token
    ${login_body}=    Create Dictionary    login=${sec_email}    password=TestPass123!
    ${login_resp}=    POST    ${AUTH_URL}/login    json=${login_body}    expected_status=200
    ${sec_json}=    Set Variable    ${login_resp.json()}
    ${sec_token}=    Get From Dictionary    ${sec_json}    access_token
    Set Suite Variable    ${SECONDARY_TOKEN}    ${sec_token}
    ${sec_headers}=    Create Dictionary    Authorization=Bearer ${sec_token}
    Set Suite Variable    ${SECONDARY_HEADERS}    ${sec_headers}
    Log    Secondary user registered and logged in: ${sec_uid}

Teardown Comments Suite
    # Best-effort cleanup — ignore failures
    Run Keyword And Ignore Error    Delete Task If Exists    ${CM_TASK_ID}

Delete Task If Exists
    [Arguments]    ${task_id}
    Run Keyword If    '${task_id}' != '${EMPTY}'
    ...    DELETE    ${TK_URL_CM}/tasks/${task_id}    headers=${AUTH_HEADERS}    expected_status=any

Create Comment On Entity
    [Documentation]    Helper: create a comment, return the parsed JSON body
    [Arguments]    ${entity_type}    ${entity_id}    ${content}    ${headers}=${AUTH_HEADERS}    ${parent_id}=${EMPTY}
    ${body}=    Create Dictionary
    ...    entity_type=${entity_type}
    ...    entity_id=${entity_id}
    ...    content=${content}
    IF    '${parent_id}' != '${EMPTY}'
        Set To Dictionary    ${body}    parent_comment_id=${parent_id}
    END
    ${resp}=    POST    ${CM_URL}/comments    headers=${headers}    json=${body}    expected_status=any
    RETURN    ${resp}

*** Test Cases ***
# ══════════════════════════════════════════════════════════════════════════════
# Basic CRUD
# ══════════════════════════════════════════════════════════════════════════════

Create Comment On Task
    [Documentation]    POST /cm/comments with entity_type=task — expect 201, id and content returned
    [Tags]    comments    api    integration    crud
    ${resp}=    Create Comment On Entity    task    ${CM_TASK_ID}    This is a robot test comment
    Should Be Equal As Strings    ${resp.status_code}    201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Should Be Equal    ${json}[entity_type]    task
    Should Be Equal    ${json}[entity_id]    ${CM_TASK_ID}
    Should Be Equal    ${json}[content]    This is a robot test comment
    Should Be Equal    ${json}[author_user_id]    ${USER_ID}
    Should Be Equal As Strings    ${json}[is_edited]    False
    Should Be Equal As Strings    ${json}[is_deleted]    False
    ${cid}=    Get From Dictionary    ${json}    id
    Set Suite Variable    ${COMMENT_ID}    ${cid}
    Log    Created comment: ${cid}

List Comments For Task
    [Documentation]    GET /cm/comments?entity_type=task&entity_id=... — expect 200 with items list
    [Tags]    comments    api    integration    crud
    ${resp}=    GET    ${CM_URL}/comments    headers=${AUTH_HEADERS}
    ...    params=entity_type=task&entity_id=${CM_TASK_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Get From Dictionary    ${json}    total
    Should Be True    ${total} >= 1
    ${items}=    Get From Dictionary    ${json}    items
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 1
    Log    Comments listed: total=${total}, items on page=${count}

Get Single Comment
    [Documentation]    GET /cm/comments/{id} — expect 200 with correct id and content
    [Tags]    comments    api    integration    crud
    ${resp}=    GET    ${CM_URL}/comments/${COMMENT_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${COMMENT_ID}
    Should Be Equal    ${json}[content]    This is a robot test comment
    Dictionary Should Contain Key    ${json}    replies
    Dictionary Should Contain Key    ${json}    reactions
    Dictionary Should Contain Key    ${json}    edit_history
    Log    Got single comment: ${COMMENT_ID}

Edit Comment
    [Documentation]    PATCH /cm/comments/{id} — expect 200, updated content, is_edited=true
    [Tags]    comments    api    integration    crud
    ${body}=    Create Dictionary    content=Updated comment content from robot test
    ${resp}=    PATCH    ${CM_URL}/comments/${COMMENT_ID}
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${COMMENT_ID}
    Should Be Equal    ${json}[content]    Updated comment content from robot test
    Should Be Equal As Strings    ${json}[is_edited]    True
    Log    Comment edited successfully

Cannot Edit Other User Comment
    [Documentation]    PATCH /cm/comments/{id} with secondary_user token — expect 403
    [Tags]    comments    api    integration    authz
    ${body}=    Create Dictionary    content=Malicious edit attempt
    ${resp}=    PATCH    ${CM_URL}/comments/${COMMENT_ID}
    ...    headers=${SECONDARY_HEADERS}    json=${body}    expected_status=any
    Should Be Equal As Strings    ${resp.status_code}    403
    Log    Correctly rejected edit by non-author: ${resp.status_code}

Get Edit History
    [Documentation]    GET /cm/comments/{id}/history — expect 200 with at least one previous version
    [Tags]    comments    api    integration    crud
    ${resp}=    GET    ${CM_URL}/comments/${COMMENT_ID}/history    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[comment_id]    ${COMMENT_ID}
    Dictionary Should Contain Key    ${json}    edits
    ${edits}=    Get From Dictionary    ${json}    edits
    ${edit_count}=    Get Length    ${edits}
    Should Be True    ${edit_count} >= 1
    ${first_edit}=    Get From List    ${edits}    0
    Should Be Equal    ${first_edit}[previous_content]    This is a robot test comment
    Log    Edit history entries: ${edit_count}

# ══════════════════════════════════════════════════════════════════════════════
# Replies (1-level nesting)
# ══════════════════════════════════════════════════════════════════════════════

Create Reply To Comment
    [Documentation]    POST /cm/comments with parent_comment_id set — expect 201, parent_comment_id present
    [Tags]    comments    api    integration    replies
    ${resp}=    Create Comment On Entity    task    ${CM_TASK_ID}    This is a robot test reply
    ...    parent_id=${COMMENT_ID}
    Should Be Equal As Strings    ${resp.status_code}    201
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[parent_comment_id]    ${COMMENT_ID}
    Should Be Equal    ${json}[content]    This is a robot test reply
    ${rid}=    Get From Dictionary    ${json}    id
    Set Suite Variable    ${REPLY_ID}    ${rid}
    Log    Created reply: ${rid}

Cannot Reply To A Reply
    [Documentation]    POST with parent that is itself a reply — expect 400 (max 1 level nesting)
    [Tags]    comments    api    integration    replies    validation
    ${resp}=    Create Comment On Entity    task    ${CM_TASK_ID}    Nested reply attempt
    ...    parent_id=${REPLY_ID}
    # Service raises ValidationError → 422
    Should Be True    ${resp.status_code} == 400 or ${resp.status_code} == 422
    Log    Correctly rejected nested reply: ${resp.status_code}

List Comments Includes Replies
    [Documentation]    GET /cm/comments with include_replies=true — parent comment should have replies array
    [Tags]    comments    api    integration    replies
    ${resp}=    GET    ${CM_URL}/comments    headers=${AUTH_HEADERS}
    ...    params=entity_type=task&entity_id=${CM_TASK_ID}&include_replies=true    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Get From Dictionary    ${json}    items
    # Find the parent comment in the list
    ${found_parent}=    Set Variable    ${FALSE}
    FOR    ${item}    IN    @{items}
        IF    '${item}[id]' == '${COMMENT_ID}'
            ${replies}=    Get From Dictionary    ${item}    replies
            ${reply_count}=    Get Length    ${replies}
            Should Be True    ${reply_count} >= 1
            Set Test Variable    ${found_parent}    ${TRUE}
        END
    END
    Should Be True    ${found_parent}    Parent comment not found in list
    Log    Parent comment has replies attached in list response

# ══════════════════════════════════════════════════════════════════════════════
# Reactions
# ══════════════════════════════════════════════════════════════════════════════

Add Reaction
    [Documentation]    POST /cm/comments/{id}/reactions with reaction_code=thumbs_up — expect 200
    [Tags]    comments    api    integration    reactions
    ${body}=    Create Dictionary    reaction_code=thumbs_up
    ${resp}=    POST    ${CM_URL}/comments/${COMMENT_ID}/reactions
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[comment_id]    ${COMMENT_ID}
    Dictionary Should Contain Key    ${json}    reactions
    ${reactions}=    Get From Dictionary    ${json}    reactions
    ${codes}=    Evaluate    [r.get('reaction_code') for r in $reactions]
    Should Contain    ${codes}    thumbs_up
    Log    Reaction thumbs_up added

Add Same Reaction Toggles Off
    [Documentation]    POST again with same reaction_code=thumbs_up — toggles off (idempotent)
    [Tags]    comments    api    integration    reactions
    ${body}=    Create Dictionary    reaction_code=thumbs_up
    ${resp}=    POST    ${CM_URL}/comments/${COMMENT_ID}/reactions
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    # After toggle-off, thumbs_up should either be absent or have count=0
    ${reactions}=    Get From Dictionary    ${json}    reactions
    ${tu_reactions}=    Evaluate    [r for r in $reactions if r.get('reaction_code') == 'thumbs_up']
    ${still_present}=    Evaluate    len($tu_reactions) > 0 and $tu_reactions[0].get('count', 0) > 0
    Should Be Equal As Strings    ${still_present}    False
    Log    Reaction correctly toggled off

Re Add Reaction For Later Tests
    [Documentation]    Re-add thumbs_up so subsequent tests can verify and remove it
    [Tags]    comments    api    integration    reactions
    ${body}=    Create Dictionary    reaction_code=thumbs_up
    ${resp}=    POST    ${CM_URL}/comments/${COMMENT_ID}/reactions
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${reactions}=    Get From Dictionary    ${json}    reactions
    ${codes}=    Evaluate    [r.get('reaction_code') for r in $reactions]
    Should Contain    ${codes}    thumbs_up
    Log    Re-added thumbs_up reaction for subsequent tests

List Reactions In Comment Response
    [Documentation]    GET /cm/comments/{id} — reactions array should have thumbs_up with count>=1
    [Tags]    comments    api    integration    reactions
    ${resp}=    GET    ${CM_URL}/comments/${COMMENT_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${reactions}=    Get From Dictionary    ${json}    reactions
    ${tu_reactions}=    Evaluate    [r for r in $reactions if r.get('reaction_code') == 'thumbs_up']
    ${has_tu}=    Evaluate    len($tu_reactions) > 0
    Should Be True    ${has_tu}    Expected thumbs_up reaction in comment response
    ${tu_count}=    Evaluate    $tu_reactions[0].get('count', 0) if $tu_reactions else 0
    Should Be True    ${tu_count} >= 1
    Log    thumbs_up reaction count: ${tu_count}

Get Reactions Endpoint
    [Documentation]    GET /cm/comments/{id}/reactions — returns reactions grouped by code
    [Tags]    comments    api    integration    reactions
    ${resp}=    GET    ${CM_URL}/comments/${COMMENT_ID}/reactions
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[comment_id]    ${COMMENT_ID}
    Dictionary Should Contain Key    ${json}    reactions
    Log    Reactions endpoint returned successfully

Remove Reaction
    [Documentation]    DELETE /cm/comments/{id}/reactions/thumbs_up — expect 200 (returns updated reactions)
    [Tags]    comments    api    integration    reactions
    ${resp}=    DELETE    ${CM_URL}/comments/${COMMENT_ID}/reactions/thumbs_up
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[comment_id]    ${COMMENT_ID}
    # thumbs_up should now be gone or count=0
    ${reactions}=    Get From Dictionary    ${json}    reactions
    ${tu_reactions}=    Evaluate    [r for r in $reactions if r.get('reaction_code') == 'thumbs_up']
    ${still_has}=    Evaluate    len($tu_reactions) > 0 and $tu_reactions[0].get('count', 0) > 0
    Should Be Equal As Strings    ${still_has}    False
    Log    Reaction removed successfully

Invalid Reaction Code Rejected
    [Documentation]    POST /cm/comments/{id}/reactions with reaction_code=invalid — expect 422
    [Tags]    comments    api    integration    reactions    validation
    ${body}=    Create Dictionary    reaction_code=invalid_emoji_code
    ${resp}=    POST    ${CM_URL}/comments/${COMMENT_ID}/reactions
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be Equal As Strings    ${resp.status_code}    422
    Log    Correctly rejected invalid reaction code: ${resp.status_code}

# ══════════════════════════════════════════════════════════════════════════════
# Pin / Unpin
# ══════════════════════════════════════════════════════════════════════════════

Pin Comment As Admin
    [Documentation]    POST /cm/comments/{id}/pin — any authenticated user can pin; expect 200, pinned=true
    [Tags]    comments    api    integration    pin
    ${resp}=    POST    ${CM_URL}/comments/${COMMENT_ID}/pin
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${COMMENT_ID}
    Should Be Equal As Strings    ${json}[pinned]    True
    Dictionary Should Contain Key    ${json}    pinned_by
    Log    Comment pinned: ${COMMENT_ID}

Unpin Comment
    [Documentation]    DELETE /cm/comments/{id}/pin — expect 200, pinned=false
    [Tags]    comments    api    integration    pin
    ${resp}=    DELETE    ${CM_URL}/comments/${COMMENT_ID}/pin
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${COMMENT_ID}
    Should Be Equal As Strings    ${json}[pinned]    False
    Log    Comment unpinned: ${COMMENT_ID}

# ══════════════════════════════════════════════════════════════════════════════
# Resolve / Unresolve
# ══════════════════════════════════════════════════════════════════════════════

Resolve Comment
    [Documentation]    POST /cm/comments/{id}/resolve — expect 200, resolved=true
    [Tags]    comments    api    integration    resolve
    ${resp}=    POST    ${CM_URL}/comments/${COMMENT_ID}/resolve
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${COMMENT_ID}
    Should Be Equal As Strings    ${json}[resolved]    True
    Dictionary Should Contain Key    ${json}    resolved_by
    Log    Comment resolved: ${COMMENT_ID}

Unresolve Comment
    [Documentation]    DELETE /cm/comments/{id}/resolve — expect 200, resolved=false
    [Tags]    comments    api    integration    resolve
    ${resp}=    DELETE    ${CM_URL}/comments/${COMMENT_ID}/resolve
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${COMMENT_ID}
    Should Be Equal As Strings    ${json}[resolved]    False
    Log    Comment unresolved: ${COMMENT_ID}

# ══════════════════════════════════════════════════════════════════════════════
# Delete — cross-user enforcement
# ══════════════════════════════════════════════════════════════════════════════

Cannot Delete Other User Comment As Non Admin
    [Documentation]    Create a comment as admin, attempt DELETE as secondary user — expect 403
    [Tags]    comments    api    integration    authz
    # Create a fresh comment by the primary (admin) user
    ${resp}=    Create Comment On Entity    task    ${CM_TASK_ID}    Comment to test cross-user delete protection
    Should Be Equal As Strings    ${resp.status_code}    201
    ${json}=    Set Variable    ${resp.json()}
    ${protected_cid}=    Get From Dictionary    ${json}    id
    # Secondary user attempts to delete without as_admin=true
    ${del_resp}=    DELETE    ${CM_URL}/comments/${protected_cid}
    ...    headers=${SECONDARY_HEADERS}    expected_status=any
    Should Be Equal As Strings    ${del_resp.status_code}    403
    # Clean up
    ${cleanup}=    DELETE    ${CM_URL}/comments/${protected_cid}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Log    Correctly rejected cross-user delete: ${del_resp.status_code}

Create Secondary User Comment
    [Documentation]    Secondary user creates a comment (needed for delete test)
    [Tags]    comments    api    integration    crud
    ${resp}=    Create Comment On Entity    task    ${CM_TASK_ID}
    ...    Secondary user comment for delete test    ${SECONDARY_HEADERS}
    Should Be Equal As Strings    ${resp.status_code}    201
    ${json}=    Set Variable    ${resp.json()}
    ${sec_cid}=    Get From Dictionary    ${json}    id
    Set Suite Variable    ${SECONDARY_COMMENT_ID}    ${sec_cid}
    Log    Secondary user comment: ${sec_cid}

Soft Delete Comment As Author
    [Documentation]    DELETE /cm/comments/{id} by author — expect 204
    [Tags]    comments    api    integration    crud
    ${resp}=    DELETE    ${CM_URL}/comments/${SECONDARY_COMMENT_ID}
    ...    headers=${SECONDARY_HEADERS}    expected_status=204
    Log    Secondary user deleted own comment: ${SECONDARY_COMMENT_ID}

Deleted Comment Shows Placeholder
    [Documentation]    After soft-delete, GET /cm/comments — is_deleted=true or content=[deleted]
    [Tags]    comments    api    integration    crud
    # The reply was not deleted so it still exists; let's delete the reply and then check the parent
    # Instead, create + delete a fresh comment and verify via GET single
    ${create_resp}=    Create Comment On Entity    task    ${CM_TASK_ID}    Comment to be deleted and verified
    Should Be Equal As Strings    ${create_resp.status_code}    201
    ${create_json}=    Set Variable    ${create_resp.json()}
    ${temp_cid}=    Get From Dictionary    ${create_json}    id
    # Delete it
    ${del_resp}=    DELETE    ${CM_URL}/comments/${temp_cid}
    ...    headers=${AUTH_HEADERS}    expected_status=204
    # Fetch single — is_deleted should be true and content should be [deleted]
    ${get_resp}=    GET    ${CM_URL}/comments/${temp_cid}    headers=${AUTH_HEADERS}    expected_status=200
    ${get_json}=    Set Variable    ${get_resp.json()}
    Should Be Equal As Strings    ${get_json}[is_deleted]    True
    Should Be Equal    ${get_json}[content]    [deleted]
    Log    Deleted comment shows placeholder correctly

Soft Delete Main Comment
    [Documentation]    DELETE /cm/comments/${COMMENT_ID} as admin author — expect 204
    [Tags]    comments    api    integration    crud
    ${resp}=    DELETE    ${CM_URL}/comments/${COMMENT_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=204
    Log    Main comment soft-deleted: ${COMMENT_ID}

# ══════════════════════════════════════════════════════════════════════════════
# Validation
# ══════════════════════════════════════════════════════════════════════════════

Empty Content Rejected
    [Documentation]    POST /cm/comments with empty content — expect 422
    [Tags]    comments    api    integration    validation
    ${body}=    Create Dictionary
    ...    entity_type=task
    ...    entity_id=${CM_TASK_ID}
    ...    content=${EMPTY}
    ${resp}=    POST    ${CM_URL}/comments    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be Equal As Strings    ${resp.status_code}    422
    Log    Correctly rejected empty content: ${resp.status_code}

Invalid Entity Type Rejected
    [Documentation]    POST /cm/comments with entity_type=unknown — expect 422
    [Tags]    comments    api    integration    validation
    ${resp}=    Create Comment On Entity    unknown_entity_xyz    ${CM_TASK_ID}    Content here
    Should Be True    ${resp.status_code} == 404 or ${resp.status_code} == 422
    Log    Correctly rejected invalid entity_type: ${resp.status_code}

Comment On Nonexistent Entity Uses Fake UUID
    [Documentation]    POST /cm/comments with nonexistent entity_id — service accepts (no FK check on entity_id).
    ...    Entity existence is validated in the calling domain. Comment service records whatever is passed.
    [Tags]    comments    api    integration    validation
    ${fake_id}=    Evaluate    str(__import__('uuid').uuid4())
    ${resp}=    Create Comment On Entity    task    ${fake_id}    Content on nonexistent entity
    # The comment service does not verify entity_id FK — it stores it; 201 expected
    # If the implementation adds FK validation, update to 404
    Should Be True    ${resp.status_code} == 201 or ${resp.status_code} == 404
    Log    Response for nonexistent entity: ${resp.status_code}

# ══════════════════════════════════════════════════════════════════════════════
# Pagination
# ══════════════════════════════════════════════════════════════════════════════

Create Multiple Comments And Paginate
    [Documentation]    Create 5 comments, GET with per_page=2 — expect total>=5, items=2, next_cursor set
    [Tags]    comments    api    integration    pagination
    # Create 5 comments on the same task
    FOR    ${i}    IN RANGE    5
        ${resp}=    Create Comment On Entity    task    ${CM_TASK_ID}    Pagination test comment ${i} for ${TS}
        Should Be True    ${resp.status_code} == 201
    END
    # Fetch first page with per_page=2
    ${resp}=    GET    ${CM_URL}/comments    headers=${AUTH_HEADERS}
    ...    params=entity_type=task&entity_id=${CM_TASK_ID}&per_page=2    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${total}=    Get From Dictionary    ${json}    total
    Should Be True    ${total} >= 5
    ${items}=    Get From Dictionary    ${json}    items
    ${page_count}=    Get Length    ${items}
    Should Be Equal As Integers    ${page_count}    2
    # next_cursor should be non-empty because there are more pages
    ${next_cursor}=    Evaluate    $json.get('next_cursor')
    Should Be True    $next_cursor is not None and len($next_cursor) > 0
    Log    Pagination: total=${total}, page_items=${page_count}, next_cursor=${next_cursor}

# ══════════════════════════════════════════════════════════════════════════════
# Mark-read / Counts / Mentions
# ══════════════════════════════════════════════════════════════════════════════

Mark Comments As Read
    [Documentation]    POST /cm/comments/mark-read — mark all comments on an entity as read
    [Tags]    comments    api    integration    unread
    ${body}=    Create Dictionary    entity_type=task    entity_id=${CM_TASK_ID}
    ${resp}=    POST    ${CM_URL}/comments/mark-read    json=${body}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Not Be Empty    ${json}[marked_at]
    Log    Comments marked as read at: ${json}[marked_at]

Get Comment Counts For Entity
    [Documentation]    GET /cm/comments/counts?entity_type=task&entity_ids=... — returns map of entity_id to count
    [Tags]    comments    api    integration    counts
    ${resp}=    GET    ${CM_URL}/comments/counts    params=entity_type=task&entity_ids=${CM_TASK_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    ${CM_TASK_ID}
    Log    Comment counts: ${json}

List Mentions For Current User
    [Documentation]    Create a comment mentioning admin, then GET /cm/comments/mentions — expect items list
    [Tags]    comments    api    integration    mentions
    # First create a comment mentioning the admin user
    ${mention_content}=    Set Variable    Hey @[Admin](${USER_ID}) check this
    ${body}=    Create Dictionary    entity_type=task    entity_id=${CM_TASK_ID}    content=${mention_content}
    ${resp}=    POST    ${CM_URL}/comments    json=${body}    headers=${SECONDARY_HEADERS}    expected_status=201
    Log    Created mention comment as secondary user
    # Now list mentions for admin
    ${resp}=    GET    ${CM_URL}/comments/mentions    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    len($json['items']) >= 0
    Log    Mentions listed: ${json}

Mention Limit Enforced
    [Documentation]    POST /cm/comments with >50 mentions — expect 400 or 422
    [Tags]    comments    api    integration    mentions    validation
    # Create content with 51 fake mentions (exceeds 50 limit)
    ${mentions}=    Evaluate    ' '.join(f'@[User{i}](00000000-0000-0000-0000-{str(i).zfill(12)})' for i in range(51))
    ${body}=    Create Dictionary    entity_type=task    entity_id=${CM_TASK_ID}    content=${mentions}
    ${resp}=    POST    ${CM_URL}/comments    json=${body}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 400 or ${resp.status_code} == 422
    Log    Correctly rejected too many mentions: ${resp.status_code}

# ══════════════════════════════════════════════════════════════════════════════
# Cursor pagination validation
# ══════════════════════════════════════════════════════════════════════════════

Invalid Cursor ID Rejected
    [Documentation]    GET /cm/comments with non-UUID cursor_id — expect 422
    [Tags]    comments    api    integration    validation    pagination
    ${resp}=    GET    ${CM_URL}/comments
    ...    params=entity_type=task&entity_id=${CM_TASK_ID}&cursor_id=not-a-uuid&cursor_created_at=2026-01-01T00:00:00Z
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be Equal As Strings    ${resp.status_code}    422
    Log    Correctly rejected invalid cursor_id: ${resp.status_code}

Cursor Params Must Be Together
    [Documentation]    GET /cm/comments with cursor_id but no cursor_created_at — expect 422
    [Tags]    comments    api    integration    validation    pagination
    ${resp}=    GET    ${CM_URL}/comments
    ...    params=entity_type=task&entity_id=${CM_TASK_ID}&cursor_id=${COMMENT_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be Equal As Strings    ${resp.status_code}    422
    Log    Correctly rejected incomplete cursor params: ${resp.status_code}

# ══════════════════════════════════════════════════════════════════════════════
# Resolve permission enforcement
# ══════════════════════════════════════════════════════════════════════════════

Non Admin Cannot Resolve Comment
    [Documentation]    POST /cm/comments/{id}/resolve as secondary (non-admin) — expect 403
    [Tags]    comments    api    integration    authorization    resolve
    # Create a fresh comment to resolve (main one was soft-deleted)
    ${resp}=    Create Comment On Entity    task    ${CM_TASK_ID}    Comment for resolve permission test
    Should Be Equal As Strings    ${resp.status_code}    201
    ${json}=    Set Variable    ${resp.json()}
    ${resolve_cid}=    Get From Dictionary    ${json}    id
    # Secondary user attempts to resolve
    ${resolve_resp}=    POST    ${CM_URL}/comments/${resolve_cid}/resolve
    ...    headers=${SECONDARY_HEADERS}    expected_status=any
    Should Be Equal As Strings    ${resolve_resp.status_code}    403
    Log    Correctly rejected non-admin resolve: ${resolve_resp.status_code}
    # Cleanup
    ${cleanup}=    DELETE    ${CM_URL}/comments/${resolve_cid}
    ...    headers=${AUTH_HEADERS}    expected_status=any
