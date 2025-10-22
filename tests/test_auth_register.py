from __future__ import annotations

import pytest
import allure

from api_client import StellarApiClient


@pytest.mark.live
class TestUserRegistration:
    @allure.title("Создание уникального пользователя: успешная регистрация")
    def test_create_unique_user(self, client: StellarApiClient, new_user_credentials):
        email, password, name = new_user_credentials
        res = client.auth_register(email, password, name)
        assert res.status_code == 200, f"Unexpected status: {res.status_code}, body: {res.text}"
        assert res.json is not None and res.json.get("success") is True
        assert res.json.get("user", {}).get("email") == email
        assert res.json.get("user", {}).get("name") == name
        assert res.json.get("accessToken"), "accessToken is missing"
        assert res.json.get("refreshToken"), "refreshToken is missing"

    @allure.title("Создание пользователя, который уже зарегистрирован: ожидаем 403")
    def test_create_user_already_registered(self, client: StellarApiClient, registered_user):
        # Try to register same user again
        res = client.auth_register(registered_user["email"], registered_user["password"], registered_user["name"])
        assert res.status_code == 403, f"Expected 403 for duplicate registration, got {res.status_code}: {res.text}"
        assert res.json is not None and res.json.get("success") is False
        assert "already exists" in (res.json.get("message", "")).lower()

    @pytest.mark.parametrize("missing_field", ["email", "password", "name"])
    @allure.title("Создание пользователя без одного обязательного поля: ожидаем 403")
    def test_create_user_missing_required_field(self, client: StellarApiClient, new_user_credentials, missing_field: str):
        email, password, name = new_user_credentials
        payload = {"email": email, "password": password, "name": name}
        payload.pop(missing_field)
        res = client._request("POST", "/auth/register", json=payload)
        # Для сервиса ожидаем 403 и сообщение о необходимых полях
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is False
        assert "required" in res.json.get("message", "").lower()
