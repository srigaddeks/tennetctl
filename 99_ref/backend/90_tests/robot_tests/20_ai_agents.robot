*** Settings ***
Documentation    AI Agents Integration Tests
Resource         common.resource
Suite Setup      Setup AI Agents Suite

*** Variables ***
${AI_URL}            ${BASE_URL}/ai
${CONV_URL}          ${AI_URL}/conversations
${ENHANCE_URL}       ${AI_URL}/enhance-text
${FORM_FILL_URL}     ${AI_URL}/form-fill
${REPORTS_URL}       ${AI_URL}/reports
${FRAMEWORK_URL}     ${AI_URL}/framework-builder
${SIGNAL_SPEC_URL}   ${AI_URL}/signal-spec
${SIGNAL_CODEGEN_URL}    ${AI_URL}/signal-codegen
${DATASET_AGENT_URL}    ${AI_URL}/dataset-agent
${RISK_ADV_URL}      ${AI_URL}/risk-advisor
${TEST_LINKER_URL}   ${AI_URL}/test-linker
${TASK_BUILDER_URL}  ${AI_URL}/task-builder
${EVIDENCE_URL}      ${AI_URL}/evidence-check
${JOBS_URL}          ${AI_URL}/jobs
${DIM_URL}           ${AI_URL}/dimensions
${AGENTS_URL}        ${AI_URL}/agents
${ADMIN_CONFIGS_URL}    ${AI_URL}/admin/agent-configs
${ADMIN_PROMPTS_URL}    ${AI_URL}/admin/prompts
${PDF_TEMPLATES_URL}    ${AI_URL}/pdf-templates

*** Keywords ***
Setup AI Agents Suite
    Login As Admin
    ${ts}=    Get Timestamp
    Set Suite Variable    ${TS}    ${ts}
    ${org_body}=    Create Dictionary
    ...    name=Robot AI Org ${ts}
    ...    slug=robot-ai-org-${ts}
    ...    org_type_code=community
    ...    description=Org for AI agent tests
    ${org_resp}=    POST    ${AM_URL}/orgs    headers=${AUTH_HEADERS}    json=${org_body}    expected_status=any
    Should Be True    ${org_resp.status_code} == 200 or ${org_resp.status_code} == 201
    ${org_json}=    Set Variable    ${org_resp.json()}
    ${oid}=    Get From Dictionary    ${org_json}    id
    Set Suite Variable    ${AI_ORG_ID}    ${oid}
    ${ws_body}=    Create Dictionary
    ...    name=Robot AI WS ${ts}
    ...    slug=robot-ai-ws-${ts}
    ...    workspace_type_code=development
    ...    description=Workspace for AI tests
    ${ws_resp}=    POST    ${AM_URL}/orgs/${AI_ORG_ID}/workspaces
    ...    headers=${AUTH_HEADERS}    json=${ws_body}    expected_status=any
    Should Be True    ${ws_resp.status_code} == 200 or ${ws_resp.status_code} == 201
    ${ws_json}=    Set Variable    ${ws_resp.json()}
    ${wsid}=    Get From Dictionary    ${ws_json}    id
    Set Suite Variable    ${AI_WS_ID}    ${wsid}
    Set Suite Variable    ${TEST_CONVERSATION_ID}    ${EMPTY}
    Set Suite Variable    ${TEST_REPORT_ID}    ${EMPTY}
    Set Suite Variable    ${TEST_AGENT_CONFIG_ID}    ${EMPTY}
    Set Suite Variable    ${TEST_PDF_TEMPLATE_ID}    ${EMPTY}
    Set Suite Variable    ${FB_SESSION_ID}    ${EMPTY}
    Set Suite Variable    ${SS_SESSION_ID}    ${EMPTY}

*** Test Cases ***
List Agent Types
    ${resp}=    GET    ${DIM_URL}/agent-types    headers=${AUTH_HEADERS}    expected_status=200
    Should Be True    len(${resp.json()}) > 0

