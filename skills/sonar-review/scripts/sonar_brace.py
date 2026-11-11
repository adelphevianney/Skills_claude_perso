"""Métriques approximatives des fonctions pour les langages à accolades (JS, TS, Java, C#, Go…)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from sonar_model import FunctionStats

FUNC_SIG = re.compile(
    r"""^\s*(?:export\s+)?(?:default\s+)?"""
    r"""(?:public|private|protected|internal|static|async|final|override|virtual|abstract|synchronized"""
    r"""|func|fun|function|def|\s)*"""
    r"""(?:[\w<>\[\],.?*&:\s]+\s+)?(?P<name>[A-Za-z_$][\w$]*)\s*(?:=\s*(?:async\s*)?)?\((?P<params>[^)]*)\)"""
    r"""\s*(?::\s*[^{=]+)?(?:=>)?\s*(?:throws\s+[\w.,\s]+)?\{\s*$"""
)
FUNC_SIG_ARROW = re.compile(
    r"""^\s*(?:export\s+)?(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?"""
    r"""\((?P<params>[^)]*)\)\s*(?::\s*[^=]+)?=>\s*\{\s*$"""
)
_CONTROL_KEYWORDS = frozenset({"if", "for", "while", "switch", "catch", "with", "return", "else", "do", "try"})
NOT_FUNC = _CONTROL_KEYWORDS | {"foreach", "using", "lock", "synchronized", "function"}
DECISION = re.compile(r"\b(if|for|foreach|while|case|catch)\b|&&|\|\||\?\?|(?<![?:])\?(?![.?:])")
NESTING_KW = re.compile(r"\b(if|for|foreach|while|switch|catch|try)\b")
_STRING_LITERAL = re.compile(r"""(['"`])(?:\\.|(?!\1).)*\1""")
_LINE_COMMENT = re.compile(r"//.*$")
_BOOLEAN_OPERATOR = re.compile(r"&&|\|\|")
_RETURN = re.compile(r"\breturn\b")


def strip_strings(line: str) -> str:
    """Remplace les littéraux chaîne par ``""`` pour ne pas compter leur contenu."""
    return _STRING_LITERAL.sub('""', line)


@dataclass
class _BodyScan:
    """Compteurs cumulés en parcourant le corps d'une fonction ligne à ligne."""

    depth: int = 0
    cyclo: int = 1
    cognitive: int = 0
    max_nest: int = 0
    returns: int = 0
    nest_stack: list[int] = field(default_factory=list)  # profondeur d'accolade de chaque structure ouverte

    def count(self, line: str) -> None:
        """Comptabilise les décisions, structures et ``return`` d'une ligne du corps."""
        self.cyclo += len(DECISION.findall(line))
        self.cognitive += len(NESTING_KW.findall(line)) * (1 + len(self.nest_stack))
        self.cognitive += len(_BOOLEAN_OPERATOR.findall(line))
        if _RETURN.search(line):
            self.returns += 1
        if NESTING_KW.search(line) and "{" in line:
            self.nest_stack.append(self.depth + 1)
            self.max_nest = max(self.max_nest, len(self.nest_stack))

    def track_braces(self, line: str) -> None:
        """Met à jour la profondeur d'accolades et ferme les structures terminées."""
        for char in line:
            if char == "{":
                self.depth += 1
            elif char == "}":
                self.depth -= 1
                while self.nest_stack and self.nest_stack[-1] > self.depth:
                    self.nest_stack.pop()


def _match_signature(line: str) -> re.Match[str] | None:
    match = FUNC_SIG.match(line) or FUNC_SIG_ARROW.match(line)
    if match and match.group("name") not in NOT_FUNC:
        return match
    return None


def _scan_body(lines: Sequence[str], start: int) -> tuple[_BodyScan, int]:
    """Parcourt la fonction ouverte à ``start`` ; renvoie les compteurs et l'index de fin."""
    scan = _BodyScan()
    end = start
    while end < len(lines):
        line = _LINE_COMMENT.sub("", strip_strings(lines[end]))
        if end > start:
            scan.count(line)
        scan.track_braces(line)
        if scan.depth <= 0:
            break
        end += 1
    return scan, end


def brace_functions(lines: Sequence[str]) -> list[FunctionStats]:
    """Fonctions détectées par heuristique, y compris les fonctions imbriquées."""
    functions = []
    for start, raw in enumerate(lines):
        match = _match_signature(strip_strings(raw))
        if match is None:
            continue
        scan, end = _scan_body(lines, start)
        params = [param for param in match.group("params").split(",") if param.strip()]
        functions.append(
            FunctionStats(
                name=match.group("name"),
                line=start + 1,
                length=end - start + 1,
                params=len(params),
                cyclomatic=scan.cyclo,
                cognitive=scan.cognitive,
                nesting=scan.max_nest,
                returns=scan.returns,
                approximate=True,
            )
        )
    return functions
