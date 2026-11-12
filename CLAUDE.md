# Consignes pour Claude

Ce dépôt contient **exclusivement les skills personnels** de son propriétaire. Chaque skill vit dans
`skills/<nom>/`. Le reste du dépôt (`tools/`, `tests/`, `templates/`, `docs/`) sert à les créer, les
valider et les empaqueter.

## Règle n° 1 : tout code doit passer le quality gate

Aucun code n'est terminé tant que `make check` n'est pas vert. Les seuils sont ceux du skill
**sonar-review** et sont détaillés dans `docs/quality-gate.md`. En résumé :

- fiabilité, sécurité et maintenabilité notées **A** : zéro bug, zéro vulnérabilité, dette ≤ 5 % ;
- **couverture ≥ 80 %** (branches incluses) ; viser 100 % sur l'outillage ;
- **duplication ≤ 3 %** ;
- par fonction : complexité cognitive ≤ 15, cyclomatique ≤ 10, ≤ 50 lignes, ≤ 7 paramètres,
  imbrication ≤ 4, ≤ 5 `return` ; fichiers ≤ 750 lignes ; lignes ≤ 120 caractères.

Ces règles valent pour **tout** code écrit ici, y compris les scripts d'un skill, et dans tous les
langages. Pour un langage autre que Python, appliquer les mêmes seuils avec l'outil natif
(`shellcheck` pour Bash, `eslint` + `tsc --strict` pour JS/TS…) et ajouter l'étape en CI.

## Méthode de travail

1. Écrire le code **et ses tests** dans le même changement (tests dans `tests/` pour `tools/`,
   dans `skills/<nom>/tests/` pour les scripts d'un skill).
2. Lancer `make check`. Corriger à la source ; ne pas contourner :
   - pas de `# noqa`, `# type: ignore`, `pragma: no cover` ni d'exclusion de fichier pour faire passer
     le gate. Exception rare : code de règle + justification sur la même ligne ;
   - ne jamais baisser un seuil dans `pyproject.toml`, `sonar-project.properties` ou `tools/quality_gate.py`.
3. Préférer la bibliothèque standard ; toute dépendance doit être épinglée (`==`).
4. Typage complet (mypy `strict`), docstrings sur les modules et fonctions publiques.
5. Aucune donnée sensible : pas de secret, token, e-mail ou chemin personnel dans le code,
   les exemples ou les tests.

## Créer ou modifier un skill

```bash
python -m tools.new_skill <nom-en-kebab-case> "Ce que fait le skill. À utiliser quand …"
python -m tools.validate_skills skills
make package SKILL=<nom>          # archive .zip dans dist/
```

- `name` doit être identique au nom du dossier (kebab-case, 64 caractères max).
- `description` (1024 caractères max) dit **ce que fait** le skill et **quand** le déclencher : c'est
  le seul texte que Claude voit pour décider de le charger.
- `SKILL.md` reste court ; le détail va dans `references/`, le code exécutable dans `scripts/`.
- Ajouter le skill au tableau « Skills disponibles » du `README.md`.
- L'activer dans Claude Code pour ce dépôt : `ln -s ../../skills/<nom> .claude/skills/<nom>`
  (lien symbolique, jamais de copie : `skills/<nom>/` reste la seule source).

### Scripts d'un skill

- Un script doit rester exécutable directement (`python3 scripts/<script>.py`) : ses modules
  s'importent entre eux par leur nom (`from sonar_rules import …`), sans paquet.
- Préfixer les modules par un nom propre au skill (`sonar_*.py`) : tous les dossiers `scripts/`
  partagent le même `sys.path` pendant les tests.
- Tests dans `skills/<nom>/tests/test_<prefixe>_*.py`, avec un `conftest.py` qui ajoute `scripts/`
  au `sys.path` (voir `skills/sonar-review/tests/conftest.py`).
- Les échantillons de code volontairement fautif (secrets factices, `eval`…) servant de données de
  test vont dans `tests/data/*.txt`, jamais dans un fichier de code : sinon les analyseurs les signalent.
- Refactoring d'un script existant : capturer d'abord sa sortie sur plusieurs entrées, puis vérifier
  qu'elle est identique après (texte et JSON). Tout changement de comportement est annoncé.

## Commandes

| Commande | Rôle |
|---|---|
| `make install` | installe les outils de développement |
| `make check` | lint, typage, validation des skills, tests + couverture, quality gate, auto-contrôle sonar |
| `make gate` | quality gate seul |
| `make sonar` | le skill sonar-review analyse le dépôt (échec dès une issue MINOR) |
| `make package SKILL=<nom>` | archive `.zip` importable dans Claude |
