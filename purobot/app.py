from __future__ import annotations

from threading import Lock

from purobot.commands.loader import CommandLoader
from purobot.core.agent import Agent
from purobot.core.model import OpenRouterModel
from purobot.core.session import Session
from purobot.tools.base import Tool
from purobot.tools.browser import BrowserTool


class App:
    def __init__(self, agent: Agent, session: Session, commands: CommandLoader) -> None:
        self.agent = agent
        self.session = session
        self.commands = commands
        self._lock = Lock()

    @classmethod
    def from_settings(cls, settings) -> "App":
        session = Session(max_history_messages=settings.max_history_messages)
        browser = BrowserTool(
            allow_dangerous_actions=settings.allow_dangerous_browser_actions,
            headless=settings.browser_headless,
        )
        tools: list[Tool] = [browser]
        model = OpenRouterModel(
            model_name=settings.model_name,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        agent = Agent(model=model, tools=tools)
        commands = CommandLoader()
        return cls(agent=agent, session=session, commands=commands)

    def handle_user_message(self, text: str) -> list[str]:
        with self._lock:
            if text.startswith("/") and not self.session.pending_approval:
                return self._handle_command(text)

            outputs = self.agent.handle_user_message(self.session, text)
            if self.session.pending_approval is None:
                self.session.active_command = None
            return outputs

    def _handle_command(self, text: str) -> list[str]:
        parts = text[1:].strip().split()
        if not parts:
            return ["Empty command."]

        name = parts[0]
        args = parts[1:]

        if name == "commands":
            commands = self.commands.list_commands()
            if not commands:
                return ["No commands available."]
            return ["Available commands: " + ", ".join(f"/{command}" for command in commands)]

        try:
            command = self.commands.load(name)
        except FileNotFoundError:
            return [f"Unknown command `/{name}`. Try `/commands`."]

        self.session.active_command = {
            "name": command.name,
            "args": args,
            "instructions": command.instructions,
        }
        command_text = self._command_prompt(command.name, args)
        outputs = self.agent.handle_user_message(self.session, command_text)
        if self.session.pending_approval is None:
            self.session.active_command = None
        return outputs

    def _command_prompt(self, name: str, args: list[str]) -> str:
        if args:
            return f"Run the `/{name}` command with arguments: {' '.join(args)}."
        return f"Run the `/{name}` command."
