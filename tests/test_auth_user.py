from __future__ import annotations

import pytest
import allure

from api_client import StellarApiClient
from helpers import unique_email


@pytest.mark.live
class TestUserUpdate:
    @allure.title("Изменение имени пользователя с авторизацией: поле name обновляется")
    def test_update_user_name_with_auth(self, client: StellarApiClient, logged_in_user):
        token = logged_in_user["token"]
        new_name = logged_in_user["name"] + " Updated"
        res = client.auth_user_patch(token, {"name": new_name})
        assert res.status_code == 200, f"Unexpected status {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is True
        assert res.json.get("user", {}).get("name") == new_name

    @allure.title("Изменение email пользователя с авторизацией: поле email обновляется")
    def test_update_user_email_with_auth(self, client: StellarApiClient, logged_in_user):
        token = logged_in_user["token"]
        new_email = unique_email()
        res = client.auth_user_patch(token, {"email": new_email})
        assert res.status_code == 200, f"Unexpected status {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is True
        assert res.json.get("user", {}).get("email") == new_email

    @allure.title("Изменение пароля пользователя с авторизацией: можно залогиниться с новым паролем")
    def test_update_user_password_with_auth(self, client: StellarApiClient, logged_in_user):
        token = logged_in_user["token"]
        new_password = logged_in_user["password"] + "_new"
        res = client.auth_user_patch(token, {"password": new_password})
        assert res.status_code == 200, f"Unexpected status {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is True
        # Password не возвращается; проверяем логином
        email = logged_in_user["email"]
        login_res = client.auth_login(email, new_password)
        assert login_res.status_code == 200 and login_res.json and login_res.json.get("success") is True

    @pytest.mark.parametrize("field,new_value", [
        ("name", "Someone Else"),
        ("email", unique_email()),
        ("password", "OtherPass123!"),
    ])
    @allure.title("Изменение данных пользователя без авторизации: ожидаем 401 и невозможность изменения")
    def test_update_user_without_auth(self, client: StellarApiClient, field: str, new_value: str):
        res = client._request("PATCH", "/auth/user", json={field: new_value})
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is False
        assert "authorised" in res.json.get("message", "").lower()
