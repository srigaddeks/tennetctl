import { fetchWithAuth } from "./apiClient";

export interface ApiKeyResponse {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  is_active: boolean;
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string;
}

export interface CreateApiKeyRequest {
  name: string;
  scopes?: string[];
  expires_at?: string | null;
}

export interface CreateApiKeyResponse extends ApiKeyResponse {
  raw_key: string; // only returned on creation
}

export async function listApiKeys(): Promise<ApiKeyResponse[]> {
  const res = await fetchWithAuth("/api/v1/am/api-keys");
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to list API keys");
  return (data.items ?? data.api_keys ?? []) as ApiKeyResponse[];
}

export async function createApiKey(payload: CreateApiKeyRequest): Promise<CreateApiKeyResponse> {
  const res = await fetchWithAuth("/api/v1/am/api-keys", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create API key");
  return data as CreateApiKeyResponse;
}

export async function rotateApiKey(keyId: string): Promise<CreateApiKeyResponse> {
  const res = await fetchWithAuth(`/api/v1/am/api-keys/${keyId}/rotate`, {
    method: "POST",
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to rotate API key");
  return data as CreateApiKeyResponse;
}

export async function revokeApiKey(keyId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/api-keys/${keyId}/revoke`, {
    method: "PATCH",
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to revoke API key");
  }
}

export async function deleteApiKey(keyId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/api-keys/${keyId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to delete API key");
  }
}
