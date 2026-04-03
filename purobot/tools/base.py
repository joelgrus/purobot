from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Protocol


@dataclass(slots=True)
class ToolResult:
    summary: str
    data: dict[str, Any]

    def render(self) -> str:
        return json.dumps(self.data)


class Tool(Protocol):
    name: str

    def run(self, arguments: dict[str, Any], session) -> ToolResult: ...

    def tool_spec(self) -> dict[str, Any]: ...

    def needs_approval(self, arguments: dict[str, Any]) -> bool: ...
