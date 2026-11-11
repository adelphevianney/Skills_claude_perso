"""Tests de tools.new_skill."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.new_skill import DEFAULT_TEMPLATE, SkillCreationError, create_skill, main
from tools.skill_meta import load_skill, validate_skill


def test_create_skill_from_repository_template(tmp_path: Path) -> None:
    target = create_skill("mon-skill", "  Fait  une chose.\nUtiliser quand X. ", tmp_path)
    assert validate_skill(target).ok
    assert load_skill(target).metadata["description"] == "Fait une chose. Utiliser quand X."
    assert (target / "scripts").is_dir()
    assert (target / "references").is_dir()


@pytest.mark.parametrize(
    ("name", "description", "message"),
    [("Mauvais_Nom", "d", "kebab-case"), ("bon-nom", "   ", "description")],
)
def test_create_skill_rejects_invalid_input(tmp_path: Path, name: str, description: str, message: str) -> None:
    with pytest.raises(SkillCreationError, match=message):
        create_skill(name, description, tmp_path)


def test_create_skill_refuses_to_overwrite(tmp_path: Path) -> None:
    (tmp_path / "existant").mkdir()
    with pytest.raises(SkillCreationError, match="existe déjà"):
        create_skill("existant", "d", tmp_path)


def test_main_creates_skill(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["mon-skill", "Description.", "--destination", str(tmp_path)]) == 0
    assert "Skill créé" in capsys.readouterr().out


def test_main_reports_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["Mauvais", "d", "--destination", str(tmp_path)]) == 1
    assert "Erreur" in capsys.readouterr().err


def test_template_keeps_placeholders() -> None:
    content = (DEFAULT_TEMPLATE / "SKILL.md").read_text(encoding="utf-8")
    assert "{{SKILL_NAME}}" in content
    assert "{{SKILL_DESCRIPTION}}" in content
