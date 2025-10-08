from __future__ import annotations

import pytest

from stellar_api import StellarApiClient, unique_email


@pytest.mark.live
class TestUserLogin:
    def test_login_existing_user(self, client: StellarApiClient, registered_user):
        res = client.auth_login(registered_user["email"], registered_user["password"])
        assert res.status_code == 200, f"Unexpected status: {res.status_code}, body: {res.text}"
        assert res.json and res.json.get("success") is True
        assert res.json.get("accessToken")
        assert res.json.get("refreshToken")

    @pytest.mark.parametrize(
        "email,password",
        [
            (lambda e: ("wrong_" + e, "P@ssw0rd!"))(unique_email()),  # wrong email
            (lambda e: (e, "wrong_password"))(unique_email()),  # this user won't exist either
        ],
    )
    def test_login_with_wrong_credentials(self, client: StellarApiClient, email: str, password: str):
        # Ensure user likely doesn't exist; attempt login
        res = client.auth_login(email, password)
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
        if res.json:
            assert res.json.get("success") is False
            assert "incorrect" in res.json.get("message", "").lower()

