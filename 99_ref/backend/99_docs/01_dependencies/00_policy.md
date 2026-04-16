# Dependency Documentation Policy

Last updated: 2026-03-13 11:20:27 IST (+0530)
Current Python runtime observed in this workspace: CPython 3.13.5

## Purpose

This folder is the evidence trail for backend dependency decisions.
`backend/requirements.txt` remains machine-readable for tooling.
Human-readable dependency context belongs here.

## Required files in this folder

- `00_policy.md`: rules for documenting dependencies
- `01_current_inventory.md`: current runtime and package inventory
- `02_dependency_template.md`: template for every new dependency entry or review

If the backend grows materially, add numbered files rather than ad hoc names.

## Required metadata for every dependency

Each dependency entry must include:

- Name
- Exact version in use
- Reviewed at datetime
- Python/runtime compatibility
- Purpose
- Where it is used
- Why it was chosen over alternatives, if the choice is security-sensitive
- Known risks or security notes
- Upgrade policy or pinning reason
- Link to the source of truth file, such as `requirements.txt`, `pyproject.toml`, or lock file

## Update rules

- Any dependency add, remove, or version change must update `01_current_inventory.md` in the same commit.
- Security-sensitive dependencies should also get a dated review note when materially changed.
- If the runtime version changes, update the timestamp and runtime section in every file in this folder that claims current state.

## Security rules

- Prefer actively maintained packages with clear release history.
- Prefer minimal dependency count over convenience.
- Reject packages with unclear ownership, dormant maintenance, or unnecessary native build risk unless justified.
- Pin exact versions for deployed environments.
- Review changelogs and vulnerability data before upgrades.

## Audit intent

This folder is designed to support future control evidence for:

- change management
- software inventory
- vulnerability management
- secure development lifecycle reviews
- vendor and dependency risk review
