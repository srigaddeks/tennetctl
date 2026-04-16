-- ============================================================
-- 20260318_seed-evidence-checker.sql
-- AI Evidence Checker — agent types, feature flag, permissions
-- Credentials are seeded separately via Python seeder (encrypted)
-- ============================================================

BEGIN;

-- ── 1. Agent type dimensions ─────────────────────────────────────────────────
-- 02_dim_agent_types has columns: code, name, description, is_active, created_at
INSERT INTO "20_ai"."02_dim_agent_types" (code, name, description, is_active)
VALUES
    ('evidence_lead',
     'Evidence Lead Agent',
     'Orchestrates evidence evaluation across all acceptance criteria for a task',
     TRUE),
    ('evidence_checker_agent',
     'Evidence Checker Agent',
     'Evaluates a single acceptance criterion against indexed document chunks',
     TRUE)
ON CONFLICT (code) DO NOTHING;

-- ── 2. Rate limit config (sequential queue — max 1 concurrent job by default) ─
INSERT INTO "20_ai"."44_fct_agent_rate_limits"
    (tenant_key, agent_type_code, org_id, max_requests_per_minute, max_tokens_per_minute,
     max_concurrent_jobs, batch_size, batch_interval_seconds, cooldown_seconds, is_active)
VALUES
    ('__platform__', 'evidence_lead', NULL, 60, 1000000, 1, 1, 0, 0, TRUE)
ON CONFLICT (agent_type_code, COALESCE(org_id::text,'')) DO UPDATE
    SET max_concurrent_jobs = EXCLUDED.max_concurrent_jobs,
        max_requests_per_minute = EXCLUDED.max_requests_per_minute,
        max_tokens_per_minute = EXCLUDED.max_tokens_per_minute,
        updated_at = NOW();

-- ── 3. Feature flag ──────────────────────────────────────────────────────────
INSERT INTO "03_auth_manage"."14_dim_feature_flags"
    (id, code, name, description, feature_scope, feature_flag_category_code,
     access_mode, lifecycle_state, initial_audience,
     env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'ai_evidence_checker',
     'AI Evidence Checker',
     'Auto-evaluate task attachments against acceptance criteria using AI multi-agent evaluation',
     'workspace', 'ai',
     'permissioned', 'active', 'all',
     TRUE, TRUE, FALSE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ── 4. Permissions ───────────────────────────────────────────────────────────
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'ai_evidence_checker.view',
     'ai_evidence_checker', 'view',
     'View Evidence Check Reports',
     'Read evidence check reports and job status for tasks',
     NOW(), NOW()),
    (gen_random_uuid(), 'ai_evidence_checker.trigger',
     'ai_evidence_checker', 'create',
     'Trigger Evidence Check',
     'Manually trigger AI evidence evaluation on a task',
     NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ── 5. Role grants ───────────────────────────────────────────────────────────
-- view: all workspace roles
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT gen_random_uuid(), r.id, fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code IN ('workspace_viewer','workspace_contributor','workspace_admin','org_admin')
  AND fp.code = 'ai_evidence_checker.view'
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
);

-- trigger: workspace_admin and above
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT gen_random_uuid(), r.id, fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code IN ('workspace_admin','org_admin','super_admin','platform_admin')
  AND fp.code = 'ai_evidence_checker.trigger'
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
);

-- ── 6. Default prompt templates ──────────────────────────────────────────────
-- Seeded as system-level (tenant_key='system', no org_id)
-- These are the fallback prompts; orgs can override via Prompt Config admin

INSERT INTO "20_ai"."33_fct_prompt_templates"
    (tenant_key, scope_code, agent_type_code, feature_code, org_id, prompt_text, is_active, created_by)
VALUES
    ('system', 'agent', 'evidence_lead', 'ai_evidence_checker', NULL,
     $PROMPT$You are the Evidence Lead AI, an expert compliance evaluation orchestrator.
Your role is to coordinate the review of task attachments against acceptance criteria.
You ensure every criterion receives a thorough, evidence-grounded evaluation.
Be precise, objective, and reference-based. Never invent evidence.$PROMPT$,
     TRUE, NULL),

    ('system', 'agent', 'evidence_checker_agent', 'ai_evidence_checker', NULL,
     $PROMPT$You are an expert compliance evidence analyst specialising in GRC documentation review.
Your task is to determine whether the provided document excerpts satisfy the given acceptance criterion.

Rules:
1. Base your verdict ONLY on the provided document chunks — do not assume or invent evidence.
2. For every claim, cite the exact document name, page number (if available), and a short excerpt (≤150 chars).
3. If chunks do not contain enough information to make a determination, return INSUFFICIENT_EVIDENCE.
4. Be precise and concise. Justification: 1–3 sentences maximum.

Return ONLY a JSON object with this exact shape:
{
  "verdict": "MET" | "PARTIALLY_MET" | "NOT_MET" | "INSUFFICIENT_EVIDENCE",
  "threshold_met": true | false | null,
  "justification": "<1-3 sentence explanation>",
  "evidence_references": [
    {
      "document_filename": "<filename>",
      "page_number": <int or null>,
      "section_or_sheet": "<string or null>",
      "excerpt": "<≤150 chars>",
      "confidence": <0.0-1.0>
    }
  ],
  "conflicting_references": [<same shape>]
}$PROMPT$,
     TRUE, NULL)
ON CONFLICT DO NOTHING;

COMMIT;
