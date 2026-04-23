# 01_auth_2fa — Scope

Multi-Factor Authentication (2FA) is a mandatory security layer for users to protect their Buffer credentials beyond just their primary passwords.

## In Scope
- **TOTP (Time-based One-Time Password)**: Authentication via apps like Google Authenticator, Authy, or Microsoft Authenticator.
- **Recovery Codes**: Generating a set of 10 static codes that a user can use to regain access if they lose their 2FA device.
- **Enforcement Policy**: Allowing Admins to require 2FA for all members of the organization.
- **SMS Auth**: (Backup only) sending short-lived codes via SMS.

## Out of Scope
- **Hardware Security Keys (WebAuthn/Yubikey)**: Currently not supported in the standard web offering.

## Acceptance Criteria
- [ ] Users must be able to view their QR code during initial setup.
- [ ] Recovery codes must be downloadable or copyable to the clipboard.
- [ ] Enabling 2FA must end all other active sessions for that user for security.
