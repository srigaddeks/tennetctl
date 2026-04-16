-- Fix old version_code values that used "v1.0" format → plain integers
-- New versions auto-generate as "1", "2", etc. but old data has "v1.0"
-- Strip leading "v" and trailing ".0" from any version codes matching that pattern

UPDATE "05_grc_library"."11_fct_framework_versions"
SET version_code = regexp_replace(
    regexp_replace(version_code, '^v', ''),  -- strip leading "v"
    '\.0$', ''                                -- strip trailing ".0"
)
WHERE version_code ~ '^v[0-9]+\.';

-- Same for tasks if they have a versions table
-- (tasks use a simple integer version column, not a versions table, so no fix needed)

-- Verify
-- SELECT id, framework_id, version_code FROM "05_grc_library"."11_fct_framework_versions";
