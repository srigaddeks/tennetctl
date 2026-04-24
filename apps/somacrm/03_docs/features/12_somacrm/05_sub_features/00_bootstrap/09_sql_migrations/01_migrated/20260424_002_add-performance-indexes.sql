-- UP ====
CREATE INDEX IF NOT EXISTS idx_contacts_status ON "12_somacrm".fct_contacts(tenant_id, status_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_contacts_email ON "12_somacrm".fct_contacts(tenant_id, email) WHERE deleted_at IS NULL AND email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_deals_status ON "12_somacrm".fct_deals(tenant_id, status_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_deals_close_date ON "12_somacrm".fct_deals(tenant_id, expected_close_date) WHERE deleted_at IS NULL AND expected_close_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_activities_due ON "12_somacrm".fct_activities(tenant_id, due_at) WHERE deleted_at IS NULL AND due_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_leads_status_score ON "12_somacrm".fct_leads(tenant_id, status_id, score) WHERE deleted_at IS NULL;

-- DOWN ====
DROP INDEX IF EXISTS "12_somacrm".idx_contacts_status;
DROP INDEX IF EXISTS "12_somacrm".idx_contacts_email;
DROP INDEX IF EXISTS "12_somacrm".idx_deals_status;
DROP INDEX IF EXISTS "12_somacrm".idx_deals_close_date;
DROP INDEX IF EXISTS "12_somacrm".idx_activities_due;
DROP INDEX IF EXISTS "12_somacrm".idx_leads_status_score;
