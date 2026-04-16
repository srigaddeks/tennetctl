# ADR-023: React Flow (XY Flow) as the Visual Canvas Library

**Status:** Accepted
**Date:** 2026-04-13

---

## Context

TennetCTL's core product is a visual flow viewer — a canvas that renders workflow graphs composed of nodes and edges. The read-only viewer (Phase 1 target) must render node graphs from the backend node registry. A future visual editor will allow composing flows on the canvas.

The canvas library choice is a foundational decision: it determines rendering performance, graph API shape, and future editor capabilities.

Candidates evaluated:

| Library | Ecosystem | License | Notes |
|---------|-----------|---------|-------|
| **React Flow / XY Flow** | React | MIT | Industry standard for React node UIs |
| **AntV X6** | React/Vue | MIT | Used by Activepieces; stronger graph features but steeper curve |
| **Reaflow** | React | Apache 2.0 | Lighter but less maintained |
| **Custom (D3 + SVG)** | Any | N/A | Full control, 3× development cost |

**Competitor reference:**
- n8n uses **Vue Flow** (Vue.js ecosystem — not applicable)
- Activepieces uses **AntV X6** (Angular ecosystem)

---

## Decision

**React Flow (XY Flow) is the canvas library for TennetCTL.**

---

## Rationale

**Why React Flow:**
- De facto standard for React workflow/node UIs. Used by Stripe, Typeform, and widely adopted in the SaaS space.
- Read-only mode is trivial: disable `nodesDraggable`, `nodesConnectable`, `elementsSelectable`. The read-only viewer (Phase target) requires almost no custom implementation.
- Handles large graphs via virtualization — important as tennetctl grows to hundreds of nodes per workflow.
- XY Flow organization actively maintains it; not a solo maintainer project.
- MIT licensed — fully compatible with AGPL-3 wrapper.
- The graph data model (nodes + edges with typed handles) maps directly to the tennetctl node contract model.

**Why not AntV X6:**
Activepieces uses X6 in an Angular codebase. X6 is more powerful for complex graph editing but has steeper learning curve, English documentation gaps, and stronger ties to the Alibaba ecosystem. For the current phase (read-only viewer), X6 adds complexity without benefit.

**Why not custom:**
3× the development cost with no advantage for the current scope.

---

## Impact on Deferred Monitoring Views

ADR-011 deferred service map and trace waterfall visualizations because no graph library was chosen. React Flow now unblocks these:

- **Service map:** Render service nodes with RED metric badges, edges as call relationships. React Flow handles this natively.
- **Trace waterfall:** Can be rendered as a timeline-ordered node column or as a true tree — React Flow supports both layouts.

These remain deferred in priority but are now technically unblocked.

---

## Implementation Notes

Graph data contract between backend and frontend:

```typescript
// Backend serves this shape from GET /api/v1/flows/{workflow_id}/graph
interface FlowGraph {
  nodes: FlowNode[]
  edges: FlowEdge[]
}

interface FlowNode {
  id: string           // node instance id in this workflow
  type: string         // node key from registry
  position: { x: number; y: number }
  data: {
    label: string
    category: string
    kind: "request" | "effect" | "control"
    config: Record<string, unknown>
  }
}

interface FlowEdge {
  id: string
  source: string
  target: string
  type: "next" | "success" | "failure" | "true" | "false"
}
```

The backend computes layout positions (using a DAG layout algorithm such as dagre) before serving the graph. The frontend renders the pre-positioned graph — it does not compute layout client-side in the read-only viewer.

---

## Consequences

- React Flow added as a frontend dependency.
- Backend must expose a `GET /api/v1/flows/{id}/graph` endpoint that returns React Flow-compatible node/edge JSON.
- Backend computes DAG layout (dagre or similar) before serving — avoids client-side layout complexity in Phase 1.
- Future visual editor: React Flow's drag-and-drop, connection handles, and node toolbar APIs are available when editor scope begins.
- Service map and trace waterfall views in Monitoring are unblocked.
