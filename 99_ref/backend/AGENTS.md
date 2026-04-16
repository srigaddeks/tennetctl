# Backend AGENTS.md

Last updated: 2026-03-13 11:22:38 IST (+0530)
Current Python runtime observed in this workspace: CPython 3.13.5

## Purpose

This file defines mandatory engineering rules for everything created under `backend/`.
The goal is practical, deployable, production-grade Python services with strong security,
clean structure, low operational risk, and evidence that supports future audits.

Primary human-readable implementation standard:
`backend/99_docs/00_backend_standards.md`

These rules are mandatory for all backend code, APIs, scripts, migrations, jobs, tests,
and documentation.

## Non-negotiable principles

1. Build for production first. No placeholder security, no fake integrations, no TODO-based controls.
2. Prefer simple, auditable designs over clever abstractions.
3. Default deny. Every permission, network path, secret, and data access path must be explicitly justified.
4. Assume hostile input at every boundary: HTTP, CLI, env vars, files, queues, caches, logs, and databases.
5. All changes must preserve deployability, observability, and rollback safety.
6. `requirements.txt` must stay machine-readable. Dependency metadata belongs in `backend/99_docs/01_dependencies/`.
7. Do not claim compliance or pentest success without external validation. Build evidence and controls so audits are feasible.

## Required backend structure

Keep the numbered folder convention and do not create ad hoc top-level sprawl.

Preferred pattern:

- `backend/00_config/`: settings, configuration loading, environment validation
- `backend/01_sql_migrations/`: migration workspace with immutable deployed history and editable in-progress files
- `backend/01_core/`: shared domain primitives, constants, base models, error types
- `backend/01_utils/`: narrowly scoped helpers only
- `backend/NN_<feature>/`: feature modules grouped by bounded context using a two-digit order prefix such as `03_auth_manage`
- `backend/90_tests/`: unit, integration, contract, security, and performance tests
- `backend/91_scripts/`: operational scripts and one-off maintenance tools
- `backend/99_docs/`: backend documentation and evidence artifacts
- `backend/99_docs/01_dependencies/`: dependency inventory, update history, risk notes

Rules:

- Every new module must have a single clear ownership boundary.
- Cross-feature imports should flow through stable interfaces, not internal files.
- Shared code belongs in `00_config`, `01_core`, or `01_utils`, not copied into feature folders.
- Documentation must follow the same numbered structure style already used in `backend/`.
- `backend/01_sql_migrations/01_migrations/` is immutable deployed history and must never be edited.
- `backend/01_sql_migrations/02_inprogress/` is the only place for active migration changes.
- Migration filenames in this repo must use `YYYYMMDD_short-explanation.yaml`.

Recommended FastAPI feature layout inside `backend/NN_<feature>/`:

- `router.py`: API route definitions only
- `schemas.py`: request and response models
- `service.py`: business logic orchestration
- `repository.py`: database access only
- `models.py`: persistence models if needed
- `dependencies.py`: feature-scoped dependency providers
- `constants.py`: feature constants and enums

## Python standards

- Target Python version: CPython 3.13.5 until explicitly changed and documented.
- Use type hints everywhere. Public functions, methods, and return types must be explicit.
- Prefer `pathlib`, `datetime` with timezone-aware values, `enum`, `dataclasses` or Pydantic models where appropriate.
- Use `src`-quality import discipline even if the repository layout is flat.
- No wildcard imports.
- No mutable default arguments.
- No hidden side effects in import time code.
- No global state for request, auth, config, or database sessions.
- One module should do one thing well. Split files before they become ambiguous.
- Prefer pure functions for business logic. Keep I/O at the edges.
- Use structured exceptions with explicit error mapping.
- Use idempotent operations wherever retries are possible.
- Prefer `Annotated[...]` for parameter metadata and dependency declarations when using FastAPI.
- Prefer `typing.Protocol` or clear interfaces when abstraction is needed.
- Prefer immutable data structures for config and domain values unless mutation is required.
- Keep modules import-safe so tests and tooling can import them without side effects.

## FastAPI architecture standards

- Use an application factory pattern so app creation is deterministic and testable.
- Use FastAPI lifespan hooks for startup and shutdown concerns, not import-time initialization.
- Register routers by feature, not by HTTP verb or database table.
- Keep endpoint handlers thin. Business rules belong in service functions or domain modules.
- Keep repositories focused on persistence and query concerns only.
- Do not let routers call the database directly unless the module is intentionally trivial and still reviewed.
- Separate input schemas, output schemas, and persistence models.
- Never return raw ORM models directly from public endpoints.
- Keep OpenAPI truthful. Every documented parameter, response, and error should match runtime behavior.
- Use explicit tags, prefixes, and versioning for routers.
- Centralize exception handlers for predictable API errors.

## FastAPI function and endpoint rules

Every FastAPI endpoint function must:

