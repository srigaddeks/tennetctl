# 01_post_composer — Scope

The Post Composer is the primary entry point for content creation in the Buffer ecosystem. It allows users to draft, preview, and schedule content across multiple social channels simultaneously.

## In Scope
- **Multi-Channel Drafting**: Simultaneously creating posts for X, LinkedIn, Instagram, etc.
- **Tailored Composer**: Platform-specific overrides for captions, hashtags, and mentions.
- **Media Management**: Uploading images/videos and integration with external designers (Canva).
- **AI Assistance**: Text generation, tone adjustment, and content expansion.
- **Live Preview**: Real-time rendering of how the post will look on each specific network.
- **First Comment**: Scheduling a secondary interaction (hashtags) for Instagram and LinkedIn.

## Out of Scope
- **Queue Management**: Handled by the `queue` sub-feature.
- **Sent History**: Managed by the `analytics` suite.

## Acceptance Criteria
- [ ] Must validate character counts per network (e.g., 280 for X).
- [ ] Must prevent scheduling if no channel is selected.
- [ ] AI generated content must be editable before save.
- [ ] Previews must match the current API standards for social platform UI.
