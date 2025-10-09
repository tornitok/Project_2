from __future__ import annotations

import os
import random
from typing import Dict, Iterable, List, Tuple

import pytest

from api_client import StellarApiClient, ensure_api_available, unique_email


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("STELLAR_BASE_URL", "https://stellarburgers.nomoreparties.site/api").rstrip("/")


@pytest.fixture(scope="session")
def client(base_url: str) -> StellarApiClient:
    return StellarApiClient(base_url=base_url)


@pytest.fixture(scope="session", autouse=True)
def ensure_api(client: StellarApiClient):
    if not ensure_api_available(client):
        pytest.skip("Stellar Burgers API is not available at the configured base URL")


@pytest.fixture()
def new_user_credentials() -> Tuple[str, str, str]:
    email = unique_email()
    password = "P@ssw0rd!"  # meets typical complexity
    name = "Test User"
    return email, password, name


@pytest.fixture()
def registered_user(client: StellarApiClient, new_user_credentials: Tuple[str, str, str]):
    email, password, name = new_user_credentials
    res = client.auth_register(email, password, name)
    assert res.status_code == 200 and res.json and res.json.get("success") is True
    token = res.json.get("accessToken", "").replace("Bearer ", "") if res.json else ""
    yield {
        "email": email,
        "password": password,
        "name": name,
        "token": token,
    }
    # Cleanup: try to delete the user if API supports it
    if token:
        try:
            client.auth_user_delete(token)
        except Exception:
            pass


@pytest.fixture()
def logged_in_user(client: StellarApiClient, registered_user: Dict[str, str]):
    email = registered_user["email"]
    password = registered_user["password"]
    res = client.auth_login(email, password)
    assert res.status_code == 200 and res.json and res.json.get("success") is True
    token = res.json.get("accessToken", "").replace("Bearer ", "") if res.json else ""
    return {
        **registered_user,
        "token": token,
    }


@pytest.fixture(scope="session")
def all_ingredients(client: StellarApiClient) -> List[str]:
    res = client.ingredients_get()
    assert res.status_code == 200 and res.json and res.json.get("success") is True
    data = res.json.get("data", []) if res.json else []
    ids = [item.get("_id") for item in data if item.get("_id")]
    assert ids, "No ingredients available from API"
    return ids


@pytest.fixture()
def valid_ingredients_subset(all_ingredients: List[str]) -> List[str]:
    # pick 2-3 random ingredients for an order
    k = 3 if len(all_ingredients) >= 3 else max(1, len(all_ingredients))
    return random.sample(all_ingredients, k)


@pytest.fixture()
def invalid_ingredients() -> List[str]:
    # Clearly invalid hashes
    return ["invalid_hash_1", "12345", "deadbeefcafebabe"]
