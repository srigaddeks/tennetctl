export interface AuthUserResponse {
  user_id: string;
  tenant_key: string;
  email: string;
  username: string | null;
  email_verified: boolean;
  account_status: string;
  user_category: string;
  is_new_user?: boolean;
}

export interface TokenPairResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  refresh_expires_in: number;
  user: AuthUserResponse | null;
}
