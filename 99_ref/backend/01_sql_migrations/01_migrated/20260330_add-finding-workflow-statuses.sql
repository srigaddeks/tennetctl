-- ─────────────────────────────────────────────────────────────────────────────
-- FINDING WORKFLOW STATUSES
--
-- Adds 4 new statuses to support the full finding resolution workflow:
--
--   acknowledged   — Org has acknowledged the finding (before remediation starts).
--   responded      — Org has submitted a remediation response or formal dispute.
--   auditor_review — Auditor is reviewing the org's response before closing.
--   escalated      — Finding escalated for further review (can re-enter auditor_review).
--
-- Full resolution flow after this migration:
--   open → acknowledged → in_remediation | disputed → responded
--        → auditor_review → verified_closed | accepted | escalated
--        → escalated → auditor_review (loop)
--
-- Note: `open`, `in_remediation`, `verified_closed`, `accepted`, `disputed`
-- already exist. This migration adds only the missing workflow states.
-- ─────────────────────────────────────────────────────────────────────────────

-- ═════════════════════════════════════════════════════════════════════════════
-- UP =========================================================================
-- ═════════════════════════════════════════════════════════════════════════════

INSERT INTO "09_assessments"."05_dim_finding_statuses"
    (code, name, description, sort_order)
VALUES
    (
        'acknowledged',
        'Acknowledged',
        'Org has acknowledged the finding. Formal review has begun but remediation has not started.',
        6
    ),
    (
        'responded',
        'Responded',
        'Org has submitted a remediation response or formal dispute for auditor review.',
        7
    ),
    (
        'auditor_review',
        'Auditor Review',
        'Auditor is reviewing the org response before closing or escalating the finding.',
        8
    ),
    (
        'escalated',
        'Escalated',
        'Finding escalated for further review. May re-enter auditor_review after escalation action.',
        9
    )
ON CONFLICT (code) DO NOTHING;


-- ═════════════════════════════════════════════════════════════════════════════
-- DOWN =======================================================================
-- ═════════════════════════════════════════════════════════════════════════════

-- -- Only safe to run if no findings currently have these statuses.
-- DELETE FROM "09_assessments"."05_dim_finding_statuses"
-- WHERE code IN ('acknowledged', 'responded', 'auditor_review', 'escalated');
