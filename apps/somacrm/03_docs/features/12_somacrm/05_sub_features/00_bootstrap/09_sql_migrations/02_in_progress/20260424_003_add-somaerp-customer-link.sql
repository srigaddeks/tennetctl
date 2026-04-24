-- UP ====
ALTER TABLE "12_somacrm".fct_contacts
  ADD COLUMN IF NOT EXISTS somaerp_customer_id VARCHAR(36);

CREATE INDEX IF NOT EXISTS idx_contacts_somaerp_customer
  ON "12_somacrm".fct_contacts(somaerp_customer_id)
  WHERE somaerp_customer_id IS NOT NULL;

COMMENT ON COLUMN "12_somacrm".fct_contacts.somaerp_customer_id
  IS 'FK reference to somaerp.fct_customers.id — cross-app contact↔customer link';

-- Recreate v_contacts to include the new column
CREATE OR REPLACE VIEW "12_somacrm".v_contacts AS
SELECT
    c.id,
    c.tenant_id,
    c.organization_id,
    o.name AS organization_name,
    c.first_name,
    c.last_name,
    concat_ws(' '::text, c.first_name, c.last_name) AS full_name,
    c.email,
    c.phone,
    c.mobile,
    c.job_title,
    c.company_name,
    c.website,
    c.linkedin_url,
    c.twitter_handle,
    c.lead_source,
    c.status_id,
    s.code AS status,
    c.somaerp_customer_id,
    c.notes_count,
    c.activities_count,
    c.deals_count,
    c.properties,
    c.deleted_at,
    c.created_by,
    c.updated_by,
    c.created_at,
    c.updated_at
FROM "12_somacrm".fct_contacts c
LEFT JOIN "12_somacrm".dim_contact_statuses s ON s.id = c.status_id
LEFT JOIN "12_somacrm".fct_organizations o ON o.id = c.organization_id AND o.deleted_at IS NULL;

-- DOWN ====
ALTER TABLE "12_somacrm".fct_contacts DROP COLUMN IF EXISTS somaerp_customer_id;
