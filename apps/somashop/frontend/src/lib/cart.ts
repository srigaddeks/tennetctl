/**
 * Tiny localStorage-backed cart for somashop.
 *
 * Cart shape: a single chosen subscription plan (slug) — mirrors how
 * Soma Delights actually sells (one plan per customer). Future revs can
 * extend to multi-line carts; v1 keeps it dead simple.
 */

const KEY = "somashop_cart";

export type Cart = {
  plan_slug: string | null;
};

export function readCart(): Cart {
  if (typeof window === "undefined") return { plan_slug: null };
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return { plan_slug: null };
    return JSON.parse(raw) as Cart;
  } catch {
    return { plan_slug: null };
  }
}

export function setCartPlan(plan_slug: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (plan_slug) localStorage.setItem(KEY, JSON.stringify({ plan_slug }));
    else localStorage.removeItem(KEY);
  } catch {
    /* swallow */
  }
}

export function clearCart(): void {
  setCartPlan(null);
}
