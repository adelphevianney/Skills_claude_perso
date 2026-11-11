"""Tests de tools.validate_skills."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import SkillFactory
from tools.validate_skills import discover_skills, main


def test_discover_skills_ignores_files_and_hidden_dirs(tmp_path: Path) -> None:
    (tmp_path / "b-skill").mkdir()
    (tmp_path / "a-skill").mkdir()
    (tmp_path / ".cache").mkdir()
    (tmp_path / ".gitkeep").touch()
    assert [path.name for path in discover_skills(tmp_path)] == ["a-skill", "b-skill"]


def test_main_succeeds_on_valid_skills(make_skill: SkillFactory, capsys: pytest.CaptureFixture[str]) -> None:
    directory = make_skill()
    assert main([str(directory.parent)]) == 0
    assert "[OK  ] demo-skill" in capsys.readouterr().out


def test_main_fails_on_invalid_skill(make_skill: SkillFactory, capsys: pytest.CaptureFixture[str]) -> None:
    directory = make_skill(content="---\nname: demo-skill\n---\ncorps")
    assert main([str(directory.parent)]) == 1
    assert "[FAIL] demo-skill" in capsys.readouterr().out


def test_main_fails_on_missing_root(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(tmp_path / "absent")]) == 1
    assert "introuvable" in capsys.readouterr().err
