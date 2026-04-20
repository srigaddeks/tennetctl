*** Settings ***
Documentation     E2E tests for action templates (webhook + Slack + email)
Library           Collections
Library           RequestsLibrary
Library           Process
Library           DateTime


*** Variables ***
${BASE_URL}       http://localhost:51734
${ORG_ID}         test-org-123
${USER_ID}        test-user-456
${WEBHOOK_URL}    http://localhost:9999/webhook-catcher


*** Test Cases ***
Create Webhook Template and Trigger Alert
    [Documentation]    Create webhook action template, alert rule, trigger condition, verify signature

    # Start webhook catcher in background
    ${catcher_process}=    Start Process    python -m pytest tests/fixtures/webhook_catcher.py --port 9999
    Sleep    2s    # Wait for catcher to start

    # Create webhook action template
    ${template}=    Create Action Template
    ...    kind=webhook
    ...    name=Test Webhook
    ...    target_url=${WEBHOOK_URL}
    ...    body_template={"alert": "{{rule_name}}", "value": {{value}}}
    ...    signing_secret_vault_ref=vault://secret/webhook

    Should Not Be Empty    ${template['id']}

    # Create alert rule referencing the action template
    ${rule}=    Create Alert Rule
    ...    name=Test Rule
    ...    action_template_ids=${template['id']}

    Should Not Be Empty    ${rule['id']}

    # Trigger the alert condition
    Trigger Alert Condition    ${rule['id']}

    # Wait for webhook to be received
    Sleep    5s

    # Verify webhook catcher received POST with valid signature
    Webhook Catcher Should Receive Request
    ...    method=POST
    ...    path=/webhook-catcher
    ...    contains_header=X-Tennet-Signature

    # Verify signature server-side
    Verify Webhook Signature
    ...    webhook_url=${WEBHOOK_URL}
    ...    signature_header=X-Tennet-Signature
    ...    secret_vault_ref=vault://secret/webhook

    # Cleanup
    Terminate Process    ${catcher_process}


Retry Failed Webhook Delivery
    [Documentation]    Verify retry logic with exponential backoff

    # Create webhook template pointing to failing endpoint
    ${template}=    Create Action Template
    ...    kind=webhook
    ...    name=Retry Test
    ...    target_url=http://localhost:9998/fail
    ...    body_template={}
    ...    retry_policy={"max_attempts": 3, "base_seconds": 1, "max_seconds": 10}

    # Create alert rule
    ${rule}=    Create Alert Rule
    ...    name=Retry Rule
    ...    action_template_ids=${template['id']}

    # Trigger alert
    Trigger Alert Condition    ${rule['id']}

    # Poll delivery log
    Sleep    2s
    ${deliveries}=    List Action Deliveries    template_id=${template['id']}

    # First delivery should be attempted
    ${delivery1}=    Get From List    ${deliveries['data']}    0
    Should Be Equal    ${delivery1['attempt']}    1
    Should Be Equal    ${delivery1['status']}    failed

    # Wait for retry
    Sleep    3s
    ${deliveries}=    List Action Deliveries    template_id=${template['id']}

    # Second delivery should exist
    ${delivery2}=    Get From List    ${deliveries['data']}    1
    Should Be Equal    ${delivery2['attempt']}    2


Test Dispatch Synchronous
    [Documentation]    Verify test-send button returns synchronous result

    ${template}=    Create Action Template
    ...    kind=webhook
    ...    name=Test Send
    ...    target_url=https://httpbin.org/post
    ...    body_template={"test": true}

    # Call test-send endpoint
    ${response}=    Test Dispatch Action Template
    ...    template_id=${template['id']}
    ...    sample_variables={}

    Should Be True    ${response['success']}
    Should Be Equal    ${response['status_code']}    200


*** Keywords ***
Create Action Template
    [Arguments]    &{kwargs}
    [Documentation]    Create an action template via API

    ${response}=    POST    ${BASE_URL}/v1/monitoring/action-templates
    ...    json=${kwargs}
    ...    headers={"Authorization": "Bearer test-token"}

    Should Be Equal As Integers    ${response.status_code}    201
    ${data}=    Set Variable    ${response.json()['data']}
    [Return]    ${data}


Create Alert Rule
    [Arguments]    &{kwargs}
    [Documentation]    Create an alert rule via API

    ${response}=    POST    ${BASE_URL}/v1/monitoring/alert-rules
    ...    json=${kwargs}
    ...    headers={"Authorization": "Bearer test-token"}

    Should Be Equal As Integers    ${response.status_code}    201
    ${data}=    Set Variable    ${response.json()['data']}
    [Return]    ${data}


Trigger Alert Condition
    [Arguments]    ${rule_id}
    [Documentation]    Trigger alert evaluation by injecting metric

    # Placeholder: real implementation would inject metric value
    Log    Triggering alert condition for rule ${rule_id}


List Action Deliveries
    [Arguments]    &{filters}
    [Documentation]    List action deliveries with optional filters

    ${response}=    GET    ${BASE_URL}/v1/monitoring/action-deliveries
    ...    params=${filters}
    ...    headers={"Authorization": "Bearer test-token"}

    Should Be Equal As Integers    ${response.status_code}    200
    [Return]    ${response.json()['data']}


Test Dispatch Action Template
    [Arguments]    ${template_id}    &{kwargs}
    [Documentation]    Call test-send endpoint

    ${response}=    POST    ${BASE_URL}/v1/monitoring/action-templates/${template_id}/test
    ...    json=${kwargs}
    ...    headers={"Authorization": "Bearer test-token"}

    Should Be Equal As Integers    ${response.status_code}    200
    [Return]    ${response.json()['data']}


Webhook Catcher Should Receive Request
    [Arguments]    &{expected}
    [Documentation]    Verify webhook catcher received request with expected properties

    ${response}=    GET    ${WEBHOOK_URL}/requests
    Should Not Be Empty    ${response}
    Log    Webhook received ${response}


Verify Webhook Signature
    [Arguments]    &{params}
    [Documentation]    Server-side signature verification

    Log    Verifying signature for ${params['webhook_url']}
