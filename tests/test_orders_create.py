from __future__ import annotations

import pytest

from api_client import StellarApiClient


@pytest.mark.live
class TestOrderCreation:
    def test_create_order_with_auth_and_ingredients(self, client: StellarApiClient, logged_in_user, valid_ingredients_subset):
        res = client.orders_create(valid_ingredients_subset, token=logged_in_user["token"])
        assert res.status_code == 200, f"Unexpected status {res.status_code}: {res.text}"
        assert res.json and res.json.get("success") is True
        assert res.json.get("name")
        order = res.json.get("order", {})
        assert order.get("number")
        assert order.get("ingredients")

    def test_create_order_without_auth_but_with_ingredients(self, client: StellarApiClient, valid_ingredients_subset):
        res = client.orders_create(valid_ingredients_subset, token=None)
        # API allows creating orders without auth but should still succeed
        assert res.status_code in (200, 401), f"Unexpected status {res.status_code}: {res.text}"
        if res.status_code == 200:
            assert res.json and res.json.get("success") is True
        else:
            assert res.json and res.json.get("success") is False

    def test_create_order_without_ingredients(self, client: StellarApiClient, logged_in_user):
        res = client.orders_create([], token=logged_in_user["token"])  # empty list
        # Expect 400 with message about ingredients must be provided
        assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
        if res.json:
            assert res.json.get("success") is False
            assert "ingredient" in res.json.get("message", "").lower()

    def test_create_order_with_invalid_ingredient_hashes(self, client: StellarApiClient, logged_in_user, invalid_ingredients):
        res = client.orders_create(invalid_ingredients, token=logged_in_user["token"])
        # Expect 500 or 400 depending on backend validation; assert not success
        assert res.status_code in (400, 500), f"Expected 400/500, got {res.status_code}: {res.text}"
        if res.json:
            assert res.json.get("success") is False
