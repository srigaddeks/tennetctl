/**
 * somashop API client. Talks to:
 *   - somashop backend (51740) for products + orders
 *   - tennetctl backend (51734) for mobile-OTP auth
 *
 * Token is stored in localStorage as `somashop_token`. All authenticated
 * requests forward it via Bearer.
 */

const SHOP_BASE =
  process.env.NEXT_PUBLIC_SOMASHOP_API_URL ?? "http://localhost:51740";
const TENNETCTL_BASE =
  process.env.NEXT_PUBLIC_TENNETCTL_BACKEND ?? "http://localhost:51734";
const STORAGE_KEY = "somashop_token";

export type ApiEnvelope<T> =
  | { ok: true; data: T }
  | { ok: false; error: { code: string; message: string } };

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (token) localStorage.setItem(STORAGE_KEY, token);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* swallow */
  }
}

function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function unwrap<T>(res: Response): Promise<T> {
  const data = (await res.json()) as ApiEnvelope<T>;
  if (!data.ok) throw new Error(data.error?.message ?? `HTTP ${res.status}`);
  return data.data;
}

/* ── Products + orders (somashop backend) ─────────────────────────── */

export type Product = {
  id: string;
  name: string;
  slug: string;
  status: string;
  description?: string | null;
  target_benefit?: string | null;
  default_serving_size_ml?: number | null;
  default_selling_price?: number | string | null;
  currency_code?: string | null;
  product_line_name?: string | null;
};

export async function listProducts(): Promise<Product[]> {
  const r = await fetch(`${SHOP_BASE}/v1/products`, {
    headers: { ...authHeaders() },
  });
  return unwrap<Product[]>(r);
}

export async function getProductBySlug(slug: string): Promise<Product | null> {
  const all = await listProducts();
  return all.find((p) => p.slug === slug) ?? null;
}

export type SubscriptionPlan = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  price_per_delivery?: number | string | null;
  currency_code?: string | null;
  frequency_code?: string | null;
  frequency_name?: string | null;
};

export async function listPlans(): Promise<SubscriptionPlan[]> {
  const r = await fetch(`${SHOP_BASE}/v1/subscription-plans`, {
    headers: { ...authHeaders() },
  });
  return unwrap<SubscriptionPlan[]>(r);
}

export async function getPlanBySlug(slug: string): Promise<SubscriptionPlan | null> {
  const all = await listPlans();
  return all.find((p) => p.slug === slug) ?? null;
}

export type Order = {
  id: string;
  status: string;
  plan_name?: string | null;
  plan_slug?: string | null;
  customer_name?: string | null;
  start_date?: string | null;
  price_per_delivery?: number | string | null;
  currency_code?: string | null;
  frequency_name?: string | null;
  created_at: string;
};

export async function listMyOrders(): Promise<Order[]> {
  const r = await fetch(`${SHOP_BASE}/v1/my-orders`, {
    headers: { ...authHeaders() },
  });
  return unwrap<Order[]>(r);
}

export type PlaceOrderBody = {
  subscription_plan_id: string;
  name: string;
  phone: string;
  address_line1: string;
  address_pincode: string;
  city: string;
  notes?: string | null;
};

export async function placeOrder(body: PlaceOrderBody): Promise<Order> {
  const r = await fetch(`${SHOP_BASE}/v1/my-orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  return unwrap<Order>(r);
}

/* ── Auth (tennetctl mobile OTP) ──────────────────────────────────── */

export async function requestMobileOtp(phone_e164: string): Promise<{
  sent: boolean;
  message: string;
  debug_code?: string;
}> {
  const r = await fetch(`${TENNETCTL_BASE}/v1/auth/mobile-otp/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone_e164 }),
  });
  return unwrap(r);
}

export async function verifyMobileOtp(input: {
  phone_e164: string;
  code: string;
  display_name?: string;
}): Promise<{ token: string; user_id: string; session_id: string }> {
  const body = {
    phone_e164: input.phone_e164,
    code: input.code,
    display_name: input.display_name,
    account_type: "soma_delights_customer" as const,
  };
  const r = await fetch(`${TENNETCTL_BASE}/v1/auth/mobile-otp/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return unwrap(r);
}

export async function getMe(): Promise<{
  user: { id: string; display_name?: string | null };
  session: { id: string; org_id: string | null; workspace_id: string | null };
} | null> {
  const t = getToken();
  if (!t) return null;
  const r = await fetch(`${TENNETCTL_BASE}/v1/auth/me`, {
    headers: { Authorization: `Bearer ${t}` },
  });
  if (r.status === 401) return null;
  return unwrap(r);
}
