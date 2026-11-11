"""Constantes de l'analyse : langages, exclusions, seuils et motifs suspects."""

from __future__ import annotations

import re
from typing import NamedTuple

# Une ligne par langage : nom puis extensions associées.
_LANGUAGE_TABLE = """
python .py
javascript .js .jsx .mjs .cjs .vue
typescript .ts .tsx
java .java
kotlin .kt
csharp .cs
php .php
go .go
c .c .h
cpp .cpp .cc .hpp
ruby .rb
rust .rs
swift .swift
scala .scala
dart .dart
sql .sql
"""
LANGS = {
    extension: language
    for language, *extensions in (row.split() for row in _LANGUAGE_TABLE.strip().splitlines())
    for extension in extensions
}
_TOOLING_DIRS = frozenset({".git", ".venv", "venv", "env", ".tox", ".mypy_cache", ".pytest_cache", ".idea", ".vscode"})
_BUILD_DIRS = frozenset({"dist", "build", "out", "target", "bin", "obj", "__pycache__", ".next", ".nuxt", ".gradle"})
_GENERATED_DIRS = frozenset({"node_modules", "vendor", "coverage", "migrations"})
EXCLUDED_DIRS = _TOOLING_DIRS | _BUILD_DIRS | _GENERATED_DIRS
EXCLUDED_FILES = ("*.min.js", "*.bundle.js", "*.d.ts", "*_pb2.py", "*.generated.*", "*.g.dart")

THRESHOLDS = {
    "cognitive": 15,
    "cyclomatic": 10,
    "length": 50,
    "params": 7,
    "nesting": 4,
    "file_lines": 750,
    "line_length": 120,
}
CRITICAL_COGNITIVE = 25

# Types et sévérités d'issues
BUG = "BUG"
VULNERABILITY = "VULNERABILITY"
SECURITY_HOTSPOT = "SECURITY_HOTSPOT"
CODE_SMELL = "CODE_SMELL"
BLOCKER = "BLOCKER"
CRITICAL = "CRITICAL"
MAJOR = "MAJOR"
MINOR = "MINOR"
INFO = "INFO"

SEV_ORDER = {BLOCKER: 0, CRITICAL: 1, MAJOR: 2, MINOR: 3, INFO: 4}
TYPE_ORDER = {VULNERABILITY: 0, BUG: 1, SECURITY_HOTSPOT: 2, CODE_SMELL: 3}
SECURITY_TYPES = frozenset({VULNERABILITY, SECURITY_HOTSPOT})
CREDENTIAL_RULE_ID = "SEC-SECRET"

PYTHON = frozenset({"python"})
JS = frozenset({"javascript"})
JS_TS = frozenset({"javascript", "typescript"})
TS = frozenset({"typescript"})
PHP = frozenset({"php"})
DYNAMIC_LANGS = frozenset({"python", "javascript", "typescript", "php"})


class Rule(NamedTuple):
    """Motif suspect : identifiant, type, sévérité, regex, langages (None = tous)."""

    rule_id: str
    type: str
    severity: str
    regex: re.Pattern[str]
    langs: frozenset[str] | None

    def applies_to(self, lang: str) -> bool:
        """Vrai si la règle concerne ce langage."""
        return self.langs is None or lang in self.langs


def _rule(rule_id: str, rule_type: str, severity: str, pattern: str, langs: frozenset[str] | None = None) -> Rule:
    return Rule(rule_id, rule_type, severity, re.compile(pattern), langs)


_CREDENTIAL_ASSIGNMENT = (
    r"""(?i)\b(pass(word|wd)?|secret|api[_-]?key|access[_-]?key|auth[_-]?token|token|private[_-]?key)\b"""
    r"""\s*[:=]\s*['"][^'"\s]{6,}['"]"""
)
_CREDENTIAL_FORMATS = r"\b(ghp|gho|github_pat)_[A-Za-z0-9_]{20,}|\bsk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}"
_SQL_CONCAT = (
    r"""(?i)(execute|query|raw|exec)\s*\(\s*(f['"]|['"][^'"]*\b(select|insert|update|delete)\b[^'"]*['"]\s*"""
    r"""(\+|%|\.format)|`[^`]*\b(select|insert|update|delete)\b[^`]*\$\{)"""
)
_TLS_OFF = (
    r"verify\s*=\s*False|rejectUnauthorized\s*:\s*false|InsecureSkipVerify\s*:\s*true|NODE_TLS_REJECT" "_UNAUTHORIZED"
)
_CORS_ANY = (
    r"""(?i)access-control-allow-origin['"]?\s*[:,]\s*['"]\*|origin\s*:\s*['"]\*['"]"""
    r"""|CORS_ORIGIN_ALLOW_ALL\s*=\s*True"""
)
_PLAIN_HTTP = r"""['"]http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|www\.w3\.org|schemas\.)[^'"\s]+"""

