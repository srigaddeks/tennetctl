# 01_unified_inbox — Scope

The Unified Inbox centralizes cross-platform audience interactions into a single stream, focusing on high-velocity engagement.

## In Scope
- **Interaction Stream**: Real-time aggregation of comments and mentions.
- **Engagement CRM**: Threaded conversation views for replies and direct responses.
- **Sentiment & Prioritization**: Highlighting interactions that require urgent attention (e.g., negative sentiment or high-intent questions).
- **Saved Replies**: Boilerplate text templates for community managers.
- **Platform Support**: Facebook, Instagram, TikTok, Mastodon, and Threads.

## Out of Scope
- **DM (Direct Message) Support**: (Varies by API level) specifically for platforms that restrict DM access to third-party tools.
- **Automated Chatbots**: Not currently part of the core engagement offering.

## Acceptance Criteria
- [ ] Users must be able to "Close" (mark as handled) an interaction.
- [ ] Must support bulk-actions (e.g., Mark all as read).
- [ ] Direct replies must appear on the native social platform within 60 seconds of submission.
