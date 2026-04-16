# Backend Standards

Last updated: 2026-03-13 12:09:40 IST (+0530)
Current Python runtime observed in this workspace: CPython 3.13.5
Dependency inventory source of truth: `backend/99_docs/01_dependencies/01_current_inventory.md`

## Purpose

This is the primary backend best-practices document for Python and FastAPI work in this repository.
It is written for high-risk, banking-style use cases where security, traceability, and operational
discipline matter from day one.

This document supports future audit readiness, but it does not by itself guarantee compliance,
certification, or a successful penetration test.

## Scope

These rules apply to:

- Python modules
- FastAPI endpoints
- authentication and authorization flows
- logging and audit trails
- database-facing service code
- admin and feature-flag behavior

## Core engineering rules

- Keep the backend structure clean and numbered.
- Prefer simple, explicit code over abstraction-heavy code.
- Keep routers thin, services focused, and repositories isolated to persistence.
- Fail closed on invalid input, missing config, and unauthorized access.
- Use exact dependency versions and track them in `backend/99_docs/01_dependencies/`.
- Treat every external input as untrusted.

## Recommended backend layout

- `backend/00_config/`: settings, environment validation, security-critical startup checks
- `backend/01_sql_migrations/`: schema migration area with immutable deployed history and editable in-progress work
- `backend/01_core/`: shared models, error types, security primitives, base types
- `backend/01_utils/`: small reusable helpers only
- `backend/NN_<feature>/router.py`: HTTP routes only
- `backend/NN_<feature>/schemas.py`: request and response schemas
- `backend/NN_<feature>/service.py`: business logic
- `backend/NN_<feature>/repository.py`: data access only
- `backend/NN_<feature>/dependencies.py`: request-scoped dependency providers
- `backend/90_tests/`: unit, integration, contract, and security tests

Migration rules:

- `backend/01_sql_migrations/01_migrations/` is deployed history and must not be changed.
- `backend/01_sql_migrations/02_inprogress/` is the only editable migration workspace.
- Migration files for this flow must use the format `YYYYMMDD_short-explanation.yaml`.

## Python coding standards

- Use type hints for all public functions, methods, and return values.
- Use timezone-aware datetimes and store server-side timestamps in UTC.
- Keep functions small and single-purpose.
- Avoid mutable default arguments, wildcard imports, hidden global state, and import-time side effects.
- Prefer explicit domain objects and schemas over loose dictionaries.
- Raise explicit domain exceptions and translate them at the API boundary.
- Keep secrets, tokens, credentials, and raw personal data out of logs, exceptions, and comments.
- Use parameterized queries only.
- Keep code deterministic unless the function is intentionally performing I/O.

## FastAPI standards

- Use an application factory pattern.
- Use lifespan hooks for startup and shutdown work.
- Use explicit request and response models for every endpoint.
- Declare status codes and failure paths deliberately.
- Use `Annotated[...]` with `Path`, `Query`, `Header`, `Body`, and `Depends`.
- Do not place business logic, authorization policy, or SQL inside route handlers.
- Separate authentication from authorization.
- Use idempotency keys for retry-sensitive writes.
- Apply request size limits, rate limits, and timeouts.
- Return a correlation ID or request ID on every request.
- Keep public response shapes stable and documented.
- Never return raw ORM models directly from public APIs.

## Security baseline

- Enforce TLS in deployed environments.
- Use least privilege for users, services, and database accounts.
- Keep secrets outside code and validate required config at startup.
- Use strong password hashing for local credentials, preferably Argon2id.
- Support MFA for privileged access.
- Protect against broken object-level authorization on every resource fetch and mutation.
- Prevent injection, path traversal, unsafe deserialization, replay attacks, and overexposed serialization.
- Pin dependencies and review them before adoption.

## Logging standards

Use application logs for diagnostics and operations, not as the primary audit system.

Every production log entry should include:

- timestamp
- severity
- service name
- environment
- request ID or correlation ID
- actor type when known
- action name
- outcome

Logging rules:

- Use structured logs, not free-form strings only.
- Never log passwords, tokens, secrets, raw KYC data, PAN-like values, or full personal identifiers.
- Mask or hash sensitive identifiers when operationally necessary.
- Log failures with enough context to investigate, but without leaking internals to clients.
- Link logs to session ID, trace ID, or external observability IDs when available.

## Audit standards

Audit is separate from diagnostic logging. Audit data must answer: who did what, to which entity, when, from where, and with what outcome.

Audit events are mandatory for:

- sign-up, login, logout, password reset, MFA enrollment, MFA reset
- token issuance, token revocation, session revocation
- role assignment, role removal, permission changes
- feature-flag changes
- admin actions
- sensitive data reads
- financial or approval-sensitive state changes
- configuration changes

Every audit record should include:

- event ID
- event timestamp in UTC
- actor ID or service ID
- actor type
- target entity type
- target entity ID
- action
- result
- request ID or correlation ID
- session ID when relevant
- IP address or network source when relevant
- approval reference when the action requires approval

Audit rules:

- Audit tables should be append-only.
- Audit history must support timeline reconstruction per user, session, role, and entity.
- Privileged changes should capture both the actor and the approver when they differ.
- Audit records must not be silently mutable.
- Keep audit retention, access control, and export paths tightly controlled.

## Data modeling guidance from current design notes

The ideas in `temp/transcription.txt` are directionally correct and should be used carefully.

Preferred pattern:

- Use a stable core table for the main entity identity.
- Use detail tables for expandable entity attributes where that improves normalization.
- Use dimension tables for small controlled reference sets such as account type, status, permission type, or feature group.
- Use transaction or event tables for frequent operational events such as login, logout, session creation, and workflow actions.
- Use a dedicated audit timeline for security-relevant history.

Rules for this pattern:

- Do not push everything into JSON if the structure is known and searchable.
- Do not over-normalize simple data just to follow a pattern mechanically.
- Use dimension tables where the same controlled values repeat across large tables.
- Keep event tables immutable except for tightly controlled correction workflows.
- Always include audit columns on core business tables.

## Permissions and feature flags

- Feature flags must be explicit and environment-aware.
- Treat feature flags as controlled configuration, not ad hoc booleans scattered in code.
- Separate feature availability from user permissions.
- Roles, permissions, and feature access should be modeled clearly enough to answer who could do what at a given point in time.
- Changes to roles, permissions, and feature flags must be audited.

## Minimum quality gates

Every backend change should be able to pass:

- formatting
- linting
- type checking
- automated tests
- dependency vulnerability scanning
- secret scanning

Minimum test coverage types:

- unit tests for business logic
- integration tests for persistence and external boundaries
- API contract tests
- negative tests for auth and validation
- security tests for permission failures and common injection paths

## Practical standard

Do not optimize for theoretical perfection. Optimize for code that is:

- secure enough for high-risk production use
- simple enough to review
- observable enough to investigate
- structured enough to extend without rework
- disciplined enough to support future audits
