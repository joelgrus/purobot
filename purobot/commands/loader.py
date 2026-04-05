from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Command:
    name: str
    path: Path
    instructions: str


class CommandLoader:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd() / "commands"

    def list_commands(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(path.stem for path in self.root.glob("*.md"))

    def load(self, name: str) -> Command:
        path = self.root / f"{name}.md"
        if not path.exists():
            raise FileNotFoundError(f"Missing command file: {path}")
        return Command(name=name, path=path, instructions=path.read_text())
