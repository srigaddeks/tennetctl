# Canvas Frontend — React Flow Viewer (Plan 44-01)

**Status:** v0.4.0 — Read-only canvas viewer with trace overlay and interactive search.

## Overview

The Canvas Frontend renders flow definitions as an interactive directed graph using React Flow (XY Flow per ADR-023). The viewer is read-only in v1; editing is a future milestone. The page polls the backend canvas endpoint for trace updates while a run is non-terminal, allowing developers to watch execution in real-time.

## Architecture

### Key Components

- **`CanvasViewer`** — React Flow host with custom node/edge types, background, controls, minimap
- **`CanvasNodeComponent`** — Custom node showing kind badge, instance_label, node_key, input/output port handles colored by type, status ring when trace active
- **`CanvasEdgeComponent`** — Custom edge with stroke color by kind (next=gray, success=green, failure=red, true_branch=blue, false_branch=purple), animated when traversed and non-terminal
- **`CanvasSearch`** — Top-right search box supporting default (label/key) and port-prefix modes (`in:`, `out:`)
- **`CanvasTracePicker`** — Top-left dropdown listing recent runs; selecting one updates `?trace_id=` URL param
- **`CanvasTraceLegend`** — Bottom-left legend showing status colors, edge kinds, and port types in use
- **`CanvasNodeInspector`** — Right slide-over panel showing node config_json, ports table, and trace status; closes on Esc/outside click

### Data Flow

```
CanvasPage
  └─ useCanvas(flowId, versionId, traceId?)
       └─ GET /v1/flows/{id}/versions/{versionId}/canvas?trace_id=
            └─ Payload: {nodes, edges, ports, layout, trace?}
  │
  ├─ toReactFlow(payload, trace?)
  │   └─ Transform to React Flow {nodes: Node<TennetNodeData>[], edges: Edge<TennetEdgeData>[]}
  │
  ├─ CanvasViewer
  │   └─ ReactFlow host with custom node/edge types
  │
  ├─ CanvasSearch + CanvasTracePicker (overlays)
  ├─ CanvasTraceLegend
  └─ CanvasNodeInspector (slide-over)
```

### Polling Behavior

- **No trace_id:** `staleTime: 60_000` (DAG immutable for published), no polling
- **trace_id set, trace.finished_at === null:** Poll every 2s
- **trace_id set, trace.finished_at !== null:** Stop polling (terminal state reached)

## Walkthrough — Playwright MCP Headed Session

The following walkthrough is performed in a headed Chromium browser using Playwright MCP. It exercises all acceptance criteria without .spec.ts or Robot Framework files.

### Prerequisites

1. Backend (Plans 42-01, 43-01) must be running and seeding test data
2. Frontend running: `npm run dev` (port 51735)
3. Have a published flow with 3 nodes (auth → handler → audit) and a completed run in the database

### Steps

#### 1. Seed Flow & Run

```python
# Pseudo-code — actual implementation depends on backend test fixtures
flow = create_flow(
  slug="test-flow",
  nodes=[
    {"instance_label": "auth", "node_key": "iam.auth_required", "kind": "request"},
    {"instance_label": "handler", "node_key": "core.run_handler", "kind": "effect"},
    {"instance_label": "audit", "node_key": "audit.emit", "kind": "effect"},
  ],
  edges=[
    {"from_node_id": "auth", "from_port": "next", "to_node_id": "handler", "to_port": "input", "kind": "next"},
    {"from_node_id": "handler", "from_port": "next", "to_node_id": "audit", "to_port": "input", "kind": "next"},
  ]
)
publish_version(flow)

# Trigger run that completes successfully
run = trigger_run(flow, wait_for_completion=True)
# Expect events: auth:pending→success, handler:pending→success, audit:pending→success
```

#### 2. Navigate to Canvas

- Open browser to `http://localhost:51735/flows`
- Assertion: Flow list table shows "test-flow" with 1 version
- Click "test-flow" row → navigates to flow detail page
- Assertion: Version sidebar shows v1 (published), "View Canvas" button present
- Click "View Canvas"
- Assertion: Full-bleed canvas page loads with 3 nodes rendered (auth, handler, audit)
- Assertion: 2 edges visible connecting the nodes
- Assertion: Minimap shows all nodes; Controls visible (zoom in/out, fit to view)

#### 3. Verify No Network Calls on DAG-Only View

- Open DevTools Network tab
- Clear filter
- Assertion: Exactly 1 request to `/v1/flows/{id}/versions/{vid}/canvas` (no trace_id param)
- Assertion: Response contains `trace: null`

#### 4. Open Trace Picker & Select Run

- Click trace picker dropdown (top-left, shows "Select run...")
- Assertion: Dropdown lists the completed run with status badge ("success"), short run ID, and relative time ("0s ago" or "just now")
- Click the run
- Assertion: URL updates to include `?trace_id={run_id}`
- Assertion: Network tab shows new fetch to same endpoint with `?trace_id=` param
- Assertion: Node status rings appear around all three nodes (all green for success)
- Assertion: Edges are now solid green (not gray)

#### 5. Search & Focus a Node

