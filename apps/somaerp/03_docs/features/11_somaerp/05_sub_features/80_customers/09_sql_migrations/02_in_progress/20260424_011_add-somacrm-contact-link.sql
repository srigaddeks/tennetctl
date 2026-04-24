-- UP ====
ALTER TABLE "11_somaerp".fct_customers
  ADD COLUMN IF NOT EXISTS somacrm_contact_id VARCHAR(36);

CREATE INDEX IF NOT EXISTS idx_customers_somacrm_contact
  ON "11_somaerp".fct_customers(somacrm_contact_id)
  WHERE somacrm_contact_id IS NOT NULL;

COMMENT ON COLUMN "11_somaerp".fct_customers.somacrm_contact_id
  IS 'FK reference to somacrm.fct_contacts.id — cross-app customer↔contact link';

-- Recreate v_customers to include the new column
DROP VIEW IF EXISTS "11_somaerp".v_customers;
CREATE OR REPLACE VIEW "11_somaerp".v_customers AS
SELECT
    c.id,
    c.tenant_id,
    c.location_id,
    l.name AS location_name,
    c.name,
    c.slug,
    c.email,
    c.phone,
    c.address_jsonb,
    c.delivery_notes,
    c.acquisition_source,
    c.status,
    c.lifetime_value,
    c.somacrm_contact_id,
    c.properties,
    c.created_at,
    c.updated_at,
    c.created_by,
    c.updated_by,
    c.deleted_at,
    COALESCE((
        SELECT count(*)::integer AS count
        FROM "11_somaerp".fct_subscriptions s
        WHERE s.customer_id::text = c.id::text
          AND s.tenant_id::text = c.tenant_id::text
          AND s.status = 'active'::text
          AND s.deleted_at IS NULL
    ), 0) AS active_subscription_count
FROM "11_somaerp".fct_customers c
LEFT JOIN "11_somaerp".fct_locations l ON l.id::text = c.location_id::text;

-- DOWN ====
DROP VIEW IF EXISTS "11_somaerp".v_customers;
ALTER TABLE "11_somaerp".fct_customers DROP COLUMN IF EXISTS somacrm_contact_id;
