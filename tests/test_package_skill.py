"""Tests de tools.package_skill."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from tests.conftest import SkillFactory
from tools.package_skill import PackagingError, main, package_skill


def test_package_skill_includes_only_distributable_files(make_skill: SkillFactory, tmp_path: Path) -> None:
    directory = make_skill()
    (directory / "scripts").mkdir()
    (directory / "scripts" / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (directory / "scripts" / "run.pyc").write_bytes(b"")
    (directory / "tests").mkdir()
    (directory / "tests" / "test_run.py").write_text("", encoding="utf-8")
    (directory / ".env").write_text("SECRET=x\n", encoding="utf-8")

    archive = package_skill(directory, tmp_path / "dist")

    with zipfile.ZipFile(archive) as zip_file:
        assert sorted(zip_file.namelist()) == ["demo-skill/SKILL.md", "demo-skill/scripts/run.py"]


def test_package_skill_rejects_invalid_skill(make_skill: SkillFactory, tmp_path: Path) -> None:
    directory = make_skill(content="---\nname: demo-skill\n---\ncorps")
    with pytest.raises(PackagingError, match="skill invalide"):
        package_skill(directory, tmp_path / "dist")


def test_main_success_and_failure(make_skill: SkillFactory, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = str(tmp_path / "dist")
    assert main([str(make_skill()), "--output", output]) == 0
    assert "Archive créée" in capsys.readouterr().out
    assert main([str(make_skill(name="cassé", content="rien")), "--output", output]) == 1
    assert "Erreur" in capsys.readouterr().err
