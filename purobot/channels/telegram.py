from __future__ import annotations

import json
from threading import Event, Thread
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TelegramChannel:
    def __init__(self, app, bot_token: str, allowed_chat_id: str | None = None) -> None:
        self.app = app
        self.bot_token = bot_token
        self.allowed_chat_id = str(allowed_chat_id) if allowed_chat_id else None
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._stop = Event()
        self._thread: Thread | None = None
        self._offset = 0

    def start(self) -> None:
        self._thread = Thread(target=self._poll_loop, name="telegram-channel", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _poll_loop(self) -> None:
        while not self._stop.is_set():
            try:
                payload = self._api_call(
                    "getUpdates",
                    {
                        "offset": self._offset,
                        "timeout": 20,
                        "allowed_updates": json.dumps(["message"]),
                    },
                )
            except (HTTPError, URLError, TimeoutError):
                self._stop.wait(2)
                continue

            for update in payload.get("result", []):
                self._offset = max(self._offset, int(update["update_id"]) + 1)
                message = update.get("message") or {}
                chat = message.get("chat") or {}
                text = (message.get("text") or "").strip()
                if not text:
                    continue

                chat_id = str(chat.get("id"))
                if self.allowed_chat_id and chat_id != self.allowed_chat_id:
                    continue

                label = self._chat_label(chat)
                print(f"\n[telegram:{label}] {text}", flush=True)
                outputs = self.app.handle_user_message(text)
                if outputs:
                    reply = "\n".join(outputs)
                    print(f"[purobot->telegram:{label}] {reply}", flush=True)
                    self._send_message(chat_id, reply)

    def _send_message(self, chat_id: str, text: str) -> None:
        self._api_call(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
            },
        )

    def _api_call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = urlencode(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/{method}",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=25) as response:
            return json.loads(response.read().decode("utf-8"))

    def _chat_label(self, chat: dict[str, Any]) -> str:
        username = chat.get("username")
        if username:
            return username
        first_name = chat.get("first_name")
        if first_name:
            return first_name
        return str(chat.get("id"))