- Declare explicit request and response models.
- Declare status codes explicitly.
- Use `Annotated` with `Path`, `Query`, `Header`, `Cookie`, `Body`, and `Depends` where relevant.
- Keep HTTP concerns in the endpoint and move business logic into a service layer.
- Translate domain errors into safe HTTP errors consistently.
- Enforce authentication before authorization-sensitive work begins.
- Avoid hidden database writes in read endpoints.
- Return stable response shapes.
- Include pagination, filtering, and ordering contracts explicitly for list endpoints.

Endpoint functions must not:

- Contain large blocks of business logic.
- Build SQL queries inline.
- Instantiate heavyweight clients on every request.
- Mix validation, authorization, persistence, and formatting into one function.
- Return inconsistent shapes based on success path shortcuts.

## Async and concurrency rules

- Use `async def` only when the call path is truly asynchronous.
- Do not call blocking network, file, or database operations from `async def` endpoints.
- If a library is synchronous, either keep the endpoint synchronous or offload safely.
- Avoid shared mutable state across requests.
- Apply timeouts and cancellation handling for outbound I/O.
- Make retry behavior explicit and idempotent.
- Background tasks are for non-critical post-response work only, never for required financial or security actions.

## Pydantic and schema rules

- Use strict request and response models.
- Validate and normalize data at the boundary.
- Separate external API schemas from internal domain objects.
- Use field constraints for lengths, ranges, regexes, and formats.
- Prefer explicit aliases and serialization rules over magic transformations.
- Do not accept arbitrary dictionaries when a typed schema is possible.
- Mark nullable fields intentionally rather than by habit.
- Keep sensitive fields excluded from default serialization.

## Dependency injection rules

- Use FastAPI dependencies for request-scoped concerns such as auth context, DB sessions, settings, and clients.
- Keep dependencies composable and side-effect aware.
- Do not hide critical authorization inside unrelated dependencies.
- Yield-based dependencies must always clean up connections, sessions, and resources.
- Dependency trees should remain shallow enough to audit.

## Error handling rules

- Standardize error response format across the API.
- Map validation, auth, permission, conflict, not-found, rate-limit, and upstream failures deliberately.
- Do not surface raw internal exception text to clients.
- Preserve enough internal detail in logs for incident investigation.
- Use custom exception types for domain and security cases that matter operationally.

## Performance and resilience rules

- Set request, database, cache, and outbound HTTP timeouts explicitly.
- Paginate large reads by default.
- Avoid N+1 query patterns.
- Cache only where correctness and invalidation rules are well understood.
- Define health, readiness, and liveness endpoints with minimal sensitive detail.
- Prefer graceful degradation over cascade failure when non-critical dependencies are unavailable.

## Function-level rules

Every function must:

- Have one clear responsibility.
- Validate inputs early and fail closed.
- Return typed, predictable values.
- Avoid leaking secrets or internal state through exceptions.
- Be deterministic unless I/O is the point of the function.
- Log meaningful context without logging sensitive data.
- Enforce authorization before data access or mutation.
- Use timezone-aware UTC timestamps for persistence and eventing unless a business rule requires another timezone.

For complex logic:

- Add a short docstring describing inputs, outputs, side effects, and failure modes.
- Prefer explicit value objects over loose dictionaries.
- Keep cyclomatic complexity low. Refactor branching-heavy code.

## API standards

Every API must:

- Use explicit request and response schemas.
- Reject malformed input with safe, consistent error responses.
- Enforce authentication and authorization separately.
- Apply rate limiting, request size limits, and timeouts.
- Use idempotency keys for retry-sensitive write operations.
- Return correlation IDs for traceability.
- Never expose stack traces, secrets, raw SQL, internal network paths, or vendor tokens.
- Version public APIs deliberately.
- Validate content type and accepted methods strictly.
- Sanitize file uploads and scan them before downstream use.
- Expose health endpoints separately from business endpoints.
- Make OpenAPI docs available only as appropriate for the environment and threat model.

Required API controls:

- TLS everywhere in deployed environments.
- Secure headers.
- CORS restricted to known origins only.
- CSRF protection where browser-authenticated flows exist.
- Replay protection for sensitive operations.
- Pagination for list endpoints.
- Safe defaults for serialization to prevent overexposure.

## Authentication and authorization

- Use strong password hashing for any local credentials: Argon2id preferred, bcrypt only if required by compatibility.
- MFA must be supported for privileged access.
- Sessions and tokens must have rotation, expiry, revocation, and audience scoping.
- Apply least privilege to service accounts, users, and internal roles.
- Use deny-by-default authorization checks close to each protected action.
- Separate authentication logic from authorization policy logic.
- Protect against broken object level authorization by verifying resource ownership or policy grants on every object fetch and mutation.

## Secrets and configuration

