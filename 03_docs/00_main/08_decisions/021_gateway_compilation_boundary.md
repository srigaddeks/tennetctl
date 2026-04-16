# ADR-021: Gateway Compilation Boundary

**Status:** Accepted  
**Date:** 2026-04-10

---

## Context

API and HTTP flows combine two different kinds of behavior:

- gateway and policy concerns
- application business logic

The platform needs a hard line between what should be compiled into the gateway
execution plane and what should remain in backend application runtime.

Without that line, responsibilities blur and the system becomes harder to
operate.

## Decision

For HTTP and API flows, Apache APISIX is the first gateway execution target.

The backend flow compiler is responsible for splitting a published flow into:

- gateway-managed execution
- backend-managed execution

## Compile to APISIX

The compiler may target APISIX for concerns such as:

- route matching
- API key auth
- request auth integration
- feature flag gate checks when supported through stable runtime hooks
- rate limiting
- request/response header transforms
- access logging hooks
- tracing hooks

Only behavior that is safe, explicit, and operationally appropriate at the
gateway should be compiled there.

## Keep in Backend Runtime

The compiler must keep these concerns in backend-managed runtime:

- business handlers
- feature-owned business decisions
- writes to domain state
- feature-owned reports and dashboards
- effect-path orchestration that depends on domain outcomes
- any logic that requires feature-internal context not meant for the gateway

## Boundary Rule

Gateway execution handles policy and edge concerns.

Backend execution handles domain behavior.

The gateway must not become the home of business logic.

## Observability Rule

Compiled gateway behavior must remain inspectable from tennetctl.

That means the system must preserve:

- route-to-flow mapping
- published workflow version
- node-to-plugin mapping, where relevant
- execution metadata sufficient for debugging

## Fallback Rule

If a node cannot be compiled safely and clearly into APISIX, it stays in backend
runtime.

The compiler favors clarity over aggressive offloading.

## Consequences

- APIs remain clean and business-focused
- gateway concerns stay reusable and operationally centralized
- the visual flow remains the single authoring surface
- compilation remains predictable because the boundary is explicit
