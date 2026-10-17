"""Peak API client for solving Cloudflare Turnstile.

Kept free of any browser-use dependency so it can be unit tested and reused
on its own. The HTTP call uses the standard library only.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

DEFAULT_API_URL = "https://api.peak.fo/solve"

# Peak's API sits behind Cloudflare, which blocks the stdlib's default
# "Python-urllib/x.y" User-Agent outright (error code 1010) before the
# request reaches Peak at all. Any normal-looking UA clears it; this one
# just also identifies the client for Peak's own request logs.
USER_AGENT = "browser-use-turnstile/0.1 (+https://github.com/CircuitSavage/browser-use-turnstile)"

# task_type sent to Peak. The proxied task requires sitekey + url + proxy;
# the proxyless task requires only sitekey + url and is solved through
# Peak's own IP pool instead of yours. Verified live against the API:
# a proxied request missing `proxy` fails with "Missing required fields:
# sitekey, url, proxy", and a proxyless request with no `proxy` key solves.
TASK_TURNSTILE = "turnstiletask"
TASK_TURNSTILE_PROXYLESS = "turnstiletaskproxyless"


class PeakError(RuntimeError):
    """Raised when Peak cannot solve the challenge or the call fails."""


def build_solve_payload(
    sitekey: str,
    url: str,
    proxy: Optional[str] = None,
    task_type: Optional[str] = None,
) -> dict:
    """Build the JSON body for POST https://api.peak.fo/solve.

    Picks the proxyless task automatically when no ``proxy`` is given,
    unless ``task_type`` is passed explicitly.
    """
    if task_type is None:
        task_type = TASK_TURNSTILE if proxy else TASK_TURNSTILE_PROXYLESS
    payload = {"task_type": task_type, "sitekey": sitekey, "url": url}
    if proxy:
        payload["proxy"] = proxy
    return payload


class PeakClient:
    """Thin client around the Peak solve endpoint."""

    def __init__(
        self,
        api_key: str,
        api_url: str = DEFAULT_API_URL,
        proxy: Optional[str] = None,
        timeout: float = 180.0,
    ) -> None:
        if not api_key:
            raise PeakError(
                "No Peak API key. Set PEAK_API_KEY (get a free key, 1,000 "
                "solves on the house, at https://peak.fo)."
            )
        self.api_key = api_key
        self.api_url = api_url
        self.proxy = proxy
        self.timeout = timeout

    def _post(self, payload: dict) -> dict:
        """Send the payload to Peak and return the parsed JSON response.

        Isolated so tests can monkeypatch a single method instead of the
        network. Uses only the standard library, so it works the same way
        whether or not an async HTTP client is installed.
        """
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.api_url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # pragma: no cover - network path
            body = exc.read().decode("utf-8", "replace")
        except urllib.error.URLError as exc:  # pragma: no cover - network path
            raise PeakError(f"Peak request failed: {exc}") from exc
        try:
            return json.loads(body)
        except ValueError as exc:  # pragma: no cover - defensive
            raise PeakError(f"Peak returned non-JSON response: {body!r}") from exc

    def solve(
        self,
        sitekey: str,
        url: str,
        proxy: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> str:
        """Solve a Turnstile challenge and return the token string.

        Raises :class:`PeakError` on failure.
        """
        payload = build_solve_payload(
            sitekey, url, proxy=proxy or self.proxy, task_type=task_type
        )
        result = self._post(payload)
        if not result.get("success"):
            raise PeakError(result.get("error") or "Peak solve failed")
        token = (result.get("data") or {}).get("token")
        if not token:
            raise PeakError("Peak response missing data.token")
        return token
