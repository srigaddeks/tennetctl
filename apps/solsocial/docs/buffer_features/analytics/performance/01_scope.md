# 01_performance — Scope

The Performance sub-feature provides data visualization for cross-platform social media metrics. It identifies trends in reach, engagement, and audience growth.

## In Scope
- **Metric Tracking**: Likes, comments, shares, retweets, and impressions per post and per channel.
- **Trend Analysis**: Percentage changes over time (Week-over-Week, Month-over-Month).
- **Post-Level Benchmarking**: A "Top Posts" list sorted by engagement rate.
- **Channel Aggregation**: A unified view of performance across Instagram, Facebook, LinkedIn, etc.

## Out of Scope
- **Individual User Tracking**: (Who clicked what) is handled by third-party cookies/trackers outside Buffer's scope.
- **Custom Reporting**: Handled by the `reports` sub-feature.

## Acceptance Criteria
- [ ] Dashboards must allow for custom date range selection.
- [ ] Data must be cached to ensure sub-second report generation.
- [ ] Must handle API failures from social networks gracefully (show "Data unavailable" state).
