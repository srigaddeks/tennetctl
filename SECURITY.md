# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` branch | Yes |
| `feat/*` branches | No (pre-release) |
| Tagged releases ≥ v0.1.6 | Yes |
| Releases < v0.1.6 | No |

## Reporting a Vulnerability

TennetCTL takes security seriously. If you discover a vulnerability, **do not** open a public GitHub issue. Instead, report it privately so we can coordinate disclosure.

### Preferred Channel — GitHub Security Advisories

Use the **"Report a vulnerability"** button on the [Security tab](../../security/advisories/new) of this repository. This opens a private advisory that only you and repository maintainers can see.

### Alternate Channel — Email

Send an encrypted email to:

```
security@tennetctl.dev
```

GPG key fingerprint: `<TO BE PUBLISHED — PGP KEY PENDING>`

Include:

- A description of the vulnerability and its potential impact
- Reproduction steps or a proof-of-concept (PoC)
- Affected component (IAM, Vault, Audit, Notify, etc.) and version/commit
- Any suggested mitigations

### What Happens Next

| Step | Timeline |
|------|----------|
| Acknowledgment | Within 72 hours |
| Initial triage | Within 7 days |
| Patch or mitigation | Within 90 days (coordinated disclosure) |
| Public disclosure | After patch is released and users have had time to upgrade |

We follow **90-day coordinated disclosure**. If a fix requires more time we will keep you informed and may request an extension.

## Scope

### In Scope

- Authentication and session management (IAM sub-features 08–14)
- Authorization bypass or privilege escalation
- Vault secret exposure or envelope encryption flaws
- SQL injection via API inputs
- Cross-tenant data leakage
- Audit log tampering
- SSRF, RCE, or path traversal in any backend component

### Out of Scope

- Denial-of-service attacks that require enormous resources
- Social engineering of maintainers
- Vulnerabilities in dependencies that are already publicly known and tracked upstream
- Issues only reproducible on unsupported configurations (non-standard Docker setups, modified source)

## Disclosure Policy

We follow a **coordinated disclosure** model:

1. Reporter submits privately
2. Maintainers confirm and triage
3. Fix developed in a private fork
4. Advisory and patch published simultaneously
5. Reporter credited in the advisory (unless they prefer anonymity)

## Acknowledgments

We maintain a hall of fame for researchers who have responsibly disclosed vulnerabilities. Thank you for helping keep TennetCTL secure.
