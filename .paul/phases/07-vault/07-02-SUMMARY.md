---
phase: 07-vault
plan: 02
subsystem: frontend
tags: [vault, ui, reveal-once, dialog, useref, tanstack-query, zod, react-hook-form, robot-framework, playwright-browser, e2e]

requires:
  - phase: 07-vault
    plan: 01
    provides: Vault backend — 5 HTTP routes under /v1/vault, VaultSecretMeta response shape, key_shape regex, reveal-once API contract (POST response never carries value)
  - phase: 01-core-infrastructure
    provides: TanStack Query + Providers, Modal / Toast / UI primitives, features.ts registry, Robot + Playwright Browser runtime
provides:
  - Vault entry in frontend/src/config/features.ts — top-bar tab + sidebar between Feature Flags and Node Catalog, auto-wires the shell
  - Vault TS types in frontend/src/types/api.ts — VaultSecretMeta / VaultSecretCreateBody / VaultSecretRotateBody (no plaintext type — reveal holds it in a ref)
  - frontend/src/features/vault/ — hooks/use-secrets.ts, schema.ts (Zod), _components/ reveal-once-dialog, create-secret-dialog, rotate-secret-dialog, secret-row-actions
  - /vault page (app router) — list / empty-state / error / CRUD entry points
  - tests/e2e/keywords/api.resource + vault.resource — shared Robot keywords (reusable by Phase 8 auth E2E)
  - tests/e2e/vault/01_secrets.robot — 4 scenarios exercising the live stack
affects: [Phase 8 (auth) — will reuse api.resource cleanup + reveal-once pattern for session signing-key rotations; future vault audit-trail sub-page]

tech-stack:
  added:
    - robotframework-requests>=0.9.7 (into .venv, was missing; api.resource needs RequestsLibrary)
  patterns:
    - "Reveal-once enforcement lives in the UI layer — raw plaintext stays in a `useRef` (not state, not TanStack cache), handed to a dialog that UNMOUNTS on dismiss (returns null when open=false). A page reload also cannot recover the value."
    - "Row-scoped testids for dialogs mounted per row — rotate-secret-form-${key} and delete-confirm-${key}, not shared testids. Browser library strict-mode rejects duplicate selectors even when only one is visible."
    - "Shared Robot resource files under tests/e2e/keywords/ — api.resource (RequestsLibrary HTTP helpers) + vault.resource (Browser keywords). Reusable by future features without duplication."
    - "Page reload in Test Teardown — cleanest way to avoid stale dialog / cached row state bleeding between tests. Cheaper than re-opening a new context."

key-files:
  created:
    - frontend/src/features/vault/hooks/use-secrets.ts
    - frontend/src/features/vault/schema.ts
    - frontend/src/features/vault/_components/reveal-once-dialog.tsx
    - frontend/src/features/vault/_components/create-secret-dialog.tsx
    - frontend/src/features/vault/_components/rotate-secret-dialog.tsx
    - frontend/src/features/vault/_components/secret-row-actions.tsx
    - frontend/src/app/(dashboard)/vault/page.tsx
    - tests/e2e/keywords/api.resource
    - tests/e2e/keywords/vault.resource
    - tests/e2e/vault/01_secrets.robot
  modified:
    - frontend/src/types/api.ts
    - frontend/src/config/features.ts

key-decisions:
  - "useRef for reveal value, not state — React state would persist across render cycles inside a React Query cache snapshot. Ref is manually cleared on dismiss; the `open=false` render path returns null from RevealOnceDialog to detach the textarea from the DOM."
  - "Row-scoped testids on row-local dialogs — Playwright strict mode flagged duplicate testids (one rotate-secret-form per row). Fixed by suffixing with the secret key on form, value, submit, and delete-confirm + delete-confirm-yes."
  - "Page reload in Test Teardown — simpler than New Context-per-test + preserves one headless Browser session. Robot run goes 7s → 15s including reloads, acceptable for 4 scenarios."
  - "Skipped the UI-level GET /v1/vault/{key} call — the UI never fetches plaintext. Create + Rotate dialogs hold the just-entered value locally and hand it to reveal-once. The admin HTTP endpoint exists for operators with curl, not for the UI."

patterns-established:
  - "Reveal-once orchestration: form component owns a useRef holding the user-entered value; after POST success, `revealRef.current = {key, value}` then `setRevealOpen(true)`; on dismiss, `revealRef.current = null; setRevealOpen(false)`."
  - "Per-row dialogs use row-scoped testids — rule of thumb: any dialog/modal rendered inside a table row or list item must include a unique key in its testid."
  - "Robot suite shape: Suite Setup opens Browser + Page; Test Teardown cleans API + reloads; Test Case drives UI + asserts API; Suite Teardown cleans + closes."
  - "Backend delete cleanup via api.resource — keeps tests hermetic across reruns without driving the UI to delete."

duration: ~35min
started: 2026-04-16T16:05:00Z
completed: 2026-04-16T16:40:00Z
---

# Phase 7 Plan 02: Vault UI + Robot E2E — Summary

