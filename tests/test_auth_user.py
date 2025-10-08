from __future__ import annotations

import pytest

from stellar_api import StellarApiClient, unique_email


@pytest.mark.live
class TestUserUpdate:
    @pytest.mark.parametrize("field,new_value_builder", [
        ("name", lambda ru: ru["name"] + " Updated"),
        ("email", lambda ru: unique_email()),
        ("password", lambda ru: ru["password"] + "_new"),
    ])
    def test_update_user_with_auth(self, client: StellarApiClient, logged_in_user, field: str, new_value_builder):
        token = logged_in_user["token"]
        new_value = new_value_builder(logged_in_user)
        res = client.auth_user_patch(token, {field: new_value})
        assert res.status_code == 200, f"Unexpected status {res.status_code}: {res.text}"
        assert res.json and res.json.get("success") is True
        if field in ("name", "email"):
            assert res.json.get("user", {}).get(field) == new_value
        elif field == "password":
            # Password not returned; verify by logging in with new password
            email = logged_in_user["email"]
            login_res = client.auth_login(email if "email" not in res.json.get("user", {}) else res.json["user"]["email"], new_value)
            assert login_res.status_code == 200 and login_res.json and login_res.json.get("success") is True

    @pytest.mark.parametrize("field,new_value", [
        ("name", "Someone Else"),
        ("email", unique_email()),
        ("password", "OtherPass123!"),
    ])
    def test_update_user_without_auth(self, client: StellarApiClient, field: str, new_value: str):
        res = client._request("PATCH", "/auth/user", json={field: new_value})
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
        if res.json:
            assert res.json.get("success") is False
            assert "authorised" in res.json.get("message", "").lower()

