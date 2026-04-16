import { API_BASE_URL, setAccessToken, clearAccessToken, getAccessToken } from "./apiClient";
import { fetchWithAuth } from "./apiClient";
import type { TokenPairResponse, AuthUserResponse } from "../types/auth";
import type { UserAccountResponse, PropertyKeyResponse } from "../types/admin";

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Store the refresh token in an httpOnly cookie via the Next.js route handler. */
async function persistRefreshToken(refreshToken: string) {
  await fetch("/api/auth/set-refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

//─── Auth API ─────────────────────────────────────────────────────────────────

export async function loginUser(
  email: string,
  password: string
): Promise<TokenPairResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/local/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login: email, password }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || "Invalid credentials");
  }

  const tokens = data as TokenPairResponse;
  // Access token → memory only
  setAccessToken(tokens.access_token);
  // Refresh token → httpOnly cookie (JS can never read it)
  await persistRefreshToken(tokens.refresh_token);

  return tokens;
}

export async function loginWithGoogle(
  idToken: string
): Promise<TokenPairResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/local/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || "Google login failed");
  }

  const tokens = data as TokenPairResponse;
  setAccessToken(tokens.access_token);
  await persistRefreshToken(tokens.refresh_token);

  return tokens;
}

export async function registerUser(
  email: string,
  password: string
): Promise<AuthUserResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/local/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();

  if (!response.ok) {
    if (Array.isArray(data.detail)) {
      const msg = data.detail.map((e: { msg: string }) => e.msg).join(", ");
      throw new Error(msg);
    }
    throw new Error(data.error?.message || data.detail || "Registration failed");
  }

  return data as AuthUserResponse;
}

export async function fetchMe(): Promise<AuthUserResponse> {
  const res = await fetchWithAuth("/api/v1/auth/local/me");
  if (!res.ok) throw new Error("Failed to load profile");
  return res.json();
}

export async function fetchUserProperties(): Promise<Record<string, string>> {
  const res = await fetchWithAuth("/api/v1/auth/local/me/properties");
  if (!res.ok) throw new Error("Failed to load user properties");
  // Backend returns { properties: [{ key, value }, ...] }
  const data: { properties: { key: string; value: string }[] } = await res.json();
  return Object.fromEntries(data.properties.map((p) => [p.key, p.value]));
}

export async function setUserProperties(
  props: Record<string, string>
): Promise<void> {
  const res = await fetchWithAuth("/api/v1/auth/local/me/properties", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ properties: props }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to save properties");
  }
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  const res = await fetchWithAuth("/api/v1/auth/local/me/password", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to change password");
  }
}

// ─── Forgot / Reset Password ────────────────────────────────────────────────

export async function forgotPassword(login: string): Promise<{ message: string; reset_token?: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/local/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message || data.detail || "Failed to request password reset");
  return data;
}

export async function resetPassword(resetToken: string, newPassword: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/local/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reset_token: resetToken, new_password: newPassword }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message || data.detail || "Failed to reset password");
  return data;
}

// ─── Email Verification ─────────────────────────────────────────────────────

export async function requestEmailVerification(): Promise<{ message: string; verification_token?: string }> {
  const res = await fetchWithAuth("/api/v1/auth/local/me/verify-email/request", { method: "POST" });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to request verification");
  return data;
}

export async function verifyEmail(verificationToken: string): Promise<{ message: string }> {
  const res = await fetchWithAuth("/api/v1/auth/local/me/verify-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ verification_token: verificationToken }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to verify email");
  return data;
}

// ─── OTP Verification ───────────────────────────────────────────────────────

export async function requestOTP(): Promise<{ message: string; otp_code?: string }> {
  const res = await fetchWithAuth("/api/v1/auth/local/me/otp/request", { method: "POST" });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to request OTP");
  return data;
}

export async function verifyOTP(otpCode: string): Promise<{ message: string }> {
  const res = await fetchWithAuth("/api/v1/auth/local/me/otp/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ otp_code: otpCode }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to verify OTP");
  return data;
}

// ─── Accounts & Property Keys ───────────────────────────────────────────────

export async function fetchUserAccounts(): Promise<UserAccountResponse[]> {
  const res = await fetchWithAuth("/api/v1/auth/local/me/accounts");
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to load accounts");
  return (data.accounts ?? []) as UserAccountResponse[];
}

export async function fetchPropertyKeys(): Promise<PropertyKeyResponse[]> {
  const res = await fetchWithAuth("/api/v1/auth/local/me/property-keys");
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to load property keys");
  return (data.keys ?? []) as PropertyKeyResponse[];
}

export async function deleteUserProperty(key: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/auth/local/me/properties/${encodeURIComponent(key)}`, { method: "DELETE" });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to delete property");
  }
}

// ─── Passwordless / Magic Link ──────────────────────────────────────────────

export async function requestMagicLink(email: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/passwordless/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data?.detail || data?.error?.message || "Failed to send magic link");
  return data;
}

export async function requestAssigneeMagicLink(email: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/passwordless/request-assignee`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data?.detail || data?.error?.message || "Failed to send assignee magic link");
  return data;
}

export async function verifyMagicLink(token: string): Promise<TokenPairResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/passwordless/verify?token=${encodeURIComponent(token)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data?.detail || data?.error?.message || "Invalid or expired magic link");
  return data as TokenPairResponse;
}

// ─── Logout ─────────────────────────────────────────────────────────────────

export async function logoutUser(): Promise<void> {
  if (typeof window === "undefined") return;

  // Server-side route handler reads the httpOnly cookie, revokes the session
  // on the backend with the real refresh token, then clears the cookie.
  try {
    const accessToken = getAccessToken();
    await fetch("/api/auth/logout", {
      method: "POST",
      headers: {
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
    });
  } catch {
    // Continue with local cleanup regardless
  }

  // Clear in-memory access token
  clearAccessToken();

  window.location.replace("/login");
}
