-- UP ====
-- Expand capture type taxonomy for comprehensive DOM scraping (posts, comments,
-- articles, companies, profiles, jobs, polls, search, hashtags, etc).
-- All types represent purely-observed events from what's already rendered in
-- the user's browser. The extension never calls LinkedIn/Twitter APIs directly.

INSERT INTO "07_social"."03_dim_capture_types" (id, code, label) VALUES
    ( 6, 'article_seen',         'Article visible in feed'),
    ( 7, 'article_opened',       'Article opened'),
    ( 8, 'newsletter_seen',      'Newsletter card seen'),
    ( 9, 'company_viewed',       'Company page viewed'),
    (10, 'profile_page_viewed',  'Profile page viewed'),
    (11, 'job_post_seen',        'Job post seen'),
    (12, 'job_post_opened',      'Job post opened'),
    (13, 'poll_seen',            'Poll seen'),
    (14, 'event_seen',           'Event seen'),
    (15, 'hashtag_feed_seen',    'Hashtag feed viewed'),
    (16, 'search_result_seen',   'Search result observed'),
    (17, 'reshare_seen',         'Repost with commentary seen'),
    (18, 'reaction_detail',      'Reactions breakdown'),
    (19, 'connection_suggested', 'Suggested connection'),
    (20, 'notification_seen',    'Notification seen'),
    (21, 'live_broadcast_seen',  'Live broadcast seen'),
    (22, 'quote_tweet_seen',     'Quote tweet seen'),
    (23, 'thread_seen',          'Thread context seen'),
    (24, 'list_viewed',          'List viewed'),
    (25, 'space_seen',           'Space seen'),
    (26, 'community_seen',       'Community seen')
ON CONFLICT (id) DO NOTHING;

COMMENT ON TABLE "07_social"."03_dim_capture_types" IS
    'Taxonomy of DOM-observed capture events. All data collected from already-rendered browser content; no platform API calls.';

-- DOWN ====
DELETE FROM "07_social"."03_dim_capture_types" WHERE id BETWEEN 6 AND 26;
