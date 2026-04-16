-- Add task_id to auditor requests to support task-level access workflow
ALTER TABLE "12_engagements"."20_trx_auditor_requests" 
ADD COLUMN IF NOT EXISTS task_id UUID REFERENCES "08_tasks"."10_fct_tasks"(id);

COMMENT ON COLUMN "12_engagements"."20_trx_auditor_requests".task_id IS 'Optional link to a specific task that access is being requested for.';