List Agent Types Via Agents Router
    ${resp}=    GET    ${AGENTS_URL}/types    headers=${AUTH_HEADERS}    expected_status=200

List Agent Runs
    ${resp}=    GET    ${AGENTS_URL}/runs    headers=${AUTH_HEADERS}    expected_status=200

Create Conversation
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    agent_type_code=copilot    title=Robot Conv ${TS}
    ${resp}=    POST    ${CONV_URL}    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} == 200 or ${resp.status_code} == 201
    ${json}=    Set Variable    ${resp.json()}
    ${cid}=    Get From Dictionary    ${json}    id
    Set Suite Variable    ${TEST_CONVERSATION_ID}    ${cid}

List Conversations
    ${resp}=    GET    url=${CONV_URL}?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=200

Get Conversation By ID
    Run Keyword If    not $TEST_CONVERSATION_ID    Skip
    ${resp}=    GET    url=${CONV_URL}/${TEST_CONVERSATION_ID}?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=200

Get Conversation Messages
    Run Keyword If    not $TEST_CONVERSATION_ID    Skip
    ${resp}=    GET    url=${CONV_URL}/${TEST_CONVERSATION_ID}/messages?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=200

Stream Message On Conversation
    Run Keyword If    not $TEST_CONVERSATION_ID    Skip
    ${body}=    Create Dictionary    content=Hello
    ${resp}=    POST    url=${CONV_URL}/${TEST_CONVERSATION_ID}/stream?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503]

Archive Conversation
    Run Keyword If    not $TEST_CONVERSATION_ID    Skip
    ${resp}=    POST    url=${CONV_URL}/${TEST_CONVERSATION_ID}/archive?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 204]

Text Enhancer Stream
    ${ctx}=    Create Dictionary    control_name=Access Review
    ${body}=    Create Dictionary    entity_type=control    field_name=description    current_value=Access controls must be reviewed.    instruction=Make this more detailed.    entity_context=${ctx}
    ${resp}=    POST    ${ENHANCE_URL}/stream    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503]

Text Enhancer Missing Instruction Returns 422
    ${body}=    Create Dictionary    entity_type=control    field_name=description    current_value=Test
    ${resp}=    POST    ${ENHANCE_URL}/stream    headers=${AUTH_HEADERS}    json=${body}    expected_status=422

Form Fill Stream
    ${ctx}=    Create Dictionary    control_name=Access Review
    ${body}=    Create Dictionary    entity_type=task    entity_context=${ctx}    instruction=Fill task details    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}
    ${resp}=    POST    ${FORM_FILL_URL}/stream    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 422, 503]

Form Fill Agent Stream
    ${body}=    Create Dictionary    entity_type=risk    message=Help fill a risk assessment.    session_id=robot-session-${TS}    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}
    ${resp}=    POST    ${FORM_FILL_URL}/agent/stream    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503]

Form Fill Missing Fields Returns 422
    ${body}=    Create Dictionary    entity_type=task
    ${resp}=    POST    ${FORM_FILL_URL}/stream    headers=${AUTH_HEADERS}    json=${body}    expected_status=422

Create Framework Builder Session
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    source_type=description    description=Build a SOC2 framework.
    ${resp}=    POST    ${FRAMEWORK_URL}/sessions    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201, 422]
    Run Keyword If    ${resp.status_code} in [200, 201]
    ...    Run Keywords
    ...    ${json}=    Set Variable    ${resp.json()}
    ...    AND    ${sid}=    Get From Dictionary    ${json}    id
    ...    AND    Set Suite Variable    ${FB_SESSION_ID}    ${sid}

List Framework Builder Sessions
    ${resp}=    GET    url=${FRAMEWORK_URL}/sessions?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 422]

Get Framework Builder Session
    Run Keyword If    not $FB_SESSION_ID    Skip
    ${resp}=    GET    url=${FRAMEWORK_URL}/sessions/${FB_SESSION_ID}?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404, 503]

