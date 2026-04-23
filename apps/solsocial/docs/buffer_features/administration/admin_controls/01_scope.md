# 01_admin_controls — Scope

Admin Controls manage multi-user access and secure identity across a Buffer organization. These features are critical for agency-level and enterprise workflows.

## In Scope
- **Role-Based Access Control (RBAC)**:
    - **Admin**: Full control over channels, billing, and team management.
    - **Editor**: Full posting rights to assigned channels.
    - **Contributor**: Can draft posts but requires approval to publish.
- **Per-Channel Permissioning**: Granting users access to only a subset of social channels (e.g., "User A can only access the LinkedIn channel").
- **Audit Logs (Team Actions)**: Tracking who added which post or invited a new member.
- **Organization Onboarding**: Inviting team members via email with predefined roles.

## Out of Scope
- **Individual Post Ownership**: All content belongs to the Organization, not the individual creator.
- **Public SSO**: SSO is restricted to Enterprise tiers.

## Acceptance Criteria
- [ ] Users must be able to switch roles for existing members.
- [ ] Removing an Admin must require at least one other Admin to remain in the organization.
- [ ] Invitation emails must expire after 7 days.
