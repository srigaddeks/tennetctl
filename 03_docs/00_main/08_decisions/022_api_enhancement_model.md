# ADR-022: API Enhancement Model

**Status:** Accepted  
**Date:** 2026-04-10

---

## Context

The node-first architecture introduces a risk of confusion:

- Does tennetctl build APIs?
- Does the visual flow replace backend handlers?
- Is business logic supposed to move into nodes?

If this stays ambiguous, the system will drift toward either an over-abstracted
API builder or a workflow toy disconnected from real application code.

That would make the platform more complex, not simpler.

## Decision

APIs remain code-first.

tennetctl does not replace application business handlers. It enhances them with
middleware, policy, observability, and side-effect orchestration.

The primary role of flows for APIs is to describe and publish how concerns are
attached around real code-defined behavior.

## What Stays in Code

Application code continues to own:

- business logic
- domain validation that belongs to the application domain
- writes to application-owned state
- response payloads derived from domain behavior

tennetctl is not the primary place to implement core domain rules.

## What tennetctl Owns Around APIs

tennetctl owns the attachment layer around APIs, including:

- route and trigger binding
- auth and access policy
- feature flag checks
- rate limiting
- gateway policy configuration
- audit event emission
- logs, traces, and metrics hooks
- notifications and other side-effect workflows
- route-level operational views, if owned by the gateway feature

## Flow Role for APIs

An API flow describes how tennetctl enhances an existing or newly declared API
surface.

For example:

`route -> auth_required -> feature_flag -> rate_limit -> run_handler -> emit_audit -> write_log -> emit_trace`

The `run_handler` node represents the code-defined business handler. It is the
boundary between platform concerns and domain logic.

## Attachment Targets

An API enhancement flow may attach to:

- an HTTP route
- a webhook endpoint
- a gateway route definition
- a code-defined handler contract
- an event emitted after handler completion

The attachment target must be explicit in the published workflow metadata.

## Presets

To keep the system simple in practice, tennetctl should support reusable API
presets such as:

- `public_api`
- `internal_api`
- `admin_api`
- `webhook_endpoint`
- `llm_gateway_route`

Presets are feature-owned compositions of nodes and defaults. They reduce manual
wiring without hiding the underlying flow structure.

## Adoption Model

API enhancement should support progressive adoption:

1. **observe-only**: logs, traces, metrics, and audit hooks
2. **protect-and-observe**: auth, flags, rate limits, and observability
3. **fully attached**: gateway policy plus effect workflows and route metadata

This lets existing APIs adopt tennetctl without a rewrite.

## Debugging Requirement

Every enhanced API route must be inspectable in one place.

The system must show:

- bound workflow
- workflow version
- attached nodes
- compiled gateway behavior
- backend attachment points
- recent executions or route-level operational data

If this is not inspectable, the model is too magical.

## Consequences

- business logic remains clean and code-owned
- tennetctl gains a clear product identity
- API enhancement becomes the simplest high-value proof of the architecture
- visual flows stay grounded in real backend contracts instead of replacing them
