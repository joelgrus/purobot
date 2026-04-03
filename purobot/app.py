from __future__ import annotations

from threading import Lock

from purobot.core.agent import Agent
from purobot.core.model import OpenRouterModel
from purobot.core.session import Session
from purobot.skills.loader import SkillLoader
from purobot.tools.base import Tool
from purobot.tools.browser import BrowserTool


class App:
    def __init__(self, agent: Agent, session: Session) -> None:
        self.agent = agent
        self.session = session
        self._lock = Lock()

    @classmethod
    def from_settings(cls, settings) -> "App":
        loader = SkillLoader()
        skills = [loader.load(name) for name in settings.skill_names]
        session = Session(active_skills=skills)
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
        return cls(agent=agent, session=session)

    def handle_user_message(self, text: str) -> list[str]:
        with self._lock:
            return self.agent.handle_user_message(self.session, text)
