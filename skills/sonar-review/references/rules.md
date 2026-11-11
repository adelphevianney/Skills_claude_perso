# Catalogue de règles

Les identifiants (`SEC-…`, `BUG-…`, `SMELL-…`) servent à référencer les règles dans le rapport. Ils
s'inspirent des catégories SonarQube, OWASP Top 10 et CWE, mais ne reprennent pas leurs numéros.
Sévérité et effort indiqués ici sont des **valeurs par défaut** : ajuste-les au contexte (code exposé sur
Internet ou script interne, chemin critique ou utilitaire de test).

## Sommaire
1. Seuils par défaut
2. Règles transverses (tous langages)
3. Python
4. JavaScript / TypeScript (Node, React, Vue, Angular)
5. Java / Kotlin
6. C# / .NET
7. PHP
8. Go
9. SQL, Docker, CI et configuration

---

## 1. Seuils par défaut

| Métrique | Seuil | Règle | Sévérité |
|---|---|---|---|
| Complexité cognitive d'une fonction | > 15 | SMELL-COGNITIVE | Critical (> 25) / Major |
| Complexité cyclomatique d'une fonction | > 10 | SMELL-CYCLO | Major |
| Longueur d'une fonction | > 50 lignes | SMELL-LONG-FN | Major |
| Taille d'un fichier | > 750 lignes | SMELL-LONG-FILE | Major |
| Nombre de paramètres | > 7 | SMELL-PARAMS | Major |
| Profondeur d'imbrication | > 4 | SMELL-NESTING | Critical |
| Instructions `return` dans une fonction | > 5 | SMELL-RETURNS | Major |
| Bloc dupliqué | ≥ 10 lignes / 100 tokens | SMELL-DUP | Major |
| Littéral chaîne répété | ≥ 3 fois | SMELL-DUP-LITERAL | Minor |
| Longueur de ligne | > 120 caractères | SMELL-LINE | Minor |

Effort par défaut : complexité ≈ 5 min + 1 min par point au-dessus du seuil ; duplication ≈ 10 min par bloc ;
fonction longue ≈ 20 min.

---

## 2. Règles transverses

### Vulnérabilités (🔓)
| ID | Règle | Sév. |
|---|---|---|
| SEC-SQLI | Requête SQL/NoSQL construite à partir d'entrées non paramétrées | Blocker |
| SEC-CMDI | Commande système construite avec des entrées utilisateur (`shell=True`, `exec`, `system`) | Blocker |
| SEC-PATH | Chemin de fichier construit à partir d'une entrée sans normalisation ni contrôle (path traversal) | Critical |
| SEC-SECRET | Mot de passe, token, clé API ou clé privée en dur dans le code ou la config versionnée | Blocker |
| SEC-XSS | Entrée injectée dans du HTML sans échappement | Critical |
| SEC-SSRF | URL de requête sortante contrôlée par l'utilisateur sans liste blanche | Critical |
| SEC-DESER | Désérialisation de données non fiables (`pickle`, `yaml.load`, `BinaryFormatter`, `unserialize`) | Blocker |
| SEC-XXE | Parseur XML avec entités externes activées | Critical |
| SEC-CRYPTO | Algorithme faible pour la sécurité (MD5/SHA1 pour mots de passe, DES, ECB, RSA < 2048) | Critical |
| SEC-RANDOM | Générateur non cryptographique pour token, mot de passe ou identifiant de session | Critical |
| SEC-TLS | Vérification de certificat TLS désactivée | Critical |
| SEC-AUTHZ | Endpoint sensible sans contrôle d'authentification ou d'autorisation | Blocker |
| SEC-REDIRECT | Redirection ouverte vers une URL fournie par l'utilisateur | Major |
| SEC-LOG-INJ | Données sensibles (mot de passe, token, PII) écrites dans les logs | Major |
| SEC-REGEX-DOS | Regex à backtracking catastrophique appliquée à une entrée utilisateur | Major |

### Security Hotspots (🔥) : à faire trancher par un humain
| ID | Règle |
|---|---|
| HOT-CORS | CORS permissif (`*`, `credentials: true` avec origine réfléchie) |
| HOT-CSRF | Protection CSRF désactivée |
| HOT-COOKIE | Cookie sans `HttpOnly` / `Secure` / `SameSite` |
| HOT-HASH | Hachage faible utilisé hors contexte sécurité évident |
| HOT-REGEX | Regex complexe sur une entrée externe |
| HOT-PERMS | Permissions de fichiers trop larges (`chmod 777`), conteneur exécuté en root |
| HOT-DEBUG | Mode debug activé dans une config susceptible d'aller en production |
| HOT-HTTP | URL `http://` en clair vers un service externe |
| HOT-IP | Adresse IP en dur |
| HOT-EXEC | Exécution dynamique de code (`eval`, `Function`, `exec`) sans entrée utilisateur prouvée |

