"""A browser-use agent that can clear Cloudflare Turnstile.

    pip install browser-use-turnstile
    export PEAK_API_KEY=pk_...
    python examples/basic_agent.py
"""

import asyncio

from browser_use import Agent, ChatAnthropic, Tools

from browser_use_turnstile import register_turnstile_action


async def main() -> None:
    tools = Tools()
    register_turnstile_action(tools)  # reads PEAK_API_KEY

    agent = Agent(
        task=(
            "Open https://example.com/login. If a Cloudflare Turnstile "
            "challenge blocks the form, solve it, then submit the form and "
            "report the page title."
        ),
        llm=ChatAnthropic(model="claude-sonnet-5-5"),
        tools=tools,
    )
    await agent.run()


asyncio.run(main())
