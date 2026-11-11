---
name: sonar-review
description: Analyse de qualité de code et correction automatique à la manière de SonarQube / SonarCloud. Détecte bugs, vulnérabilités, security hotspots, code smells, duplications, complexité et dette technique ; attribue des sévérités (Blocker→Info), des notes A–E, évalue un Quality Gate, produit un rapport puis corrige le code. Utilise ce skill dès que l'utilisateur demande une code review, un audit qualité, une analyse statique, « passer le projet au crible », « nettoyer / refactorer / corriger les problèmes » d'un projet, de chercher des failles ou de la dette technique, ou mentionne SonarQube, SonarLint, Sonar, quality gate, code smells ou clean code — même s'il ne prononce pas le mot « Sonar ».
---

# Sonar Review — revue et correction de code façon SonarQube

Ce skill reproduit la démarche de SonarQube : une analyse **systématique** (pas une relecture « au feeling »),
des issues **classées et traçables**, des **métriques chiffrées**, une **décision binaire** (Quality Gate
passé / échoué), puis une **correction priorisée** et vérifiée.

La valeur de SonarQube tient surtout à sa rigueur : chaque problème a un type, une sévérité, une règle,
une localisation précise et un coût de correction. Applique cette même discipline, même pour un petit projet.

## 0. Cadrer la demande

