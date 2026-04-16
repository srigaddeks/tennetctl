# ADR-016: Node-First Architecture

**Status:** Accepted  
**Date:** 2026-04-10

---

## Context

tennetctl needs an architecture that stays understandable as the product grows to many features and many sub-features.

The repeated concerns are clear:

- route and trigger definition
- auth and access decisions
- feature flags
- rate limiting
- audit emission
- logs, traces, and metrics
- feature-specific dashboards and reports

If these concerns are implemented ad hoc inside handlers, the system becomes hard to reason about. If they are moved into a visual layer without backend authority, the UI drifts from reality.

## Decision

tennetctl adopts a node-first architecture built from four concepts:

- **Feature**: a bounded domain that owns business behavior, contracts, dashboards, and reports.
- **Sub-feature**: the smallest independently shippable capability inside a feature.
- **Node**: a registered backend building block, usually implemented as a Python function with typed config, typed inputs, typed outputs, and runtime/editor metadata.
- **Flow**: a visual composition of nodes that the backend validates and executes or compiles.

## Node Definition

A public node is not just a callable. It must define:

- stable key
- label and category
- config schema
- input schema
- output schema
- runtime class
- backend handler

In most cases the handler is a Python function.

## Runtime Classes

Nodes are split into runtime classes:

- **request nodes**: run in the live request path and influence the response path
- **effect nodes**: run as side effects after or around a decision
- **control nodes**: branch, fan-out, merge, or otherwise control graph structure

Examples:

- request: auth, feature flag, rate limit, validate input, run handler
- effect: emit audit, write log, emit trace, increment metric, send notification
- control: branch, on-success, on-failure, merge

## Backend and Frontend Responsibilities

The backend is the source of truth for node contracts and execution semantics.

The frontend owns:

- flow authoring
- node configuration UX
- graph visualization
- run inspection

The frontend does not invent node behavior that the backend does not own.

## Feature Ownership

Dashboards and reports remain feature-owned.

- IAM owns IAM dashboards
- Audit owns Audit dashboards
- Monitoring owns Monitoring dashboards

There is no separate cross-product dashboard feature for behavior that already belongs to an existing feature.

## Gateway Execution Plane

For HTTP and API policy execution, the first gateway target is Apache APISIX.

Reasoning:

- route and plugin composition maps naturally to node-based policy graphs
- dynamic configuration is better aligned with a control-plane compiler than plain static proxy configuration
- auth, rate limiting, logging, and tracing concerns map well to gateway-managed policy

Application handlers remain responsible for business logic.

## Consequences

- features stay small and bounded
- repeated platform concerns become reusable nodes
- flows become a visual contract over real backend behavior
- the backend can compile or execute flows consistently
- documentation can scale by treating features, sub-features, and nodes as separate planning surfaces
