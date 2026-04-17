---
phase: 20-iam-hardening-for-oss
plan: 01
status: complete
completed: 2026-04-17
---

# 20-01 SUMMARY: Auth Policy Config Layer

## Files Created / Modified

| File | Change |
|------|--------|
| `backend/02_features/03_iam/auth_policy.py` | NEW — AuthPolicy service + domain dataclasses + POLICY_KEYS (20 keys) |
| `backend/02_features/03_iam/auth_policy_bootstrap.py` | NEW — ensure_policy_defaults(), idempotent seed |
| `backend/02_features/02_vault/sub_features/02_configs/service.py` | MODIFIED — set_auth_policy_ref() + _invalidate_if_policy_key() wired into create/update/delete |
| `backend/main.py` | MODIFIED — AuthPolicy registered on app.state.auth_policy + bootstrap + invalidation hook wired |
| `tests/test_auth_policy.py` | NEW — 6 tests (resolver precedence, cache SWR, domain getters) |
| `tests/test_auth_policy_bootstrap.py` | NEW — 3 tests (20 rows on first boot, idempotent, preserves operator values) |
| `tests/test_auth_policy_invalidation.py` | NEW — 3 tests (org invalidation, global invalidation, delete refold) |

## Seed Count (first boot)
20 `iam.policy.*` entries at scope=global. Second boot: 0 inserts.

## Pytest Results
- Baseline IAM + vault: 136 tests
- Post-plan: **148 tests (12 new — all PASS)**
- No regression

## Deviations
- **Test file location**: Plan specified `backend/02_features/03_iam/tests/`. Project convention puts all tests in `tests/`. Used `tests/` to follow project convention.
- **21 vs 20 keys**: Plan action listed `otp.totp_window` as a 21st key but the verify command asserts 20. Dropped `otp.totp_window` (TOTP window is TOTP-specific; OtpPolicy covers email OTP delivery).
- **Bootstrap takes no ctx param**: Plan passed a `ctx` from main.py lifespan. Bootstrap builds its own setup-scope NodeContext internally (matches vault bootstrap precedent). Simpler + no main.py NodeContext dependency.
- **Vault-IAM coupling seam**: Module-level `_auth_policy_ref` + `set_auth_policy_ref()` in vault.configs service. Called from main.py lifespan after AuthPolicy registered. Documented in code as NCP §11 shared-primitive exception.

## Decision Record
| Decision | Impact |
|----------|--------|
| Module-level singleton ref in vault.configs service for invalidation | Avoids service signature changes + route modifications; well-documented coupling seam |
| Auth policy bootstrap runs only when vault module is enabled | vault.configs tables don't exist without vault; graceful skip when vault disabled |
| Hardcoded defaults as last-resort fallback in resolve() | Prevents signin breakage if vault row missing; logs WARNING |

## Next Plan
20-02 — Auth policy admin UI (`/iam/security/policy` page reads AuthPolicy, writes vault.configs).
