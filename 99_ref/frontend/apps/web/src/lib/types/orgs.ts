export interface CreateOrgPayload {
  name: string;
  slug: string;
  org_type_code: string;
  description?: string;
}

export interface OrgResponse {
  id: string;
  tenant_key: string;
  name: string;
  slug: string;
  org_type_code: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrgMemberResponse {
  id: string;
  org_id: string;
  user_id: string;
  role: string;
  is_active: boolean;
  joined_at: string | null;
  email: string | null;
  display_name: string | null;
}

export interface CreateWorkspacePayload {
  name: string;
  slug: string;
  workspace_type_code: string;
  product_id?: string;
  description?: string;
}

export interface WorkspaceResponse {
  id: string;
  org_id: string;
  workspace_type_code: string;
  product_id: string | null;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMemberResponse {
  id: string;
  workspace_id: string;
  user_id: string;
  role: string;
  is_active: boolean;
  joined_at: string | null;
  email: string | null;
  display_name: string | null;
  grc_role_code: string | null;
}
