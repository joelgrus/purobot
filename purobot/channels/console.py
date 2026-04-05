from __future__ import annotations

class ConsoleChannel:
    def __init__(self, app) -> None:
        self.app = app

    def run(self) -> None:
        print("Purobot console mode. Type `exit` to quit.")

        while True:
            try:
                text = input("> ").strip()
            except EOFError:
                print()
                break

            if not text:
                continue
            if text.lower() in {"exit", "quit"}:
                break

            for line in self.app.handle_user_message(text):
                print(line)
