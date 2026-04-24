-- UP ====
-- Expand capture types with behavior-signal events. These are not "content"
-- captures — they're interaction events (dwell, click, copy, selection, video
-- play) that signal user intent. Critical for building personas that reflect
-- what users actually engaged with vs. what just scrolled past them.

INSERT INTO "07_social"."03_dim_capture_types" (id, code, label, default_retention_days) VALUES
    (27, 'post_dwell',         'Post in viewport ≥ dwell threshold',  90),
    (28, 'post_clicked',       'Post/link clicked through',           180),
    (29, 'text_selected',      'User highlighted text',               180),
    (30, 'text_copied',        'User copied text',                    180),
    (31, 'video_played',       'User played embedded video',          180),
    (32, 'link_hovered',       'User hovered over an outbound link',  60),
    (33, 'page_visit',         'Navigated to a new social URL',       90),
    (34, 'job_recommendation', '"Jobs recommended for you" card',     60),
    (35, 'messaging_thread',   'Messaging inbox thread preview',      90),
    (36, 'activity_item',      'Own profile activity feed row',       180),
    (37, 'saved_item',         'Item saved/bookmarked by the user',   365),
    (38, 'reactors_list',      'Who reacted to this post',            90),
    (39, 'reposters_list',     'Who reposted/retweeted',              90),
    (40, 'follower_item',      'Row in followers/following list',     90)
ON CONFLICT (id) DO NOTHING;

-- DOWN ====
DELETE FROM "07_social"."03_dim_capture_types" WHERE id BETWEEN 27 AND 40;
