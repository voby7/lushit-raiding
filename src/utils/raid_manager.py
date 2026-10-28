# raid_manager.py
# Records message IDs sent by the bot per guild/channel so they can be cleaned by /reset

from pathlib import Path
import json
from typing import Dict, List

STATE_FILE = Path("sent_messages_state.json")


def _load():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf8"))
    except Exception:
        return {}  # { guild_id: { channel_id: [msg_id, ...] } }


def _save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf8")


class RaidManager:
    def __init__(self):
        self._data = _load()

    def record_message(self, guild_id: str, channel_id: str, message_id: int):
        g = self._data.setdefault(str(guild_id), {})
        c = g.setdefault(str(channel_id), [])
        c.append(int(message_id))
        _save(self._data)

    def list_messages_for_guild(self, guild_id: str) -> Dict[str, List[int]]:
        return self._data.get(str(guild_id), {})

    def pop_messages_for_guild(self, guild_id: str) -> Dict[str, List[int]]:
        return self._data.pop(str(guild_id), {})

    def add_many(self, guild_id: str, channel_id: str, ids):
        g = self._data.setdefault(str(guild_id), {})
        c = g.setdefault(str(channel_id), [])
        c.extend([int(x) for x in ids])
        _save(self._data)
