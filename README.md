# Projet CEBD-JO 2025

Projet pédagogique de Licence 3 – UE « Conception et Exploitation de Bases de Données ».

Ce projet illustre la modélisation, la création et l'exploitation d'une base SQL autour des Jeux Olympiques (épreuves, sportifs, équipes, inscriptions et médailles) à partir d'une source Excel. nous traitons :
1. Conception du schéma relationnel (tables, clés, contraintes, vues, triggers).
2. Extraction / transformation / génération automatique d'un script d'insertion SQL depuis un fichier Excel (`LesJO.xlsx`).
3. Mise en place de règles d'intégrité via des triggers.
4. Création de vues analytiques (âges, tailles d’équipes, classement des médailles, etc.).
5. Jeux de tests automatisés pour valider cohérence et intégrité de notre code et notre base.

---
## 1. Structure du dépôt

```
cebd-jo-2025/
	main.py                  # Interface menu simple (CLI)
	actions/
		database_functions.py  # Création / insertion / suppression
		database_queries.py    # Exemples de requêtes (liste épreuves...)
	utils/
		db.py                  # Exécution sécurisée de scripts SQL (executescript)
		excel_extractor.py     # Génération du fichier d'insertion depuis Excel ( genere data/vo_extractionDB.sql )
	data/
		v0_createDB.sql        # Schéma (tables + contraintes)
		v0_viewDB.sql          # Vues analytiques
		v0_triggerDB.sql       # Triggers d’intégrité
		v0_deleteDB.sql        # Script de suppresion/nettoyage de la base
		LesJO.xlsx             # Source des données (non versionnée si volumineuse)
	tests/
		test_db_validation.py  # Validation automatique (compte, triggers, vues)
```

---
## 2. Objectifs pédagogiques
- Illustrer la transition du modèle conceptuel au modèle physique.
- Manipuler les clés composites (ex : `Inscription(numIn, numEp)`).
- Mettre en œuvre des contraintes CHECK pour la cohérence métier (forme d’épreuve, catégories, tailles d’équipes).
- Appliquer la génération de données (Excel → SQL).
- Démontrer l’usage de triggers pour renforcer les règles au-delà des contraintes déclaratives.
- Exploiter la notion des vues.

---
## 3. Schéma relationnel (résumé)

| Table | Rôle | Points clés |
|-------|------|-------------|
| Discipline | Liste des disciplines | PK `nomDi` |
| LesEpreuves | Épreuves des JO | Forme (`individuelle`, `par equipe`, `par couple`), catégorie (`feminin`, `masculin`, `mixte`), date nullable, `nbSportifsEp` conforme à la forme |
| LesSportifs | Sportifs | Catégorie sportive (`feminin` ou `masculin`), date de naissance |
| Equipe | Équipes nationales | Numéro borné (1–100) |
| AppartientA | Association Sportif–Équipe | PK composite `(numSp, numEq)` |
| Inscription | Super-table des participations | PK composite `(numIn, numEp)`, `numIn` unique pour réutilisation dans sous-classes |
| InscriptionIndiv | Détail inscription individuelle | FK vers Inscription + FK sportif |
| InscriptionEquipe | Détail inscription équipe | FK vers Inscription + FK équipe |
| Or / Argent / Bronze | Médailles attribuées | FK composite `(numIn,numEp)` vers Inscription |

Contraintes notables :
- Forme d’épreuve contrôlée (`chk_lesepreuve_forme`).
- Catégorie d’épreuve contrôlée (`chk_lesepreuve_categorie`).
- Cohérence `nbSportifsEp` selon la forme (`individuelle` → NULL, `par couple` → 2, `par equipe` → NULL ou >0).
- Clé composite dans les sous-classes pour refléter la spécialisation sans redondance d’épreuve.

---
## 4. Vues analytiques (`v0_viewDB.sql`)
- `LesAgesSportifs` : âge calculé des sportifs à partir de la date de naissance.
- `LesNbsEquipiers` : cardinalité des membres par équipe (LEFT JOIN pour équipes vides).
- `AgesMoyensEquipesOr` : âge moyen (arrondi) des membres des équipes médaillées d’or.
- `ClassementPaysMedaille` : classement des pays (RANK) par nombre de médailles (or → argent → bronze → total → pays).

---
## 5. Triggers d’intégrité (`v0_triggerDB.sql`)
1. `trg_insc_indiv_validate` :
	 - Interdit une inscription individuelle sur épreuve non individuelle.
	 - Vérifie compatibilité catégorie sportif / épreuve (sauf épreuve `mixte`).
