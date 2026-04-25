"""
End-to-end smoke test for the somashop customer flow.

Runs against the live local stack (ports 51734 + 51736 + 51740). Exercises
the actual customer journey:

    1. Mobile-OTP request → grab debug_code
    2. Mobile-OTP verify → mint a fresh customer + session
    3. List products + plans (public)
    4. Place an order (creates somaerp customer + subscription)
    5. List my orders → confirm the new subscription appears

Exits 0 on success, 1 on any assertion failure. Prints each step.

Usage:
    PYTHONPATH=. .venv/bin/python -m scripts.smoke_somashop_e2e
"""

from __future__ import annotations

import os
import secrets
import sys
import time

import httpx

TENNETCTL = os.environ.get("TENNETCTL_BASE_URL", "http://localhost:51734")
SOMASHOP = os.environ.get("SOMASHOP_BASE_URL", "http://localhost:51740")


def expect(cond: bool, msg: str) -> None:
    if not cond:
        print(f"FAIL: {msg}", file=sys.stderr)
        sys.exit(1)


def step(label: str) -> None:
    print(f"→ {label}")


def main() -> None:
    # Unique phone per run so we always create a fresh customer
    suffix = secrets.randbelow(900_000) + 100_000  # 6-digit
    phone = f"+91876{suffix}"
    print(f"smoke phone: {phone}")

    with httpx.Client(timeout=15.0) as http:
        step("health check")
        for url in (
            f"{TENNETCTL}/health",
            f"{SOMASHOP}/health",
        ):
            r = http.get(url)
            expect(r.status_code == 200, f"{url} not 200 (got {r.status_code})")

        step("mobile-OTP request")
        r = http.post(
            f"{TENNETCTL}/v1/auth/mobile-otp/request",
            json={"phone_e164": phone},
        )
        expect(r.status_code == 200, f"OTP request {r.status_code}: {r.text[:200]}")
        body = r.json()["data"]
        expect(body.get("sent") is True, "sent != true")
        debug_code = body.get("debug_code")
        expect(debug_code is not None, "no debug_code (Twilio config in vault?)")
        print(f"   debug_code = {debug_code}")

        step("mobile-OTP verify")
        r = http.post(
            f"{TENNETCTL}/v1/auth/mobile-otp/verify",
            json={
                "phone_e164": phone,
                "code": debug_code,
                "display_name": "E2E Smoke",
                "account_type": "soma_delights_customer",
            },
        )
        expect(r.status_code == 200, f"OTP verify {r.status_code}: {r.text[:200]}")
        token = r.json()["data"]["token"]
        user_id = r.json()["data"]["user_id"]
        print(f"   token = {token[:24]}…  user_id = {user_id}")

        auth = {"Authorization": f"Bearer {token}"}

        step("list products (public)")
        r = http.get(f"{SOMASHOP}/v1/products", headers=auth)
        expect(r.status_code == 200, f"products {r.status_code}: {r.text[:200]}")
        products = r.json()["data"]
        expect(len(products) > 0, "products empty — run scripts.seed_soma_catalog first")
        print(f"   {len(products)} products")

        step("list subscription plans")
        r = http.get(f"{SOMASHOP}/v1/subscription-plans", headers=auth)
        expect(r.status_code == 200, f"plans {r.status_code}: {r.text[:200]}")
        plans = r.json()["data"]
        expect(len(plans) > 0, "plans empty")
        plan = next((p for p in plans if p["slug"] == "daily-essentials"), plans[0])
        print(f"   chose plan = {plan['slug']} ({plan['id']})")

        step("place order")
        r = http.post(
            f"{SOMASHOP}/v1/my-orders",
            headers={**auth, "Content-Type": "application/json"},
            json={
                "subscription_plan_id": plan["id"],
                "name": "E2E Smoke",
                "phone": phone,
                "address_line1": "E2E Test Address, Plot 1",
                "address_pincode": "500034",
                "city": "Hyderabad",
                "notes": "smoke test — please ignore",
            },
        )
        expect(r.status_code == 201, f"place order {r.status_code}: {r.text[:300]}")
        sub = r.json()["data"]
        sub_id = sub["id"]
        print(f"   subscription = {sub_id} status={sub.get('status')}")

        # Brief grace; somaerp views are committed by now.
        time.sleep(0.5)

        step("list my orders")
        r = http.get(f"{SOMASHOP}/v1/my-orders", headers=auth)
        expect(r.status_code == 200, f"my-orders {r.status_code}: {r.text[:200]}")
        my = r.json()["data"]
        expect(len(my) >= 1, "my-orders is empty after place")
        ids = [m["id"] for m in my]
        expect(sub_id in ids, f"new subscription {sub_id} not in {ids}")
        print(f"   {len(my)} order(s); new subscription visible")

    print("PASS — full somashop customer flow works end-to-end")


if __name__ == "__main__":
    main()