Framework Builder Hierarchy Stream
    Run Keyword If    not $FB_SESSION_ID    Skip
    ${resp}=    GET    url=${FRAMEWORK_URL}/sessions/${FB_SESSION_ID}/stream/hierarchy?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503]

Framework Builder Controls Stream
    Run Keyword If    not $FB_SESSION_ID    Skip
    ${resp}=    GET    url=${FRAMEWORK_URL}/sessions/${FB_SESSION_ID}/stream/controls?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503]

Create Signal Spec Session
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    prompt=Check if all GitHub repos have branch protection enabled.
    ${resp}=    POST    ${SIGNAL_SPEC_URL}/sessions    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201, 422]
    Run Keyword If    ${resp.status_code} in [200, 201]
    ...    Run Keywords
    ...    ${json}=    Set Variable    ${resp.json()}
    ...    AND    ${sid}=    Get From Dictionary    ${json}    id
    ...    AND    Set Suite Variable    ${SS_SESSION_ID}    ${sid}

List Signal Spec Sessions
    ${resp}=    GET    url=${SIGNAL_SPEC_URL}/sessions?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=200

Get Signal Spec Session
    Run Keyword If    not $SS_SESSION_ID    Skip
    ${resp}=    GET    url=${SIGNAL_SPEC_URL}/sessions/${SS_SESSION_ID}?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404]

Signal Spec Generate Stream
    Run Keyword If    not $SS_SESSION_ID    Skip
    ${resp}=    GET    url=${SIGNAL_SPEC_URL}/sessions/${SS_SESSION_ID}/stream/generate?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503]

Signal Spec Feasibility Stream
    Run Keyword If    not $SS_SESSION_ID    Skip
    ${resp}=    GET    url=${SIGNAL_SPEC_URL}/sessions/${SS_SESSION_ID}/stream/feasibility?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503]

Signal Spec Data Sufficiency
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    connector_type=github    asset_type=github_repo
    ${resp}=    POST    ${SIGNAL_SPEC_URL}/data-sufficiency    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404, 422, 503]

Signal Codegen Generate
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}
    ${resp}=    POST    ${SIGNAL_CODEGEN_URL}/generate    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201, 202, 404, 422, 503]

Signal Codegen Retry Invalid ID
    ${body}=    Create Dictionary    signal_id=00000000-0000-0000-0000-000000000000    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}
    ${resp}=    POST    ${SIGNAL_CODEGEN_URL}/retry    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 202, 404, 422, 503]

Dataset Agent Explain Record
    ${record}=    Create Dictionary    name=bucket-1    region=us-east-1    encryption=AES256
    ${body}=    Create Dictionary    record_data=${record}    asset_type_hint=cloud_storage    connector_type=aws
    ${resp}=    POST    ${DATASET_AGENT_URL}/explain-record    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503]

Dataset Agent Compose Test Data
    ${keys}=    Create List    name    private    default_branch
    ${body}=    Create Dictionary    property_keys=${keys}    asset_type=github_repo    connector_type=github    record_count=5
    ${resp}=    POST    ${DATASET_AGENT_URL}/compose-test-data    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503]

Dataset Agent Enhance Dataset
    ${r1}=    Create Dictionary    name=repo-1    private=true
    ${records}=    Create List    ${r1}
    ${body}=    Create Dictionary    records=${records}    asset_type=github_repo    connector_type=github
    ${resp}=    POST    ${DATASET_AGENT_URL}/enhance-dataset    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 503]

Dataset Agent Empty Body Returns 422
    ${body}=    Create Dictionary
    ${resp}=    POST    ${DATASET_AGENT_URL}/explain-record    headers=${AUTH_HEADERS}    json=${body}    expected_status=422

List Reports
    ${resp}=    GET    url=${REPORTS_URL}?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=200

