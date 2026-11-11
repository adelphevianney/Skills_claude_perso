# Gabarit du rapport `SONAR_REPORT.md`

Reproduis cette structure. Remplace les éléments entre `<>`. Garde les tableaux, même vides
(écris alors « Aucune issue »). Les identifiants d'issue sont séquentiels : `S-001`, `S-002`…

---

```markdown
# Rapport qualité — <nom du projet>

> Analyse du <date> · Périmètre : <projet entier | nouveau code depuis <branche> | fichiers…>
> Langages : <…> · NCLOC : <n> · Fichiers : <n> · Outils : sonar_metrics.py<, eslint, ruff…>

## Quality Gate : ✅ PASSÉ | ❌ ÉCHOUÉ

| Condition | Seuil | Valeur | Statut |
|---|---|---|---|
| Note de fiabilité | A | <X> | ✅/❌ |
| Note de sécurité | A | <X> | ✅/❌ |
| Note de maintenabilité | A | <X> | ✅/❌ |
| Hotspots revus | 100 % | <n> % | ✅/❌ |
| Couverture | ≥ 80 % | <n % / non mesurée> | ✅/❌/➖ |
| Duplication | ≤ 3 % | <n> % | ✅/❌ |

## Vue d'ensemble

| Dimension | Note | Détail |
|---|---|---|
| 🐞 Fiabilité | <A–E> | <n> bugs (<x> Blocker, <y> Critical, …) |
| 🔓 Sécurité | <A–E> | <n> vulnérabilités |
| 🔥 Revue sécurité | <A–E> | <n> hotspots à revoir |
| 🧹 Maintenabilité | <A–E> | <n> code smells · dette <durée> · ratio <n> % |
| 📋 Duplication | — | <n> % (<n> blocs, <n> lignes) |
| 🧪 Couverture | — | <n % / non mesurée> |
| 🌀 Complexité | — | cyclomatique totale <n> · <n> fonctions au-dessus du seuil cognitif |

## Points chauds (fichiers les plus problématiques)

| Fichier | Issues | Dette | Complexité cognitive max |
|---|---|---|---|

## Issues

Triées par type (Vulnérabilité, Bug, Hotspot, Code Smell), puis par sévérité.

| ID | Type | Sévérité | Règle | Emplacement | Problème | Effort |
|---|---|---|---|---|---|---|
| S-001 | 🔓 Vulnérabilité | Blocker | SEC-SQLI | `src/db.py:42` | Requête SQL construite par concaténation de `user_id` | 15 min |

### Détail des issues Blocker et Critical

Pour chacune :

#### S-001 · <titre court>
- **Pourquoi** : <impact concret, scénario d'exploitation ou de panne>
- **Code** :
  ```<lang>
  <extrait fautif, 3 à 10 lignes>
  ```
- **Correction proposée** :
  ```<lang>
  <code corrigé>
  ```

## Security Hotspots à revoir

| ID | Emplacement | Catégorie | Question à trancher |
|---|---|---|---|

## Duplications

| Bloc | Occurrences | Lignes |
|---|---|---|

## Recommandations

1. <action prioritaire et gain attendu>
2. …

<!-- Sections à ajouter seulement en mode correction -->

## Corrections appliquées

| ID | Fichier | Changement | Vérification |
|---|---|---|---|
| S-001 | `src/db.py` | Requête paramétrée | tests ✅ |

## Non corrigé : action humaine requise

| ID | Raison |
|---|---|

## Avant / Après

| Indicateur | Avant | Après |
|---|---|---|
| Quality Gate | ❌ | ✅ |
| Bugs / Vulnérabilités / Smells | | |
| Notes F / S / M | | |
| Dette technique | | |
| Duplication | | |
```
