# Frontend Auth & Session Bridge

## Overview
The Frontend Auth Bridge manages the lifecycle of identity tokens (JWTs) and ensures seamless communication with the backend authentication services.

## Key Components
- **API Client (`src/lib/api/apiClient.ts`)**: Centralized fetch wrapper with automatic Bearer token injection and transparent 401/token refresh handling.
- **Auth Utilities (`src/lib/api/auth.ts`)**: Domain-specific calls for Login, Registration, and Logout.
- **Token Management**: Secure storage of `access_token` and `refresh_token` in `localStorage`.

## Workflows

### 1. Persistent Login
1. User enters credentials on `AuthPage`.
2. `loginUser` API is called.
3. Tokens are saved to `localStorage`.
4. App hydrates the Access Context.

### 2. Automatic Token Refresh
1. API call returns `401 Unauthorized`.
2. `apiClient` intercepts the failure.
3. `refresh_token` is sent to the backend.
4. If successful, new tokens are saved and the original request is retried.
5. If refresh fails, user is forcefully logged out to ensure security.

## File Structure
- `src/lib/api/apiClient.ts`: Base fetch wrapper.
- `src/lib/api/auth.ts`: Login/Register/Logout implementation.
- `src/lib/types/auth.ts`: TypeScript definitions for auth responses.
