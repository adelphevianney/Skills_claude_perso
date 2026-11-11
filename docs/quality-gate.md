# Quality gate du dépôt

Seuils repris du skill **sonar-review** (profil « Sonar way »). Ils s'appliquent à **tout le code**
du dépôt : outillage (`tools/`) et scripts embarqués dans les skills (`skills/*/scripts/`).

## Conditions du gate

Le gate est **échoué** si une seule condition n'est pas remplie.

| # | Condition | Seuil | Vérifié par |
|---|---|---|---|
| 1 | Note de fiabilité | A (0 bug) | ruff (`B`, `PL`, `F`), mypy strict, tests |
| 2 | Note de sécurité | A (0 vulnérabilité) | ruff (`S` = règles bandit), revue |
| 3 | Note de maintenabilité | A (dette ≤ 5 %) | ruff + `tools.quality_gate` |
| 4 | Security hotspots revus | 100 % | revue (voir ci-dessous) |
| 5 | Couverture | ≥ 80 % (branches incluses) | pytest-cov (`fail_under = 80`) |
| 6 | Lignes dupliquées | ≤ 3 % | `tools.quality_gate` |

## Seuils par fonction et par fichier

| Métrique | Seuil | Règle | Outil |
|---|---|---|---|
| Complexité cognitive | ≤ 15 | SMELL-COGNITIVE | `tools.quality_gate` |
| Complexité cyclomatique | ≤ 10 | SMELL-CYCLO | ruff `C901` |
| Longueur d'une fonction | ≤ 50 lignes | SMELL-LONG-FN | `tools.quality_gate` |
| Taille d'un fichier | ≤ 750 lignes | SMELL-LONG-FILE | `tools.quality_gate` |
| Paramètres | ≤ 7 | SMELL-PARAMS | ruff `PLR0913` |
| Imbrication | ≤ 4 | SMELL-NESTING | `tools.quality_gate`, ruff `PLR1702` |
| `return` par fonction | ≤ 5 | SMELL-RETURNS | ruff `PLR0911` |
| Bloc dupliqué | < 10 lignes identiques | SMELL-DUP | `tools.quality_gate` |
| Longueur de ligne | ≤ 120 caractères | SMELL-LINE | ruff `E501` |
| Nombre magique | interdit en comparaison | — | ruff `PLR2004` |

## Security hotspots : à trancher à la main

Les outils ne savent pas décider : chaque occurrence doit être justifiée dans la PR.

- exécution dynamique (`eval`, `exec`, `subprocess` avec `shell=True`) ;
- lecture d'un chemin de fichier venant d'une entrée utilisateur ;
- requête réseau vers une URL fournie par l'utilisateur ;
- générateur aléatoire utilisé pour autre chose qu'un tirage non sensible ;
- désactivation d'une vérification (TLS, signature, `# noqa`, `# type: ignore`).

Un `# noqa` ou `# type: ignore` n'est accepté qu'avec le code de la règle **et** une justification
sur la même ligne.

## Lancer le gate

```bash
make check                                   # tout, comme la CI
python -m tools.quality_gate tools skills    # gate seul
python -m tools.quality_gate skills/mon-skill --json rapport.json
```

## SonarQube Cloud (optionnel)

`sonar-project.properties` est prêt. Pour activer l'analyse serveur : importer le dépôt dans
SonarQube Cloud, renseigner `sonar.organization` et `sonar.projectKey`, puis ajouter le secret
`SONAR_TOKEN` dans les paramètres GitHub du dépôt. Le job CI correspondant s'active seul.
