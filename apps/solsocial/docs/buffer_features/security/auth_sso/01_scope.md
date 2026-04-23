# 01_auth_sso — Scope

Single Sign-On (SSO) enables enterprise-level identity management, allowing large teams to manage user access through centralized identity providers (IdPs).

## In Scope
- **SAML 2.0 Integration**: Connecting Buffer to identity providers like Okta, Azure AD (Entra ID), or OneLogin.
- **Just-In-Time (JIT) Provisioning**: Automatically creating a Buffer user account upon a successful SSO login from the IdP.
- **SLO (Single Logout)**: (Optional, Tier-dependent) ensuring logouts are synced across the organization.
- **Strict Mode**: Enforcing SSO-only logins and disabling standard email/password credentials for the organization.

## Out of Scope
- **Social Auth SSO**: (Google/Facebook login) is managed separately as a consumer feature.
- **SCIM (System for Cross-domain Identity Management)**: Full automated user provisioning/deprovisioning is an Enterprise Tier configuration.

## Acceptance Criteria
- [ ] Users must be able to test their SSO configuration before enforcing it.
- [ ] Admins must have an "Emergency Bypass" link or a separate login for recovery.
- [ ] Metadata XML from the IdP must be validated before save.
