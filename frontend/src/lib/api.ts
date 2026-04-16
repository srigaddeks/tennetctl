/**
 * Typed API client for TennetCTL backend.
 *
 * All API calls go through apiFetch which:
 * - Prepends the API base URL
 * - Parses JSON response
 * - Checks the ok field in the envelope
 * - Throws on error responses with the server message
 */

import type { ApiResponse } from "@/types/api";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:51734";

export class ApiClientError extends Error {
  code: string;
  statusCode: number;

  constructor(code: string, message: string, statusCode: number) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.statusCode = statusCode;
  }
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  const data: ApiResponse<T> = await res.json();

  if (!data.ok) {
    throw new ApiClientError(
      data.error.code,
      data.error.message,
      res.status
    );
  }

  return data.data;
}
