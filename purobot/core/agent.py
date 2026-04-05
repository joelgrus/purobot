from __future__ import annotations

from typing import Any

from purobot.core.model import OpenRouterModel
from purobot.core.session import Session
from purobot.tools.base import Tool


class Agent:
    def __init__(
        self,
        model: OpenRouterModel,
        tools: list[Tool],
    ) -> None:
        self.model = model
        self.tools_by_name = {tool.name: tool for tool in tools}

    def handle_user_message(self, session: Session, text: str) -> list[str]:
        session.messages.append({"role": "user", "content": text})
        session.prune_history()

        if session.pending_approval:
            return self._handle_approval_response(session, text)

        outputs: list[str] = []
        for _ in range(100):
            response = self.model.next_action(
                session,
                [tool.tool_spec() for tool in self.tools_by_name.values()],
            )
            if response["type"] == "text":
                session.messages.append({"role": "assistant", "content": response["text"]})
                session.prune_history()
                outputs.append(response["text"])
                return outputs

            if response["type"] == "tool_call":
                tool_call_id = response.get("id") or f"{response['name']}-call"
                session.messages.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": response["name"],
                                    "arguments": response["arguments"],
                                },
                            }
                        ],
                    }
                )
                session.prune_history()
                tool = self.tools_by_name[response["name"]]
                if tool.needs_approval(response["arguments"]):
                    response["id"] = tool_call_id
                    session.pending_approval = response
                    prompt = self._approval_prompt(response)
                    session.messages.append({"role": "assistant", "content": prompt})
                    session.prune_history()
                    outputs.append(prompt)
                    return outputs

                result = tool.run(response["arguments"], session)
                session.messages.append(
                    {
                        "role": "tool",
                        "name": tool.name,
                        "tool_call_id": tool_call_id,
                        "content": result.render(),
                    }
                )
                session.prune_history()
                outputs.append(f"[tool:{tool.name}] {result.summary}")
                continue

        message = "Stopped after too many tool steps."
        session.messages.append({"role": "assistant", "content": message})
        session.prune_history()
        outputs.append(message)
        return outputs

    def _handle_approval_response(self, session: Session, text: str) -> list[str]:
        normalized = text.strip().lower()
        pending = session.pending_approval
        if pending is None:
            return []

        if normalized not in {"approve", "reject"}:
            reminder = "Pending approval. Reply with `approve` or `reject`."
            session.messages.append({"role": "assistant", "content": reminder})
            session.prune_history()
            return [reminder]

        if normalized == "reject":
            session.pending_approval = None
            denied = f"Cancelled `{pending['name']}`."
            session.messages.append({"role": "assistant", "content": denied})
            session.prune_history()
            return [denied]

        tool = self.tools_by_name[pending["name"]]
        result = tool.run(pending["arguments"], session)
        session.pending_approval = None
        tool_call_id = pending.get("id") or f"{pending['name']}-call"
        session.messages.append(
            {
                "role": "tool",
                "name": tool.name,
                "tool_call_id": tool_call_id,
                "content": result.render(),
            }
        )
        session.prune_history()
        final = f"Approved `{tool.name}`. {result.summary}"
        session.messages.append({"role": "assistant", "content": final})
        session.prune_history()
        return [final]

    def _approval_prompt(self, response: dict[str, Any]) -> str:
        if response["name"] != "browser":
            return f"Approve `{response['name']}`? Reply `approve` or `reject`."

        tool = self.tools_by_name["browser"]
        arguments = tool._normalize_arguments(response["arguments"])
        action = arguments.get("action")
        if action == "open":
            target = arguments.get("url", "a URL")
            return f"Approve opening `{target}`? Reply `approve` or `reject`."
        if action == "click":
            target = arguments.get("selector", "a page element")
            return f"Approve clicking `{target}`? Reply `approve` or `reject`."
        if action == "type":
            target = arguments.get("selector", "a field")
            return f"Approve typing into `{target}`? Reply `approve` or `reject`."
        if action == "read":
            target = arguments.get("selector") or "the current page"
            return f"Approve reading `{target}`? Reply `approve` or `reject`."
        return "Approve this browser action? Reply `approve` or `reject`."
