-- ─────────────────────────────────────────────────────────────────────────────
-- TASK EVIDENCE APPROVAL STATUSES
--
-- Adds two new statuses to support the GRC evidence approval chain:
--
--   in_review  — Evidence submitted internally, under review by control owner / GRC Lead.
--                Not yet visible to external auditors.
--   published  — Evidence approved by GRC Lead. Auditor-visible.
--
-- Full status flow after this migration:
--   open → in_progress → pending_verification → in_review → published → resolved
--
-- UUID pattern: b3c3xxxx-0000-0000-0000-000000000000 (matches existing rows)
-- ─────────────────────────────────────────────────────────────────────────────

-- ═════════════════════════════════════════════════════════════════════════════
-- UP =========================================================================
-- ═════════════════════════════════════════════════════════════════════════════

INSERT INTO "08_tasks"."04_dim_task_statuses"
    (id, code, name, description, is_terminal, sort_order, is_active, created_at, updated_at)
VALUES
    (
        'b3c30007-0000-0000-0000-000000000000',
        'in_review',
        'Under Review',
        'Evidence submitted and under internal review by control owner or GRC Lead. Not yet visible to external auditors.',
        FALSE,
        7,
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'b3c30008-0000-0000-0000-000000000000',
        'published',
        'Ready for Auditor',
        'Evidence approved by GRC Lead. Visible to external auditors in the engagement. Internal label: Published.',
        FALSE,
        8,
        TRUE,
        NOW(),
        NOW()
    )
ON CONFLICT (code) DO NOTHING;


-- ═════════════════════════════════════════════════════════════════════════════
-- DOWN =======================================================================
-- ═════════════════════════════════════════════════════════════════════════════

-- -- Only safe to run if no tasks currently have these statuses.
-- DELETE FROM "08_tasks"."04_dim_task_statuses"
-- WHERE id IN (
--     'b3c30007-0000-0000-0000-000000000000',
--     'b3c30008-0000-0000-0000-000000000000'
-- );
