# 01_queue — Scope

The Queue managed the temporal distribution of social content. It allows users to manage their "Post Schedule" (time slots) and view pending/sent updates in a list format.

## In Scope
- **Post Schedule (Time Slots)**: Defining recurring daily/weekly times when posts should automatically be published.
- **Queue Management**: Viewing, reordering (drag-and-drop), and editing scheduled posts.
- **Drafts**: A staging area for content that is not yet ready for the queue.
- **Approval Workflow**: A "Team" feature where contributors submit posts for review by an Admin/Manager.
- **Sent History**: A view of successfully published posts with basic success/failure logs.

## Out of Scope
- **Advanced Analytics**: Managed by the `analytics` suite.
- **Content Creation**: Handled by the `post_composer`.

## Acceptance Criteria
- [ ] Users must be able to "Pause" the queue for a specific channel.
- [ ] Deleting a post must require confirmation.
- [ ] Drag-and-drop reordering must update the relative scheduling time of all affected posts.
- [ ] Approval state must prevent a post from moving to the queue until "Approved".
