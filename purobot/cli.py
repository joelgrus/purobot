from __future__ import annotations

import argparse

from dotenv import load_dotenv

from purobot.app import App
from purobot.channels.console import ConsoleChannel
from purobot.channels.telegram import TelegramChannel
from purobot.config import Settings

load_dotenv()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Purobot CLI")
    parser.add_argument(
        "--allow-dangerous-browser-actions",
        action="store_true",
        help="Allow dangerous browser actions after explicit approval.",
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Run Playwright in headful mode so you can watch the browser.",
    )
    parser.add_argument(
        "--model",
        help="Model name for the selected backend. For OpenRouter this is the routed model id.",
    )
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Poll Telegram on this laptop using TELEGRAM_BOT_TOKEN.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = Settings.from_args(
        allow_dangerous_browser_actions=args.allow_dangerous_browser_actions,
        model_name=args.model,
        browser_headless=not args.show_browser,
    )
    app = App.from_settings(settings)

    telegram: TelegramChannel | None = None
    if args.telegram:
        if not settings.telegram_bot_token:
            raise RuntimeError("Set TELEGRAM_BOT_TOKEN before using --telegram.")
        telegram = TelegramChannel(
            app,
            bot_token=settings.telegram_bot_token,
            allowed_chat_id=settings.telegram_chat_id,
        )
        telegram.start()
        print("Telegram polling enabled.")

    try:
        channel = ConsoleChannel(app)
        channel.run()
    finally:
        if telegram is not None:
            telegram.stop()


if __name__ == "__main__":
    main()
