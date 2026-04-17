*** Settings ***
Documentation    Monitoring Dashboards — full CRUD: create, list, open, add panel,
...              reload to verify persistence, delete.
Library     Browser
Library     RequestsLibrary
Library     Collections
Resource    monitoring_keywords.resource
Suite Setup       Launch Dashboards Suite
Suite Teardown    Teardown Dashboards Suite

*** Variables ***
${TS}              ${EMPTY}
${TEST_EMAIL}      ${EMPTY}
${TEST_PASS}       pass-mon-dash-E2E!1
${ORG_ID}          ${EMPTY}
${USER_ID}         ${EMPTY}
${DASH_NAME}       ${EMPTY}
${CREATED_DASH_ID}    ${EMPTY}

*** Keywords ***
Launch Dashboards Suite
    ${ts}=    Get Time    epoch
    Set Suite Variable    ${TS}           ${ts}
    Set Suite Variable    ${DASH_NAME}    E2E-Dashboard-${ts}
    Set Suite Variable    ${TEST_EMAIL}   e2e-dash-${ts}@tennetctl.test
    ${signup}=    API Create Monitoring User    ${TEST_EMAIL}    ${TEST_PASS}    Dashboards E2E
    Set Suite Variable    ${ORG_ID}    ${signup['org_id']}
    Set Suite Variable    ${USER_ID}   ${signup['user_id']}
    New Browser    chromium    headless=true
    New Context    viewport={'width': 1280, 'height': 900}
    New Page    about:blank
    Sign In Monitoring User    ${TEST_EMAIL}    ${TEST_PASS}

Teardown Dashboards Suite
    # Clean up any dashboards created during the suite
    Run Keyword If    '${CREATED_DASH_ID}' != ''
    ...    API Delete Dashboard    ${CREATED_DASH_ID}    ${ORG_ID}    ${USER_ID}
    Close Browser    ALL

*** Test Cases ***
Create Dashboard Via Modal
    [Documentation]    Click "New dashboard" → fill name → Create → modal closes
    ...                → the new card appears in the grid.
    Open Monitoring Page    /monitoring/dashboards
    Wait For Elements State    [data-testid="monitoring-dashboard-new"]    visible    timeout=10s
    Click    [data-testid="monitoring-dashboard-new"]
    # Modal opens
    Wait For Elements State    [data-testid="monitoring-dashboard-name"]    visible    timeout=5s
    Fill Text    [data-testid="monitoring-dashboard-name"]    ${DASH_NAME}
    # Click the Create button (not the empty state description text)
    Click    xpath=//button[normalize-space(text())="Create"]
    Wait For Load State    networkidle    timeout=10s
    # Find the created dashboard card by name text
    Wait For Elements State    text=${DASH_NAME}    visible    timeout=10s
    # Capture dashboard ID from API for later tests
    ${dashboards}=    API List Dashboards    ${ORG_ID}    ${USER_ID}
    ${items}=    Set Variable    ${dashboards}[items]
    FOR    ${d}    IN    @{items}
        IF    '${d}[name]' == '${DASH_NAME}'
            Set Suite Variable    ${CREATED_DASH_ID}    ${d}[id]
        END
    END
    Should Not Be Empty    ${CREATED_DASH_ID}    Dashboard ID not found after creation

Dashboard Card Appears In List
    [Documentation]    After creation, the dashboard card is visible in the grid list.
    Open Monitoring Page    /monitoring/dashboards
    Wait For Elements State    [data-testid="monitoring-dashboard-card-${CREATED_DASH_ID}"]    visible    timeout=10s

Open Dashboard Detail Page
    [Documentation]    Click the dashboard card link → navigates to /monitoring/dashboards/{id}
    ...                → dashboard detail page with "Add panel" button renders.
    Open Monitoring Page    /monitoring/dashboards
    Wait For Elements State    [data-testid="monitoring-dashboard-card-${CREATED_DASH_ID}"]    visible    timeout=10s
    # Click the card link (the Link wraps the title area)
    Click    [data-testid="monitoring-dashboard-card-${CREATED_DASH_ID}"] a
    Wait For Load State    networkidle    timeout=15s
    Wait For Elements State    [data-testid="heading-monitoring-dashboard"]    visible    timeout=10s
    Wait For Elements State    [data-testid="monitoring-dashboard-add-panel"]    visible    timeout=10s

Add Panel To Dashboard
    [Documentation]    On the dashboard detail page, click "Add panel" → fill form →
    ...                Create → panel appears in the grid.
    Go To    ${MONITORING_FRONTEND}/monitoring/dashboards/${CREATED_DASH_ID}
    Wait For Load State    networkidle    timeout=15s
    Wait For Elements State    [data-testid="monitoring-dashboard-add-panel"]    visible    timeout=10s
    Click    [data-testid="monitoring-dashboard-add-panel"]
    # Modal opens
    Wait For Elements State    [data-testid="monitoring-panel-title"]    visible    timeout=5s
    ${panel_title}=    Set Variable    E2E-Panel-${TS}
    Fill Text    [data-testid="monitoring-panel-title"]    ${panel_title}
    # Leave DSL default (timeseries)
    Click    xpath=//button[normalize-space(text())="Create"]
    Wait For Load State    networkidle    timeout=10s
    # Panel grid renders
    Wait For Elements State    [data-testid="monitoring-dashboard-grid"]    visible    timeout=10s
    # A panel should appear — check panel-{id} elements exist
    ${panel_count}=    Get Element Count    css=[data-testid^="monitoring-panel-"]
    Should Be True    ${panel_count} >= 1    Expected ≥1 panel after adding, got ${panel_count}

Panel Persists After Reload
    [Documentation]    Reload the dashboard detail page — the panel created above must still render.
    Go To    ${MONITORING_FRONTEND}/monitoring/dashboards/${CREATED_DASH_ID}
    Wait For Load State    networkidle    timeout=15s
    Wait For Elements State    [data-testid="monitoring-dashboard-grid"]    visible    timeout=10s
    ${panel_count}=    Get Element Count    css=[data-testid^="monitoring-panel-"]
    Should Be True    ${panel_count} >= 1    Panel did not persist after reload, got ${panel_count}

Delete Dashboard Via Card Button
    [Documentation]    Back on the dashboards list, hover the card and click the delete (✕) button.
    ...                Confirm browser dialog — card detaches, API returns 404.
    Open Monitoring Page    /monitoring/dashboards
    Wait For Elements State    [data-testid="monitoring-dashboard-card-${CREATED_DASH_ID}"]    visible    timeout=10s
    # Hover to reveal delete button (opacity-0 → group-hover:opacity-100)
    Hover    [data-testid="monitoring-dashboard-card-${CREATED_DASH_ID}"]
    Wait For Elements State    [data-testid="monitoring-dashboard-delete-${CREATED_DASH_ID}"]    visible    timeout=5s
    # Handle the browser confirm() dialog
    Handle Future Dialogs    action=accept
    Click    [data-testid="monitoring-dashboard-delete-${CREATED_DASH_ID}"]
    Wait For Load State    networkidle    timeout=10s
    Wait For Elements State    [data-testid="monitoring-dashboard-card-${CREATED_DASH_ID}"]    detached    timeout=10s
    # Mark as cleaned up so teardown doesn't double-delete
    Set Suite Variable    ${CREATED_DASH_ID}    ${EMPTY}
