-- Soft-delete all test and debug templates accumulated from Robot Framework test runs
-- and manual development experiments. Also marks existing robot_* entries as is_test = TRUE
-- before deleting so the is_test flag stays accurate for audit purposes.

UPDATE "03_notifications"."10_fct_templates"
SET
    is_test    = TRUE,
    is_deleted = TRUE,
    deleted_at = NOW(),
    deleted_by = NULL
WHERE
    is_deleted = FALSE
    AND is_system = FALSE
    AND (
        code LIKE 'robot\_%'      ESCAPE '\'
        OR code LIKE 'robot\_debug\_%' ESCAPE '\'
        OR code LIKE 'Email\_%'   ESCAPE '\'   -- manual test entries with wrong casing
    );
