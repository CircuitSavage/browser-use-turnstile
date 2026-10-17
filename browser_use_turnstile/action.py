"""A browser-use action that solves Cloudflare Turnstile through Peak.

Register it on your agent's tools and the LLM can call
``solve_cloudflare_turnstile`` when a page is blocked by a Turnstile
widget. The action reads the sitekey off the live page, asks Peak for a
token, and writes the token back into the page, so the agent's next step
(click Submit) works.
"""

import asyncio
import os
from typing import Any, Optional

from .inject import FIND_SITEKEY_JS, INJECT_TOKEN_JS
from .peak import DEFAULT_API_URL, PeakClient, PeakError

__all__ = ["register_turnstile_action", "solve_on_page"]

DESCRIPTION = (
    "Solve the Cloudflare Turnstile widget on the current page. Use it when "
    "the page shows a Turnstile challenge ('Verify you are human' checkbox, "
    "or a form that will not submit) and clicking the widget does not clear "
    "it. Takes no arguments: it reads the sitekey from the page and puts the "
    "solved token back. Call it once, then continue with the task."
)


async def solve_on_page(
    page: Any,
    page_url: str,
    client: PeakClient,
    sitekey: Optional[str] = None,
) -> str:
    """Find the sitekey, solve it with Peak, inject the token. Returns a status line.

    ``page`` is browser-use's actor ``Page`` (anything with an async
    ``evaluate(js, *args)`` works). Errors come back as ``"ERROR: ..."``
    text so the agent can read them and react.
    """
    if not sitekey:
        sitekey = (await page.evaluate(FIND_SITEKEY_JS) or "").strip()
    if not sitekey:
        return "ERROR: no Turnstile sitekey found on this page"
    try:
        token = await asyncio.get_running_loop().run_in_executor(
            None, lambda: client.solve(sitekey, page_url)
        )
    except PeakError as exc:
        return f"ERROR: {exc}"
    placed = await page.evaluate(INJECT_TOKEN_JS, token)
    if str(placed).lower() != "true":
        return (
            "Token solved but the page has no cf-turnstile-response field or "
            "data-callback to receive it. Check that the widget is on this page."
        )
    return f"Solved Cloudflare Turnstile (sitekey {sitekey}); token placed in the page."


def register_turnstile_action(
    tools: Any,
    api_key: Optional[str] = None,
    api_url: str = DEFAULT_API_URL,
    proxy: Optional[str] = None,
) -> PeakClient:
    """Add ``solve_cloudflare_turnstile`` to a browser-use ``Tools`` object.

        from browser_use import Agent, Tools
        from browser_use_turnstile import register_turnstile_action

        tools = Tools()
        register_turnstile_action(tools)           # reads PEAK_API_KEY
        agent = Agent(task=..., llm=llm, tools=tools)

    Pass ``proxy`` (``http://user:pass@host:port``) when the browser runs
    behind a proxy, so the token is solved from the same exit IP.
    """
    # Real (non-string) annotations are required: browser-use type-checks the
    # injected browser_session argument, so no `from __future__ import annotations`.
    from browser_use import ActionResult, BrowserSession
    from browser_use.tools.views import NoParamsAction

    client = PeakClient(
        api_key or os.environ.get("PEAK_API_KEY", ""), api_url=api_url, proxy=proxy
    )

    @tools.action(DESCRIPTION)
    async def solve_cloudflare_turnstile(_: NoParamsAction, browser_session: BrowserSession) -> ActionResult:
        page = await browser_session.must_get_current_page()
        url = await browser_session.get_current_page_url()
        message = await solve_on_page(page, url, client)
        if message.startswith("ERROR"):
            return ActionResult(error=message)
        return ActionResult(extracted_content=message, long_term_memory=message)

    return client
