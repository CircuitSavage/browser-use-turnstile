<div align="center">

# browser-use-turnstile

**Let a browser-use agent solve Cloudflare Turnstile.** One call registers a `solve_cloudflare_turnstile` action on your agent's tools. When the agent lands on a page blocked by a Turnstile widget, it calls the action, which reads the sitekey from the page, gets a token from [Peak](https://peak.fo), and writes the token back into the form.

<p>
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/browser--use-action-000000?style=for-the-badge" alt="browser-use">
  <img src="https://img.shields.io/badge/license-MIT-007EC7?style=for-the-badge" alt="MIT License">
</p>

</div>

---

A browser-use agent clicks the Turnstile checkbox, the widget decides it is not a person, and the run stalls on a form that will not submit. The model cannot fix that by reasoning harder. The token has to be minted outside the browser. This package gives the agent that move as a tool.

The action takes no arguments. The agent does not have to find the sitekey or paste a token. The action does both against the live page.

## Install

```bash
pip install browser-use-turnstile
```

browser-use needs Python 3.11 or newer, so this package does too.

## Use it

```python
from browser_use import Agent, ChatAnthropic, Tools
from browser_use_turnstile import register_turnstile_action

tools = Tools()
register_turnstile_action(tools)  # reads PEAK_API_KEY from the environment

agent = Agent(
    task="Open https://example.com/login, clear any Turnstile challenge, submit the form.",
    llm=ChatAnthropic(model="claude-sonnet-5-5"),
    tools=tools,
)
await agent.run()
```

Pass the key directly with `register_turnstile_action(tools, api_key="pk_...")` if you do not want the environment variable. A runnable version is in [`examples/basic_agent.py`](examples/basic_agent.py).

## What the action does

1. Reads the sitekey from the current page: `[data-sitekey]` first, then the `challenges.cloudflare.com` iframe `src` for widgets rendered through the JS API.
2. Sends the sitekey and the page URL to Peak.
3. Fills every `cf-turnstile-response` field with the token, fires `input` and `change`, and calls the widget's `data-callback` if the page registered one.
4. Tells the agent what happened in one line, so its next step is "click Submit" and not a guess.

Failures come back as an error result the model can read (no sitekey on the page, no balance, bad key) instead of an exception that ends the run.

## Matching the exit IP

Turnstile scores the IP that submits the token. If your browser runs behind a proxy, pass the same one:

```python
register_turnstile_action(tools, proxy="http://user:pass@host:port")
```

Without `proxy`, the solve goes through Peak's own IP pool. That works for most sites and fails on the ones that bind the token to the requesting IP.

## Use the pieces on their own

```python
from browser_use_turnstile import PeakClient, solve_on_page

client = PeakClient("pk_...")
token = client.solve(sitekey="0x4AAAAAAA...", url="https://example.com/login")
```

`solve_on_page(page, url, client)` is the same logic the action runs, for use inside your own custom action.

## Getting a key

The action needs an API key for the solver it calls: [Peak](https://peak.fo). Turnstile solves come back in about a second, you pay only for the ones that land, and the free trial is enough to wire this up and test it.

<div align="center">

For **Cloudflare Turnstile**, **Cloudflare 5s challenge**, **AWS WAF**, and **DataDome**:
<br>
<a href="https://peak.fo/?utm_source=github&utm_medium=repo&utm_campaign=packages&utm_content=browser-use-turnstile"><img src="https://img.shields.io/badge/Get_a_key-Peak-FF6B35?style=for-the-badge" alt="Peak"></a>
<br>
<sub>API-first · <strong>$0.35 – $1.00 / 1K</strong> · volume tiers · pay only on success · <a href="https://peak.fo/?utm_source=github&utm_medium=repo&utm_campaign=packages&utm_content=browser-use-turnstile">peak.fo</a></sub>

</div>

## Related

Other agent and browser wrappers for the same API: [langchain-turnstile](https://github.com/CircuitSavage/langchain-turnstile) · [crewai-turnstile](https://github.com/CircuitSavage/crewai-turnstile) · [playwright-turnstile](https://github.com/CircuitSavage/playwright-turnstile) · [nodriver-turnstile](https://github.com/CircuitSavage/nodriver-turnstile) · [camoufox-turnstile](https://github.com/CircuitSavage/camoufox-turnstile).

## Notes

Use this on sites and accounts you are allowed to automate. Respect each target's Terms of Service and `robots.txt`. This is tooling for legitimate agents, testing, and public-data access. Nothing here helps with credential stuffing or abuse. Not affiliated with Cloudflare or browser-use.

## License

MIT