### Bugs (🐞)
| ID | Règle | Sév. |
|---|---|---|
| BUG-NULL | Déréférencement possible de null / None / undefined | Critical |
| BUG-RESOURCE | Ressource (fichier, connexion, curseur, stream) non fermée sur tous les chemins | Critical |
| BUG-SWALLOW | Exception capturée et ignorée silencieusement (`catch {}`, `except: pass`) | Critical |
| BUG-BROAD-CATCH | Capture trop large (`except Exception`, `catch (Throwable)`) qui masque des erreurs | Major |
| BUG-IDENTICAL-BRANCH | Branches `if`/`else` ou cas `switch` identiques | Major |
| BUG-SELF-ASSIGN | Auto-affectation ou comparaison d'une expression avec elle-même | Major |
| BUG-ALWAYS | Condition toujours vraie ou toujours fausse | Major |
| BUG-UNREACHABLE | Code inatteignable après `return`, `throw` ou `break` | Major |
| BUG-RETURN-IGNORED | Valeur de retour d'une fonction pure ou sans effet ignorée (ex. `str.replace` en Java) | Major |
| BUG-FLOAT-EQ | Égalité stricte entre flottants | Major |
| BUG-OFF-BY-ONE | Borne de boucle ou indice incorrect | Critical |
| BUG-CONCURRENCY | État partagé muté sans synchronisation, double-checked locking incorrect | Critical |
| BUG-ASYNC | Promesse ou tâche non attendue (`await` manquant), `async void` | Critical |
| BUG-INFINITE | Boucle ou récursion sans condition de sortie atteignable | Blocker |
| BUG-DIV-ZERO | Division par une valeur pouvant être nulle | Critical |
| BUG-TZ | Manipulation de dates sans fuseau horaire là où il compte | Major |

### Code smells (🧹)
| ID | Règle | Sév. |
|---|---|---|
| SMELL-COGNITIVE / CYCLO / LONG-FN / NESTING / PARAMS | voir les seuils | voir les seuils |
| SMELL-DUP | Bloc de code dupliqué | Major |
| SMELL-DEAD | Code mort : fonction, variable ou import inutilisé, code commenté | Major (fonction) / Minor |
| SMELL-UNUSED-PARAM | Paramètre inutilisé | Minor |
| SMELL-MAGIC | Nombre magique ou chaîne magique | Minor |
| SMELL-NAMING | Nom non conforme aux conventions ou peu expressif (`data2`, `tmp`, `x`) | Minor |
| SMELL-TODO | Commentaire TODO / FIXME / HACK | Info |
| SMELL-GOD | Classe ou module aux responsabilités multiples (> 20 méthodes, > 750 lignes) | Major |
| SMELL-BOOL-PARAM | Paramètre booléen qui change le comportement de la fonction | Minor |
| SMELL-NESTED-TERNARY | Ternaires imbriqués | Major |
| SMELL-EMPTY-BLOCK | Bloc vide sans commentaire | Major |
| SMELL-REDUNDANT | `if (x) return true; else return false;`, cast ou parenthèses inutiles | Minor |
| SMELL-DEPRECATED | API dépréciée | Minor |
| SMELL-GLOBAL | État global mutable | Major |
| SMELL-PRINT | `print` / `console.log` de débogage resté dans du code applicatif | Minor |
| SMELL-NO-TEST | Module critique sans aucun test | Major |

---

## 3. Python
- `except:` nu ou `except Exception: pass` → BUG-SWALLOW
- argument par défaut mutable (`def f(x=[])`) → **Bug** Major
- `== None` au lieu de `is None` → Minor ; `type(x) == T` au lieu de `isinstance` → Minor
- `open()` sans `with` → BUG-RESOURCE
- `subprocess.*(…, shell=True)` avec chaîne formatée, `os.system` → SEC-CMDI
- `pickle.loads`, `yaml.load` sans `SafeLoader`, `eval` / `exec` sur une entrée → SEC-DESER / SEC-CMDI
- f-string ou `%` dans `cursor.execute` → SEC-SQLI
- `requests.*(verify=False)` → SEC-TLS ; `random` pour un secret au lieu de `secrets` → SEC-RANDOM
- `assert` utilisé pour un contrôle de sécurité ou une validation (supprimé avec `-O`) → Bug Major
- `DEBUG = True` dans les settings Django, `app.run(debug=True)` → HOT-DEBUG
- import `*` → Minor ; variable qui masque un builtin (`list`, `id`, `type`) → Minor
- boucle `for i in range(len(x))` quand `enumerate` suffit → Minor

