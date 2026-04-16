*** Settings ***
Documentation    Tasks API Integration Tests — CRUD, status transitions, dependencies, events, clone, bulk-update, summary, export
Resource         common.resource
Suite Setup      Setup Tasks Suite

*** Variables ***
${TK_URL}    ${BASE_URL}/tk

*** Keywords ***
Setup Tasks Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    # Create an org for task scoping
    ${org_slug}=    Set Variable    robot-task-org-${TS}
    ${org_body}=    Create Dictionary
    ...    name=Robot Task Org ${TS}
    ...    slug=${org_slug}
    ...    org_type_code=community
    ...    description=Org for task tests
    ${org_resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${org_body}    expected_status=any
    Should Be True    ${org_resp.status_code} == 200 or ${org_resp.status_code} == 201
    ${org_json}=    Set Variable    ${org_resp.json()}
    ${oid}=    Evaluate    $org_json.get('id') or $org_json.get('org_id')
    Set Suite Variable    ${TK_ORG_ID}    ${oid}
    Log    Created org for tasks: ${oid}
    # Create a workspace under that org
    ${ws_slug}=    Set Variable    robot-task-ws-${TS}
    ${ws_body}=    Create Dictionary
    ...    name=Robot Task WS ${TS}
    ...    slug=${ws_slug}
    ...    workspace_type_code=development
    ...    description=Workspace for task tests
    ${ws_resp}=    POST    ${AM_URL}/orgs/${TK_ORG_ID}/workspaces
    ...    headers=${AUTH_HEADERS}    json=${ws_body}    expected_status=any
    Should Be True    ${ws_resp.status_code} == 200 or ${ws_resp.status_code} == 201
    ${ws_json}=    Set Variable    ${ws_resp.json()}
    ${wsid}=    Evaluate    $ws_json.get('id') or $ws_json.get('workspace_id')
    Set Suite Variable    ${TK_WS_ID}    ${wsid}
    Log    Created workspace for tasks: ${wsid}

*** Test Cases ***
List Task Types
    [Documentation]    GET /tk/task-types → expect 4
    ${resp}=    GET    ${TK_URL}/task-types    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be Equal As Integers    ${count}    4
    Log    Task types count: ${count}

List Task Priorities
    [Documentation]    GET /tk/task-priorities → expect 4
    ${resp}=    GET    ${TK_URL}/task-priorities    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be Equal As Integers    ${count}    4
    Log    Task priorities count: ${count}

List Task Statuses
    [Documentation]    GET /tk/task-statuses → expect 6
    ${resp}=    GET    ${TK_URL}/task-statuses    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be True    isinstance($json, list)
    ${count}=    Get Length    ${json}
    Should Be Equal As Integers    ${count}    6
    Log    Task statuses count: ${count}

Create Task
    [Documentation]    POST /tk/tasks
    ${body}=    Create Dictionary
    ...    org_id=${TK_ORG_ID}
    ...    workspace_id=${TK_WS_ID}
    ...    task_type_code=general
    ...    title=Robot Task ${TS}
    ...    description=Task created by Robot Framework tests
    ${resp}=    POST    ${TK_URL}/tasks    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${taskid}=    Evaluate    $json.get('id') or $json.get('task_id')
    Set Suite Variable    ${TASK_ID}    ${taskid}
    Log    Created task: ${taskid}

List Tasks
    [Documentation]    GET /tk/tasks?workspace_id=X
    ${resp}=    GET    ${TK_URL}/tasks    headers=${AUTH_HEADERS}
    ...    params=workspace_id=${TK_WS_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('tasks', []))
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 1
    Log    Tasks count: ${count}

Get Task Detail
    [Documentation]    GET /tk/tasks/${TASK_ID}
    ${resp}=    GET    ${TK_URL}/tasks/${TASK_ID}    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Should Be Equal    ${json}[title]    Robot Task ${TS}
    Log    Task detail retrieved: ${TASK_ID}

Update Task Status
    [Documentation]    PATCH /tk/tasks/${TASK_ID} with status_code=in_progress
    ${body}=    Create Dictionary    status_code=in_progress
    ${resp}=    PATCH    ${TK_URL}/tasks/${TASK_ID}
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${status}=    Evaluate    $json.get('status_code') or $json.get('status')
    Should Be Equal    ${status}    in_progress

Add Co Assignee
    [Documentation]    POST /tk/tasks/${TASK_ID}/assignments with assignment_role=reviewer
    ${body}=    Create Dictionary    user_id=${USER_ID}    assignment_role=reviewer
    ${resp}=    POST    ${TK_URL}/tasks/${TASK_ID}/assignments
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${assignid}=    Evaluate    $json.get('id') or $json.get('assignment_id')
    Set Suite Variable    ${ASSIGN_ID}    ${assignid}
    Log    Added co-assignee: ${assignid}

List Assignments
    [Documentation]    GET /tk/tasks/${TASK_ID}/assignments
    ${resp}=    GET    ${TK_URL}/tasks/${TASK_ID}/assignments
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('assignments', []))
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 1
    Log    Assignments count: ${count}