**The vault ships as a first-class UI feature: /vault list, create-with-reveal-once, rotate-with-reveal-once, delete-with-confirm. Reveal-once enforcement proven at the DOM level — dismiss removes the value, page reload cannot recover it. Full Robot + Playwright suite passes against the live stack.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~35min |
| Tasks | 4 (3 UI + 1 E2E) |
| Files created | 10 (7 frontend + 3 E2E) |
| Files modified | 2 (types/api.ts + config/features.ts) |
| New code lines | ~660 (UI 500 + Robot 160) |
| Routes in build | 15, including /vault as static |
| Typecheck | tsc --noEmit exit 0 |
| Production build | next build exit 0, /vault listed |
| Robot E2E | 4/4 pass |

## Acceptance Criteria Results

| Criterion | Status | Evidence |
|-----------|--------|----------|
| AC-1: Top-bar + sidebar expose Vault | Pass | Chrome DevTools MCP snapshot of /vault: nav has Vault between Feature Flags and Node Catalog; sidebar reads "Vault" + "All secrets" link; active state highlighted. |
| AC-2: Empty-state list shows CTA | Pass | EmptyState component mounted when `data.items.length === 0` with "No secrets yet" + "+ Create first secret" button. |
| AC-3: Create secret flow with reveal-once | Pass | MCP drive + Robot `Create Secret Shows Value Once` — form submits, dialog closes, reveal-once dialog shows value; Copy button wired to navigator.clipboard; "Got it" dismisses; sentinel absent from DOM + localStorage + sessionStorage after dismiss. |
| AC-4: Rotate secret flow with reveal-once | Pass | Robot `Rotate Secret Bumps Version` — version bumps to v2 in the row, reveal-once shows new value, post-dismiss sentinel is absent from DOM. |
| AC-5: Delete secret with confirm | Pass | Robot `Delete Secret Removes Row` — confirm dialog appears, "Delete" fires mutation + toast, row detaches, API list no longer includes the key. |
| AC-6: Invalid inputs rejected at form layer | Pass | Zod schema (`secretCreateSchema`) mirrors backend key regex; "onChange" mode blocks submit + shows inline error. |
| AC-7: Conflict handled gracefully | Pass | `setServerError` on mutate throw → inline red error div in the create dialog; dialog does NOT close; reveal-once does NOT open. (Tested indirectly — recycling-refused is backend-enforced, surfaced in UI error state.) |
| AC-8: Robot E2E suite covers happy path | Pass | `.venv/bin/robot --outputdir /tmp/vault-robot tests/e2e/vault/` — 4/4 scenarios pass; evidence at /tmp/vault-robot/report.html. |
| AC-9: No plaintext leak in network or storage | Pass | MCP `evaluate_script` post-dismiss — `document.body.innerText.includes(sentinel) === false`; `localStorage` no match; `sessionStorage` no match. Robot `Reveal Once Is Truly Once` reloads page + greps DOM + inspects API list response for forbidden keys. |
| AC-10: Typecheck + build + full E2E green | Pass | `npx tsc --noEmit` exit 0; `npx next build` exit 0 with /vault in route list; vault Robot suite 4/4 pass. Core Robot health suite has 2 pre-existing failures from a prior deletion of frontend/src/app/page.tsx (unrelated to vault). |

## Accomplishments

- **Reveal-once works at the DOM level** — `useRef` holds the user-entered plaintext through POST, hands it to RevealOnceDialog, ref nulls on dismiss. Dialog returns null when closed, so the textarea is fully detached from the DOM. Page reload cannot recover the value (verified by Robot `Reveal Once Is Truly Once`).
- **Live E2E pass against running stack** — Robot runs drive headless Chromium via Playwright Browser library against backend on 51734 + Next on 51735. Each scenario uses `pw-vault-${epoch}` keys and cleans up via API in Test Teardown.
- **Visual smoke via Chrome DevTools MCP** — Exercised create + rotate + delete manually, confirmed no sentinel leak into DOM or browser storage after every dismiss.
- **Feature registry auto-wired** — one `FEATURES` entry inserts top-bar tab + sidebar link. No manual topbar/sidebar code edits.
- **Row-scoped testids** — each row's rotate + delete dialogs carry `${secret.key}` in their testids to avoid Playwright strict-mode duplicate-selector errors.

## Files Created/Modified

### Created (10)

| File | Purpose |
|------|---------|
| `frontend/src/features/vault/hooks/use-secrets.ts` | TanStack hooks: useSecrets / useCreateSecret / useRotateSecret / useDeleteSecret |
| `frontend/src/features/vault/schema.ts` | Zod schemas mirroring backend Pydantic (key regex + value/description limits) |
| `frontend/src/features/vault/_components/reveal-once-dialog.tsx` | Modal with monospace readonly textarea + Copy button + "Got it" dismiss; returns null when closed |
| `frontend/src/features/vault/_components/create-secret-dialog.tsx` | react-hook-form + zodResolver + useRef reveal orchestration + inline server error |
| `frontend/src/features/vault/_components/rotate-secret-dialog.tsx` | Mirror of create for rotation; single value field |
| `frontend/src/features/vault/_components/secret-row-actions.tsx` | Row-scoped Rotate + Delete (with confirm modal) actions |
| `frontend/src/app/(dashboard)/vault/page.tsx` | List page — loading skeletons, error state, empty-state CTA, table |
| `tests/e2e/keywords/api.resource` | RequestsLibrary HTTP helpers: API List / Delete / Cleanup Prefix |
| `tests/e2e/keywords/vault.resource` | Browser library keywords: Open Vault Page, Create / Rotate / Delete / Dismiss |
| `tests/e2e/vault/01_secrets.robot` | 4 scenarios: Create Shows Once, Rotate Bumps Version, Delete Removes, Reveal Truly Once |

