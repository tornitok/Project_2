from __future__ import annotations

import pytest
import allure

from api_client import StellarApiClient


@pytest.mark.live
class TestUserOrdersFetch:
    @allure.title("Получение заказов пользователя: авторизованный пользователь")
    def test_get_orders_authorized_user(self, client: StellarApiClient, logged_in_user, valid_ingredients_subset):
        create_res = client.orders_create(valid_ingredients_subset, token=logged_in_user["token"])
        assert create_res.status_code == 200 and create_res.json and create_res.json.get("success") is True

        res = client.orders_get_user(token=logged_in_user["token"])
        assert res.status_code == 200, f"Unexpected status {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is True
        assert isinstance(res.json.get("orders"), list)
        assert len(res.json.get("orders")) >= 1

    @allure.title("Получение заказов пользователя: без авторизации — ожидаем 401")
    def test_get_orders_unauthorized_user(self, client: StellarApiClient):
        res = client._request("GET", "/orders")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is False
        assert "authorised" in res.json.get("message", "").lower()
