"""Valide tous les skills d'un dossier (par défaut ``skills/``).

Usage : ``python -m tools.validate_skills [dossier]`` — code de sortie 1 en cas d'erreur.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tools.skill_meta import ValidationResult, validate_skill


def discover_skills(root: Path) -> list[Path]:
    """Liste les sous-dossiers de ``root`` (hors dossiers cachés), triés par nom."""
    return sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith("."))


def validate_all(root: Path) -> list[ValidationResult]:
    """Valide chaque skill trouvé sous ``root``."""
    return [validate_skill(directory) for directory in discover_skills(root)]


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée en ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default="skills", type=Path, help="dossier contenant les skills")
    args = parser.parse_args(argv)

    if not args.root.is_dir():
        print(f"Dossier introuvable : {args.root}", file=sys.stderr)
        return 1

    results = validate_all(args.root)
    for result in results:
        status = "OK  " if result.ok else "FAIL"
        print(f"[{status}] {result.directory.name}")
        for error in result.errors:
            print(f"       - {error}")

    failures = sum(not result.ok for result in results)
    print(f"{len(results)} skill(s) analysé(s), {failures} en échec.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
