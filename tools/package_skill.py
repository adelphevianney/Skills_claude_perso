"""Empaquette un skill en archive ``.zip`` prête à être importée dans Claude.

Usage : ``python -m tools.package_skill skills/<nom> [--output dist]``

L'archive contient le dossier du skill à sa racine. Les fichiers de cache, de test
et les fichiers cachés ne sont pas inclus.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from collections.abc import Iterator, Sequence
from pathlib import Path

from tools.skill_meta import validate_skill

EXCLUDED_PARTS = {"__pycache__", "tests", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


class PackagingError(RuntimeError):
    """Le skill ne peut pas être empaqueté."""


def iter_skill_files(directory: Path) -> Iterator[Path]:
    """Fichiers à inclure dans l'archive, triés pour un résultat reproductible."""
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if not path.is_file() or path.suffix in EXCLUDED_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS or part.startswith(".") for part in relative.parts):
            continue
        yield path


def package_skill(directory: Path, output: Path) -> Path:
    """Valide puis empaquette le skill ; renvoie le chemin de l'archive."""
    result = validate_skill(directory)
    if not result.ok:
        raise PackagingError("skill invalide : " + "; ".join(result.errors))
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{directory.name}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in iter_skill_files(directory):
            zip_file.write(path, Path(directory.name) / path.relative_to(directory))
    return archive


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée en ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path, help="dossier du skill")
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args(argv)

    try:
        archive = package_skill(args.skill, args.output)
    except PackagingError as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1
    print(f"Archive créée : {archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
