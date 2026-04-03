from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Skill:
    name: str
    path: Path
    instructions: str


class SkillLoader:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd() / "skills"

    def load(self, name: str) -> Skill:
        path = self.root / name / "SKILL.md"
        if not path.exists():
            raise FileNotFoundError(f"Missing skill file: {path}")
        return Skill(name=name, path=path, instructions=path.read_text())

