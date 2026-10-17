"""JS that runs on the live page: find the Turnstile sitekey, place a token.

Both snippets are arrow functions, the format browser-use's
``Page.evaluate`` requires.
"""

from __future__ import annotations

# Returns the first Turnstile sitekey on the page, or "" if none. Checks the
# explicit [data-sitekey] attribute first, then the challenges.cloudflare.com
# iframe src, which carries the key for widgets rendered through the JS API.
FIND_SITEKEY_JS = r"""() => {
  var el = document.querySelector('.cf-turnstile[data-sitekey], [data-sitekey]');
  if (el && el.getAttribute('data-sitekey')) return el.getAttribute('data-sitekey');
  var frames = document.querySelectorAll('iframe[src*="challenges.cloudflare.com"]');
  for (var i = 0; i < frames.length; i++) {
    var m = frames[i].src.match(/\/(0x[0-9A-Za-z_-]+)\//);
    if (m) return m[1];
  }
  return "";
}"""

# Fills every cf-turnstile-response field, fires input/change, and calls the
# widget's data-callback if the page registered one. Returns true if it
# found somewhere to put the token.
INJECT_TOKEN_JS = r"""(token) => {
  var fields = document.querySelectorAll(
    'input[name="cf-turnstile-response"], textarea[name="cf-turnstile-response"]'
  );
  fields.forEach(function (f) {
    f.value = token;
    f.dispatchEvent(new Event('input', { bubbles: true }));
    f.dispatchEvent(new Event('change', { bubbles: true }));
  });
  var called = false;
  document.querySelectorAll('[data-callback]').forEach(function (w) {
    var name = w.getAttribute('data-callback');
    if (name && typeof window[name] === 'function') {
      window[name](token);
      called = true;
    }
  });
  return fields.length > 0 || called;
}"""
