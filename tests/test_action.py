"""Unit tests. Peak's HTTP call and the browser page are mocked, so no key,
browser, or LLM is needed.  Run: python -m pytest tests/ -v
"""

from __future__ import annotations

import asyncio
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from browser_use_turnstile import (  # noqa: E402
    FIND_SITEKEY_JS,
    INJECT_TOKEN_JS,
    PeakClient,
    PeakError,
    build_solve_payload,
    solve_on_page,
)

SITEKEY = "1x00000000000000000000AA"
URL = "https://protected.example/login"


class FakePage:
    def __init__(self, sitekey=SITEKEY, placed="true"):
        self.sitekey, self.placed, self.calls = sitekey, placed, []

    async def evaluate(self, js, *args):
        self.calls.append((js, args))
        return self.sitekey if not args else self.placed


def run(coro):
    return asyncio.run(coro)


def ok(*_a, **_k):
    return {"success": True, "data": {"token": "TOK.EN"}}


class SolveOnPageTests(unittest.TestCase):
    def test_happy_path_injects_token(self):
        page, client = FakePage(), PeakClient("pk_test")
        with mock.patch.object(PeakClient, "_post", side_effect=ok) as post:
            msg = run(solve_on_page(page, URL, client))
        self.assertIn("Solved", msg)
        self.assertEqual(post.call_args.args[0]["sitekey"], SITEKEY)
        self.assertEqual(post.call_args.args[0]["task_type"], "turnstiletaskproxyless")
        self.assertEqual(page.calls[-1], (INJECT_TOKEN_JS, ("TOK.EN",)))

    def test_no_sitekey_returns_error_text(self):
        msg = run(solve_on_page(FakePage(sitekey=""), URL, PeakClient("pk_test")))
        self.assertTrue(msg.startswith("ERROR"))

    def test_peak_failure_returns_error_text(self):
        bad = lambda *a, **k: {"success": False, "error": "no balance"}
        with mock.patch.object(PeakClient, "_post", side_effect=bad):
            msg = run(solve_on_page(FakePage(), URL, PeakClient("pk_test")))
        self.assertEqual(msg, "ERROR: no balance")

    def test_token_with_nowhere_to_go_is_reported(self):
        with mock.patch.object(PeakClient, "_post", side_effect=ok):
            msg = run(solve_on_page(FakePage(placed="false"), URL, PeakClient("pk_test")))
        self.assertIn("no cf-turnstile-response", msg)

    def test_proxy_switches_to_proxied_task(self):
        p = build_solve_payload(SITEKEY, URL, proxy="http://u:p@1.2.3.4:80")
        self.assertEqual(p["task_type"], "turnstiletask")

    def test_missing_key_raises(self):
        with self.assertRaises(PeakError):
            PeakClient("")

    def test_js_snippets_are_arrow_functions(self):
        for js in (FIND_SITEKEY_JS, INJECT_TOKEN_JS):
            self.assertTrue(js.startswith("(") and "=>" in js)


class RegisterTests(unittest.TestCase):
    def test_registers_action(self):
        from browser_use import Tools
        from browser_use_turnstile import register_turnstile_action

        tools = Tools()
        register_turnstile_action(tools, api_key="pk_test")
        self.assertIn("solve_cloudflare_turnstile", tools.registry.registry.actions)


if __name__ == "__main__":
    unittest.main()