## 4. JavaScript / TypeScript
- `==` au lieu de `===` → Major
- `var` → Minor ; `let` jamais réaffecté → Minor
- `any` explicite, `@ts-ignore`, assertion non-null `!` non justifiée → Major / Minor
- promesse non gérée, `.then` sans `.catch`, `forEach(async …)` → BUG-ASYNC
- `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `document.write` avec des données → SEC-XSS
- `eval`, `new Function`, `setTimeout(string)` → SEC / HOT-EXEC
- `child_process.exec` avec template string → SEC-CMDI
- requête SQL ou Mongo construite avec des entrées (`$where`, objets de requête non filtrés) → SEC-SQLI
- React : `key` = index dans une liste dynamique (Major), dépendances de `useEffect` manquantes (Bug Major), mutation directe du state (Bug Critical)
- `console.log` / `debugger` → SMELL-PRINT / Major
- `JSON.parse` sans `try` sur une entrée externe → Major
- `jwt.verify` sans liste d'algorithmes, `jwt.decode` utilisé pour l'authentification → SEC-AUTHZ

## 5. Java / Kotlin
- `equals` redéfini sans `hashCode` → Bug Major
- comparaison de `String` avec `==` → Bug Major
- `catch (Exception e) { e.printStackTrace(); }` → Major
- stream, connexion ou `ResultSet` sans try-with-resources → BUG-RESOURCE
- `Statement` + concaténation au lieu de `PreparedStatement` → SEC-SQLI
- `Optional.get()` sans `isPresent` → BUG-NULL
- `SimpleDateFormat` partagé entre threads → BUG-CONCURRENCY
- champ `public static` non `final` → SMELL-GLOBAL
- `Thread.sleep` dans un test ou une boucle d'attente active → Major
- Kotlin : `!!` → BUG-NULL Major

## 6. C# / .NET
- `async void` hors gestionnaire d'événements, `.Result` / `.Wait()` → BUG-ASYNC
- `IDisposable` sans `using` → BUG-RESOURCE
- `BinaryFormatter` → SEC-DESER
- `SqlCommand` avec concaténation → SEC-SQLI
- `catch (Exception) {}` → BUG-SWALLOW
- `[AllowAnonymous]` sur une action sensible, `[Authorize]` manquant → SEC-AUTHZ

## 7. PHP
- `mysqli_query` ou `$pdo->query` avec variables interpolées → SEC-SQLI
- `echo $_GET[...]` sans `htmlspecialchars` → SEC-XSS
- `unserialize` sur une entrée utilisateur → SEC-DESER
- `include` / `require` d'un chemin dynamique → SEC-PATH (Blocker)
- `md5($password)`, `sha1($password)` → SEC-CRYPTO (utiliser `password_hash`)
- `==` sur des valeurs sensibles (type juggling) → Bug Critical
- `@` pour masquer les erreurs → BUG-SWALLOW

## 8. Go
- erreur ignorée (`_ = f()`, ou `err` jamais testé) → BUG-SWALLOW
- `defer` dans une boucle → Bug Major
- goroutine sans mécanisme d'arrêt, fuite de channel → BUG-CONCURRENCY
- `rows` non fermé, `resp.Body` non fermé → BUG-RESOURCE
- `fmt.Sprintf` dans une requête SQL → SEC-SQLI
- `InsecureSkipVerify: true` → SEC-TLS

## 9. SQL, Docker, CI et configuration
- `SELECT *` dans du code applicatif → Minor ; `DELETE` ou `UPDATE` sans `WHERE` → Bug Blocker
- Dockerfile : image `:latest` (Minor), exécution en root (HOT-PERMS), secret dans `ENV` ou `ARG` (SEC-SECRET), `curl | sh` (HOT)
- `.env` versionné contenant des secrets → SEC-SECRET
- CI : secrets affichés dans les logs, actions tierces non épinglées par SHA → HOT
- dépendances : version non épinglée ou vulnérabilité connue (lancer `npm audit`, `pip-audit` ou `osv-scanner` s'ils sont disponibles) → Vulnérabilité, sévérité selon le CVSS