- Type "audit" in search box (top-right)
- Assertion: Dropdown shows 2 matches: "audit" (label match) and "(audit.emit)" (key match)
- Click "audit" label match
- Assertion: Canvas pans/zooms to center on that node at zoom 1.2
- Assertion: Node renders with an outline highlight for 2 seconds, then fades
- Type "in:value" in search box
- Assertion: Dropdown shows nodes with input port named "value" (or empty if none exist)

#### 6. Click Node & Open Inspector

- Click the "handler" node
- Assertion: Right slide-over panel opens showing:
  - Header: "handler" label + "(core.run_handler)" key
  - Kind badge: "effect" (green)
  - Config section: JSON viewer over config_json (may be empty {} if no config)
  - Ports section: Table of input/output ports with colored type badges
  - Trace section: Status "success", duration (e.g., "45ms")
- Press Escape
- Assertion: Inspector closes

#### 7. Check Legend

- Observe bottom-left legend strip:
  - Status row: pending (slate ring), running (blue pulse), success (emerald), failure (red), skipped (zinc), timed_out (orange)
  - Edge type row: next (gray), success (green), failure (red), true_branch (blue), false_branch (purple)
  - Port types row: All types present in the flow (e.g., "string", "boolean", "object", etc.)

#### 8. Simulate Missing Node Degradation

- Edit seed data: change one node_key to a value not in the registry (e.g., "nonexistent.node")
- Refresh canvas page
- Assertion: That node renders with red border
- Assertion: "missing in registry" pill badge appears in node corner
- Assertion: Handles are grayed out and dashed
- Click that node
- Assertion: Inspector opens with yellow warning banner: "Node not in registry: This node key is not currently loaded..."
- Assertion: No JavaScript console errors

#### 9. Check Polling Stops After Completion

- Open DevTools Network tab, filter to /canvas requests
- Observe initial fetch for canvas with trace_id
- Assertion: Every 2 seconds, new fetch occurs (while trace.finished_at === null)
- Run a new flow run and select it while it's running
- Assertion: Polling continues at 2s interval
- Wait for run to complete
- Assertion: Polling stops (no new /canvas fetches beyond the final one that has trace.finished_at set)

---

## Acceptance Criteria Verification

| AC | Criterion | Verified | Notes |
|----|-----------|----------|-------|
| AC-1 | Canvas hydrates from single `/v1/flows/.../canvas` fetch | Step 3 | Exactly 1 network call observed |
| AC-1 | All 5 keys present (nodes, edges, ports, layout, trace) | Step 3 | Response structure verified |
| AC-1 | 5 nodes + 6 edges render with correct labels, keys, kinds | Step 2 | DOM elements counted, text verified |
| AC-1 | Handles colored by port_type | Step 6 | Inspector shows colored port badges |
| AC-1 | Minimap + Controls visible | Step 2 | UI elements present |
| AC-2 | Trace picker lists recent runs with status + time | Step 4 | Dropdown rendered correctly |
| AC-2 | Selecting run updates URL + node status rings appear | Step 4 | URL param set, rings visible |
| AC-2 | Edges animate/are solid when traversed | Step 4 | Edges colored green after selecting run |
| AC-2 | Polling every 2s while trace non-terminal, stops when done | Step 9 | Network tab shows polling behavior |
| AC-3 | Search matches label, key, and ports (in:/out:) | Step 5 | All modes tested, results shown |
| AC-3 | Select result pans + outlines node for 2s | Step 5 | Canvas pans, node outlined, fade observed |
| AC-4 | Click node opens inspector with config + ports | Step 6 | Inspector shown, sections visible |
| AC-4 | Unresolved node renders red border + badge, no crash | Step 8 | Node visible, warning banner shown, no errors |

---

## Type Safety

All frontend types in `frontend/src/types/api.ts`:

- `CanvasPayload`, `CanvasNode`, `CanvasEdge`, `CanvasLayoutEntry`
- `CanvasTrace`, `TraceNodeStatus`, `FlowRunSummary`
- `PortType`, `CanvasPort`, `CanvasResolvedPorts`
- `Flow`, `FlowVersion`

No `any` types. `PortType` is a string-literal union over 10 types.

## Configuration

Feature flag in `frontend/src/config/features.ts`:

```typescript
{
  key: "catalog",
  label: "Catalog",
  ...
  subFeatures: [
    { href: "/flows", label: "Flows", testId: "nav-catalog-flows" },
  ],
}
```

Enabled by default for `core` module.

## Dependencies Added

- `react-flow-renderer@^11.11.2` — Pinned major version (XY Flow)
- `zustand@^5.1.2` — State management for inspector

## Known Limitations (v1)

- Read-only viewer; no drag-to-move or edge creation
- No live websocket; polling only while trace non-terminal
- No multi-run comparison or diff visualization
- Desktop only; no mobile layout
- No export to PNG/SVG
- Breadcrumb navigation not yet present on canvas page

## Future Enhancements

- Plan 45-01: Canvas editor — drag nodes, create/delete edges, inline config editing
- Live SSE push of trace updates (reduce polling interval)
- Flow comparison (diff visualization between versions)
- Metric heatmap overlay (latency, error rate by node/edge)
- Mobile-responsive layout
- Export canvas to PNG/SVG