RULES = (
    _rule(CREDENTIAL_RULE_ID, VULNERABILITY, BLOCKER, _CREDENTIAL_ASSIGNMENT),
    _rule(CREDENTIAL_RULE_ID, VULNERABILITY, BLOCKER, r"AKIA[0-9A-Z]{16}"),
    _rule(CREDENTIAL_RULE_ID, VULNERABILITY, BLOCKER, r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    _rule(CREDENTIAL_RULE_ID, VULNERABILITY, BLOCKER, _CREDENTIAL_FORMATS),
    _rule("SEC-SQLI", VULNERABILITY, BLOCKER, _SQL_CONCAT),
    _rule("SEC-CMDI", VULNERABILITY, BLOCKER, r"shell\s*=\s*True|\bos\.system\s*\(|\bos\.popen\s*\(", PYTHON),
    _rule(
        "SEC-CMDI", VULNERABILITY, BLOCKER, r"child_process.*\bexec(Sync)?\s*\(|\bexec(Sync)?\s*\(\s*`[^`]*\$\{", JS_TS
    ),
    _rule("SEC-DESER", VULNERABILITY, BLOCKER, r"\bpickle\.loads?\s*\(|\byaml\.load\s*\((?![^)]*SafeLoader)", PYTHON),
    _rule("SEC-DESER", VULNERABILITY, BLOCKER, r"\bunserialize\s*\(", PHP),
    _rule("SEC-DESER", VULNERABILITY, BLOCKER, r"\bBinaryFormatter\b", frozenset({"csharp"})),
    _rule("SEC-TLS", VULNERABILITY, CRITICAL, _TLS_OFF),
    _rule(
        "SEC-XSS",
        VULNERABILITY,
        CRITICAL,
        r"\.innerHTML\s*=|dangerouslySetInnerHTML|v-html=|document\.write\s*\(",
        JS_TS,
    ),
    _rule("SEC-XSS", VULNERABILITY, CRITICAL, r"echo\s+\$_(GET|POST|REQUEST|COOKIE)", PHP),
    _rule("SEC-CRYPTO", VULNERABILITY, CRITICAL, r"(?i)\b(md5|sha1)\s*\(\s*\$?\w*pass"),
    _rule(
        "HOT-EXEC",
        SECURITY_HOTSPOT,
        MAJOR,
        r"(?<![\w.])eval\s*\(|new\s+Function\s*\(|(?<![\w.])exec\s*\(",
        DYNAMIC_LANGS,
    ),
    _rule("HOT-DEBUG", SECURITY_HOTSPOT, MAJOR, r"\bDEBUG\s*=\s*True\b|debug\s*=\s*True", PYTHON),
    _rule("HOT-CORS", SECURITY_HOTSPOT, MAJOR, _CORS_ANY),
    _rule("HOT-HTTP", SECURITY_HOTSPOT, MINOR, _PLAIN_HTTP),
    _rule(
        "HOT-RANDOM",
        SECURITY_HOTSPOT,
        MAJOR,
        r"Math\.random\s*\(|\brandom\.(random|randint|choice)\s*\(",
        JS_TS | PYTHON,
    ),
    _rule("BUG-SWALLOW", BUG, CRITICAL, r"^\s*except\s*(Exception\s*)?(as\s+\w+\s*)?:\s*(pass)?\s*$", PYTHON),
    _rule("BUG-SWALLOW", BUG, CRITICAL, r"catch\s*(\([^)]*\))?\s*\{\s*\}"),
    _rule("BUG-MUTABLE-DEFAULT", BUG, MAJOR, r"def\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|set\(\))", PYTHON),
    _rule("BUG-LOOSE-EQ", CODE_SMELL, MAJOR, r"[^=!<>]==[^=]|!=[^=]", JS),
    _rule("SMELL-PRINT", CODE_SMELL, MINOR, r"\bconsole\.(log|debug)\s*\(|^\s*debugger\s*;?\s*$", JS_TS),
    _rule("SMELL-PRINT", CODE_SMELL, MINOR, r"\bpdb\.set_trace\(\)|\bbreakpoint\(\)", PYTHON),
    _rule("SMELL-TODO", CODE_SMELL, INFO, r"(#|//|/\*|\*)\s*(TODO|FIXME|HACK|XXX)\b"),
    _rule("SMELL-ANY", CODE_SMELL, MINOR, r":\s*any\b|as\s+any\b|@ts-ignore", TS),
)
