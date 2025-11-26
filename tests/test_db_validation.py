"""
Script de validation de la base JO.
Exécuter: python tests/test_db_validation.py

Vérifie:
 - Création du schéma, vues et triggers
 - Insertion des données depuis LesJO.xlsx
 - Cohérence du nombre d'épreuves (Excel vs BD)
 - Présence des médailles et vues non vides
 - Fonctionnement des triggers (insertion invalide bloquée)
"""

import os
import sys
import sqlite3
import pandas as pd

# Assurer que le dossier racine (contenant actions/, utils/) est dans sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from actions import database_functions
from utils import excel_extractor, db

EXCEL_FILE = os.path.join(ROOT_DIR, "data", "LesJO.xlsx")
DB_FILE = os.path.join(ROOT_DIR, "data", "test_validation.db")

def print_result(label: str, ok: bool, detail: str = ""):
    status = "OK" if ok else "ECHEC"
    print(f"[{'V' if ok else 'X'}] {label:<50} {status} {detail}")

def main():
    # Nettoyage éventuel
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    # Lecture Excel pour attentes
    if not os.path.exists(EXCEL_FILE):
        print_result("Fichier Excel présent", False, "absent")
        return
    df_epreuves = pd.read_excel(EXCEL_FILE, sheet_name='LesEpreuves', dtype=str)
    df_epreuves = df_epreuves.where(pd.notnull(df_epreuves), 'null')
    expected_num_epreuves = len(set(df_epreuves['numEp']))

    # Création BD
    conn = sqlite3.connect(DB_FILE)
    try:
        database_functions.database_create(conn)
        print_result("Création schéma + vues + triggers", True)
    except Exception as e:
        print_result("Création schéma", False, repr(e))
        return

    # Génération + insertion
    try:
        tmp_sql = os.path.join(ROOT_DIR, 'data', 'tmp_validation_inserts.sql')
        excel_extractor.generate_sql_insert_file(conn, EXCEL_FILE, tmp_sql)
        db.updateDBfile(conn, tmp_sql)
        conn.commit()
        print_result("Insertion données", True)
    except Exception as e:
        print_result("Insertion données", False, repr(e))
        return

    cur = conn.cursor()

    # Vérification nombre d'épreuves
    try:
        db_count = cur.execute("SELECT COUNT(*) FROM LesEpreuves").fetchone()[0]
        print_result("Nombre d'épreuves (Excel vs BD)", db_count == expected_num_epreuves, f"Excel={expected_num_epreuves} BD={db_count}")
    except Exception as e:
        print_result("Lecture LesEpreuves", False, repr(e))

    # Vérification médailles
    for table in ["Or", "Argent", "Bronze"]:
        try:
            count = cur.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            print_result(f"Table {table} non vide", count > 0, f"{count} lignes")
        except Exception as e:
            print_result(f"Lecture table {table}", False, repr(e))

    # Vérification vues
    vues = ["LesAgesSportifs", "LesNbsEquipiers", "AgesMoyensEquipesOr", "ClassementPaysMedaille"]
    for v in vues:
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
            print_result(f"Vue {v} accessible", True, f"{count} lignes")
        except Exception as e:
            print_result(f"Vue {v} accessible", False, repr(e))

    # Test trigger InscriptionIndiv: inscrire sportif sur épreuve non individuelle
    trigger_indiv_ok = False
    try:
        # On choisit une épreuve 'par equipe' (ex: numEp=5 si présent)
        ep_non_ind = cur.execute("SELECT numEp FROM LesEpreuves WHERE formeEp <> 'individuelle' LIMIT 1").fetchone()
        sp_any = cur.execute("SELECT numSp FROM LesSportifs LIMIT 1").fetchone()
        if ep_non_ind and sp_any:
            numEp_bad = ep_non_ind[0]
            numSp = sp_any[0]
            # Créer inscription artificielle
            cur.execute("INSERT INTO Inscription(numIn, numEp) VALUES (?, ?)", (99990, numEp_bad))
            try:
                cur.execute("INSERT INTO InscriptionIndiv(numIn, numEp, numSp) VALUES (?,?,?)", (99990, numEp_bad, numSp))
            except sqlite3.DatabaseError as te:
                trigger_indiv_ok = 'individuelle interdite' in str(te).lower()
        conn.rollback()  # rollback test
    except Exception as e:
        pass
    print_result("Trigger InscriptionIndiv (forme) actif", trigger_indiv_ok)

    # Test trigger InscriptionEquipe: équipe sur épreuve individuelle
    trigger_equipe_forme_ok = False
    try:
        ep_ind = cur.execute("SELECT numEp FROM LesEpreuves WHERE formeEp='individuelle' LIMIT 1").fetchone()
        eq_any = cur.execute("SELECT numEq FROM Equipe LIMIT 1").fetchone()
        if ep_ind and eq_any:
            numEp_ind = ep_ind[0]
            numEq = eq_any[0]
            cur.execute("INSERT INTO Inscription(numIn, numEp) VALUES (?, ?)", (99991, numEp_ind))
            try:
                cur.execute("INSERT INTO InscriptionEquipe(numIn, numEp, numEq) VALUES (?,?,?)", (99991, numEp_ind, numEq))
            except sqlite3.DatabaseError as te:
                trigger_equipe_forme_ok = 'individuelle' in str(te).lower()
        conn.rollback()
    except Exception:
        pass
    print_result("Trigger InscriptionEquipe (épreuve individuelle) actif", trigger_equipe_forme_ok)

    # Résumé final
    print("\nFin des tests.")
    conn.close()

if __name__ == "__main__":
    main()