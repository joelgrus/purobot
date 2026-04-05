from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class Settings:
    allow_dangerous_browser_actions: bool = False
    browser_headless: bool = True
    max_history_messages: int = 100
    model_name: str = "google/gemini-3-flash-preview"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    @classmethod
    def from_args(
        cls,
        *,
        allow_dangerous_browser_actions: bool,
        model_name: str | None,
        browser_headless: bool,
    ) -> "Settings":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Set OPENROUTER_API_KEY before running purobot.")
        return cls(
            allow_dangerous_browser_actions=allow_dangerous_browser_actions,
            browser_headless=browser_headless,
            max_history_messages=int(os.environ.get("PUROBOT_MAX_HISTORY_MESSAGES", "100")),
            model_name=model_name
            or os.environ.get("CODBOT_MODEL", "google/gemini-3-flash-preview"),
            openrouter_api_key=api_key,
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID"),
        )
