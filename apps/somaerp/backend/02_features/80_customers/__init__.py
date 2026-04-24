"""80_customers sub-feature — tenant-scoped customer identity CRUD.

Status transitions: prospect <-> active <-> paused; active/paused -> churned;
any -> blocked (fraud). Transitions emit `somaerp.customers.status_changed`;
non-status field edits emit `.updated`.
"""
