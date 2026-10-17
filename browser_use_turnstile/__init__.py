"""browser-use-turnstile: a browser-use action for solving Cloudflare Turnstile via Peak.

    from browser_use import Agent, Tools
    from browser_use_turnstile import register_turnstile_action

    tools = Tools()
    register_turnstile_action(tools)  # reads PEAK_API_KEY
"""

from __future__ import annotations

from .action import register_turnstile_action, solve_on_page
from .inject import FIND_SITEKEY_JS, INJECT_TOKEN_JS
from .peak import PeakClient, PeakError, build_solve_payload

__version__ = "0.1.0"

__all__ = [
    "register_turnstile_action",
    "solve_on_page",
    "PeakClient",
    "PeakError",
    "build_solve_payload",
    "FIND_SITEKEY_JS",
    "INJECT_TOKEN_JS",
    "__version__",
]
