"""Lecture et validation de l'en-tête (frontmatter) d'un fichier SKILL.md.

Le parseur ne gère que le sous-ensemble YAML utilisé par les skills (``clé: valeur``,
lignes de continuation indentées, scalaires ``>`` et ``|``) afin de ne dépendre
que de la bibliothèque standard.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SKILL_FILE = "SKILL.md"
FRONTMATTER_DELIMITER = "---"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
REQUIRED_KEYS = ("name", "description")
BLOCK_SCALARS = {">", ">-", "|", "|-"}
QUOTES = frozenset({"'", '"'})
_KEY_LINE = re.compile(r"^([A-Za-z][\w-]*):\s*(.*)$")


class FrontmatterError(ValueError):
    """L'en-tête de SKILL.md est absent ou mal formé."""


@dataclass(frozen=True)
class Skill:
    """Skill chargé depuis son dossier."""

    directory: Path
    metadata: dict[str, str]
    body: str

    @property
    def name(self) -> str:
        """Nom déclaré dans l'en-tête (chaîne vide s'il est absent)."""
        return self.metadata.get("name", "")


@dataclass
class ValidationResult:
    """Résultat de validation d'un skill : liste d'erreurs bloquantes."""

    directory: Path
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Vrai si aucune erreur n'a été relevée."""
        return not self.errors


def split_frontmatter(text: str) -> tuple[str, str]:
    """Sépare l'en-tête (sans délimiteurs) du corps du document."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        raise FrontmatterError("SKILL.md doit commencer par une ligne '---'")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1 :])
    raise FrontmatterError("délimiteur de fin '---' introuvable")


def parse_frontmatter(header: str) -> dict[str, str]:
    """Convertit l'en-tête en dictionnaire ``{clé: valeur}``."""
    metadata: dict[str, str] = {}
    current_key: str | None = None
    for raw_line in header.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        match = _KEY_LINE.match(raw_line)
        if match and not raw_line[0].isspace():
            current_key, value = match.group(1), match.group(2).strip()
            metadata[current_key] = "" if value in BLOCK_SCALARS else _unquote(value)
        elif current_key is not None:
            metadata[current_key] = f"{metadata[current_key]} {raw_line.strip()}".strip()
        else:
            raise FrontmatterError(f"ligne d'en-tête invalide : {raw_line!r}")
    return metadata


def _unquote(value: str) -> str:
    if len(value) > 1 and value[0] == value[-1] and value[0] in QUOTES:
        return value[1:-1]
    return value


def load_skill(directory: Path) -> Skill:
    """Charge le skill contenu dans ``directory``."""
    skill_file = directory / SKILL_FILE
    if not skill_file.is_file():
        raise FrontmatterError(f"{SKILL_FILE} introuvable")
    header, body = split_frontmatter(skill_file.read_text(encoding="utf-8"))
    return Skill(directory=directory, metadata=parse_frontmatter(header), body=body)


def validate_skill(directory: Path) -> ValidationResult:
    """Vérifie qu'un dossier contient un skill conforme."""
    result = ValidationResult(directory=directory)
    try:
        skill = load_skill(directory)
    except FrontmatterError as error:
        result.errors.append(str(error))
        return result
    result.errors.extend(_metadata_errors(skill.metadata, directory.name))
    if not skill.body.strip():
        result.errors.append("le corps de SKILL.md est vide")
    return result


def _metadata_errors(metadata: dict[str, str], directory_name: str) -> list[str]:
    errors = [f"champ obligatoire manquant ou vide : '{key}'" for key in REQUIRED_KEYS if not metadata.get(key)]
    name = metadata.get("name", "")
    if name:
        errors.extend(name_errors(name))
        if name != directory_name:
            errors.append(f"le nom '{name}' doit être identique au dossier '{directory_name}'")
    if len(metadata.get("description", "")) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"description trop longue (> {MAX_DESCRIPTION_LENGTH} caractères)")
    return errors


def name_errors(name: str) -> list[str]:
    """Erreurs de format d'un nom de skill (kebab-case, 64 caractères max)."""
    errors = []
    if not NAME_PATTERN.match(name):
        errors.append(f"nom '{name}' invalide : kebab-case attendu (a-z, 0-9, tirets)")
    if len(name) > MAX_NAME_LENGTH:
        errors.append(f"nom trop long (> {MAX_NAME_LENGTH} caractères)")
    return errors
