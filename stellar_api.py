from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import requests

try:
    import allure  # type: ignore
except Exception:  # pragma: no cover - allure is optional at runtime
    class DummyAllure:
        def step(self, name: str):
            from contextlib import contextmanager

            @contextmanager
            def _cm():
                yield

            return _cm()

        def attach(self, body: str, name: str, attachment_type: Any | None = None):
            return None

    allure = DummyAllure()  # type: ignore


DEFAULT_BASE_URL = os.getenv("STELLAR_BASE_URL", "https://stellarburgers.nomoreparties.site/api")


@dataclass
class ApiResponse:
    status_code: int
    json: Dict[str, Any] | None
    text: str
    headers: Dict[str, str]


class StellarApiClient:
    def __init__(self, base_url: str | None = None, session: Optional[requests.Session] = None) -> None:
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.session = session or requests.Session()
        # Default headers used for JSON APIs
        self._json_headers = {"Content-Type": "application/json"}

    # Low-level request wrapper with Allure attachments
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

        with allure.step(f"{method} {url}"):
            if json is not None:
                try:
                    import json as _json
                    allure.attach(
                        _json.dumps(json, ensure_ascii=False, indent=2),
                        name="request.json",
                    )
                except Exception:
                    pass
            if params:
                try:
                    import json as _json
                    allure.attach(
                        _json.dumps(params, ensure_ascii=False, indent=2),
                        name="request.params",
                    )
                except Exception:
                    pass

            resp = self.session.request(method=method, url=url, headers=headers, json=json, params=params, timeout=20)
            text = resp.text
            try:
                payload = resp.json()
            except Exception:
                payload = None

            try:
                import json as _json
                allure.attach(text if not payload else _json.dumps(payload, ensure_ascii=False, indent=2), name="response")
            except Exception:
                pass

            return ApiResponse(status_code=resp.status_code, json=payload, text=text, headers=dict(resp.headers))

    # Convenience high-level calls
    def ingredients_get(self) -> ApiResponse:
        return self._request("GET", "/ingredients")

    def auth_register(self, email: str, password: str, name: str) -> ApiResponse:
        return self._request("POST", "/auth/register", json={"email": email, "password": password, "name": name})

    def auth_login(self, email: str, password: str) -> ApiResponse:
        return self._request("POST", "/auth/login", json={"email": email, "password": password})

    def auth_user_patch(self, token: str, data: Dict[str, Any]) -> ApiResponse:
        return self._request("PATCH", "/auth/user", token=token, json=data)

    def auth_user_delete(self, token: str) -> ApiResponse:
        # Not officially documented everywhere; attempt for cleanup if supported
        return self._request("DELETE", "/auth/user", token=token)

    def orders_create(self, ingredients: Iterable[str], token: Optional[str] = None) -> ApiResponse:
        return self._request("POST", "/orders", token=token, json={"ingredients": list(ingredients)})

    def orders_get_user(self, token: str) -> ApiResponse:
        return self._request("GET", "/orders", token=token)


# Utilities

def unique_email(domain: str = "example.com") -> str:
    return f"user_{uuid.uuid4().hex[:12]}@{domain}"


def ensure_api_available(client: StellarApiClient) -> bool:
    try:
        res = client.ingredients_get()
        return res.status_code == 200 and bool(res.json and res.json.get("success"))
    except Exception:
        return False

