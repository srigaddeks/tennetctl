# Global Control Test Library + Clone-on-Subscribe

**Priority:** P2 — the platform's distribution moat
**Status:** New module
**Module:** `backend/10_sandbox/21_global_library/`
**Base path:** `/api/v1/sb`

---

## Overview

Platform admins curate a global control test library that any organization can subscribe to. When an org subscribes, they get local clones of all signals, threat types, and policies — which they can customize (adjust thresholds, configurable args) while still receiving update notifications when the global version changes.

This is the platform's moat: a growing catalog of tested, validated control tests that customers can use instantly.

---

## Database Schema

### Migration: `20260320_global-library.sql`

```sql
-- Global library catalog (platform-admin managed)
CREATE TABLE "15_sandbox"."80_fct_global_libraries" (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_library_id   UUID NOT NULL REFERENCES "15_sandbox"."29_fct_libraries"(id),
    source_org_id       UUID NOT NULL,
    global_code         VARCHAR(100) UNIQUE NOT NULL,
    global_name         VARCHAR(255) NOT NULL,
    description         TEXT,
    category_code       VARCHAR(50),
    connector_type_codes TEXT[] NOT NULL DEFAULT '{}',
    curator_user_id     UUID NOT NULL,
    publish_status      VARCHAR(20) NOT NULL DEFAULT 'draft',
    is_featured         BOOLEAN NOT NULL DEFAULT FALSE,
    download_count      INT NOT NULL DEFAULT 0,
    version_number      INT NOT NULL DEFAULT 1,
    published_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_publish_status CHECK (publish_status IN ('draft', 'review', 'published', 'deprecated'))
);

-- Org subscriptions
CREATE TABLE "15_sandbox"."81_lnk_org_library_subscriptions" (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL,
    global_library_id   UUID NOT NULL REFERENCES "15_sandbox"."80_fct_global_libraries"(id),
    subscribed_by       UUID NOT NULL,
    subscribed_version  INT NOT NULL,
    local_library_id    UUID REFERENCES "15_sandbox"."29_fct_libraries"(id),
    auto_update         BOOLEAN NOT NULL DEFAULT TRUE,
    subscribed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(org_id, global_library_id)
);

CREATE INDEX idx_global_libraries_status ON "15_sandbox"."80_fct_global_libraries" (publish_status);
CREATE INDEX idx_global_libraries_category ON "15_sandbox"."80_fct_global_libraries" (category_code);
CREATE INDEX idx_org_subscriptions_org ON "15_sandbox"."81_lnk_org_library_subscriptions" (org_id);
```

---

## API Endpoints

### GET `/api/v1/sb/global-libraries`

**Permission:** `sandbox.view` (any authenticated user)

List published global libraries. Filterable.

**Query params:** `category_code`, `connector_type_code`, `is_featured`, `search`, `page`, `page_size`

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "global_code": "pg_identity_compliance",
      "global_name": "PostgreSQL Identity Compliance Pack",
      "description": "Dormant accounts, privilege escalation, MFA enforcement for PostgreSQL",
      "category_code": "identity",
      "connector_type_codes": ["postgresql"],
      "publish_status": "published",
      "is_featured": true,
      "download_count": 42,
      "version_number": 3,
      "signal_count": 5,
      "threat_type_count": 3,
      "policy_count": 3,
      "published_at": "2026-03-15T00:00:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 20
}
```

### POST `/api/v1/sb/global-libraries`

**Permission:** `sandbox.promote` (platform admin only)

Publish an org library to the global catalog.

**Request:**

```json
{
  "source_library_id": "uuid",
  "global_code": "pg_identity_compliance",
  "global_name": "PostgreSQL Identity Compliance Pack",
  "description": "...",
  "category_code": "identity",
  "is_featured": false
}
```

**What happens:**
1. Validate source library exists and is published within the org
2. Snapshot all linked policies, threat types, and signals into the global record
3. Set `publish_status = 'published'`, `published_at = NOW()`
4. Extract `connector_type_codes` from linked signals

### POST `/api/v1/sb/global-libraries/{id}/subscribe`

**Permission:** `sandbox.create` (org admin)
**Query params:** `org_id` (required)

**What happens (clone-on-subscribe):**
1. Clone all signals from the global library into the org (new signal records with `cloned_from_global` EAV)
2. Clone all threat types (expression trees reference the new local signal codes)
3. Clone all policies
4. Create a local library linking all cloned entities
5. Create subscription record linking org → global library + local library
6. Org can now customize: change configurable_args defaults, adjust thresholds, modify policies

### GET `/api/v1/sb/global-libraries/subscriptions`

**Query params:** `org_id` (required)

List org's subscriptions with update availability.

**Response:**

```json
{
  "items": [
    {
      "global_library_id": "uuid",
      "global_code": "pg_identity_compliance",
      "subscribed_version": 2,
      "latest_version": 3,
      "has_update": true,
      "local_library_id": "uuid",
      "subscribed_at": "2026-03-10T00:00:00Z"
    }
  ]
}
```

---

## Permission

New permission: `sandbox.publish_global` — seed in migration alongside existing sandbox permissions.

---

## Files to Create

| File | Purpose |
|------|---------|
| `backend/10_sandbox/21_global_library/__init__.py` | Module init |
| `backend/10_sandbox/21_global_library/models.py` | GlobalLibraryRecord, SubscriptionRecord |
| `backend/10_sandbox/21_global_library/repository.py` | CRUD for global libraries + subscriptions |
| `backend/10_sandbox/21_global_library/schemas.py` | Request/response Pydantic models |
| `backend/10_sandbox/21_global_library/service.py` | Publish, subscribe, clone, update check |
| `backend/10_sandbox/21_global_library/dependencies.py` | FastAPI DI |
| `backend/10_sandbox/21_global_library/router.py` | Endpoints |
| `backend/01_sql_migrations/02_inprogress/20260320_global-library.sql` | Migration |

---

## Verification

1. Create org library with 3 signals + 2 threats + 2 policies → publish to global
2. Different org subscribes → verify local clones created (new signal IDs, same code)
3. Customize cloned signal (change dormant_days default) → verify doesn't affect global
4. Publish v2 of global library → verify subscriber sees `has_update: true`
5. Frontend: global library catalog with search, category filter, subscribe button