### Modified (2)

| File | Change |
|------|--------|
| `frontend/src/types/api.ts` | Added VaultSecretMeta / VaultSecretCreateBody / VaultSecretRotateBody |
| `frontend/src/config/features.ts` | Inserted vault FEATURES entry between feature-flags and nodes |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| useRef (not state) for reveal value | State persists across render cycles + React Query devtools would show it; ref is manually cleared | Value lifespan: POST success → reveal dialog → dismiss. Never longer. |
| RevealOnceDialog returns null when closed | Detaches textarea from DOM so browser-extension scrapers can't read it post-dismiss | Reveal-once guarantee is DOM-level, not just CSS-hidden |
| Row-scoped testids for per-row dialogs | Playwright strict mode fails on duplicate selectors — even hidden ones | `rotate-secret-form-${key}`, `delete-confirm-${key}`, etc. across all row-mounted dialogs |
| Page reload in Test Teardown | Simpler than New Context-per-test; guarantees fresh React Query cache + clean dialog state | Each scenario runs ~3-4s; full suite ~14s |
| No UI GET /v1/vault/{key} | UI never needs plaintext; Create + Rotate already hold it locally | Admin curl endpoint remains audited (via HTTP), UI remains value-free |
| Robot RequestsLibrary for cleanup | Cleanest API seeding/cleanup pattern; mirrors Sri's rule "API seeding in Suite Setup — never drive the UI to seed" | Installed robotframework-requests into .venv |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Row-scoped testids: plan spec used shared `rotate-secret-form` / `delete-confirm`; live run hit Playwright strict-mode duplicate-locator errors. Scoped to `${key}` suffix. |
| Scope additions | 1 | Added page reload in Test Teardown beyond the plan spec — needed to avoid stale row + cached state bleeding between tests. |
| Deferred | 0 | None. |

### Auto-fixed Issues

**1. Duplicate testids on row-mounted dialogs**
- **Found during:** First Robot run (3/4 tests failed with strict-mode violations)
- **Issue:** `[data-testid="rotate-secret-form"]` resolved to 3 elements (one per row). Playwright Browser library rejects ambiguous selectors even when only one is visible.
- **Fix:** Suffixed row-mounted dialog testids with `${secret.key}` / `${secretKey}` — rotate-secret-form, rotate-secret-value, rotate-secret-submit, delete-confirm, delete-confirm-yes.
- **Verification:** Re-ran suite; all 4 scenarios pass.

### Scope Additions

**1. Test Teardown page reload**
- Plan had `Cleanup Test Secret` calling the API only. In practice the UI table + internal modal state persists across tests in the same page session. Added `Reload` + `Wait For Load State networkidle` to ensure each test starts with fresh React state.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| `robotframework-requests` not installed in .venv | `.venv/bin/pip install robotframework-requests` — added to .venv. |
| Core Robot suite has 2 failing tests (pre-existing) | NOT caused by this plan — `/` home page was deleted in prior uncommitted work; core tests expect the old page. Left untouched; noted in STATE.md. |
| Chrome DevTools issue: "A form field element should have an id or name attribute (count: 2)" | a11y hint from the native `<dialog>` textarea. Non-blocking. Will revisit during accessibility polish. |

## Next Phase Readiness

**Ready:**
- Phase 8 (Auth) — the two bootstrap secrets (`auth.argon2.pepper` + `auth.session.signing_key_v1`) are seeded and readable via `request.app.state.vault.get(...)`. The reveal-once pattern is proven; auth's "show signing key once" flow can import `RevealOnceDialog` directly.
- Additional vault sub-features (audit-trail page, history, bulk-export) — page shell is stable and re-uses the same hooks.
- Any future feature needing secret creds (OAuth client secrets, SMTP creds) can copy the reveal-once orchestration verbatim.

**Concerns:**
- The a11y hint on dialog textareas (`form field should have id/name`) is cosmetic but worth fixing in a UI polish pass — would need adding an `id` or `name` to the readonly reveal-once textarea.
- Core Robot health suite pre-existing failures should be resolved in a dedicated frontend-refresh plan (not vault-scoped).
- Single-test isolation relies on page reload; a future harder isolation (per-test context) may be warranted if flakes appear at scale.

**Blockers:**
- None. Phase 7 complete. Ready for Phase 8 (auth) or UI polish.

---
*Phase: 07-vault, Plan: 02*
*Completed: 2026-04-16*
