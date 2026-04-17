# Plan 12-02 Summary — OTP Sub-Feature (Email OTP + TOTP)

**Status:** COMPLETE
**Date:** 2026-04-17
**Phase:** 12 (IAM Security Completion)

## What Was Built

### DB
- Migration 030: `"03_iam"."23_fct_iam_otp_codes"` — email OTP codes table (code_hash, attempts, expires_at, consumed_at, rate-limit index)
- Migration 030: `"03_iam"."24_fct_iam_totp_credentials"` — TOTP secrets table (envelope-encrypted: secret_ciphertext, secret_dek, secret_nonce, all base64 text columns)

### Backend
- `sub_features/12_otp/` — full sub-feature (schemas, repository, service, routes)
- Email OTP: `POST /v1/auth/otp/request` (rate-limited 3/15min, no enumeration) + `POST /v1/auth/otp/verify` (max 3 attempts, returns session)
- TOTP: `POST /v1/auth/totp/setup` (generates secret, envelope-encrypts with vault root key, returns otpauth URI) + `POST /v1/auth/totp/verify` (pyotp.TOTP.verify, returns session)
- TOTP: `GET /v1/auth/totp` (list enrolled devices) + `DELETE /v1/auth/totp/{id}` (soft-delete)
- Routes wired in `backend/02_features/03_iam/routes.py`

### Crypto Fix
- `_encrypt_secret`/`_decrypt_secret` corrected: uses `vault_client._root_key` (not non-existent `VaultClient._root_key_from_env()`)
- `Envelope` is a frozen dataclass with `.ciphertext`, `.wrapped_dek`, `.nonce` as bytes; stored in DB as base64-encoded text strings

### Tests (`tests/test_iam_otp.py` — 7 tests)
- Email OTP: unknown email → 200 (no enumeration)
- Email OTP: known email → 200 + code created
- Email OTP: invalid code → 401 INVALID_CODE
- Email OTP: too many attempts → 401 MAX_ATTEMPTS
- Email OTP: valid code → 200 + session returned
- TOTP: setup + verify happy path → 200 + session
- TOTP: wrong code → 401 INVALID_CODE

### Frontend
- Types: `OtpRequestBody`, `OtpVerifyBody`, `TotpSetupBody`, `TotpSetupResponse`, `TotpVerifyBody`, `TotpCredential`, `TotpListResponse` added to `api.ts`
- Hooks: `useOtpRequest`, `useOtpVerify`, `useTotpSetup`, `useTotpVerify`, `useTotpList`, `useTotpDelete` added to `use-auth.ts`
- OTP tab added to signin form — send code → verify code → redirect flow
- `/account/security` page: TOTP device enrollment (QR code + verify) + device management (list + delete)

## Decisions
- TOTP secrets AES-256-GCM envelope-encrypted using vault root key directly (no separate vault secret entry — key material handled at the same layer as vault itself)
- `list_totp` / `delete_totp` exposed as thin service wrappers over repository (no session returned — these are management operations)
- QR code rendered via external qrserver.com (consistent with acceptable third-party rendering for non-sensitive URI)
- `pyotp` installed via pip