Create Report
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    report_type=compliance_summary    title=Robot Report ${TS}
    ${resp}=    POST    ${REPORTS_URL}    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201, 503]
    IF    ${resp.status_code} in [200, 201]
        ${json}=    Set Variable    ${resp.json()}
        ${rid}=    Get From Dictionary    ${json}    id
        Set Suite Variable    ${TEST_REPORT_ID}    ${rid}
    END

Get Report By ID
    Run Keyword If    not $TEST_REPORT_ID    Skip
    ${resp}=    GET    url=${REPORTS_URL}/${TEST_REPORT_ID}?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404]

Evidence Checker Verdicts
    ${resp}=    GET    url=${EVIDENCE_URL}/tasks/verdicts?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 403, 404, 422]

Evidence Checker Dashboard
    ${resp}=    GET    url=${EVIDENCE_URL}/dashboard?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 403, 404]

Evidence Checker Queue
    ${resp}=    GET    url=${EVIDENCE_URL}/queue?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 403, 404]

Risk Advisor Suggest Controls
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    risk_description=Unauthorized access to production databases
    ${resp}=    POST    ${RISK_ADV_URL}/suggest-controls    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404, 422, 503]

Risk Advisor Bulk Link
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}
    ${resp}=    POST    ${RISK_ADV_URL}/bulk-link    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 202, 404, 503]

Test Linker Suggest Controls
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    test_id=00000000-0000-0000-0000-000000000000
    ${resp}=    POST    ${TEST_LINKER_URL}/suggest-controls    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404, 503, 500]

Test Linker Suggest Tests
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    control_id=00000000-0000-0000-0000-000000000000
    ${resp}=    POST    ${TEST_LINKER_URL}/suggest-tests    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404, 503]

Test Linker List Pending
    ${resp}=    GET    url=${TEST_LINKER_URL}/pending?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=200

Task Builder Preview Invalid Framework
    ${body}=    Create Dictionary    framework_id=00000000-0000-0000-0000-000000000000    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    user_context=Test
    ${resp}=    POST    ${TASK_BUILDER_URL}/preview    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [404, 503]

Task Builder Preview Missing Fields Returns 422
    ${body}=    Create Dictionary
    ${resp}=    POST    ${TASK_BUILDER_URL}/preview    headers=${AUTH_HEADERS}    json=${body}    expected_status=422

Task Builder Apply Empty Groups
    ${body}=    Create Dictionary    framework_id=00000000-0000-0000-0000-000000000000    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    task_groups=${EMPTY}
    ${resp}=    POST    ${TASK_BUILDER_URL}/apply    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201, 422]

List PDF Templates
    ${resp}=    GET    url=${PDF_TEMPLATES_URL}?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 403, 404]

Create PDF Template
    ${body}=    Create Dictionary    org_id=${AI_ORG_ID}    workspace_id=${AI_WS_ID}    name=Robot Template ${TS}    template_type=report
    ${resp}=    POST    ${PDF_TEMPLATES_URL}    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201, 403, 422]

Get PDF Template
    Run Keyword If    not $TEST_PDF_TEMPLATE_ID    Skip
    ${resp}=    GET    url=${PDF_TEMPLATES_URL}/${TEST_PDF_TEMPLATE_ID}?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404]

Delete PDF Template
    Run Keyword If    not $TEST_PDF_TEMPLATE_ID    Skip
    ${resp}=    DELETE    url=${PDF_TEMPLATES_URL}/${TEST_PDF_TEMPLATE_ID}?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 204, 404]

List Jobs
    ${resp}=    GET    ${JOBS_URL}    headers=${AUTH_HEADERS}    expected_status=200

Get Queue Depth
    ${resp}=    GET    ${JOBS_URL}/admin/queue-depth    headers=${AUTH_HEADERS}    expected_status=200

Get Rate Limits
    ${resp}=    GET    ${JOBS_URL}/admin/rate-limits    headers=${AUTH_HEADERS}    expected_status=200

Get Nonexistent Job
    ${resp}=    GET    ${JOBS_URL}/00000000-0000-0000-0000-000000000000    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [404, 200]

