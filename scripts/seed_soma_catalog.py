"""
Seed real Soma Delights catalog into somaerp via HTTP.

Idempotent: re-running only inserts missing rows (slug uniqueness drops dups).
Usage:
    PYTHONPATH=. .venv/bin/python -m scripts.seed_soma_catalog
"""

from __future__ import annotations

import os
import sys
from typing import Any

import httpx


TENNETCTL = os.environ.get("TENNETCTL_BASE_URL", "http://localhost:51734")
SOMAERP = os.environ.get("SOMAERP_BASE_URL", "http://localhost:51736")
EMAIL = os.environ.get("SOMASHOP_SERVICE_EMAIL", "sri@tennetctl.dev")
PASSWORD = os.environ.get("SOMASHOP_SERVICE_PASSWORD", "DevPass123!")
WS = os.environ.get("SOMAERP_DEFAULT_WORKSPACE_ID", "019dc2ca-865a-7043-b9dc-5a5ff7521f9f")
ORG = os.environ.get("SOMAERP_DEFAULT_ORG_ID", "019db460-92e0-7c61-968b-6c01d507511c")


PRODUCT_LINES = [
    {"slug": "classic-juices",  "name": "Classic Juices",   "category_id": 1},
    {"slug": "wellness-shots",  "name": "Wellness Shots",   "category_id": 2},
    {"slug": "therapeutic",     "name": "Therapeutic",      "category_id": 1},
]


PRODUCTS = [
    # (slug, name, line_slug, description, target_benefit, ml, price)
    ("abc-juice",        "ABC Juice",         "classic-juices",
     "Apple-Beetroot-Carrot. The most popular cold-pressed juice in India. Naturally sweet, nutritionally dense.",
     "Energy + skin radiance + iron absorption", 250, 180),
    ("classic-green",    "Classic Green",     "classic-juices",
     "Spinach + cucumber + apple + lemon + ginger. Gateway green juice — balanced, approachable.",
     "Detox + alkalinity", 250, 200),
    ("clarity-greens",   "Clarity Greens",    "classic-juices",
     "Kale + celery + apple + lemon + parsley. Stronger green for daily greens drinkers.",
     "Mental clarity + chlorophyll", 250, 220),
    ("beet-boost",       "Beet Boost",        "classic-juices",
     "Beetroot + ginger + lemon. Pre-workout endurance booster — nitrates → nitric oxide.",
     "Stamina + circulation", 250, 200),
    ("amla-juice",       "Amla Juice",        "wellness-shots",
     "Indian gooseberry shot. 600mg vitamin C per 60ml — 10× an orange.",
     "Immunity + collagen", 60, 90),
    ("turmeric-glow",    "Turmeric Glow",     "wellness-shots",
     "Turmeric + ginger + black pepper + lemon. Curcumin absorption optimised by piperine.",
     "Anti-inflammatory + skin", 60, 100),
    ("immunity-shield",  "Immunity Shield",   "wellness-shots",
     "Ginger + turmeric + lemon + cayenne + honey. Daily immune support shot.",
     "Immunity + circulation", 60, 110),
    ("digest-ease",      "Digest Ease",       "wellness-shots",
     "Ginger + mint + lemon + ajwain. Pre/post-meal digestive aid.",
     "Digestion + bloat relief", 60, 100),
    ("diabetes-care",    "Diabetes Care",     "therapeutic",
     "Karela + jamun + amla + neem. Glycemic-friendly therapeutic blend.",
     "Blood sugar regulation", 250, 240),
    ("bp-balance",       "BP Balance",        "therapeutic",
     "Beetroot + celery + lauki + lemon. Blood pressure-friendly therapeutic blend.",
     "Blood pressure regulation", 250, 240),
]


