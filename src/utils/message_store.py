# message_store.py
# This file handles storing and retrieving custom user message presets.
import json
import os

FILE = "messages.json"

def load_messages():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_messages(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_custom_message(user_id: int) -> str:
    data = load_messages()
    return data.get(str(user_id), "Default spam message")

def set_custom_message(user_id: int, message: str):
    data = load_messages()
    data[str(user_id)] = message
    save_messages(data)
