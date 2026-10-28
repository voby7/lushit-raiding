# access_manager.py
# Access control, authorization, allow/block lists, global lock, cooldowns, audit logging.
from __future__ import annotations
import json
import csv
import os
from pathlib import Path
from typing import Optional
import datetime
import logging

STATE_PATH = Path("access_state.json")
AUDIT_PATH = Path("access_audit.csv")

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level)
logger = logging.getLogger("access")


def _default_state():
    return {
        "owner_id": os.environ.get("BOT_OWNER_ID"),
        "global_locked": False,
        "users": {"allowlist": [], "blocklist": []},
        "command_cooldowns": {},  # { "user:command": timestamp_ms }
        "_tokens": {},
        "command_count": 0,
        "version": os.environ.get("BOT_VERSION", "unknown"),
    }


class AccessManager:
    def __init__(self) -> None:
        self.state = self._load_state()
        if not self.state.get("owner_id"):
            self.state["owner_id"] = os.environ.get("BOT_OWNER_ID")

        self.start_time = datetime.datetime.now()   # uptime tracking

        self._save_state()
        # ensure audit CSV header
        if not AUDIT_PATH.exists():
            with AUDIT_PATH.open("w", newline="", encoding="utf8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp_iso", "actor_id", "actor_tag", "guild_id", "channel_id", "action", "target", "result", "note"])

    def increment_command_count(self):
        self.state["command_count"] = int(self.state.get("command_count", 0)) + 1
        self._save_state()

    def get_command_count(self) -> int:
        return int(self.state.get("command_count", 0))

    def get_uptime(self) -> str:
        delta = datetime.datetime.now() - self.start_time
        return str(delta).split('.')[0]

    def get_version(self) -> str:
        return self.state.get("version", "unknown")

    def _load_state(self) -> dict:
        try:
            with STATE_PATH.open("r", encoding="utf8") as f:
                return json.load(f)
        except Exception:
            return _default_state()

    def _save_state(self) -> None:
        with STATE_PATH.open("w", encoding="utf8") as f:
            json.dump(self.state, f, indent=2)

    # owner check
    def is_owner(self, user_id: int | str) -> bool:
        return str(user_id) == str(self.state.get("owner_id"))

    # allow/block management
    def is_user_allowed(self, user_id: int | str) -> bool:
        logging.debug(f"Checking if user {user_id} is allowed.")
        return str(user_id) in [str(x) for x in self.state["users"]["allowlist"]]

    def is_user_blocked(self, user_id: int | str) -> bool:
        logging.debug(f"Checking if user {user_id} is blocked.")
        return str(user_id) in [str(x) for x in self.state["users"]["blocklist"]]

    def allow_user(self, user_id: int | str, actor: Optional[dict] = None) -> None:
        uid = str(user_id)
        if uid not in self.state["users"]["allowlist"]:
            self.state["users"]["allowlist"].append(uid)
        # ensure not blocked
        self.state["users"]["blocklist"] = [u for u in self.state["users"]["blocklist"] if u != uid]
        self._save_state()
        self.audit(actor or {"id": self.state["owner_id"], "tag": "OWNER"}, "authorize", uid, "ok")

    def remove_allowed_user(self, user_id: int | str, actor: Optional[dict] = None) -> None:
        uid = str(user_id)
        self.state["users"]["allowlist"] = [u for u in self.state["users"]["allowlist"] if u != uid]
        self._save_state()
        self.audit(actor or {"id": self.state["owner_id"], "tag": "OWNER"}, "unauthorize", uid, "ok")
        logging.debug(f"Removed user {user_id} from allowlist.")

    def block_user(self, user_id: int | str, actor: Optional[dict] = None) -> None:
        uid = str(user_id)
        if uid not in self.state["users"]["blocklist"]:
            self.state["users"]["blocklist"].append(uid)
        self.state["users"]["allowlist"] = [u for u in self.state["users"]["allowlist"] if u != uid]
        self._save_state()
        self.audit(actor or {"id": self.state["owner_id"], "tag": "OWNER"}, "block", uid, "ok")
        logging.debug(f"Blocked user {user_id}.")

    def unblock_user(self, user_id: int | str, actor: Optional[dict] = None) -> None:
        uid = str(user_id)
        self.state["users"]["blocklist"] = [u for u in self.state["users"]["blocklist"] if u != uid]
        self._save_state()
        self.audit(actor or {"id": self.state["owner_id"], "tag": "OWNER"}, "unblock", uid, "ok")
        logging.debug(f"Unblocked user {user_id}.")

    # global lock
    def set_global_lock(self, value: bool, actor: Optional[dict] = None) -> None:
        self.state["global_locked"] = bool(value)
        self._save_state()
        self.audit(actor or {"id": self.state["owner_id"], "tag": "OWNER"}, "set_global_lock", str(self.state["global_locked"]), "ok")
        logging.debug(f"Global lock set to {value}.")

    # cooldowns
    def check_cooldown(self, user_id: int | str, command: str, seconds: float = 3.0) -> dict:
        import time
        key = f"{user_id}:{command}"
        now_ms = int(time.time() * 1000)
        last = int(self.state.get("command_cooldowns", {}).get(key, 0))
        wait_ms = int(seconds * 1000) - (now_ms - last)
        if wait_ms > 0:
            logging.debug(f"Cooldown active for {key}. Waiting {wait_ms}ms.")
            return {"ok": False, "wait": round(wait_ms / 1000, 1)}
        # set last
        logging.debug(f"Setting cooldown for {key} to {now_ms}.")
        self.state.setdefault("command_cooldowns", {})[key] = now_ms
        self._save_state()
        logging.debug(f"Cooldown set for {key}.")
        return {"ok": True}

    # audit
    def audit(self, actor: dict, action: str, target: str = "", result: str = "ok", note: str = "", guild_id: str = "", channel_id: str = "") -> None:
        from datetime import datetime
        row = [
            datetime.utcnow().isoformat() + "Z",
            str(actor.get("id", "")),
            str(actor.get("tag", "")),
            str(guild_id or ""),
            str(channel_id or ""),
            action,
            target,
            result,
            note,
        ]
        with AUDIT_PATH.open("a", newline="", encoding="utf8") as f:
            writer = csv.writer(f)
            writer.writerow(row)
            logging.debug(f"Audit log entry added: {row}")

    # guard to call before executing a protected command
    # opts: { action: 'name', cooldown_seconds: n, allow_during_lock: bool }
    async def guard(self, interaction, opts: Optional[dict] = None) -> dict:
        opts = opts or {}
        actor_id = str(interaction.user.id)
        actor_tag = f"{interaction.user.name}#{interaction.user.discriminator}"
        guild_id = str(interaction.guild.id) if interaction.guild else ""
        channel_id = str(interaction.channel.id) if interaction.channel else ""

        if self.is_owner(actor_id):
            self.audit({"id": actor_id, "tag": actor_tag}, opts.get("action", "guard"), "", "allowed_owner", guild_id, channel_id)
            return {"ok": True}

        if self.state.get("global_locked") and not opts.get("allow_during_lock"):
            self.audit({"id": actor_id, "tag": actor_tag}, opts.get("action", "guard"), "", "denied_global_lock", guild_id, channel_id)
            return {"ok": False, "reason": "global_locked"}

        if self.is_user_blocked(actor_id):
            self.audit({"id": actor_id, "tag": actor_tag}, opts.get("action", "guard"), "", "denied_blocklist", guild_id, channel_id)
            return {"ok": False, "reason": "user_blocked"}

        # Role-based authorization check
        auth_guild_id = os.environ.get("AUTH_GUILD_ID")
        auth_role_id = os.environ.get("AUTH_ROLE_ID")

        is_authorized = False
        if auth_guild_id and auth_role_id:
            # Find the member in the specific guild
            guild = interaction.client.get_guild(int(auth_guild_id))
            if guild:
                member = guild.get_member(interaction.user.id)
                if not member:
                    try:
                        member = await guild.fetch_member(interaction.user.id)
                    except:
                        member = None

                if member and any(str(role.id) == str(auth_role_id) for role in member.roles):
                    is_authorized = True

        # Fallback to manual allowlist if role check fails or is not configured
        if not is_authorized and self.is_user_allowed(actor_id):
            is_authorized = True

        if not is_authorized:
            self.audit({"id": actor_id, "tag": actor_tag}, opts.get("action", "guard"), "", "denied_not_authorized", guild_id, channel_id)
            return {"ok": False, "reason": "not_authorized"}

        if opts.get("cooldown_seconds"):
            cd = self.check_cooldown(actor_id, opts.get("action", "generic"), opts.get("cooldown_seconds"))
            if not cd.get("ok"):
                self.audit({"id": actor_id, "tag": actor_tag}, opts.get("action", "guard"), "", "denied_rate_limit", guild_id, channel_id)
                return {"ok": False, "reason": "rate_limited", "wait": cd.get("wait")}

        self.audit({"id": actor_id, "tag": actor_tag}, opts.get("action", "guard"), "", "allowed", guild_id, channel_id)
        return {"ok": True}

    # helpers
    def list_authorized(self) -> list:
        return list(self.state["users"]["allowlist"])

    def list_blocked(self) -> list:
        return list(self.state["users"]["blocklist"])
