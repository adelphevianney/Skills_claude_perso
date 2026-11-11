"""Crée un nouveau skill à partir du gabarit ``templates/skill``.

Usage : ``python -m tools.new_skill <nom> "<description>"``
"""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

from tools.skill_meta import SKILL_FILE, name_errors

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = REPO_ROOT / "templates" / "skill"
DEFAULT_DESTINATION = REPO_ROOT / "skills"
NAME_PLACEHOLDER = "{{SKILL_NAME}}"
DESCRIPTION_PLACEHOLDER = "{{SKILL_DESCRIPTION}}"


class SkillCreationError(RuntimeError):
    """Le skill ne peut pas être créé."""


def create_skill(name: str, description: str, destination: Path, template: Path = DEFAULT_TEMPLATE) -> Path:
    """Copie le gabarit dans ``destination/name`` et renseigne l'en-tête."""
    errors = name_errors(name)
    if errors:
        raise SkillCreationError("; ".join(errors))
    if not description.strip():
        raise SkillCreationError("la description ne peut pas être vide")
    target = destination / name
    if target.exists():
        raise SkillCreationError(f"le dossier {target} existe déjà")

    shutil.copytree(template, target)
    skill_file = target / SKILL_FILE
    content = skill_file.read_text(encoding="utf-8")
    content = content.replace(NAME_PLACEHOLDER, name).replace(DESCRIPTION_PLACEHOLDER, " ".join(description.split()))
    skill_file.write_text(content, encoding="utf-8")
    return target


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée en ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="nom du skill en kebab-case")
    parser.add_argument("description", help="ce que fait le skill et QUAND l'utiliser")
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args(argv)

    try:
        target = create_skill(args.name, args.description, args.destination)
    except SkillCreationError as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1
    print(f"Skill créé : {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
