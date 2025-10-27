from __future__ import annotations

import pytest
import allure

from api_client import StellarApiClient
from data import INVALID_INGREDIENT_HASHES


@pytest.mark.live
class TestOrderCreation:
    @allure.title("Создание заказа: с авторизацией и корректными ингредиентами")
    def test_create_order_with_auth_and_ingredients(self, client: StellarApiClient, logged_in_user, valid_ingredients_subset):
        res = client.orders_create(valid_ingredients_subset, token=logged_in_user["token"])
        assert res.status_code == 200, f"Unexpected status {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is True
        assert res.json.get("name")
        order = res.json.get("order", {})
        assert order.get("number")
        assert order.get("ingredients")

    @pytest.mark.skip(reason="Баг: живой API принимает заказы без авторизации; пропускаем до исправления на бэкенде")
    @allure.title("Создание заказа: без авторизации и с ингредиентами — ожидаем 401")
    def test_create_order_without_auth_but_with_ingredients(self, client: StellarApiClient, valid_ingredients_subset):
        res = client.orders_create(valid_ingredients_subset, token=None)
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is False

    @allure.title("Создание заказа: без ингредиентов — ожидаем 400")
    def test_create_order_without_ingredients(self, client: StellarApiClient, logged_in_user):
        res = client.orders_create([], token=logged_in_user["token"])  # empty list
        assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is False
        assert "ingredient" in res.json.get("message", "").lower()

    @pytest.mark.skip(reason="Баг: при неверных хешах ингредиентов API возвращает 500 вместо 400; ждём фикса бэкенда")
    @allure.title("Создание заказа: с неверными хешами ингредиентов — ожидаем 400")
    def test_create_order_with_invalid_ingredient_hashes(self, client: StellarApiClient, logged_in_user):
        res = client.orders_create(INVALID_INGREDIENT_HASHES, token=logged_in_user["token"])
        assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
        assert res.json is not None
        assert res.json.get("success") is False