2. `trg_insc_equipe_validate` :
	 - Interdit une inscription d’équipe sur épreuve individuelle.
	 - Impose, pour forme `par couple`, exactement 2 membres.
	 - Contrôle la taille réelle de l’équipe pour forme `par equipe` si `nbSportifsEp` renseigné.

Les triggers utilisent `SELECT RAISE(ABORT, 'message')` pour bloquer l’insertion et renvoyer un message métier.

---
## 6. Génération et insertion des données

Le module `excel_extractor.py` lit le fichier Excel et génère un script SQL (`v0_extractionDB.sql` ou fichier temporaire) avec les INSERT dans l’ordre logique : disciplines → sportifs → équipes → appartenance → épreuves → inscriptions → médailles.

Points clés :
- Normalisation des valeurs (catégories, formes d’épreuve).
- Valeurs par défaut (par exemple `nbSportifsEp = NULL` sauf cas couple). 
- Attribution des médailles à partir de la feuille des résultats.

---
## 7. Tests (`tests/test_db_validation.py`)
Le script :
- Crée une base de test à partir des scripts.
- Exécute les inserts générés.
- Vérifie :
	- Compte minimal attendu de lignes (cohérence extraction).
	- Existence et lisibilité des vues (SELECT simple).
	- Fonctionnement des triggers en tentant des insertions invalides (capture des erreurs ABORT).

Usage recommandé pour valider rapidement après modification du schéma.

---
## 8. Installation & Pré-requis

Pré-requis : Python ≥ 3.10.

Installer l’environnement (si `requirements.txt` présent) :
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # (adapter si utilisation du fichier test)
```

Si le fichier Excel n’est pas dans `data/`, l’ajouter sous le nom `LesJO.xlsx`.

---
## 9. Utilisation (menu CLI)

Lancer le programme :
```bash
python main.py
```
Menu :
- 1 : création schéma + vues + triggers (`data/jo.db`).
- 2 : génération + insertion des données depuis Excel.
- 3 : suppression des objets (DROP …).
- 4 : exemple de requête listant les épreuves d’une discipline.

Exécution directe sans menu (depuis Python) :
```python
import sqlite3
from actions import database_functions
conn = sqlite3.connect('data/jo.db')
database_functions.database_create(conn)
database_functions.database_insert(conn)
```

---
## 10. Séquence technique recommandée
1. Vérifier / placer `LesJO.xlsx` dans `data/`.
2. `python main.py` → Option 1 (création).
3. Option 2 (insertion). Vérifier absence d’erreurs.
4. Interroger les vues, ex. :
	 ```sql
	 SELECT * FROM LesAgesSportifs LIMIT 10;
	 SELECT * FROM ClassementPaysMedaille ORDER BY rang;
	 ```
5. Tester triggers (insertion volontairement invalide) pour observer le message d’abort.
6. Lancer le script de test de validation (facultatif) :
	 ```bash
	 python tests/test_db_validation.py
	 ```

---
## 11. Points de conception notables
- Usage de la clé composite `(numIn, numEp)` pour relier les sous-classes d’inscription sans duplication de la référence épreuve.
- Nullabilité de `dateEp` pour couvrir les épreuves sans date dans la source.

---
## 12. Idées d’extensions
- Ajouter un trigger empêchant qu’une même épreuve reçoive deux médailles du même type.
- Introduire une table de résultats détaillés (temps, score) pour enrichir les analyses.
- Exposer une API REST (FastAPI) lisant la base SQLite.
- Générer des statistiques supplémentaires (distribution par tranche d’âge, ratio médailles / participants par pays).

---
## 13. Dépannage rapide
| Problème | Cause fréquente | Solution |
|----------|-----------------|----------|
| Erreur near "équipe" | Apostrophe mal échappée dans trigger | Vérifier chaînes : utiliser `''` pour une apostrophe |
| Trigger non actif | Fichier exécuté en mode split ancien | Confirmer usage `executescript` dans `db.updateDBfile` |
| Médailles absentes | Extraction incomplète | Regénérer script d’insertion via option 2 |
| Conflit nbSportifsEp | Valeur non conforme à forme | Adapter Excel / logique défaut dans extraction |


---
## 14. Auteurs
Travail étudiant (L3) – Adapté et structuré dans le cadre de l’UE CEBD. 
- @Laghrouy 
- @TomGontard

---
## 15. Vérification rapide
Pour vérifier les triggers après modification :
```bash
python - <<'PY'
import sqlite3
from actions import database_functions
conn=sqlite3.connect(':memory:')
database_functions.database_create(conn)
print('OK création schema + triggers')
PY
```

---
## 16. Remarques finales
La séparation claire (schéma / vues / triggers / insertion) facilite la maintenance et le rechargement intégral de la base. La génération SQL intermédiaire documente implicitement la transformation des données sources.
