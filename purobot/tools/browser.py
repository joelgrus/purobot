from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

from purobot.tools.base import ToolResult


@dataclass(slots=True)
class BrowserSession:
    playwright: Any
    browser: Any
    page: Page


class BrowserTool:
    def __init__(self, allow_dangerous_actions: bool, headless: bool = True) -> None:
        self.allow_dangerous_actions = allow_dangerous_actions
        self.headless = headless
        self._session: BrowserSession | None = None
        self.name = "browser"
        self.description = (
            "Drive a browser session with structured actions. "
            "This tool is for visiting and interacting with specific websites, not for ordinary knowledge tasks the model can answer directly. "
            "Do not use it as a generic web search step unless the user explicitly asked to browse or use a website. "
            "Use action=read with mode=snapshot to inspect the current page generally. "
            "Use selector+mode=text or selector+mode=value only when targeting a specific element. "
            "Mark dangerous=true only for irreversible actions like final order submission."
        )

    def run(self, arguments: dict[str, Any], session) -> ToolResult:
        action = arguments["action"]
        browser_session = self._get_session()
        page = browser_session.page
        state = session.state.setdefault("browser", {})

        try:
            if action == "open":
                url = arguments["url"]
                page.goto(url, wait_until="domcontentloaded")
                state["current_url"] = page.url
                summary = self._page_summary(page)
                return ToolResult(
                    summary=f"Opened {page.url}.",
                    data={
                        "ok": True,
                        "action": action,
                        "url": page.url,
                        **summary,
                    },
                )

            if action == "click":
                selector = arguments["selector"]
                page.locator(selector).first.click()
                return ToolResult(
                    summary=f"Clicked `{selector}`.",
                    data={"ok": True, "action": action, "selector": selector, "url": page.url},
                )

            if action == "type":
                selector = arguments["selector"]
                text = arguments["text"]
                locator = page.locator(selector).first
                locator.fill("")
                locator.fill(text)
                return ToolResult(
                    summary=f"Typed into `{selector}`.",
                    data={"ok": True, "action": action, "selector": selector, "text": text},
                )

            if action == "read":
                selector = arguments.get("selector")
                mode = arguments.get("mode", "text")
                data = self._read(page, selector, mode)
                return ToolResult(
                    summary="Read browser state.",
                    data={"ok": True, "action": action, "selector": selector, "mode": mode, **data},
                )

            if action == "wait":
                milliseconds = int(arguments.get("milliseconds", 1000))
                page.wait_for_timeout(milliseconds)
                return ToolResult(
                    summary=f"Waited {milliseconds}ms.",
                    data={"ok": True, "action": action, "milliseconds": milliseconds},
                )
        except (PlaywrightError, ValueError) as exc:
            return ToolResult(
                summary=f"Browser action `{action}` failed.",
                data={"ok": False, "action": action, "error": str(exc)},
            )

        raise ValueError(f"Unsupported browser action: {action}")

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["open", "click", "type", "read", "wait"],
                    "description": (
                        "Browser action to execute. "
                        "After clicks or page changes, prefer action=read with mode=snapshot."
                    ),
                },
                "url": {"type": "string", "description": "URL to open for action=open."},
                "selector": {
                    "type": "string",
                    "description": (
                        "CSS selector for click, type, or targeted read actions. "
                        "Do not omit selector unless using read with mode=snapshot."
                    ),
                },
                "text": {"type": "string", "description": "Text for action=type."},
                "mode": {
                    "type": "string",
                    "enum": ["text", "value", "snapshot"],
                    "description": (
                        "Read mode for action=read. "
                        "Use snapshot for page-wide inspection. "
                        "Use text or value only with a selector."
                    ),
                },
                "milliseconds": {
                    "type": "integer",
                    "description": "Delay for action=wait.",
                },
                "dangerous": {
                    "type": "boolean",
                    "description": "Mark true only for irreversible browser actions.",
                },
            },
            "required": ["action"],
            "additionalProperties": False,
        }

    def needs_approval(self, arguments: dict[str, Any]) -> bool:
        return bool(arguments.get("dangerous")) and not self.allow_dangerous_actions

    def _get_session(self) -> BrowserSession:
        if self._session is not None:
            return self._session

        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=self.headless)
        page = browser.new_page()
        page.set_default_timeout(1500)
        self._session = BrowserSession(playwright=playwright, browser=browser, page=page)
        return self._session

    def _read(self, page: Page, selector: str | None, mode: str) -> dict[str, Any]:
        if mode == "snapshot":
            return self._page_summary(page)

        if selector is None:
            raise ValueError("`selector` is required unless mode is `snapshot`.")

        locator = page.locator(selector).first
        if mode == "text":
            return {"text": locator.inner_text()}
        if mode == "value":
            return {"value": locator.input_value()}
        raise ValueError(f"Unsupported read mode: {mode}")

    def _page_summary(self, page: Page) -> dict[str, Any]:
        buttons = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('button, [role="button"], a'))
                .slice(0, 20)
                .map((element) => ({
                    text: (element.innerText || element.textContent || '').trim().slice(0, 120),
                    id: element.id || null,
                    selector_hint:
                        element.id ? `#${element.id}` :
                        element.getAttribute('data-add-item') ? `[data-add-item="${element.getAttribute('data-add-item')}"]` :
                        element.getAttribute('name') ? `${element.tagName.toLowerCase()}[name="${element.getAttribute('name')}"]` :
                        null
                }))
            """
        )
        inputs = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('input, textarea, select'))
                .slice(0, 20)
                .map((element) => ({
                    name: element.getAttribute('name'),
                    id: element.id || null,
                    type: element.getAttribute('type') || element.tagName.toLowerCase(),
                    placeholder: element.getAttribute('placeholder'),
                    selector_hint:
                        element.id ? `#${element.id}` :
                        element.getAttribute('name') ? `${element.tagName.toLowerCase()}[name="${element.getAttribute('name')}"]` :
                        null
                }))
            """
        )
        body = page.locator("body").inner_text()
        return {
            "url": page.url,
            "title": page.title(),
            "text": body[:4000],
            "buttons": buttons,
            "inputs": inputs,
        }

    def tool_spec(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema(),
            },
        }
