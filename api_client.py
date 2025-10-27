from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import requests
from urls import get_base_url


@dataclass
class ApiResponse:
    status_code: int
    json: Dict[str, Any] | None
    text: str
    headers: Dict[str, str]


class StellarApiClient:
    def __init__(self, base_url: str | None = None, session: Optional[requests.Session] = None) -> None:
        self.base_url = (base_url or get_base_url()).rstrip("/")
        self.session = session or requests.Session()
        self._json_headers = {"Content-Type": "application/json"}

    def _request(
        self,
        method: str,
        path: str,
        token: Optional[str] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> ApiResponse:
        url = f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        headers = dict(self._json_headers)
        if token:
            headers["Authorization"] = f"Bearer {token}"

        resp = self.session.request(method=method, url=url, headers=headers, json=json, params=params, timeout=20)
        text = resp.text
        try:
            payload: Dict[str, Any] | None = resp.json()
        except Exception:
            payload = None
        return ApiResponse(status_code=resp.status_code, json=payload, text=text, headers=dict(resp.headers))

    def ingredients_get(self) -> ApiResponse:
        return self._request("GET", "/ingredients")

    def auth_register(self, email: str, password: str, name: str) -> ApiResponse:
        return self._request("POST", "/auth/register", json={"email": email, "password": password, "name": name})

    def auth_login(self, email: str, password: str) -> ApiResponse:
        return self._request("POST", "/auth/login", json={"email": email, "password": password})

    def auth_user_patch(self, token: str, data: Dict[str, Any]) -> ApiResponse:
        return self._request("PATCH", "/auth/user", token=token, json=data)

    def auth_user_delete(self, token: str) -> ApiResponse:
        return self._request("DELETE", "/auth/user", token=token)

    def orders_create(self, ingredients: Iterable[str], token: Optional[str] = None) -> ApiResponse:
        return self._request("POST", "/orders", token=token, json={"ingredients": list(ingredients)})

    def orders_get_user(self, token: str) -> ApiResponse:
        return self._request("GET", "/orders", token=token)


def ensure_api_available(client: StellarApiClient) -> bool:
    try:
        res = client.ingredients_get()
        return res.status_code == 200 and bool(res.json and res.json.get("success"))
    except Exception:
        return False
