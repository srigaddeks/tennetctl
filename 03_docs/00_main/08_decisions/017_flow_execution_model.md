# ADR-017: Flow Execution Model

**Status:** Accepted  
**Date:** 2026-04-10

---

## Context

ADR-016 defines features, nodes, and flows, but it does not yet define how a
flow actually executes. Without a strict execution model, the frontend canvas
would drift into a diagramming tool instead of a reliable backend contract.

The system needs one simple execution model that works across API flows,
internal workflows, and feature-owned operational flows.

## Decision

A flow is a directed graph of typed node invocations with one of three runtime
classes:

- **request path**: live decision path for an incoming request or trigger
- **effect path**: side effects emitted from the request path or another flow
- **control path**: branching and join behavior

The execution engine validates flows before they can be published and enforces
the same semantics for every feature.

## Entry Points

A flow starts from one trigger:

- `http`
- `event`
- `manual`

Each flow has exactly one declared trigger type.

## Edge Types

The allowed edge types are:

- `next`: normal sequential execution
- `success`: execute only if the upstream node succeeds
- `failure`: execute only if the upstream node fails
- `true`: boolean branch for control nodes
- `false`: boolean branch for control nodes

No other edge semantics are allowed in v1.

## Branching and Parallelism

v1 supports:

- sequential execution
- conditional branching
- parallel fan-out
- explicit merge

v1 does not support:

- loops
- recursion
- subflow calls
- implicit joins

Every parallel branch must join through an explicit merge node if later nodes
depend on the branch outputs together.

## Data Passing

Nodes do not exchange unbounded shared state.

Each node invocation receives:

- resolved config
- typed input payload
- execution context
- zero or more artifact references

Each node invocation may produce:

- typed output payload
- zero or more artifact references
- structured run metadata

## Request vs Effect Semantics

Request-path nodes may:

- allow execution to continue
- deny execution
- transform request data
- produce response data
- terminate the request path

Effect nodes may:

- run after success
- run after failure
- emit durable side effects
- produce artifacts and logs

Effect nodes must not silently alter the already-decided request outcome.

## Failure Model

Each node execution ends in one of:

- `succeeded`
- `failed`
- `skipped`
- `cancelled`
- `timed_out`

Flows must declare per-node failure policy through node metadata and runtime
config. v1 supports only:

- fail the current path
- continue on failure
- route to `failure` edge

Global rollback semantics are out of scope for v1.

## Retry Model

Retries are explicit node configuration, not a hidden runtime behavior.

v1 allows:

- `max_attempts`
- `backoff_seconds`

Retries are allowed only for nodes marked retryable by the backend node
definition.

## Consequences

- the flow editor has a small, stable graph model
- the backend can validate and execute every flow predictably
- API flows and async side-effect flows share one mental model
- the system stays simple by refusing loops and implicit behavior in v1
