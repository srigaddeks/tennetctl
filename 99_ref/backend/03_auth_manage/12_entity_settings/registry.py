"""Entity type registry — single source of truth for all EAV entity configurations."""

from __future__ import annotations

from dataclasses import dataclass

SCHEMA = '"03_auth_manage"'


@dataclass(frozen=True, slots=True)
class EntityConfig:
    """Configuration for one EAV-backed entity type."""

    entity_type: str
    detail_table: str
    dimension_table: str
    entity_id_column: str
    fact_table: str
    fact_id_column: str
    permission_prefix: str
    audit_entity_type: str
    audit_event_type: str
    cache_prefix: str
    tenant_key_column: str
    resolve_from_code: bool = False
    code_lookup_table: str | None = None
    code_lookup_column: str | None = None
    tenant_key_column: str | None = "tenant_key"  # None for dimension tables without tenant_key


ENTITY_REGISTRY: dict[str, EntityConfig] = {
    "org": EntityConfig(
        entity_type="org",
        detail_table=f'{SCHEMA}."30_dtl_org_settings"',
        dimension_table=f'{SCHEMA}."31_dim_org_setting_keys"',
        entity_id_column="org_id",
        fact_table=f'{SCHEMA}."29_fct_orgs"',
        fact_id_column="id",
        permission_prefix="org_management",
        audit_entity_type="org",
        audit_event_type="org_updated",
        cache_prefix="org",
        tenant_key_column="tenant_key",
    ),
    "workspace": EntityConfig(
        entity_type="workspace",
        detail_table=f'{SCHEMA}."35_dtl_workspace_settings"',
        dimension_table=f'{SCHEMA}."36_dim_workspace_setting_keys"',
        entity_id_column="workspace_id",
        fact_table=f'{SCHEMA}."34_fct_workspaces"',
        fact_id_column="id",
        permission_prefix="workspace_management",
        audit_entity_type="workspace",
        audit_event_type="workspace_updated",
        cache_prefix="workspace",
        tenant_key_column=None,  # 34_fct_workspaces has no tenant_key — tenant resolved via parent org
    ),
    "role": EntityConfig(
        entity_type="role",
        detail_table=f'{SCHEMA}."22_dtl_role_settings"',
        dimension_table=f'{SCHEMA}."22_dim_role_setting_keys"',
        entity_id_column="role_id",
        fact_table=f'{SCHEMA}."16_fct_roles"',
        fact_id_column="id",
        permission_prefix="group_access_assignment",
        audit_entity_type="role",
        audit_event_type="role_updated",
        cache_prefix="role",
        tenant_key_column="tenant_key",
    ),
    "group": EntityConfig(
        entity_type="group",
        detail_table=f'{SCHEMA}."27_dtl_group_settings"',
        dimension_table=f'{SCHEMA}."27_dim_group_setting_keys"',
        entity_id_column="group_id",
        fact_table=f'{SCHEMA}."17_fct_user_groups"',
        fact_id_column="id",
        permission_prefix="group_access_assignment",
        audit_entity_type="group",
        audit_event_type="group_updated",
        cache_prefix="group",
        tenant_key_column="tenant_key",
    ),
    "feature": EntityConfig(
        entity_type="feature",
        detail_table=f'{SCHEMA}."21_dtl_feature_flag_settings"',
        dimension_table=f'{SCHEMA}."21_dim_feature_flag_setting_keys"',
        entity_id_column="feature_flag_id",
        fact_table=f'{SCHEMA}."14_dim_feature_flags"',
        fact_id_column="id",
        permission_prefix="feature_flag_registry",
        audit_entity_type="feature_flag",
        audit_event_type="flag_updated",
        cache_prefix="feature_flag",
        tenant_key_column=None,  # 14_dim_feature_flags is a dimension table — no tenant_key column
        resolve_from_code=True,
        code_lookup_table=f'{SCHEMA}."14_dim_feature_flags"',
        code_lookup_column="code",
    ),
    "product": EntityConfig(
        entity_type="product",
        detail_table=f'{SCHEMA}."25_dtl_product_settings"',
        dimension_table=f'{SCHEMA}."26_dim_product_setting_keys"',
        entity_id_column="product_id",
        fact_table=f'{SCHEMA}."24_fct_products"',
        fact_id_column="id",
        permission_prefix="product_management",
        audit_entity_type="product",
        audit_event_type="product_updated",
        cache_prefix="product",
        tenant_key_column="tenant_key",
    ),
}
