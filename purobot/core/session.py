from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any


@dataclass(slots=True)
class Session:
    messages: list[dict[str, Any]] = field(default_factory=list)
    active_command: dict[str, Any] | None = None
    pending_approval: dict[str, Any] | None = None
    state: dict[str, Any] = field(default_factory=dict)

    def last_user_message(self) -> str | None:
        for message in reversed(self.messages):
            if message["role"] == "user":
                return message["content"]
        return None

    def has_recent_tool(self, tool_name: str) -> bool:
        return any(
            message["role"] == "tool" and message.get("name") == tool_name
            for message in self.messages
        )

    def has_recent_browser_action(self, action: str) -> bool:
        for message in reversed(self.messages):
            if message["role"] != "tool" or message.get("name") != "browser":
                continue
            payload = json.loads(message["content"])
            if payload.get("action") == action:
                return True
        return False

    def last_tool_payload(self, tool_name: str) -> dict[str, Any]:
        for message in reversed(self.messages):
            if message["role"] == "tool" and message.get("name") == tool_name:
                return json.loads(message["content"])
        return {}
