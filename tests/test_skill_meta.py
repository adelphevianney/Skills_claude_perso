"""Tests de tools.skill_meta."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import SkillFactory
from tools.skill_meta import (
    FrontmatterError,
    load_skill,
    name_errors,
    parse_frontmatter,
    split_frontmatter,
    validate_skill,
)


def test_split_frontmatter_separates_header_and_body() -> None:
    header, body = split_frontmatter("---\nname: a\n---\ncorps")
    assert header == "name: a"
    assert body == "corps"


@pytest.mark.parametrize("text", ["", "name: a\n---", "---\nname: a\n"])
def test_split_frontmatter_rejects_missing_delimiters(text: str) -> None:
    with pytest.raises(FrontmatterError):
        split_frontmatter(text)


def test_parse_frontmatter_handles_quotes_comments_and_continuations() -> None:
    header = "# commentaire\nname: 'mon-skill'\ndescription: >\n  ligne un\n  ligne deux\nother: \"x\"\n"
    assert parse_frontmatter(header) == {
        "name": "mon-skill",
        "description": "ligne un ligne deux",
        "other": "x",
    }


def test_parse_frontmatter_rejects_orphan_continuation() -> None:
    with pytest.raises(FrontmatterError, match="invalide"):
        parse_frontmatter("  orpheline")


def test_load_skill_reads_metadata_and_body(make_skill: SkillFactory) -> None:
    skill = load_skill(make_skill())
    assert skill.name == "demo-skill"
    assert "# Titre" in skill.body


def test_load_skill_requires_skill_file(tmp_path: Path) -> None:
    with pytest.raises(FrontmatterError, match=r"SKILL\.md introuvable"):
        load_skill(tmp_path)


def test_validate_skill_accepts_valid_skill(make_skill: SkillFactory) -> None:
    assert validate_skill(make_skill()).ok


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("---\ndescription: d\n---\ncorps", "champ obligatoire manquant ou vide : 'name'"),
        ("---\nname: demo-skill\n---\ncorps", "champ obligatoire manquant ou vide : 'description'"),
        ("---\nname: autre\ndescription: d\n---\ncorps", "doit être identique au dossier"),
        ("---\nname: demo-skill\ndescription: d\n---\n   \n", "le corps de SKILL.md est vide"),
        (f"---\nname: demo-skill\ndescription: {'x' * 1025}\n---\ncorps", "description trop longue"),
        ("pas d'en-tête", "doit commencer par"),
    ],
)
def test_validate_skill_reports_errors(make_skill: SkillFactory, content: str, expected: str) -> None:
    result = validate_skill(make_skill(content=content))
    assert not result.ok
    assert any(expected in error for error in result.errors)


@pytest.mark.parametrize("name", ["Mon_Skill", "-debut", "fin-", "a--b"])
def test_name_errors_rejects_non_kebab_case(name: str) -> None:
    assert name_errors(name)


def test_name_errors_rejects_too_long_name() -> None:
    assert any("trop long" in error for error in name_errors("a" * 65))


def test_name_errors_accepts_kebab_case() -> None:
    assert name_errors("sonar-review-2") == []
