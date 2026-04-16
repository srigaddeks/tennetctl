# Dependency Entry Template

Template updated: 2026-03-13 11:20:27 IST (+0530)
Current Python runtime observed in this workspace: CPython 3.13.5

Use this template whenever a dependency is added, upgraded, or receives a security review.

## Template

Name: `<package-name>`
Exact version: `<x.y.z>`
Reviewed at: `<YYYY-MM-DD HH:MM:SS TZ (+ZZZZ)>`
Python compatibility: `<for example: CPython 3.13>`
Used by: `<feature folder or module>`
Source of truth: `backend/requirements.txt`
Purpose: `<why this package exists>`
Alternatives considered: `<optional but required for security-sensitive packages>`
Security notes: `<known risks, hardening notes, CVE review summary, or "none identified at review time">`
License notes: `<license or policy note if relevant>`
Upgrade policy: `<pinning reason and expected review cadence>`

## Example

Name: `fastapi`
Exact version: `0.115.0`
Reviewed at: `2026-03-13 11:20:27 IST (+0530)`
Python compatibility: `CPython 3.13`
Used by: `backend/02_api/`
Source of truth: `backend/requirements.txt`
Purpose: `HTTP API framework with typed request and response validation`
Alternatives considered: `Flask, Django Ninja`
Security notes: `Review middleware defaults, error handling behavior, request size controls, and dependency CVEs before adoption`
License notes: `Confirm policy acceptance before production use`
Upgrade policy: `Pin exact version and re-review on every minor or patch upgrade`
