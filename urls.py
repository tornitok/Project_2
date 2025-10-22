from __future__ import annotations

import os

DEFAULT_BASE_URL = "https://stellarburgers.education-services.ru/api"


def get_base_url() -> str:
    """Return configured base URL for the Stellar Burgers API.

    Respects STELLAR_BASE_URL env var and falls back to DEFAULT_BASE_URL.
    Trailing slash is stripped to keep URLs consistent.
    """
    return os.getenv("STELLAR_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