List Agent Configs
    ${resp}=    GET    ${ADMIN_CONFIGS_URL}    headers=${AUTH_HEADERS}    expected_status=200

List Agent Configs Filtered
    ${resp}=    GET    url=${ADMIN_CONFIGS_URL}?agent_type_code=copilot    headers=${AUTH_HEADERS}    expected_status=200

Create Agent Config
    ${body}=    Create Dictionary    agent_type_code=copilot    provider_type=openai_compatible    provider_base_url=https://api.openai.com    model_id=gpt-4o    temperature=0.7    max_tokens=2048
    ${resp}=    POST    ${ADMIN_CONFIGS_URL}    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 201, 409, 422]
    Run Keyword If    ${resp.status_code} in [200, 201]
    ...    Run Keywords
    ...    ${json}=    Set Variable    ${resp.json()}
    ...    AND    ${cid}=    Get From Dictionary    ${json}    id
    ...    AND    Set Suite Variable    ${TEST_AGENT_CONFIG_ID}    ${cid}

Update Agent Config
    Run Keyword If    not $TEST_AGENT_CONFIG_ID    Skip
    ${body}=    Create Dictionary    temperature=0.5
    ${resp}=    PATCH    ${ADMIN_CONFIGS_URL}/${TEST_AGENT_CONFIG_ID}    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404]

Delete Agent Config
    Run Keyword If    not $TEST_AGENT_CONFIG_ID    Skip
    ${resp}=    DELETE    ${ADMIN_CONFIGS_URL}/${TEST_AGENT_CONFIG_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 204, 404]

Agent Config Invalid Body Returns 422
    ${body}=    Create Dictionary    temperature=0.5
    ${resp}=    POST    ${ADMIN_CONFIGS_URL}    headers=${AUTH_HEADERS}    json=${body}    expected_status=422

List Prompt Templates
    ${resp}=    GET    ${ADMIN_PROMPTS_URL}    headers=${AUTH_HEADERS}    expected_status=200

Preview Prompt Template
    ${vars}=    Create Dictionary    entity_type=framework
    ${body}=    Create Dictionary    template_content=You are a GRC assistant.    variables=${vars}
    ${resp}=    POST    ${ADMIN_PROMPTS_URL}/preview    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 422]

List MCP Tools
    ${resp}=    GET    ${AI_URL}/mcp/tools    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404]

Memory Health
    ${resp}=    GET    ${AI_URL}/memory/health    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404, 503]

List Approvals
    ${resp}=    GET    ${AI_URL}/approvals    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [200, 404]

Conversation List Without Auth Returns 401
    ${resp}=    GET    url=${CONV_URL}?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    expected_status=any
    Should Be True    ${resp.status_code} in [401, 403]

Text Enhancer Without Auth Returns 401
    ${body}=    Create Dictionary    entity_type=control    field_name=description    current_value=Test    instruction=Improve
    ${resp}=    POST    ${ENHANCE_URL}/stream    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [401, 403]

Framework Builder Without Auth Returns 401
    ${body}=    Create Dictionary    description=Test
    ${resp}=    POST    ${FRAMEWORK_URL}/sessions    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [401, 403]

Task Builder Without Auth Returns 401
    ${body}=    Create Dictionary    framework_id=xxx    org_id=xxx    workspace_id=xxx
    ${resp}=    POST    ${TASK_BUILDER_URL}/preview    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [401, 403]

Conversation Invalid Body Returns 422
    ${body}=    Create Dictionary
    ${resp}=    POST    ${CONV_URL}    headers=${AUTH_HEADERS}    json=${body}    expected_status=any
    Should Be True    ${resp.status_code} in [400, 422]

Conversation Invalid UUID Returns Error
    ${resp}=    GET    url=${CONV_URL}/not-valid-uuid?org_id=${AI_ORG_ID}&workspace_id=${AI_WS_ID}    headers=${AUTH_HEADERS}    expected_status=any
    Should Be True    ${resp.status_code} in [400, 404, 422, 500]