# frequency_id matches dim_subscription_frequencies — 1=daily, 2=5x/week, 4=weekly
PLANS = [
    {
        "slug": "daily-essentials",
        "name": "Daily Essentials",
        "description": "One classic juice + one wellness shot every morning. The Soma starter plan.",
        "frequency_id": 1,
        "price_per_delivery": 280,
    },
    {
        "slug": "weekday-detox",
        "name": "Weekday Detox",
        "description": "Five-day cleanse: green juice + shot, Mon to Fri. Reset your week.",
        "frequency_id": 2,
        "price_per_delivery": 360,
    },
    {
        "slug": "wellness-warrior",
        "name": "Wellness Warrior",
        "description": "Two juices + two shots daily. Maximum support for high performers.",
        "frequency_id": 1,
        "price_per_delivery": 540,
    },
]


def signin() -> str:
    r = httpx.post(
        f"{TENNETCTL}/v1/auth/signin",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=10.0,
    )
    r.raise_for_status()
    token = r.json()["data"]["token"]
    print(f"signin ok — token {token[:20]}…")
    return token


def headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "x-org-id": ORG,
        "x-workspace-id": WS,
        "Content-Type": "application/json",
    }


def upsert_product_line(token: str, line: dict) -> str:
    """Returns line id. If slug already exists, fetches it."""
    r = httpx.post(
        f"{SOMAERP}/v1/somaerp/catalog/product-lines",
        json={
            "category_id": line["category_id"],
            "name": line["name"],
            "slug": line["slug"],
            "status": "active",
            "properties": {},
        },
        headers=headers(token),
        timeout=10.0,
    )
    if r.status_code == 201:
        line_id = r.json()["data"]["id"]
        print(f"+ product_line {line['slug']:20s} {line_id}")
        return line_id
    if r.status_code == 409:
        # Already exists — fetch
        list_r = httpx.get(
            f"{SOMAERP}/v1/somaerp/catalog/product-lines",
            headers=headers(token), timeout=10.0,
        )
        for row in list_r.json()["data"]:
            if row["slug"] == line["slug"]:
                print(f"= product_line {line['slug']:20s} {row['id']}")
                return row["id"]
    print(f"! product_line {line['slug']} status={r.status_code} body={r.text[:200]}")
    sys.exit(1)


def upsert_product(token: str, line_id: str, p: tuple[Any, ...]) -> None:
    slug, name, _, desc, benefit, ml, price = p
    r = httpx.post(
        f"{SOMAERP}/v1/somaerp/catalog/products",
        json={
            "product_line_id": line_id,
            "name": name,
            "slug": slug,
            "description": desc,
            "target_benefit": benefit,
            "default_serving_size_ml": ml,
            "default_shelf_life_hours": 72,
            "default_selling_price": price,
            "currency_code": "INR",
            "status": "active",
            "tag_codes": [],
            "properties": {},
        },
        headers=headers(token),
        timeout=10.0,
    )
    if r.status_code == 201:
        print(f"+ product      {slug:20s} {r.json()['data']['id']}")
    elif r.status_code == 409:
        print(f"= product      {slug:20s} (exists)")
    else:
        print(f"! product {slug} status={r.status_code} body={r.text[:200]}")


def upsert_plan(token: str, plan: dict) -> None:
    r = httpx.post(
        f"{SOMAERP}/v1/somaerp/subscriptions/plans",
        json={
            "name": plan["name"],
            "slug": plan["slug"],
            "description": plan["description"],
            "frequency_id": plan["frequency_id"],
            "price_per_delivery": plan["price_per_delivery"],
            "currency_code": "INR",
            "status": "active",
            "properties": {},
        },
        headers=headers(token),
        timeout=10.0,
    )
    if r.status_code in (200, 201):
        print(f"+ plan         {plan['slug']:20s} {r.json()['data']['id']}")
    elif r.status_code == 409:
        print(f"= plan         {plan['slug']:20s} (exists)")
    else:
        print(f"! plan {plan['slug']} status={r.status_code} body={r.text[:200]}")


def main() -> None:
    token = signin()
    line_ids: dict[str, str] = {}
    for line in PRODUCT_LINES:
        line_ids[line["slug"]] = upsert_product_line(token, line)

    for p in PRODUCTS:
        line_id = line_ids[p[2]]
        upsert_product(token, line_id, p)

    for plan in PLANS:
        upsert_plan(token, plan)

    print("done.")


if __name__ == "__main__":
    main()
