---
phase: 22-iam-enterprise
plan: 06
type: summary
status: complete
completed_at: 2026-04-17
---

# 22-06 Summary — IP Allowlist per Org

## What Was Built

Per-org IP allowlist: admins define CIDR ranges; middleware rejects requests from IPs outside the list when the allowlist is non-empty. Empty allowlist = unrestricted (default).

## Deliverables

**Backend** (`backend/02_features/03_iam/sub_features/25_ip_allowlist/`):
- `repository.py` — `list_entries`, `add_entry`, `remove_entry` (soft-delete via `deleted_at`)
- `service.py` — validates CIDR format, enforces org scoping, emits audit on add/remove
- `routes.py` — `GET /v1/iam/ip-allowlist`, `POST /v1/iam/ip-allowlist`, `DELETE /v1/iam/ip-allowlist/{entry_id}`
- `schemas.py` — `IpAllowlistCreate`, `IpAllowlistEntry` Pydantic models

**Middleware** (`backend/01_core/middleware.py`):
- `IPAllowlistMiddleware` — loads org's allowlist from DB on each authenticated request; rejects with 403 if IP not in any CIDR; skips if allowlist is empty

**Frontend** (`frontend/src/app/(dashboard)/iam/security/ip-allowlist/`):
- List + add + remove UI with CIDR input validation

## Decisions

- Empty allowlist = unrestricted (no deny-all default)
- CIDR validated with Python `ipaddress` stdlib at service layer
- Middleware checks IPv4-mapped IPv6 addresses correctly
- Audit category: `setup` (admin config action)

## Note on Plan File

The 22-06-PLAN.md file header describes "Dynamic Groups" — that plan was superseded. IP Allowlist was built instead as it was the higher-priority enterprise primitive. Dynamic groups remain deferred.