- No hardcoded secrets, keys, tokens, salts, or credentials in code, docs, or tests.
- Load configuration through validated settings objects.
- Fail startup if required secrets or security-critical config are missing.
- Distinguish local, test, staging, and production configuration explicitly.
- Secret rotation must not require code changes.
- `.env.example` may contain names and formats only, never real values.
- Log whether secure config is present, not the values themselves.

## Data protection

- Classify data as public, internal, confidential, restricted, or regulated before storing it.
- Minimize collection. Do not store data unless it is required.
- Encrypt sensitive data in transit and at rest.
- Prefer field-level protection or tokenization for highly sensitive values.
- Never log secrets, PAN-like values, auth tokens, government identifiers, or raw personal data unless explicitly required and masked.
- Define retention and deletion rules for every stored data class.
- Support legal hold and auditable deletion paths where applicable.

## Database and storage rules

- Use parameterized queries only. Never build SQL with string interpolation.
- Apply migrations through versioned, reviewed migration files.
- Enforce constraints in the database, not only in application code.
- Use optimistic or pessimistic locking where concurrent writes can corrupt state.
- Scope database credentials per service and environment.
- Backups must be encrypted, tested, and access controlled.
- Sensitive exports must be tracked and access logged.

## Secure coding rules

- Treat every external dependency as a supply-chain risk.
- Pin package versions.
- Verify dependency purpose, maintenance status, license, and known vulnerabilities before use.
- Avoid unsafe deserialization, dynamic code execution, shell injection patterns, and implicit trust of filenames or paths.
- Never use `eval`, `exec`, `pickle`, or unsafe YAML loaders on untrusted data.
- Guard subprocess usage with explicit argument arrays and allowlists.
- Normalize and validate file paths to prevent traversal.
- Use constant-time comparison for secret material where relevant.
- Limit outbound network access to approved destinations in deployment.

## Logging, monitoring, and auditability

- Use structured logs.
- Include timestamp, severity, service, environment, correlation ID, actor type, and action outcome.
- Separate audit logs from diagnostic logs when possible.
- Audit logs for auth, privilege changes, money movement, sensitive reads, config changes, and admin actions are mandatory.
- Logs must be tamper-evident or shipped to immutable storage in production.
- Metrics and alerts must cover auth failures, permission denials, input validation failures, latency, error rates, and dependency failures.

## Testing standards

Every backend change must add or update tests as appropriate.

Minimum expected coverage types:

- Unit tests for business logic
- Integration tests for database, queue, cache, and third-party boundaries
- API contract tests for request and response behavior
- Negative tests for auth, validation, and permission failures
- Security tests for injection, traversal, deserialization, replay, and privilege escalation paths
- Concurrency or async behavior tests where the service uses async workflows
- Schema serialization tests for sensitive-field exclusion and backward compatibility

Required quality gates when tooling is added:

- Formatting
- Linting
- Type checking
- Automated tests
- Dependency vulnerability scanning
- Secret scanning

## Compliance-oriented engineering

These practices support future readiness for SOC 2, ISO 27001, DPDP, and similar frameworks, but they do not replace formal certification work.

Mandatory evidence-friendly practices:

- Document data flows and trust boundaries.
- Document dependency ownership, review date, and version history.
- Maintain change history through reviewed commits and pull requests.
- Track access control design and privileged role definitions.
- Record incident response expectations and logging coverage.
- Define backup, restore, retention, and deletion behavior.
- Keep environment-specific configuration documented.
- Maintain asset inventory for services, data stores, queues, and third-party providers.

## Dependency governance

All dependency metadata must be maintained in `backend/99_docs/01_dependencies/`.

For every dependency, record:

- package name
- exact version in use
- introduced or reviewed datetime
- purpose
- owning module or feature
- source of truth file
- security notes
- license notes if relevant
- upgrade notes or constraints

If `requirements.txt` changes, the corresponding dependency documentation must be updated in the same change.

## Documentation requirements

New backend capabilities must update docs when they affect:

- dependencies
- configuration
- API behavior
- security model
- operational runbooks
- data handling

Documentation must describe the system that actually exists, not the intended future state.

## Prohibited shortcuts

- No placeholder auth.
- No broad `except Exception` without re-raising or safe translation.
- No silent failures.
- No storing secrets in code comments or sample payloads.
- No unaudited admin backdoors.
- No debug modes enabled by default.
- No direct production data access from local scripts without explicit safeguards.
- No merging code with failing quality or security checks.

## Definition of done for backend work

A backend change is not done unless:

1. The code is deployable.
2. The structure remains clean and consistent.
3. Types, validation, and error handling are explicit.
4. Security controls are implemented, not implied.
5. Tests cover success and failure paths.
6. Dependency docs are updated if packages or runtimes changed.
7. Logs and auditability are sufficient for investigation.
8. Data handling is minimal and documented.
9. Compliance-supporting evidence is easier after the change, not harder.
10. FastAPI routing, schemas, and service boundaries remain clean and testable.