Create Second Task
    [Documentation]    POST /tk/tasks — second task for dependency test
    ${body}=    Create Dictionary
    ...    org_id=${TK_ORG_ID}
    ...    workspace_id=${TK_WS_ID}
    ...    task_type_code=general
    ...    title=Robot Task 2 ${TS}
    ...    description=Second task for dependency tests
    ${resp}=    POST    ${TK_URL}/tasks    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${task2id}=    Evaluate    $json.get('id') or $json.get('task_id')
    Set Suite Variable    ${TASK2_ID}    ${task2id}
    Log    Created second task: ${task2id}

Add Dependency
    [Documentation]    POST /tk/tasks/${TASK2_ID}/dependencies with blocking_task_id
    ${body}=    Create Dictionary    blocking_task_id=${TASK_ID}
    ${resp}=    POST    ${TK_URL}/tasks/${TASK2_ID}/dependencies
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${depid}=    Evaluate    $json.get('id') or $json.get('dependency_id')
    Set Suite Variable    ${DEP_ID}    ${depid}
    Log    Added dependency: ${depid}

List Dependencies
    [Documentation]    GET /tk/tasks/${TASK2_ID}/dependencies — response shape is {blockers, blocked_by}
    ${resp}=    GET    ${TK_URL}/tasks/${TASK2_ID}/dependencies
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    # Response shape: { blockers: [...], blocked_by: [...] }
    ${blockers}=    Evaluate    $json.get('blockers', [])
    ${count}=    Get Length    ${blockers}
    Should Be True    ${count} >= 1
    Log    Blockers count: ${count}

Add Comment
    [Documentation]    POST /tk/tasks/${TASK_ID}/events — accepts {comment: str} only
    ${body}=    Create Dictionary
    ...    comment=Test comment added by Robot Framework
    ${resp}=    POST    ${TK_URL}/tasks/${TASK_ID}/events
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    Log    Added comment to task: ${TASK_ID}

List Events
    [Documentation]    GET /tk/tasks/${TASK_ID}/events → should have created + status_changed + comment events
    ${resp}=    GET    ${TK_URL}/tasks/${TASK_ID}/events
    ...    headers=${AUTH_HEADERS}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    ${items}=    Evaluate    $json if isinstance($json, list) else $json.get('items', $json.get('events', []))
    ${count}=    Get Length    ${items}
    Should Be True    ${count} >= 3
    Log    Task events count: ${count}
    # Verify event types present
    ${types}=    Evaluate    [item.get('event_type') for item in $items]
    Should Contain    ${types}    comment_added

Clone Task
    [Documentation]    POST /tk/tasks/${TASK_ID}/clone → returns a new task copy
    ${resp}=    POST    ${TK_URL}/tasks/${TASK_ID}/clone
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${cloneid}=    Evaluate    $json.get('id') or $json.get('task_id')
    Set Suite Variable    ${CLONE_ID}    ${cloneid}
    # Verify it is a different task
    Should Not Be Equal    ${cloneid}    ${TASK_ID}
    Log    Cloned task: ${cloneid}

