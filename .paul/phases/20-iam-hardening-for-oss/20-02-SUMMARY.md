---
phase: 20-iam-hardening-for-oss
plan: 02
status: complete
completed: 2026-04-17
---

# 20-02 SUMMARY: Auth Policy Admin UI

## Files Created / Modified

| File | Change |
|------|--------|
| `frontend/src/types/api.ts` | MODIFIED — added `AuthPolicyKey` union (20 string literals), `PolicyGroup` union, `PolicyEntry` type |
| `frontend/src/features/iam/hooks/use-auth-policy.ts` | NEW — `useGlobalPolicy`, `useOrgOverrides`, `useUpdatePolicy`, `useCreatePolicy`, `useDeletePolicy` |
| `frontend/src/features/iam/_components/PolicyForm.tsx` | NEW — 6 grouped sections (Password, Lockout, Session, Magic Link, OTP, Password Reset); inline Save button appears on dirty field |
| `frontend/src/features/iam/_components/OrgOverrideList.tsx` | NEW — org dropdown + existing overrides table + remove + per-org policy form |
| `frontend/src/app/(dashboard)/iam/security/policy/page.tsx` | NEW — tabbed page: "Global defaults" + "Per-org overrides" |
| `frontend/src/config/features.ts` | MODIFIED — added "Auth Policy" (`/iam/security/policy`) to IAM sidebar subFeatures |

## UI Test Results (Chrome DevTools)

- Page loads at `/iam/security/policy` with all 20 policy fields pre-populated from vault.configs (global scope)
- "Auth Policy" link appears in Identity sidebar — active/highlighted correctly
- Editing Min length 12→16: Save button appears inline
- Click Save → `PATCH /v1/vault-configs/{id}` returns 200
- Save button disappears, field stays at new value (no dirty state)
- Toast displayed after save

## Deviations

- **No Zod schema for the form**: Policy fields are individually typed and validated by value_type (number → `Number(raw)`, boolean → dropdown, string → free text). No form-level submit. Per-field save was simpler and matches the vault configs UX pattern.
- **No separate `ListResult` import in hook**: `apiList<T>` returns `{ items, total }` — used `.items` directly inside the queryFn rather than returning the full ListResult shape.

## Next Plan

20-03 — Account lockout enforcement (backend: track failed attempts, lock accounts, expose unlock endpoint).
