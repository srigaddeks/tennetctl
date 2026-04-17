---
type: community
cohesion: 0.10
members: 30
---

# OAuth & Auth Shell

**Cohesion:** 0.10 - loosely connected
**Members:** 30 nodes

## Members
- [[AuthMeResponse  AuthResponseBody  SigninBody  SignupBody  OAuthCallbackBody  OtpRequestBody  OtpVerifyBody (types)]] - code - frontend/src/types/api.ts
- [[AuthShell — auth page wrapper component]] - code - frontend/src/app/auth/signup/page.tsx
- [[CSRF state nonce (sessionStorage per-tab anti-tampering)]] - document - frontend/src/features/auth/_components/oauth-callback.tsx
- [[GithubCallbackPage — GitHub OAuth callback]] - code - frontend/src/app/auth/callback/github/page.tsx
- [[GoogleCallbackPage — Google OAuth callback]] - code - frontend/src/app/auth/callback/google/page.tsx
- [[OAUTH_STATE_KEY (CSRF nonce constant)]] - code - frontend/src/features/auth/_components/oauth-buttons.tsx
- [[OAuth2 Authorization Code Flow (Google + GitHub)]] - document - frontend/src/features/auth/_components/oauth-buttons.tsx
- [[OAuthButtons]] - code - frontend/src/features/auth/_components/oauth-buttons.tsx
- [[OAuthCallback — shared OAuth provider callback handler]] - code - frontend/src/app/auth/callback/google/page.tsx
- [[POST v1auth (signin, signup, magic-link, otp, totp, passkeys, password-reset, oauth)]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[PUBLIC_PREFIXES — unauthenticated routes]] - code - frontend/src/proxy.ts
- [[PasskeyAuthBeginResponse  PasskeyListResponse  PasskeyRegisterBeginResponse (types)]] - code - frontend/src/types/api.ts
- [[SignInForm — emailpassword signin form]] - code - frontend/src/app/auth/signin/page.tsx
- [[SignInPage — sign-in page]] - code - frontend/src/app/auth/signin/page.tsx
- [[SignUpForm — emailpassword signup form]] - code - frontend/src/app/auth/signup/page.tsx
- [[SignUpPage — emailpassword registration page]] - code - frontend/src/app/auth/signup/page.tsx
- [[proxy() — session guard middleware]] - code - frontend/src/proxy.ts
- [[tennetctl_session cookie]] - code - frontend/src/proxy.ts
- [[use-auth (hook module)]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[useMagicLinkRequest]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[useMe]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[useOAuthExchange]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[useOtpRequest]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[useOtpVerify]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[usePasskeyRegisterBeginComplete  usePasskeyAuthBeginComplete  usePasskeyList  usePasskeyDelete]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[usePasswordResetRequest  usePasswordResetComplete]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[useSignin]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[useSignout]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[useSignup]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[useTotpSetup  useTotpVerify  useTotpList  useTotpDelete]] - code - frontend/src/features/auth/hooks/use-auth.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/OAuth_&_Auth_Shell
SORT file.name ASC
```
