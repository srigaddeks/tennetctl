import { fetchWithAuth } from "./apiClient";
import type { AccessContextResponse } from "../types/access";

export async function fetchAccessContext(
  orgId?: string,
  workspaceId?: string
): Promise<AccessContextResponse> {
  const params = new URLSearchParams();
  if (orgId) params.append("org_id", orgId);
  if (workspaceId) params.append("workspace_id", workspaceId);

  const queryParams = params.toString() ? `?${params.toString()}` : "";
  const res = await fetchWithAuth(`/api/v1/am/access${queryParams}`);
  
  if (!res.ok) {
    throw new Error("Failed to fetch access context");
  }

  return await res.json();
}
