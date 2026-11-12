# Skills Claude perso

Dépôt personnel de **skills pour Claude** (Claude Code, claude.ai, Cowork), accompagné de l'outillage
pour les créer, les valider, les empaqueter et garantir la qualité de tout le code qu'ils contiennent.

[![Quality gate](https://github.com/adelphevianney/Skills_claude_perso/actions/workflows/quality.yml/badge.svg)](https://github.com/adelphevianney/Skills_claude_perso/actions/workflows/quality.yml)

## Skills disponibles

| Skill | Description |
|---|---|
| [`sonar-review`](skills/sonar-review/SKILL.md) | Revue et correction de code façon SonarQube : bugs, vulnérabilités, hotspots, code smells, duplication, complexité, notes A–E, Quality Gate, rapport puis corrections. Script `sonar_metrics.py` sans dépendance. |

## Structure

```
.
├── skills/                  # un dossier par skill : skills/<nom>/SKILL.md (+ references/, scripts/, tests/)
│   └── sonar-review/        #   revue de code façon SonarQube
├── templates/skill/         # gabarit utilisé par tools.new_skill
├── tools/                   # outillage Python (bibliothèque standard uniquement)
│   ├── new_skill.py         #   crée un skill à partir du gabarit
│   ├── validate_skills.py   #   vérifie l'en-tête et la structure de chaque skill
│   ├── package_skill.py     #   produit une archive .zip importable
│   ├── quality_gate.py      #   quality gate local (seuils Sonar way)
│   ├── cognitive.py         #   complexité cognitive / imbrication
│   ├── duplication.py       #   détection de code dupliqué
│   └── skill_meta.py        #   lecture et validation de SKILL.md
├── tests/                   # tests de l'outillage (couverture 100 %)
├── docs/quality-gate.md     # seuils qualité détaillés
├── CLAUDE.md                # consignes suivies par Claude dans ce dépôt
├── sonar-project.properties # configuration SonarQube / SonarQube Cloud
└── .github/                 # CI (quality gate) et modèle de PR
```

## Démarrage

Prérequis : Python 3.11 ou plus récent.

```bash
python -m venv .venv && source .venv/bin/activate
make install
make check
```

## Créer un skill

```bash
python -m tools.new_skill mon-skill "Ce que fait le skill. À utiliser quand l'utilisateur demande …"
```

Puis compléter `skills/mon-skill/SKILL.md`, ajouter la documentation dans `references/`, les scripts
dans `scripts/` et leurs tests dans `tests/`, enfin vérifier :

```bash
make check
```

Règles de l'en-tête de `SKILL.md` :

| Champ | Règle |
|---|---|
| `name` | kebab-case, 64 caractères max, identique au nom du dossier |
| `description` | obligatoire, 1024 caractères max : **ce que fait** le skill et **quand** l'utiliser |

## Installer un skill

**Claude Code, dans ce dépôt** : les skills sont déclarés comme skills de projet via des liens
symboliques dans `.claude/skills/`, chargés automatiquement par toute session Claude Code ouverte ici
(locale ou cloud). Pour en ajouter un :

```bash
ln -s ../../skills/mon-skill .claude/skills/mon-skill
```

**Claude Code, pour tous vos projets** : lier le dossier dans le répertoire personnel des skills.

```bash
ln -s "$PWD/skills/mon-skill" ~/.claude/skills/mon-skill
```

**claude.ai / application Claude** : générer l'archive puis l'importer depuis les paramètres
(section Capacités → Skills).

```bash
make package SKILL=mon-skill      # crée dist/mon-skill.zip
```

## Qualité du code

Tout le code du dépôt doit passer le **quality gate** aligné sur le profil « Sonar way » du skill
sonar-review : notes A en fiabilité, sécurité et maintenabilité, couverture ≥ 80 %, duplication ≤ 3 %,
complexité cognitive ≤ 15 par fonction. Le détail des seuils et des outils est dans
[`docs/quality-gate.md`](docs/quality-gate.md).

| Vérification | Outil |
|---|---|
| Lint, sécurité, complexité cyclomatique, paramètres, retours | ruff |
| Typage | mypy (`strict`) |
| Structure des skills | `tools.validate_skills` |
| Tests et couverture ≥ 80 % | pytest + pytest-cov |
| Complexité cognitive, imbrication, taille, duplication | `tools.quality_gate` |
| Auto-contrôle : le skill sonar-review analyse le dépôt (échec dès une issue MINOR) | `make sonar` |
| Scripts Bash | shellcheck |
| Analyse serveur (optionnelle) | SonarQube Cloud via `SONAR_TOKEN` |

La CI GitHub Actions exécute ces vérifications à chaque push et pull request.