Get Task Summary
    [Documentation]    GET /tk/tasks/summary → verify summary shape
    ${resp}=    GET    ${TK_URL}/tasks/summary    headers=${AUTH_HEADERS}
    ...    params=org_id=${TK_ORG_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    open_count
    Dictionary Should Contain Key    ${json}    overdue_count
    Log    Task summary: ${json}

Test Invalid Status Transition
    [Documentation]    PATCH /tk/tasks/${CLONE_ID} with invalid transition → expect 422
    ${body}=    Create Dictionary    status_code=resolved
    ${resp}=    PATCH    ${TK_URL}/tasks/${CLONE_ID}
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    # open → resolved is not a valid direct transition; expect 422 or 400
    Should Be True    ${resp.status_code} == 422 or ${resp.status_code} == 400 or ${resp.status_code} == 409
    Log    Invalid transition returned: ${resp.status_code}

Test Valid Status Transition Chain
    [Documentation]    PATCH open → in_progress → pending_verification on clone task
    ${body1}=    Create Dictionary    status_code=in_progress
    ${resp1}=    PATCH    ${TK_URL}/tasks/${CLONE_ID}
    ...    headers=${AUTH_HEADERS}    json=${body1}    expected_status=200
    ${json1}=    Set Variable    ${resp1.json()}
    ${status1}=    Evaluate    $json1.get('status_code') or $json1.get('status')
    Should Be Equal    ${status1}    in_progress
    ${body2}=    Create Dictionary    status_code=pending_verification
    ${resp2}=    PATCH    ${TK_URL}/tasks/${CLONE_ID}
    ...    headers=${AUTH_HEADERS}    json=${body2}    expected_status=200
    ${json2}=    Set Variable    ${resp2.json()}
    ${status2}=    Evaluate    $json2.get('status_code') or $json2.get('status')
    Should Be Equal    ${status2}    pending_verification
    Log    Transition chain completed: open → in_progress → pending_verification

Test Cycle Detection
    [Documentation]    Adding a circular dependency should return 422
    # TASK_ID → TASK2_ID already. Try adding TASK_ID blocked by TASK2_ID (cycle)
    ${body}=    Create Dictionary    blocking_task_id=${TASK2_ID}
    ${resp}=    POST    ${TK_URL}/tasks/${TASK_ID}/dependencies
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    # Should detect cycle and return 422 or 409
    Should Be True    ${resp.status_code} == 422 or ${resp.status_code} == 409 or ${resp.status_code} == 400
    Log    Cycle detection returned: ${resp.status_code}

Bulk Update Tasks
    [Documentation]    POST /tk/tasks/bulk-update → update both tasks to same priority
    ${task_ids}=    Create List    ${TASK_ID}    ${TASK2_ID}
    ${body}=    Create Dictionary
    ...    task_ids=${task_ids}
    ...    priority_code=high
    ${resp}=    POST    ${TK_URL}/tasks/bulk-update
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${updated}=    Evaluate    $json.get('updated_count', 0)
    Should Be True    ${updated} >= 1
    Log    Bulk updated ${updated} tasks

Export Tasks CSV
    [Documentation]    GET /tk/tasks/export → returns CSV data
    ${resp}=    GET    ${TK_URL}/tasks/export    headers=${AUTH_HEADERS}
    ...    params=org_id=${TK_ORG_ID}    expected_status=200
    ${content_type}=    Evaluate    $resp.headers.get('Content-Type', '')
    Should Contain    ${content_type}    text/csv
    ${body_text}=    Set Variable    ${resp.text}
    Should Not Be Empty    ${body_text}
    Log    CSV export returned ${body_text[:100]}...

Filter Tasks By Due Date Range
    [Documentation]    GET /tk/tasks?due_date_from=X&due_date_to=Y — filters by date window
    ${resp}=    GET    ${TK_URL}/tasks    headers=${AUTH_HEADERS}
    ...    params=org_id=${TK_ORG_ID}&due_date_from=2020-01-01&due_date_to=2099-12-31    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Log    Tasks in date range: ${json}[total]

Filter Tasks By Priority Sort
    [Documentation]    GET /tk/tasks?sort_by=priority_code&sort_dir=asc — returns sorted list
    ${resp}=    GET    ${TK_URL}/tasks    headers=${AUTH_HEADERS}
    ...    params=org_id=${TK_ORG_ID}&sort_by=priority_code&sort_dir=asc    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Log    Sorted tasks by priority asc: ${json}[total]

Filter Tasks By Entity Type
    [Documentation]    Create a task with entity_type=risk then filter by entity_type=risk
    ${body}=    Create Dictionary
    ...    org_id=${TK_ORG_ID}
    ...    workspace_id=${TK_WS_ID}
    ...    task_type_code=general
    ...    title=Risk-linked Task ${TS}
    ...    entity_type=risk
    ${resp}=    POST    ${TK_URL}/tasks    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${entity_task_json}=    Set Variable    ${resp.json()}
    ${entity_task_id}=    Evaluate    $entity_task_json.get('id') or $entity_task_json.get('task_id')
    Set Suite Variable    ${ENTITY_TASK_ID}    ${entity_task_id}
    # Filter by entity_type
    ${filter_resp}=    GET    ${TK_URL}/tasks    headers=${AUTH_HEADERS}
    ...    params=org_id=${TK_ORG_ID}&entity_type=risk    expected_status=200
    ${filter_json}=    Set Variable    ${filter_resp.json()}
    ${items}=    Evaluate    $filter_json.get('items', [])
    ${entity_types}=    Evaluate    [item.get('entity_type') for item in $items]
    Should Contain    ${entity_types}    risk
    Log    entity_type filter works: ${filter_json}[total] risk tasks found

Filter Tasks By Reporter
    [Documentation]    GET /tk/tasks?reporter_user_id=ADMIN → returns tasks reported by admin
    ${resp}=    GET    ${TK_URL}/tasks    headers=${AUTH_HEADERS}
    ...    params=org_id=${TK_ORG_ID}&reporter_user_id=${USER_ID}    expected_status=200
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    items
    Log    Tasks by reporter: ${json}[total]

Add Observer Assignment
    [Documentation]    POST /tk/tasks/${TASK_ID}/assignments with assignment_role=observer
    ${body}=    Create Dictionary    user_id=${USER_ID}    assignment_role=observer
    ${resp}=    POST    ${TK_URL}/tasks/${TASK_ID}/assignments
    ...    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    # May return 409 if already assigned; both 201 and 409 are acceptable
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201 or ${resp.status_code} == 409
    Log    Observer assignment returned: ${resp.status_code}

Cleanup Entity Task
    [Documentation]    DELETE entity-typed task
    ${resp}=    DELETE    ${TK_URL}/tasks/${ENTITY_TASK_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted entity task: ${ENTITY_TASK_ID}

Cleanup Clone
    [Documentation]    DELETE cloned task
    ${resp}=    DELETE    ${TK_URL}/tasks/${CLONE_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted clone: ${CLONE_ID}

Cleanup Dependency
    [Documentation]    DELETE dependency
    ${resp}=    DELETE    ${TK_URL}/tasks/${TASK2_ID}/dependencies/${DEP_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted dependency: ${DEP_ID}

Cleanup Assignment
    [Documentation]    DELETE assignment
    ${resp}=    DELETE    ${TK_URL}/tasks/${TASK_ID}/assignments/${ASSIGN_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted assignment: ${ASSIGN_ID}

Cleanup Second Task
    [Documentation]    DELETE second task (soft-delete)
    ${resp}=    DELETE    ${TK_URL}/tasks/${TASK2_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted second task: ${TASK2_ID}

Cleanup First Task
    [Documentation]    DELETE first task (soft-delete)
    ${resp}=    DELETE    ${TK_URL}/tasks/${TASK_ID}
    ...    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 204
    Log    Deleted first task: ${TASK_ID}
