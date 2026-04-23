/**
 * TennetCTL API client for the extension background service worker.
 * All network calls go through here — never from content scripts directly.
 */

export class ApiError extends Error {
  constructor(code, message, status) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export async function apiFetch(path, { method = "GET", body, token, baseUrl }) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(baseUrl + path, {
    method,
    headers,
    body: body != null ? JSON.stringify(body) : undefined,
  });

  let json;
  try {
    json = await res.json();
  } catch {
    throw new ApiError("PARSE_ERROR", `HTTP ${res.status} — non-JSON response`, res.status);
  }

  if (!json.ok) {
    throw new ApiError(
      json.error?.code ?? "API_ERROR",
      json.error?.message ?? "unknown error",
      res.status,
    );
  }
  return json.data;
}
