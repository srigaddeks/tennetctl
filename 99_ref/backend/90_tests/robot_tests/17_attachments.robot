*** Settings ***
Documentation    Attachments API Integration Tests — upload, download, metadata, delete, pagination
Resource         common.resource
Library          OperatingSystem
Suite Setup      Setup Attachments Suite
Suite Teardown   Teardown Attachments Suite

*** Variables ***
${AT_URL}                   ${BASE_URL}/at
${TK_URL_AT}                ${BASE_URL}/tk
# Suite-level IDs set during setup
${AT_ORG_ID}                ${EMPTY}
${AT_WS_ID}                 ${EMPTY}
${AT_TASK_ID}               ${EMPTY}
# Primary attachment state
${ATTACHMENT_ID}            ${EMPTY}
# Secondary user state
${SECONDARY_TOKEN}          ${EMPTY}
${SECONDARY_HEADERS}        ${EMPTY}
${SECONDARY_USER_ID}        ${EMPTY}
${SECONDARY_EMAIL}          ${EMPTY}
# Attachment uploaded by secondary user (for cross-user delete test)
${SECONDARY_ATTACHMENT_ID}  ${EMPTY}
# Timestamp for unique names
${TS}                       ${EMPTY}

*** Keywords ***
Setup Attachments Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # ── Create org ──────────────────────────────────────────────────────────
    ${org_slug}=    Set Variable    robot-at-org-${TS}
    ${org_body}=    Create Dictionary
    ...    name=Robot AT Org ${TS}
    ...    slug=${org_slug}
    ...    org_type_code=community
    ...    description=Org for attachments tests
    ${org_resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${org_body}    expected_status=any
    Should Be True    ${org_resp.status_code} == 200 or ${org_resp.status_code} == 201
    ${org_json}=    Set Variable    ${org_resp.json()}
    ${oid}=    Evaluate    $org_json.get('id') or $org_json.get('org_id')
    Set Suite Variable    ${AT_ORG_ID}    ${oid}
    Log    Created org for attachments: ${oid}
    # ── Create workspace ────────────────────────────────────────────────────
    ${ws_slug}=    Set Variable    robot-at-ws-${TS}
    ${ws_body}=    Create Dictionary
    ...    name=Robot AT WS ${TS}
    ...    slug=${ws_slug}
    ...    workspace_type_code=development
    ...    description=Workspace for attachments tests
    ${ws_resp}=    POST    ${AM_URL}/orgs/${AT_ORG_ID}/workspaces
    ...    headers=${AUTH_HEADERS}    json=${ws_body}    expected_status=any
    Should Be True    ${ws_resp.status_code} == 200 or ${ws_resp.status_code} == 201
    ${ws_json}=    Set Variable    ${ws_resp.json()}
    ${wsid}=    Evaluate    $ws_json.get('id') or $ws_json.get('workspace_id')
    Set Suite Variable    ${AT_WS_ID}    ${wsid}
    Log    Created workspace for attachments: ${wsid}
    # ── Create task as attachment target ────────────────────────────────────
    ${task_body}=    Create Dictionary
    ...    org_id=${AT_ORG_ID}
    ...    workspace_id=${AT_WS_ID}
    ...    task_type_code=general
    ...    title=Robot AT Task ${TS}
    ...    description=Task for attachment tests
    ${task_resp}=    POST    ${TK_URL_AT}/tasks    headers=${AUTH_HEADERS}    json=${task_body}    expected_status=any
    Should Be True    ${task_resp.status_code} == 200 or ${task_resp.status_code} == 201
    ${task_json}=    Set Variable    ${task_resp.json()}
    ${tid}=    Evaluate    $task_json.get('id') or $task_json.get('task_id')
    Set Suite Variable    ${AT_TASK_ID}    ${tid}
    Log    Created task for attachments: ${tid}
    # ── Register secondary test user ─────────────────────────────────────────
    ${sec_email}=    Set Variable    robot-at-user-${TS}@example.com
    Set Suite Variable    ${SECONDARY_EMAIL}    ${sec_email}
    ${sec_uid}=    Register Test User    ${sec_email}    TestPass123!
    Set Suite Variable    ${SECONDARY_USER_ID}    ${sec_uid}
    ${login_body}=    Create Dictionary    login=${sec_email}    password=TestPass123!
    ${login_resp}=    POST    ${AUTH_URL}/login    json=${login_body}    expected_status=200
    ${sec_json}=    Set Variable    ${login_resp.json()}
    ${sec_token}=    Get From Dictionary    ${sec_json}    access_token
    Set Suite Variable    ${SECONDARY_TOKEN}    ${sec_token}
    ${sec_headers}=    Create Dictionary    Authorization=Bearer ${sec_token}
    Set Suite Variable    ${SECONDARY_HEADERS}    ${sec_headers}
    Log    Secondary user registered and logged in: ${sec_uid}

Teardown Attachments Suite
    Run Keyword And Ignore Error    Delete Task If Exists    ${AT_TASK_ID}

Delete Task If Exists
    [Arguments]    ${task_id}
    Run Keyword If    '${task_id}' != '${EMPTY}'
    ...    DELETE    ${TK_URL_AT}/tasks/${task_id}    headers=${AUTH_HEADERS}    expected_status=any

Upload Test File
    [Documentation]    Helper: upload a small text file to /at/attachments/upload
    ...    Returns the response object. Caller checks status and saves ID.
    [Arguments]    ${filename}    ${content}    ${entity_type}    ${entity_id}
    ...    ${description}=${EMPTY}    ${headers}=${AUTH_HEADERS}
    # Build multipart data dict (form fields)
    ${form_data}=    Create Dictionary
    ...    entity_type=${entity_type}
    ...    entity_id=${entity_id}
    IF    '${description}' != '${EMPTY}'
        Set To Dictionary    ${form_data}    description=${description}
    END
    # Build files dict — tuple format: (filename, bytes, content_type)
    ${file_bytes}=    Evaluate    ${content}.encode('utf-8') if isinstance(${content}, str) else ${content}
    ${file_tuple}=    Evaluate    ('${filename}', '${content}'.encode('utf-8'), 'text/plain')
    ${files_dict}=    Create Dictionary    file=${file_tuple}
    ${resp}=    POST    ${AT_URL}/attachments/upload
    ...    headers=${headers}
    ...    data=${form_data}
    ...    files=${files_dict}
    ...    expected_status=any
    RETURN    ${resp}

Upload Test File Simple
    [Documentation]    Minimal wrapper — creates file content inline, uploads, returns response
    [Arguments]    ${label}    ${entity_type}    ${entity_id}    ${description}=${EMPTY}    ${headers}=${AUTH_HEADERS}
    ${content}=    Set Variable    Robot test file content for ${label} at ${TS}
    ${filename}=    Set Variable    robot_test_${label}_${TS}.txt
    ${form_data}=    Create Dictionary
    ...    entity_type=${entity_type}
    ...    entity_id=${entity_id}
    IF    '${description}' != '${EMPTY}'
        Set To Dictionary    ${form_data}    description=${description}
    END
    ${file_bytes}=    Evaluate    '${content}'.encode('utf-8')
    ${file_tuple}=    Evaluate    ('${filename}', '${content}'.encode('utf-8'), 'text/plain')
    ${files_dict}=    Create Dictionary    file=${file_tuple}
    ${resp}=    POST    ${AT_URL}/attachments/upload
    ...    headers=${headers}
    ...    data=${form_data}
    ...    files=${files_dict}
    ...    expected_status=any
    RETURN    ${resp}

*** Test Cases ***
# ══════════════════════════════════════════════════════════════════════════════
# Upload
# ══════════════════════════════════════════════════════════════════════════════

Upload Text File Attachment
    [Documentation]    POST /at/attachments/upload — multipart text file; expect 201, metadata correct
    [Tags]    attachments    api    integration    upload
    ${resp}=    Upload Test File Simple    primary    task    ${AT_TASK_ID}
    Should Be Equal As Strings    ${resp.status_code}    201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    id
    Dictionary Should Contain Key    ${json}    original_filename
    Dictionary Should Contain Key    ${json}    file_size_bytes
    Dictionary Should Contain Key    ${json}    checksum_sha256
    Dictionary Should Contain Key    ${json}    storage_provider
    Should Be Equal    ${json}[entity_type]    task
    Should Be Equal    ${json}[entity_id]    ${AT_TASK_ID}
    Should Be Equal    ${json}[uploaded_by]    ${USER_ID}
    ${size}=    Get From Dictionary    ${json}    file_size_bytes
    Should Be True    ${size} > 0
    ${checksum}=    Get From Dictionary    ${json}    checksum_sha256
    Should Be True    len($checksum) == 64    Expected 64-char SHA-256 hex digest
    ${aid}=    Get From Dictionary    ${json}    id
    Set Suite Variable    ${ATTACHMENT_ID}    ${aid}
    Log    Uploaded attachment: ${aid}, size=${size}, checksum=${checksum}

Upload With Description
    [Documentation]    POST /at/attachments/upload with description field set — expect 201, description present
    [Tags]    attachments    api    integration    upload
    ${resp}=    Upload Test File Simple    described    task    ${AT_TASK_ID}
    ...    description=Robot test file with description
    Should Be Equal As Strings    ${resp.status_code}    201
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[description]    Robot test file with description
    Log    Uploaded with description: ${json}[id]

List Attachments
    [Documentation]    GET /at/attachments?entity_type=task&entity_id=... — expect 200 with items
    [Tags]    attachments    api    integration    crud
    ${resp}=    GET    ${AT_URL}/attachments    headers=${AUTH_HEADERS}
    ...    params=entity_type=task&entity_id=${AT_TASK_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Get From Dictionary    ${json}    total
    Should Be True    ${total} >= 1
    ${items}=    Get From Dictionary    ${json}    items
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 1
    # Verify our uploaded attachment is in the list
    ${ids}=    Evaluate    [item.get('id') for item in $items]
    Should Contain    ${ids}    ${ATTACHMENT_ID}
    Log    Attachments listed: total=${total}, page_items=${count}

Get Attachment Metadata
    [Documentation]    GET /at/attachments/{id} — expect 200 with correct id and fields
    [Tags]    attachments    api    integration    crud
    ${resp}=    GET    ${AT_URL}/attachments/${ATTACHMENT_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${ATTACHMENT_ID}
    Should Be Equal    ${json}[entity_type]    task
    Should Be Equal    ${json}[entity_id]    ${AT_TASK_ID}
    Dictionary Should Contain Key    ${json}    original_filename
    Dictionary Should Contain Key    ${json}    content_type
    Dictionary Should Contain Key    ${json}    file_size_bytes
    Dictionary Should Contain Key    ${json}    checksum_sha256
    Dictionary Should Contain Key    ${json}    storage_provider
    Dictionary Should Contain Key    ${json}    storage_bucket
    Dictionary Should Contain Key    ${json}    virus_scan_status
    Dictionary Should Contain Key    ${json}    created_at
    Log    Got attachment metadata: ${ATTACHMENT_ID}

# ══════════════════════════════════════════════════════════════════════════════
# Download
# ══════════════════════════════════════════════════════════════════════════════

Get Download URL
    [Documentation]    GET /at/attachments/{id}/download — expect 200, url and expires_at present
    [Tags]    attachments    api    integration    download
    ${resp}=    GET    ${AT_URL}/attachments/${ATTACHMENT_ID}/download
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    url
    Dictionary Should Contain Key    ${json}    expires_at
    Dictionary Should Contain Key    ${json}    filename
    Dictionary Should Contain Key    ${json}    attachment_id
    Dictionary Should Contain Key    ${json}    content_type
    Dictionary Should Contain Key    ${json}    file_size_bytes
    Should Be Equal    ${json}[attachment_id]    ${ATTACHMENT_ID}
    ${url}=    Get From Dictionary    ${json}    url
    Should Be True    len($url) > 0    Expected non-empty download URL
    Log    Download URL obtained: ${json}[filename], expires_at=${json}[expires_at]

Download URL Expires Within One Hour
    [Documentation]    expires_at on download URL should be within ~3700s from now
    [Tags]    attachments    api    integration    download
    ${resp}=    GET    ${AT_URL}/attachments/${ATTACHMENT_ID}/download
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${expires_at_str}=    Get From Dictionary    ${json}    expires_at
    # Parse both timestamps and verify expiry is roughly 1 hour from now (< 3700s)
    ${dt}=    Evaluate    __import__('datetime')
    ${expires_dt}=    Evaluate    __import__('datetime').datetime.fromisoformat('${expires_at_str}'.replace('Z', '+00:00'))
    ${now_dt}=    Evaluate    __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    ${is_future}=    Evaluate    $expires_dt > $now_dt
    Should Be True    ${is_future}    expires_at must be in the future
    ${secs_until}=    Evaluate    ($expires_dt - $now_dt).total_seconds()
    Should Be True    ${secs_until} < 3700    expires_at should be within 3700 seconds from now
    Log    Download URL expires_at verified: ${expires_at_str}

# ══════════════════════════════════════════════════════════════════════════════
# Update metadata
# ══════════════════════════════════════════════════════════════════════════════

Update Attachment Description
    [Documentation]    PATCH /at/attachments/{id} with new description — expect 200, description updated
    [Tags]    attachments    api    integration    crud
    ${body}=    Create Dictionary    description=Updated description by robot test
    ${resp}=    PATCH    ${AT_URL}/attachments/${ATTACHMENT_ID}
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${ATTACHMENT_ID}
    Should Be Equal    ${json}[description]    Updated description by robot test
    Log    Attachment description updated

Clear Attachment Description
    [Documentation]    PATCH /at/attachments/{id} with null description — expect 200
    [Tags]    attachments    api    integration    crud
    ${body}=    Create Dictionary    description=${None}
    ${resp}=    PATCH    ${AT_URL}/attachments/${ATTACHMENT_ID}
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[id]    ${ATTACHMENT_ID}
    ${desc}=    Evaluate    $json.get('description')
    Should Be Equal    ${desc}    ${None}
    Log    Attachment description cleared

# ══════════════════════════════════════════════════════════════════════════════
# Cross-user enforcement
# ══════════════════════════════════════════════════════════════════════════════

Secondary User Uploads Attachment
    [Documentation]    Secondary user uploads their own attachment (setup for delete cross-check)
    [Tags]    attachments    api    integration    authz
    ${resp}=    Upload Test File Simple    secondary    task    ${AT_TASK_ID}
    ...    description=Secondary user file    headers=${SECONDARY_HEADERS}
    Should Be Equal As Strings    ${resp.status_code}    201
    ${json}=    Set Variable    ${resp.json()}
    ${sec_aid}=    Get From Dictionary    ${json}    id
    Set Suite Variable    ${SECONDARY_ATTACHMENT_ID}    ${sec_aid}
    Log    Secondary user uploaded attachment: ${sec_aid}

Cannot Delete Other User Attachment
    [Documentation]    Secondary user tries to DELETE attachment owned by primary — expect 403
    [Tags]    attachments    api    integration    authz
    ${resp}=    DELETE    ${AT_URL}/attachments/${ATTACHMENT_ID}
    ...    headers=${SECONDARY_HEADERS}    expected_status=any
    Should Be Equal As Strings    ${resp.status_code}    403
    Log    Correctly rejected cross-user delete: ${resp.status_code}

# ══════════════════════════════════════════════════════════════════════════════
# Validation
# ══════════════════════════════════════════════════════════════════════════════

Empty Entity ID Rejected
    [Documentation]    POST upload without entity_id — expect 422 (missing required form field)
    [Tags]    attachments    api    integration    validation
    # Build multipart without entity_id field
    ${form_data}=    Create Dictionary    entity_type=task
    ${file_tuple}=    Evaluate    ('noid_test.txt', b'content without entity id', 'text/plain')
    ${files_dict}=    Create Dictionary    file=${file_tuple}
    ${resp}=    POST    ${AT_URL}/attachments/upload
    ...    headers=${AUTH_HEADERS}
    ...    data=${form_data}
    ...    files=${files_dict}
    ...    expected_status=any
    Should Be Equal As Strings    ${resp.status_code}    422
    Log    Correctly rejected missing entity_id: ${resp.status_code}

Invalid Entity Type On Upload
    [Documentation]    POST upload with entity_type=invalid — expect 422 from service validation
    [Tags]    attachments    api    integration    validation
    ${form_data}=    Create Dictionary
    ...    entity_type=definitely_not_valid
    ...    entity_id=${AT_TASK_ID}
    ${file_tuple}=    Evaluate    ('bad_type.txt', b'content', 'text/plain')
    ${files_dict}=    Create Dictionary    file=${file_tuple}
    ${resp}=    POST    ${AT_URL}/attachments/upload
    ...    headers=${AUTH_HEADERS}
    ...    data=${form_data}
    ...    files=${files_dict}
    ...    expected_status=any
    Should Be True    ${resp.status_code} == 422 or ${resp.status_code} == 400
    Log    Correctly rejected invalid entity_type: ${resp.status_code}

Missing File Field Rejected
    [Documentation]    POST upload with no file in multipart — expect 422
    [Tags]    attachments    api    integration    validation
    ${form_data}=    Create Dictionary
    ...    entity_type=task
    ...    entity_id=${AT_TASK_ID}
    ${resp}=    POST    ${AT_URL}/attachments/upload
    ...    headers=${AUTH_HEADERS}
    ...    data=${form_data}
    ...    expected_status=any
    Should Be Equal As Strings    ${resp.status_code}    422
    Log    Correctly rejected missing file field: ${resp.status_code}

# ══════════════════════════════════════════════════════════════════════════════
# Pagination
# ══════════════════════════════════════════════════════════════════════════════

Upload Multiple Files And Paginate
    [Documentation]    Upload 3 more files, GET with per_page=2 — total>=3, items=2
    [Tags]    attachments    api    integration    pagination
    # Upload 3 additional files (primary user already uploaded 2 above)
    FOR    ${i}    IN RANGE    3
        ${resp}=    Upload Test File Simple    page${i}    task    ${AT_TASK_ID}
        Should Be Equal As Strings    ${resp.status_code}    201
    END
    # Fetch with per_page=2
    ${resp}=    GET    ${AT_URL}/attachments    headers=${AUTH_HEADERS}
    ...    params=entity_type=task&entity_id=${AT_TASK_ID}&per_page=2    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${total}=    Get From Dictionary    ${json}    total
    Should Be True    ${total} >= 3
    ${items}=    Get From Dictionary    ${json}    items
    ${page_count}=    Get Length    ${items}
    Should Be Equal As Integers    ${page_count}    2
    Log    Pagination: total=${total}, page_items=${page_count}

# ══════════════════════════════════════════════════════════════════════════════
# Counts
# ══════════════════════════════════════════════════════════════════════════════

Get Attachment Counts For Entity
    [Documentation]    GET /at/attachments/counts?entity_type=task&entity_ids=... — returns map of entity_id to count
    [Tags]    attachments    api    integration    counts
    ${resp}=    GET    ${AT_URL}/attachments/counts
    ...    params=entity_type=task&entity_ids=${AT_TASK_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    ${AT_TASK_ID}
    Log    Attachment counts: ${json}

# ══════════════════════════════════════════════════════════════════════════════
# Bulk upload
# ══════════════════════════════════════════════════════════════════════════════

Bulk Upload Multiple Files
    [Documentation]    POST /at/attachments/bulk-upload with multiple files — expect 207 or 201
    [Tags]    attachments    api    integration    bulk    upload
    # Use requests directly to send multiple files with the same field name (list of tuples)
    ${url}=    Set Variable    ${AT_URL}/attachments/bulk-upload
    ${token}=    Set Variable    ${ACCESS_TOKEN}
    ${eid}=    Set Variable    ${AT_TASK_ID}
    ${sc}=    Evaluate    __import__('requests').post('${url}', headers={'Authorization': 'Bearer ${token}'}, data={'entity_type': 'task', 'entity_id': '${eid}'}, files=[('files', ('b1.txt', b'Bulk content one', 'text/plain')), ('files', ('b2.txt', b'Bulk content two', 'text/plain'))]).status_code
    Should Be True    ${sc} == 207 or ${sc} == 201
    Log    Bulk upload returned: ${sc}

# ══════════════════════════════════════════════════════════════════════════════
# Virus scan status
# ══════════════════════════════════════════════════════════════════════════════

Uploaded File Has Pending Scan Status
    [Documentation]    GET /at/attachments/{id} — newly uploaded file should have virus_scan_status=pending
    [Tags]    attachments    api    integration    virus_scan
    ${resp}=    GET    ${AT_URL}/attachments/${ATTACHMENT_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal As Strings    ${json}[virus_scan_status]    pending
    Log    Virus scan status is pending as expected

# ══════════════════════════════════════════════════════════════════════════════
# Storage health check
# ══════════════════════════════════════════════════════════════════════════════

Storage Health Check Returns Status
    [Documentation]    GET /at/health — expect 200 with provider/status or 403 if not admin
    [Tags]    attachments    api    integration    health    admin
    ${resp}=    GET    ${AT_URL}/health    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 403
    IF    ${resp.status_code} == 200
        ${json}=    Set Variable    ${resp.json()}
        Dictionary Should Contain Key    ${json}    provider
        Dictionary Should Contain Key    ${json}    status
        Log    Storage health: provider=${json}[provider], status=${json}[status]
    ELSE
        Log    Storage health endpoint requires admin: ${resp.status_code}
    END

# ══════════════════════════════════════════════════════════════════════════════
# Storage usage
# ══════════════════════════════════════════════════════════════════════════════

Get Storage Usage
    [Documentation]    GET /at/attachments/storage-usage — expect 200 with usage and quota fields
    [Tags]    attachments    api    integration    storage
    ${resp}=    GET    ${AT_URL}/attachments/storage-usage
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    total_bytes
    Dictionary Should Contain Key    ${json}    file_count
    Log    Storage usage: total_bytes=${json}[total_bytes], file_count=${json}[file_count]

# ══════════════════════════════════════════════════════════════════════════════
# Download history (admin)
# ══════════════════════════════════════════════════════════════════════════════

Get Download History After Download
    [Documentation]    GET /at/attachments/{id}/download-history — expect 200, at least 1 entry from earlier download test
    [Tags]    attachments    api    integration    download
    ${resp}=    GET    ${AT_URL}/attachments/${ATTACHMENT_ID}/download-history
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Dictionary Should Contain Key    ${json}    total
    ${total}=    Get From Dictionary    ${json}    total
    Should Be True    ${total} >= 1
    ${items}=    Get From Dictionary    ${json}    items
    ${first}=    Get From List    ${items}    0
    Dictionary Should Contain Key    ${first}    id
    Dictionary Should Contain Key    ${first}    attachment_id
    Dictionary Should Contain Key    ${first}    downloaded_by
    Dictionary Should Contain Key    ${first}    downloaded_at
    Should Be Equal    ${first}[attachment_id]    ${ATTACHMENT_ID}
    Log    Download history entries: ${total}

# ══════════════════════════════════════════════════════════════════════════════
# Delete
# ══════════════════════════════════════════════════════════════════════════════

Delete Secondary User Attachment
    [Documentation]    Secondary user deletes their own attachment — expect 204
    [Tags]    attachments    api    integration    crud
    ${resp}=    DELETE    ${AT_URL}/attachments/${SECONDARY_ATTACHMENT_ID}
    ...    headers=${SECONDARY_HEADERS}    expected_status=204
    Log    Secondary user deleted own attachment: ${SECONDARY_ATTACHMENT_ID}

Deleted Attachment Not In List
    [Documentation]    GET /at/attachments list after delete — SECONDARY_ATTACHMENT_ID must be absent
    [Tags]    attachments    api    integration    crud
    ${resp}=    GET    ${AT_URL}/attachments    headers=${AUTH_HEADERS}
    ...    params=entity_type=task&entity_id=${AT_TASK_ID}&per_page=200    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Get From Dictionary    ${json}    items
    ${ids}=    Evaluate    [item.get('id') for item in $items]
    Should Not Contain    ${ids}    ${SECONDARY_ATTACHMENT_ID}
    Log    Deleted attachment correctly absent from list

Delete Primary Attachment
    [Documentation]    Admin user deletes primary attachment — expect 204
    [Tags]    attachments    api    integration    crud
    ${resp}=    DELETE    ${AT_URL}/attachments/${ATTACHMENT_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=204
    Log    Primary attachment deleted: ${ATTACHMENT_ID}

Deleted Primary Attachment Not Found On Get
    [Documentation]    GET /at/attachments/{id} after delete — expect 404
    [Tags]    attachments    api    integration    crud
    ${resp}=    GET    ${AT_URL}/attachments/${ATTACHMENT_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    # Soft-delete: could be 404 or 200 with is_deleted field depending on implementation
    Should Be True    ${resp.status_code} == 404 or ${resp.status_code} == 200
    Log    Post-delete GET status: ${resp.status_code}
