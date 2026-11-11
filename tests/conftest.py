"""Fixtures partagées."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

SkillFactory = Callable[..., Path]


@pytest.fixture
def make_skill(tmp_path: Path) -> SkillFactory:
    """Fabrique un dossier de skill avec un SKILL.md donné."""

    def factory(name: str = "demo-skill", content: str | None = None) -> Path:
        directory = tmp_path / "skills" / name
        directory.mkdir(parents=True)
        if content is None:
            content = f"---\nname: {name}\ndescription: Démo de test.\n---\n\n# Titre\n"
        (directory / "SKILL.md").write_text(content, encoding="utf-8")
        return directory

    return factory
