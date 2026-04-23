# 01_approval_workflows — Scope

Approval Workflows allow teams to collaborate with trust by ensuring all content created by Contributors is reviewed before going live.

## In Scope
- **"Request Approval" Post State**: Content that has been drafted by a Contributor.
- **Approval Dashboards**: A separate "Awaiting Approval" tab in the Publishing suite.
- **Notification Loops**: Notifying an Admin/Editor when content is ready for review.
- **Approval Actions**:
    - **Approve**: Move the post to the Queue for its scheduled slot.
    - **Reject & Comment**: Return the post to "Drafts" with feedback for the Contributor.
    - **Edit & Approve**: Modify the Contributor's draft and schedule it instantly.

## Out of Scope
- **Multi-Level Approvals**: (e.g., Legal -> Manager -> Admin). Currently, only one approval is required.
- **Externally Linked Review**: (e.g., Client-only approval links without login). This is an "Agency" tier feature.

## Acceptance Criteria
- [ ] Users with the "Contributor" role must be blocked from using "Schedule Now" or "Share Now".
- [ ] Admins must receive an email notification for each new approval request.
- [ ] Rejections must require a "Reason" comment.
- [ ] Approval must be network-agnostic (one approval for all channels in the draft).
