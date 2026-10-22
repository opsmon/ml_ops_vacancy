"""Sequential (concurrency=1), budgeted official API client. Never log response bodies."""

import os
import random
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx


class CollectionError(RuntimeError):
    pass


class AccessFailure(CollectionError):
    pass


class Unavailable(CollectionError):
    pass


class HHClient:
    def __init__(self, token=None, user_agent=None, budget=None, transport=None, sleep=time.sleep):
        token = token or os.environ.get("HH_TOKEN", "")
        user_agent = user_agent or os.environ.get("HH_USER_AGENT", "")
        if not token or "@" not in user_agent or "example." in user_agent:
            raise AccessFailure("Configure HH_TOKEN and HH_USER_AGENT with a real developer contact")
        self.client = httpx.Client(
            base_url="https://api.hh.ru",
            timeout=float(os.getenv("HH_TIMEOUT", "25")),
            headers={"Authorization": f"Bearer {token}", "HH-User-Agent": user_agent},
            transport=transport,
            follow_redirects=False,
        )
        self.budget = budget if budget is not None else int(os.getenv("HH_REQUEST_BUDGET", "800"))
        self.retries = max(0, min(5, int(os.getenv("HH_RETRIES", "3"))))
        self.count = 0
        self.sleep = sleep

    def close(self):
        self.client.close()

    def get(self, path, params=None):
        if not path.startswith("/") or path.startswith("//") or ":" in path:
            raise CollectionError("Only relative official API endpoints are allowed")
        for attempt in range(self.retries + 1):
            if self.count >= self.budget:
                raise CollectionError("API request budget exhausted")
            self.count += 1
            try:
                response = self.client.get(path, params=params)
            except httpx.TransportError:
                if attempt == self.retries:
                    raise CollectionError("API transport failed") from None
                self.sleep(min(30, 2**attempt) + random.uniform(0, 1))
                continue
            try:
                body = response.json()
            except ValueError:
                body = {}
            # Do not propagate source error strings, CAPTCHA URLs or tokens.
            if isinstance(body, dict) and "captcha" in str(body.get("errors", "")).lower():
                raise AccessFailure("CAPTCHA challenge: stop collection and review application access")
            if response.status_code in (401, 403):
                raise AccessFailure("Authentication/authorization failed: review token and app permissions")
            if response.status_code in (404, 410):
                raise Unavailable("Vacancy inaccessible; not proof of archival")
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == self.retries:
                    raise CollectionError(f"API retries exhausted (HTTP {response.status_code})")
                delay = min(30, 2**attempt) + random.uniform(0, 1)
                retry = response.headers.get("Retry-After")
                if retry:
                    try:
                        delay = max(delay, float(retry))
                    except ValueError:
                        try:
                            delay = max(
                                delay, (parsedate_to_datetime(retry) - datetime.now(UTC)).total_seconds()
                            )
                        except (ValueError, TypeError):
                            pass
                if delay > 120:
                    raise CollectionError("Retry-After exceeds run wait budget; retry in a later run")
                self.sleep(delay)
                continue
            if not response.is_success or not isinstance(body, (dict, list)):
                raise CollectionError(f"API response rejected (HTTP {response.status_code})")
            return body
        raise CollectionError("API retry policy exhausted")