Détermine rapidement (sans interroger l'utilisateur si le contexte suffit) :

- **Périmètre** : projet entier, un dossier, des fichiers précis, ou uniquement le *nouveau code*
  (diff git : `git diff --name-only <branche_base>...HEAD` ou modifications non commitées). Comme dans
  SonarQube, le Quality Gate porte en priorité sur le nouveau code quand il y en a un.
- **Mode** :
  - `analyse` : rapport seul, sans toucher au code ;
  - `analyse + correction` (le cas par défaut quand l'utilisateur dit « corrige », « nettoie », « fixe ») ;
  - `correction ciblée` : corriger uniquement certaines sévérités ou certains types.
- **Langages et stack** : repère les extensions, `package.json`, `pyproject.toml`, `pom.xml`, `*.csproj`,
  `go.mod`, `composer.json`, etc. pour adapter les règles (voir `references/rules.md`).

S'il manque une information vraiment bloquante (ex. le projet fait 2 000 fichiers et aucun périmètre
n'est donné), pose **une seule** question. Sinon, avance.

## 1. Collecter les métriques (automatique)

Lance le script fourni, qui ne dépend que de la bibliothèque standard Python :

```bash
python3 <chemin-du-skill>/scripts/sonar_metrics.py <dossier_ou_fichiers> --json metrics.json
```

Il calcule : lignes de code (NCLOC), complexité cyclomatique et cognitive par fonction, fonctions trop
longues / trop de paramètres / imbrication profonde, **duplication** (blocs de 10 lignes normalisées),
marqueurs TODO/FIXME, et une première passe de motifs suspects (secrets en dur, `eval`, `except: pass`,
`catch {}` vide, SQL concaténé, `debugger`, etc.). Ses résultats sont des **indices** : vérifie chacun
avant d'en faire une issue, et écarte les faux positifs (tests, fixtures, code généré).

Si des analyseurs natifs sont **déjà installés** dans le projet, exécute-les aussi et intègre leurs résultats
(ne les installe pas sans accord) : `eslint`, `tsc --noEmit`, `ruff`/`flake8`/`pylint`, `mypy`, `bandit`,
`semgrep`, `golangci-lint`/`go vet`, `phpstan`, `dotnet build -warnaserror`, `mvn -q spotbugs:check`…
Pour la **couverture**, réutilise un rapport existant (`coverage.xml`, `lcov.info`, `jacoco.xml`) ou lance
la commande de test avec couverture si elle est évidente et rapide ; sinon indique « couverture non mesurée ».

## 2. Revue manuelle guidée par les règles

Le script ne voit que des motifs ; la vraie valeur vient de ta lecture du code. Lis les fichiers du
périmètre (en commençant par les plus complexes et les plus exposés : points d'entrée HTTP, accès aux
données, authentification, parsing d'entrées) et applique le catalogue de `references/rules.md`.
Lis la section du langage concerné ainsi que la section transverse.

Classe chaque problème dans **un seul type** :

| Type | Question à se poser | Qualité impactée |
|---|---|---|
| 🐞 **Bug** | Ce code produit-il (ou peut-il produire) un comportement incorrect ? | Fiabilité |
| 🔓 **Vulnérabilité** | Un attaquant peut-il l'exploiter, de façon certaine ? | Sécurité |
| 🔥 **Security Hotspot** | Code sensible dont la sûreté **dépend du contexte** : un humain doit trancher | Revue sécurité |
| 🧹 **Code Smell** | Le code marche, mais il est difficile à lire, faire évoluer ou tester | Maintenabilité |

Attribue une **sévérité** selon l'impact × la probabilité :

| Sévérité | Critère | Exemples |
|---|---|---|
| **Blocker** | Impact fort et probable : à corriger immédiatement | injection SQL exploitable, secret de production en dur, crash systématique, perte de données |
| **Critical** | Impact fort, probabilité plus faible | NPE sur un chemin d'erreur, ressource jamais fermée, XSS sur une page interne, `except: pass` qui masque des pannes |
| **Major** | Impact notable sur la productivité ou le risque | complexité cognitive > 15, gros bloc dupliqué, code mort important, valeur de retour ignorée |
| **Minor** | Impact faible | nommage, paramètre inutilisé, import inutile, magic number |
| **Info** | Ni bug ni smell : simple information | TODO / FIXME, usage déprécié non urgent |

Estime l'**effort de remédiation** de chaque issue (5 min, 10 min, 30 min, 1 h, 1 j…) : c'est la base
de la dette technique.

**Sois précis et honnête** : une issue doit citer `fichier:ligne`, la règle, et expliquer *pourquoi* c'est
un problème. Mieux vaut 15 issues justes que 80 issues bruitées : le bruit est ce qui fait que les équipes
ignorent les outils d'analyse. N'invente pas d'issue pour « remplir » une catégorie.

## 3. Calculer les notes et le Quality Gate

Utilise les mêmes formules que SonarQube :

- **Fiabilité** (à partir des bugs) et **Sécurité** (à partir des vulnérabilités) :
  A = 0 issue · B = au moins une Minor · C = au moins une Major · D = au moins une Critical · E = au moins une Blocker
- **Revue sécurité** (hotspots) : A ≥ 80 % de hotspots revus · B ≥ 70 % · C ≥ 50 % · D ≥ 30 % · E < 30 %.
  Les hotspots que tu signales sont « à revoir » tant que l'utilisateur ne les a pas tranchés.
- **Maintenabilité** : ratio de dette = effort total des code smells ÷ (NCLOC × 30 min).
  A ≤ 5 % · B ≤ 10 % · C ≤ 20 % · D ≤ 50 % · E > 50 %

**Quality Gate « Sonar way »** (appliqué au nouveau code s'il existe, sinon au code global) — il est
**ÉCHOUÉ** si l'une des conditions n'est pas remplie :

1. Note de fiabilité = A
2. Note de sécurité = A
3. Note de maintenabilité = A
4. Hotspots revus = 100 %
5. Couverture ≥ 80 % (condition ignorée et signalée comme telle si la couverture n'est pas mesurée)
6. Lignes dupliquées ≤ 3 %

Si le projet a un `sonar-project.properties` ou une config de quality gate, respecte ses seuils et exclusions.

## 4. Rédiger le rapport

Écris le rapport dans `SONAR_REPORT.md` à la racine du périmètre analysé (sauf si l'utilisateur veut
autre chose), en suivant **exactement** le gabarit de `references/report-template.md`. Dans la réponse
du chat, donne uniquement la synthèse : statut du Quality Gate, les 4 notes, le top 5 des issues, et le
chemin du rapport.

## 5. Corriger (si demandé)

Corrige dans cet ordre, parce qu'il maximise la réduction du risque par minute passée :
**Vulnérabilités → Bugs → Code smells Blocker/Critical → Major → Minor**.

Principes, à respecter pour que les corrections soient sûres :

- **Ne change pas le comportement fonctionnel.** Un refactoring doit être invisible pour l'appelant. Si
  une correction de bug modifie volontairement un comportement, dis-le explicitement.
- **Corrections minimales et locales.** Un problème = un changement ciblé. Ne reformate pas des fichiers
  entiers et ne réécris pas un module au passage : la diff doit rester relisible.
- **Respecte le style du projet** (conventions, linter, formateur, idiomes déjà en place).
- **Les Security Hotspots ne se corrigent pas à l'aveugle** : propose le correctif et la question à
  trancher (« ce endpoint est-il public ? »), mais applique-le seulement si le risque est évident.
- **Ne touche pas** au code généré, aux dépendances vendorisées ni aux migrations déjà appliquées.
- **Secrets** : remplace le secret par une variable d'environnement, et rappelle à l'utilisateur que le
  secret doit être **révoqué**, car il reste dans l'historique git.
- **Vérifie après chaque lot** : relance les tests, le build ou le linter disponibles. Si un test casse,
  annule ou corrige avant de continuer. Si aucun test n'existe, signale-le, et ajoute un test ciblé pour
  les bugs corrigés quand c'est raisonnable.
- Ce qui est risqué, ambigu ou demande une décision d'architecture (ex. découper une classe de 2 000 lignes)
  va dans une section « Non corrigé — action humaine requise », avec la raison.

Une fois les corrections faites, **relance l'étape 1 et recalcule les notes**, puis ajoute au rapport
la section « Avant / Après » (issues, notes, dette, Quality Gate). Termine par un résumé des fichiers
modifiés.

## Fichiers de référence

- `references/rules.md` : catalogue de règles par type et par langage (Python, JS/TS, Java, C#, PHP,
  Go, SQL, plus les règles transverses), avec les seuils par défaut. Lis-le à l'étape 2.
- `references/report-template.md` : gabarit du rapport. Lis-le à l'étape 4.
- `scripts/sonar_metrics.py` : collecte des métriques (`--help` pour les options). Point d'entrée qui
  s'appuie sur les modules voisins `sonar_*.py` (règles, parcours des fichiers, AST Python, heuristique
  accolades, duplication, synthèse) : garder tout le dossier `scripts/` ensemble.
