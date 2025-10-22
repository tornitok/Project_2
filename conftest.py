from __future__ import annotations

import random
from typing import Dict, List, Tuple

import pytest

from api_client import StellarApiClient, ensure_api_available
from helpers import unique_email, delete_user_safely
from urls import get_base_url
from data import DEFAULT_NAME, DEFAULT_PASSWORD, INVALID_INGREDIENT_HASHES


@pytest.fixture(scope="session")
def base_url() -> str:
    return get_base_url()


@pytest.fixture(scope="session")
def client(base_url: str) -> StellarApiClient:
    return StellarApiClient(base_url=base_url)


@pytest.fixture()
def new_user_credentials() -> Tuple[str, str, str]:
    email = unique_email()
    password = DEFAULT_PASSWORD
    name = DEFAULT_NAME
    return email, password, name


@pytest.fixture()
def registered_user(client: StellarApiClient, new_user_credentials: Tuple[str, str, str]):
    email, password, name = new_user_credentials
    res = client.auth_register(email, password, name)
    if not (res.status_code == 200 and res.json and res.json.get("success") is True):
        raise RuntimeError(f"Precondition failed: could not register user. Status: {res.status_code}, body: {res.text}")
    token = res.json.get("accessToken", "").replace("Bearer ", "") if res.json else ""
    yield {
        "email": email,
        "password": password,
        "name": name,
        "token": token,
    }
    # Teardown: delete the user; enforce cleanup success
    deleted = delete_user_safely(client, email=email, password=password, token=token)
    if not deleted:
        raise RuntimeError("Teardown failed: user was not deleted from the system")


@pytest.fixture()
def logged_in_user(client: StellarApiClient, registered_user: Dict[str, str]):
    email = registered_user["email"]
    password = registered_user["password"]
    res = client.auth_login(email, password)
    if not (res.status_code == 200 and res.json and res.json.get("success") is True):
        raise RuntimeError(f"Precondition failed: could not login user. Status: {res.status_code}, body: {res.text}")
    token = res.json.get("accessToken", "").replace("Bearer ", "") if res.json else ""
    return {
        **registered_user,
        "token": token,
    }


@pytest.fixture(scope="session")
def all_ingredients(client: StellarApiClient) -> List[str]:
    res = client.ingredients_get()
    if not (res.status_code == 200 and res.json and res.json.get("success") is True):
        raise RuntimeError(f"Precondition failed: could not fetch ingredients. Status: {res.status_code}, body: {res.text}")
    data = res.json.get("data", []) if res.json else []
    ids = [item.get("_id") for item in data if item.get("_id")]
    if not ids:
        raise RuntimeError("Precondition failed: no ingredients available from API")
    return ids


@pytest.fixture()
def valid_ingredients_subset(all_ingredients: List[str]) -> List[str]:
    # pick 2-3 random ingredients for an order
    k = 3 if len(all_ingredients) >= 3 else max(1, len(all_ingredients))
    return random.sample(all_ingredients, k)


@pytest.fixture()
def invalid_ingredients() -> List[str]:
    return INVALID_INGREDIENT_HASHES


# Skip only tests marked `live` if API is unavailable

def pytest_collection_modifyitems(config: pytest.Config, items: List[pytest.Item]) -> None:
    live_items = [item for item in items if item.get_closest_marker("live")]
    if not live_items:
        return

    client = StellarApiClient(base_url=get_base_url())
    if not ensure_api_available(client):
        skip_marker = pytest.mark.skip(reason="Stellar Burgers API is not available at the configured base URL")
        for item in live_items:
            item.add_marker(skip_marker)
