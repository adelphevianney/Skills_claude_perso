"""Parcours des fichiers sources et extraction des lignes de code."""

from __future__ import annotations

import fnmatch
import os
import re
from collections.abc import Iterator, Sequence
from pathlib import Path

from sonar_rules import EXCLUDED_DIRS, EXCLUDED_FILES, LANGS

CodeLine = tuple[int, str]

_TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|fixtures?|mocks?)/|[._-](test|spec)\.\w+$|/test_[^/]+$")
_DOCSTRING_QUOTES = ('"""', "'''")
_QUOTE_LENGTH = 3


def is_test_path(path: str) -> bool:
    """Vrai si le chemin désigne du code de test, une fixture ou un mock."""
    return bool(_TEST_PATH.search(path.replace("\\", "/").lower()))


def language_of(path: str) -> str:
    """Langage déduit de l'extension (``other`` si inconnue)."""
    return LANGS.get(Path(path).suffix.lower(), "other")


def _join(directory: str, filename: str) -> str:
    """Jointure de chemins sans normalisation : les motifs ``--exclude`` portent sur le chemin tel que fourni."""
    return os.path.join(directory, filename)  # noqa: PTH118 - pathlib normaliserait « ./src » en « src »


def _is_source_file(full_path: str, filename: str, excludes: Sequence[str]) -> bool:
    if Path(filename).suffix.lower() not in LANGS:
        return False
    if any(fnmatch.fnmatch(filename, pattern) for pattern in EXCLUDED_FILES):
        return False
    return not any(fnmatch.fnmatch(full_path, pattern) for pattern in excludes)


def iter_files(paths: Sequence[str], excludes: Sequence[str]) -> Iterator[str]:
    """Fichiers sources sous ``paths`` (un fichier donné explicitement est toujours retenu)."""
    for root in paths:
        if Path(root).is_file():
            yield root
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if name not in EXCLUDED_DIRS and not name.startswith(".")]
            candidates = ((_join(dirpath, name), name) for name in filenames)
            yield from (full for full, name in candidates if _is_source_file(full, name, excludes))


def comment_prefixes(lang: str) -> tuple[str, ...]:
    """Préfixes de commentaire de ligne du langage."""
    if lang in {"python", "ruby"}:
        return ("#",)
    if lang == "sql":
        return ("--",)
    if lang == "php":
        return ("//", "#", "*", "/*")
    return ("//", "*", "/*")


class _DocstringSkipper:
    """Repère les docstrings Python (sur une ou plusieurs lignes)."""

    def __init__(self) -> None:
        self.inside = False

    def skip(self, line: str) -> bool:
        if self.inside:
            if any(quote in line for quote in _DOCSTRING_QUOTES):
                self.inside = False
            return True
        if line.startswith(_DOCSTRING_QUOTES):
            quote = line[:_QUOTE_LENGTH]
            closed_on_same_line = line.count(quote) > 1 and len(line) > _QUOTE_LENGTH
            self.inside = not closed_on_same_line
            return True
        return False


class _BlockCommentSkipper:
    """Repère les commentaires ``/* … */`` répartis sur plusieurs lignes."""

    def __init__(self) -> None:
        self.inside = False

    def skip(self, line: str) -> bool:
        if self.inside:
            self.inside = "*/" not in line
            return True
        if line.startswith("/*") and "*/" not in line:
            self.inside = True
            return True
        return False


def code_lines(lines: Sequence[str], lang: str) -> list[CodeLine]:
    """Lignes de code ``(index, ligne nettoyée)``, sans blancs ni commentaires."""
    skipper = _DocstringSkipper() if lang == "python" else _BlockCommentSkipper()
    prefixes = comment_prefixes(lang)
    result = []
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped and not skipper.skip(stripped) and not stripped.startswith(prefixes):
            result.append((index, stripped))
    return result
