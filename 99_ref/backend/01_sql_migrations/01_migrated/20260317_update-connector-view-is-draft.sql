-- Update 60_vw_connector_instance_detail to expose is_draft column
-- ---------------------------------------------------------------------------

DROP VIEW IF EXISTS "15_sandbox"."60_vw_connector_instance_detail";
CREATE VIEW "15_sandbox"."60_vw_connector_instance_detail" AS
SELECT
    ci.id,
    ci.tenant_key,
    ci.org_id,
    ci.workspace_id,
    ci.instance_code,
    ci.connector_type_code,
    ct.name                 AS connector_type_name,
    ct.category_code        AS connector_category_code,
    cc.name                 AS connector_category_name,
    ci.asset_version_id,
    ci.collection_schedule,
    ci.last_collected_at,
    ci.health_status,
    ci.is_active,
    ci.is_draft,
    ci.is_deleted,
    ci.created_at,
    ci.updated_at,
    (SELECT p.property_value FROM "15_sandbox"."40_dtl_connector_instance_properties" p
     WHERE p.connector_instance_id = ci.id AND p.property_key = 'name'
     LIMIT 1)        AS name,
    (SELECT p.property_value FROM "15_sandbox"."40_dtl_connector_instance_properties" p
     WHERE p.connector_instance_id = ci.id AND p.property_key = 'description'
     LIMIT 1)        AS description
FROM "15_sandbox"."20_fct_connector_instances" ci
LEFT JOIN "15_sandbox"."03_dim_connector_types"     ct ON ct.code = ci.connector_type_code
LEFT JOIN "15_sandbox"."02_dim_connector_categories" cc ON cc.code = ct.category_code
WHERE ci.is_deleted = FALSE;
