from __future__ import annotations

import json
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from purobot.core.session import Session

class OpenRouterModel:
    def __init__(self, model_name: str, api_key: str | None, base_url: str) -> None:
        self.model_name = model_name
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def next_action(
        self, session: Session, tool_specs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=build_messages(session),
            tools=tool_specs,
            tool_choice="auto",
        )
        return parse_message(completion.choices[0].message)


def parse_message(message: ChatCompletionMessage) -> dict[str, Any]:
    if getattr(message, "tool_calls", None):
        tool_call = message.tool_calls[0]
        return {
            "type": "tool_call",
            "id": getattr(tool_call, "id", None),
            "name": tool_call.function.name,
            "arguments": json.loads(tool_call.function.arguments or "{}"),
        }
    return {"type": "text", "text": message.content or "No response content."}


def build_messages(session: Session) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": _system_prompt(session)}]
    for message in session.messages:
        if message["role"] == "user":
            messages.append({"role": "user", "content": message["content"]})
            continue
        if message["role"] == "assistant":
            payload: dict[str, Any] = {"role": "assistant", "content": message["content"]}
            if message.get("tool_calls"):
                payload["tool_calls"] = [
                    {
                        "id": tool_call["id"],
                        "type": tool_call["type"],
                        "function": {
                            "name": tool_call["function"]["name"],
                            "arguments": json.dumps(tool_call["function"]["arguments"]),
                        },
                    }
                    for tool_call in message["tool_calls"]
                ]
            messages.append(payload)
            continue
        if message["role"] == "tool":
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": message["tool_call_id"],
                    "content": message["content"],
                }
            )
    return messages


def _system_prompt(session: Session) -> str:
    skill_blocks = "\n\n".join(
        f"[skill:{skill.name}]\n{skill.instructions}" for skill in session.active_skills
    )
    browser_context = json.dumps(session.state.get("browser", {}), indent=2, sort_keys=True)
    return (
        "You are Purobot, a small tool-using assistant. "
        "Use tools when browser interaction is needed. "
        "Do not use the browser for normal knowledge, creative, or conversational requests when you can answer directly from the model. "
        "For example, recipe ideas, coding explanations, brainstorming, summaries, and ordinary advice should usually be answered without the browser. "
        "Only use the browser when the user explicitly asks you to browse, search the web, open a site, use a URL, interact with a website, or when live page interaction is actually necessary. "
        "Only mark `dangerous=true` for irreversible actions like submitting an order. "
        "Be concise. If you have enough information to help without tools, answer directly.\n\n"
        f"Active skills:\n{skill_blocks or '[skill:none]'}\n\n"
        f"Browser state:\n{browser_context}\n\n"
        "Use whatever URLs or sites the user explicitly gives you. "
        "Prefer reading the page before taking blind actions."
    )
