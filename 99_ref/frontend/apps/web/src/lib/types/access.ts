export interface AccessActionResponse {
  feature_code: string;
  action_code: string;
  category_code: string;
  access_mode: string;
  env_dev: boolean;
  env_staging: boolean;
  env_prod: boolean;
}

export interface AccessScope {
  actions: AccessActionResponse[];
}

export interface OrgScope extends AccessScope {
  org_id: string;
  name: string;
  slug: string;
  org_type_code: string;
}

export interface WorkspaceScope extends AccessScope {
  workspace_id: string;
  org_id: string;
  name: string;
  slug: string;
  workspace_type_code: string;
  product_id: string | null;
  product_name: string | null;
  product_code: string | null;
  product_actions: AccessActionResponse[];
}

export interface AccessContextResponse {
  user_id: string;
  tenant_key: string;
  platform: AccessScope;
  current_org?: OrgScope | null;
  current_workspace?: WorkspaceScope | null;
}
