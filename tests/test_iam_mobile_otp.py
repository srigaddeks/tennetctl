"""IAM mobile-OTP — request/verify happy path + edge cases."""

from __future__ import annotations


class TestMobileOtp:
    async def test_request_otp_returns_debug_code_in_stub_mode(self, client):
        resp = await client.post(
            "/v1/auth/mobile-otp/request",
            json={"phone_e164": "+919876543299"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()["data"]
        assert body["sent"] is True
        # Stub mode: vault has no sms.twilio.* config, so debug_code echoes.
        assert body.get("debug_code"), "expected debug_code in stub mode"
        assert body["debug_code"].isdigit()
        assert len(body["debug_code"]) == 6

    async def test_invalid_phone_format_rejected(self, client):
        resp = await client.post(
            "/v1/auth/mobile-otp/request",
            json={"phone_e164": "9876543210"},  # missing +
        )
        assert resp.status_code == 422, resp.text

    async def test_verify_creates_user_and_returns_token(self, client):
        phone = "+919876543298"
        req = await client.post(
            "/v1/auth/mobile-otp/request",
            json={"phone_e164": phone},
        )
        code = req.json()["data"]["debug_code"]
        verify = await client.post(
            "/v1/auth/mobile-otp/verify",
            json={
                "phone_e164": phone,
                "code": code,
                "display_name": "Test Customer",
                "account_type": "soma_delights_customer",
            },
        )
        assert verify.status_code == 200, verify.text
        data = verify.json()["data"]
        assert data["token"]
        assert data["user_id"]
        assert data["session_id"]

    async def test_verify_wrong_code_rejected(self, client):
        phone = "+919876543297"
        await client.post("/v1/auth/mobile-otp/request", json={"phone_e164": phone})
        verify = await client.post(
            "/v1/auth/mobile-otp/verify",
            json={
                "phone_e164": phone,
                "code": "000000",
                "account_type": "soma_delights_customer",
            },
        )
        assert verify.status_code == 400, verify.text
        assert verify.json()["error"]["code"] == "OTP_INVALID"

    async def test_verify_unknown_phone_returns_not_found(self, client):
        verify = await client.post(
            "/v1/auth/mobile-otp/verify",
            json={
                "phone_e164": "+919876500000",
                "code": "123456",
                "account_type": "soma_delights_customer",
            },
        )
        assert verify.status_code == 400, verify.text
        assert verify.json()["error"]["code"] == "OTP_NOT_FOUND"

    async def test_verify_existing_user_signs_in_without_creating_new(self, client):
        phone = "+919876543296"
        # First signup
        req1 = await client.post("/v1/auth/mobile-otp/request", json={"phone_e164": phone})
        code1 = req1.json()["data"]["debug_code"]
        v1 = await client.post(
            "/v1/auth/mobile-otp/verify",
            json={"phone_e164": phone, "code": code1, "display_name": "First Login",
                  "account_type": "soma_delights_customer"},
        )
        assert v1.status_code == 200
        first_user_id = v1.json()["data"]["user_id"]

        # Second OTP for same phone — should reuse same user
        req2 = await client.post("/v1/auth/mobile-otp/request", json={"phone_e164": phone})
        code2 = req2.json()["data"]["debug_code"]
        v2 = await client.post(
            "/v1/auth/mobile-otp/verify",
            json={"phone_e164": phone, "code": code2,
                  "account_type": "soma_delights_customer"},
        )
        assert v2.status_code == 200
        assert v2.json()["data"]["user_id"] == first_user_id
