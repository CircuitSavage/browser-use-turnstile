<div align="center">

# browser-use-turnstile

**Let a browser-use agent solve Cloudflare Turnstile.** One call registers a `solve_cloudflare_turnstile` action on your agent's tools. When the agent lands on a page blocked by a Turnstile widget, it calls the action, which reads the sitekey from the page, gets a token from [Peak](https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=browser-use-turnstile), and writes the token back into the form.

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

The action needs an API key for the solver it calls: [Peak](https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=browser-use-turnstile). You pay only for the solves that land, and the free trial (1,000 solves, no card) is enough to wire this up and test it. Peak also solves the Cloudflare 5-second challenge (`task_type: "cloudflare5stask"`); this package covers Turnstile.

<div align="center">

<a href="https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=browser-use-turnstile"><img src="https://img.shields.io/badge/Get_a_key-Peak-FF6B35?style=for-the-badge" alt="Peak"></a>
<br>
<sub><strong>$0.90 per 1,000 Turnstile solves</strong>, down to $0.35 at volume · pay only on success · 1,000 free solves · <a href="https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=browser-use-turnstile#pricing">peak.fo</a></sub>

</div>

## Troubleshooting

The failures people report with this package come down to a short list. Each one has a longer write-up on the Peak blog.

- **The agent never calls the action.** The model picks tools from their descriptions and from the task text. Name the challenge in the task ("clear any Turnstile challenge, then submit") the way the example above does, and keep `register_turnstile_action` before `Agent(...)` so the tool is in the list the model sees.
- **`ERROR: no Turnstile sitekey found on this page`.** The action reads the DOM once; it does not wait. The agent called it before the widget rendered, or the site loads the widget from a script the selectors never see. Have the agent wait or scroll and call it again, or pass the key yourself through `solve_on_page(page, url, client, sitekey="0x4AAA...")` from a custom action. [How to find a Cloudflare Turnstile sitekey](https://blog.peak.fo/how-to-find-a-cloudflare-turnstile-sitekey/) covers the DevTools route and the places sites hide it (also on [Hashnode](https://peakfo.hashnode.dev/how-to-find-a-cloudflare-turnstile-sitekey)).
- **"Token solved but the page has no cf-turnstile-response field or data-callback to receive it."** The solve worked. The page renders the widget through the JS API with a callback closure and no hidden input, or it re-rendered the widget and wiped the field. [cf-turnstile-response is empty](https://blog.peak.fo/cf-turnstile-response-empty/) lists the causes in order, and [the cf-turnstile-response token explained](https://blog.peak.fo/the-cf-turnstile-response-token-explained/) covers what the server does with the token once it arrives.
- **The page still answers 403 after the token lands.** That is a different wall. A Turnstile token satisfies a widget on a form. A 403 interstitial wants a `cf_clearance` cookie from the 5-second challenge, which is Peak's `cloudflare5stask`, not this package. [Turnstile token vs cookie](https://blog.peak.fo/cloudflare-turnstile-token-vs-cookie/) explains which one you need, [Cloudflare Turnstile 403](https://blog.peak.fo/cloudflare-turnstile-403-scraper-fix/) walks through the fix, and [the Cloudflare 5-second challenge explained](https://blog.peak.fo/the-cloudflare-5-second-challenge-explained/) covers the cookie side.
- **The widget shows an error code** such as 110200, 300030 or 600010. [Cloudflare Turnstile error codes](https://blog.peak.fo/cloudflare-turnstile-error-codes/) groups them by what failed, from a domain missing on the sitekey's allowlist to a challenge run that died inside the iframe.
- **`ERROR: No Peak API key`.** Set `PEAK_API_KEY` in the environment, or pass `api_key=` to `register_turnstile_action`.

For the bigger picture, including why the `proxy` you pass to Peak should match the browser's egress IP, read [How to solve Cloudflare Turnstile in 2026](https://blog.peak.fo/how-to-solve-cloudflare-turnstile-in-2026-dev-guide/).

## Related

Other agent wrappers for the same API: [langchain-turnstile](https://github.com/CircuitSavage/langchain-turnstile) · [crewai-turnstile](https://github.com/CircuitSavage/crewai-turnstile). Browser wrappers: [playwright-turnstile](https://github.com/CircuitSavage/playwright-turnstile) · [patchright-turnstile](https://github.com/CircuitSavage/patchright-turnstile) · [camoufox-turnstile](https://github.com/CircuitSavage/camoufox-turnstile) · [nodriver-turnstile](https://github.com/CircuitSavage/nodriver-turnstile) · [pydoll-turnstile](https://github.com/CircuitSavage/pydoll-turnstile) · [drissionpage-turnstile](https://github.com/CircuitSavage/drissionpage-turnstile) · [selenium-turnstile](https://github.com/CircuitSavage/selenium-turnstile) · [botasaurus-turnstile](https://github.com/CircuitSavage/botasaurus-turnstile) · [puppeteer-extra-plugin-turnstile](https://github.com/CircuitSavage/puppeteer-extra-plugin-turnstile) · [crawlee-turnstile](https://github.com/CircuitSavage/crawlee-turnstile). Full list in [awesome-turnstile-solvers](https://github.com/CircuitSavage/awesome-turnstile-solvers).

If you want to know what the widget does before it hands out a token, [cloudflare-turnstile-reversed](https://github.com/CircuitSavage/cloudflare-turnstile-reversed) documents the challenge flow, the widget parameters and the fingerprinting it runs.

## Notes

Use this on sites and accounts you are allowed to automate. Respect each target's Terms of Service and `robots.txt`. This is tooling for legitimate agents, testing, and public-data access. Nothing here helps with credential stuffing or abuse. Not affiliated with Cloudflare or browser-use.

## License

MIT
