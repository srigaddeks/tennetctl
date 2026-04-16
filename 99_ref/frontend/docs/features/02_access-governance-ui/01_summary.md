# Frontend Access Governance & Feature Flags

## Overview
This feature integrates the backend's fine-grained access governance (RBAC/Scopes) into the React UI layer. It allows for declarative UI gating and global permission hydration.

## Core Pillars

### 1. The Access Provider (`src/components/providers/AccessProvider.tsx`)
A top-level React Context that:
- Fetches the user's "Access Context" (Platform, Org, and Workspace actions) upon app load.
- Provides `hasPlatformAction` and `hasOrgAction` helpers to the entire component tree.
- Exposes a `refreshAccess()` function to re-sync permissions after login or scope changes.

### 2. Feature Gating (`src/components/auth/FeatureGate.tsx`)
A declarative component used to shield UI elements from unauthorized users.

**Usage:**
```tsx
<FeatureGate actionCode="feature_flag_registry.create" scope="platform">
  <CreateFlagButton />
</FeatureGate>
```

### 3. Scope Awareness
The system distinguishes between:
- **Platform Scope**: Global administrative actions (e.g., managing the feature flag registry itself).
- **Org/Workspace Scope**: Tenant-specific actions (e.g., managing policies within a specific company).

## Integration points
- **Hydration**: Occurs automatically in `RootLayout`.
- **API**: Uses `GET /api/v1/am/access` via `src/lib/api/access.ts`.
- **Permissions**: String-based keys matching the backend `dim_feature_permissions` table (e.g., `auth_password_login.enable`, `policy_management.create`).

## File Structure
- `src/components/providers/AccessProvider.tsx`: Global state manager.
- `src/components/auth/FeatureGate.tsx`: UI gating component.
- `src/lib/api/access.ts`: Permission fetching logic.
- `src/lib/types/access.ts`: TypeScript types for the access matrix.
