import sqlite3, pandas
from sqlite3 import IntegrityError
from pathlib import Path

# Nouvelle fonction : génération d'un fichier SQL d'insertion pour le schéma actuel
def generate_sql_insert_file(data: sqlite3.Connection, excel_file: str, output_sql: str):
    """
        Lit les onglets Excel et génère un fichier SQL contenant les INSERT pour :
            - Discipline
            - Equipe
            - LesSportifs
            - AppartientA
            - LesEpreuves
            - Inscription (+ InscriptionIndiv / InscriptionEquipe)
            - Médailles (Or / Argent / Bronze)

        Hypothèses / limites :
            - Les colonnes des onglets 'LesSportifsEQ', 'LesEpreuves', 'LesInscriptions', 'LesResultats' sont conformes.
            - Onglet LesInscriptions contient deux colonnes: numIn, numEp MAIS on interprète numIn comme identifiant PARTICIPANT (numSp ou numEq).
                -> On génère un nouvel identifiant d'inscription interne (auto-incrément logique) par couple (participant, numEp).
            - Les valeurs 'numIn' < 1000 sont considérées comme équipes; >= 1000 comme sportifs.
            - LesResultats contient colonnes (numEp, gold, silver, bronze) avec identifiants participant (sportif ou équipe) et pas l'identifiant inscription.
                -> On crée les inscriptions manquantes pour relier les médailles.
            - Les valeurs 'null' (strings) deviennent NULL SQL.
    """
    df_sportifs = pandas.read_excel(excel_file, sheet_name='LesSportifsEQ', dtype=str)
    df_sportifs = df_sportifs.where(pandas.notnull(df_sportifs), 'null')

    df_epreuves = pandas.read_excel(excel_file, sheet_name='LesEpreuves', dtype=str)
    # Les inscriptions (participant,event)
    try:
        df_insc_raw = pandas.read_excel(excel_file, sheet_name='LesInscriptions', dtype=str)
        df_insc_raw = df_insc_raw.where(pandas.notnull(df_insc_raw), 'null')
    except Exception:
        df_insc_raw = pandas.DataFrame(columns=['numIn','numEp'])  # vide si absent
    # Les résultats (médailles)
    try:
        df_resultats = pandas.read_excel(excel_file, sheet_name='LesResultats', dtype=str)
        df_resultats = df_resultats.where(pandas.notnull(df_resultats), 'null')
    except Exception:
        df_resultats = pandas.DataFrame(columns=['numEp','gold','silver','bronze'])
    df_epreuves = df_epreuves.where(pandas.notnull(df_epreuves), 'null')

    disciplines = set(df_epreuves['nomDi'].dropna())
    equipes = {}
    # Construire mapping numEq -> pays à partir des sportifs (première occurrence)
    for ix, row in df_sportifs.iterrows():
        numEq = row['numEq']
        pays = row['pays']
        if numEq != 'null' and numEq not in equipes:
            equipes[numEq] = pays

    def sql_val(v: str):
        if v is None or v.lower() == 'null':
            return 'NULL'
        return "'" + v.replace("'", "''") + "'"

    lines = []
    lines.append('-- Fichier généré automatiquement depuis LesJO.xlsx')
    lines.append('BEGIN TRANSACTION;')

    # Discipline
    for d in sorted(disciplines):
        if d and d.lower() != 'null':
            lines.append(f"INSERT OR IGNORE INTO Discipline(nomDi) VALUES ({sql_val(d)});")

    # Equipe
    for numEq, pays in sorted(equipes.items(), key=lambda x: int(x[0])):
        lines.append(f"INSERT OR IGNORE INTO Equipe(numEq, pays) VALUES ({numEq}, {sql_val(pays)});")

    # LesSportifs + AppartientA
    for ix, row in df_sportifs.iterrows():
        numSp = row['numSp']
        nomSp = row['nomSp']
        prenomSp = row['prenomSp']
        pays = row['pays']
        categorieSp = row['categorieSp']
        dateNaisSp = row['dateNaisSp']
        numEq = row['numEq']
        lines.append(
            f"INSERT OR IGNORE INTO LesSportifs(numSp, nomSp, prenomSp, pays, categorieSp, dateNaisSp) VALUES ("\
            f"{numSp}, {sql_val(nomSp)}, {sql_val(prenomSp)}, {sql_val(pays)}, {sql_val(categorieSp)}, {sql_val(dateNaisSp)});"
        )
        if numEq.lower() != 'null':
            lines.append(f"INSERT OR IGNORE INTO AppartientA(numSp, numEq) VALUES ({numSp}, {numEq});")

    # LesEpreuves
    for ix, row in df_epreuves.iterrows():
        numEp = row['numEp']
        nomEp = row['nomEp']
        formeEp = row['formeEp']
        nomDi = row['nomDi']
        categorieEp = row['categorieEp']
        nbSportifsEp = row['nbSportifsEp']
        dateEp = row['dateEp']
        nb_val = 'NULL' if nbSportifsEp.lower() == 'null' else nbSportifsEp
        date_val = 'NULL' if dateEp.lower() == 'null' else sql_val(dateEp)
        lines.append(
            f"INSERT OR IGNORE INTO LesEpreuves(numEp, nomEp, formeEp, nomDi, categorieEp, dateEp, nbSportifsEp) VALUES ("\
            f"{numEp}, {sql_val(nomEp)}, {sql_val(formeEp)}, {sql_val(nomDi)}, {sql_val(categorieEp)}, {date_val}, {nb_val});"
        )

    # Inscriptions: construire mapping participant+epreuve -> numInInscription interne
    inscription_map = {}  # (participant_id, numEp) -> internal_numIn
    next_numIn = 1

    def is_team(pid: str) -> bool:
        try:
            return pid != 'null' and int(pid) < 1000
        except ValueError:
            return False

    def is_sportif(pid: str) -> bool:
        try:
            return pid != 'null' and 1000 <= int(pid) <= 2000
        except ValueError:
            return False

    # Pré-charger à partir de LesInscriptions (interprété comme participant,event)
    for ix, row in df_insc_raw.iterrows():
        participant = row['numIn']
        numEp = row['numEp']
        if participant.lower() == 'null' or numEp.lower() == 'null':
            continue
        key = (participant, numEp)
        if key not in inscription_map:
            internal_num = next_numIn
            next_numIn += 1
            inscription_map[key] = internal_num

            # Inscription
            lines.append(f"INSERT OR IGNORE INTO Inscription(numIn, numEp) VALUES ({internal_num}, {numEp});")
            # Sous-classe
            if is_team(participant):
                lines.append(f"INSERT OR IGNORE INTO InscriptionEquipe(numIn, numEp, numEq) VALUES ({internal_num}, {numEp}, {participant});")
            elif is_sportif(participant):
                lines.append(f"INSERT OR IGNORE INTO InscriptionIndiv(numIn, numEp, numSp) VALUES ({internal_num}, {numEp}, {participant});")
            else:
                lines.append(f"-- Participant {participant} ignoré (type inconnu) pour épreuve {numEp}")

    # Traiter les médailles -> assurer existence inscription puis insérer Or/Argent/Bronze
    def ensure_inscription(participant: str, numEp: str):
        if participant.lower() == 'null' or numEp.lower() == 'null':
            return None
        key = (participant, numEp)
        if key not in inscription_map:
            internal_num = next_numIn
            next_numIn += 1
            inscription_map[key] = internal_num
            lines.append(f"INSERT OR IGNORE INTO Inscription(numIn, numEp) VALUES ({internal_num}, {numEp});")
            if is_team(participant):
                lines.append(f"INSERT OR IGNORE INTO InscriptionEquipe(numIn, numEp, numEq) VALUES ({internal_num}, {numEp}, {participant});")
            elif is_sportif(participant):
                lines.append(f"INSERT OR IGNORE INTO InscriptionIndiv(numIn, numEp, numSp) VALUES ({internal_num}, {numEp}, {participant});")
            else:
                lines.append(f"-- Participant {participant} ignoré (type inconnu) pour épreuve {numEp} (médailles)")
        return inscription_map[key]

    for ix, row in df_resultats.iterrows():
        numEp = row.get('numEp','null')
        gold = row.get('gold','null')
        silver = row.get('silver','null')
        bronze = row.get('bronze','null')
        # OR
        gi = ensure_inscription(gold, numEp)
        if gi is not None:
            # "Or" est un mot clé logique en SQL, il faut le citer
            lines.append(f"INSERT OR IGNORE INTO \"Or\"(numEp, numIn) VALUES ({numEp}, {gi});")
        # ARGENT
        si = ensure_inscription(silver, numEp)
        if si is not None:
            lines.append(f"INSERT OR IGNORE INTO \"Argent\"(numEp, numIn) VALUES ({numEp}, {si});")
        # BRONZE
        bi = ensure_inscription(bronze, numEp)
        if bi is not None:
            lines.append(f"INSERT OR IGNORE INTO \"Bronze\"(numEp, numIn) VALUES ({numEp}, {bi});")

    lines.append('COMMIT;')

    Path(output_sql).write_text('\n'.join(lines), encoding='utf-8')
    print(f"Fichier SQL généré : {output_sql} ({len(lines)} lignes)")

# Fonction permettant de lire le fichier Excel des JO et d'insérer les données dans la base
def read_excel_file_V0(data:sqlite3.Connection, file):
    # Lecture de l'onglet du fichier excel LesSportifsEQ, en interprétant toutes les colonnes comme des strings
    # pour construire uniformement la requête
    df_sportifs = pandas.read_excel(file, sheet_name='LesSportifsEQ', dtype=str)
    df_sportifs = df_sportifs.where(pandas.notnull(df_sportifs), 'null')

    cursor = data.cursor()
    for ix, row in df_sportifs.iterrows():
        try:
            query = "insert into V0_LesSportifsEQ values ({},'{}','{}','{}','{}','{}',{})".format(
                row['numSp'], row['nomSp'], row['prenomSp'], row['pays'], row['categorieSp'], row['dateNaisSp'], row['numEq'])
            # On affiche la requête pour comprendre la construction. A enlever une fois compris.
            print(query)
            cursor.execute(query)
        except IntegrityError as err:
            print(err)

    # Lecture de l'onglet LesEpreuves du fichier excel, en interprétant toutes les colonnes comme des string
    # pour construire uniformement la requête
    df_epreuves = pandas.read_excel(file, sheet_name='LesEpreuves', dtype=str)
    df_epreuves = df_epreuves.where(pandas.notnull(df_epreuves), 'null')

    cursor = data.cursor()
    for ix, row in df_epreuves.iterrows():
        try:
            query = "insert into V0_LesEpreuves values ({},'{}','{}','{}','{}',{},".format(
                row['numEp'], row['nomEp'], row['formeEp'], row['nomDi'], row['categorieEp'], row['nbSportifsEp'])

            if row['dateEp'] != 'null':
                query = query + "'{}')".format(row['dateEp'])
            else:
                query = query + "null)"
            # On affiche la requête pour comprendre la construction. A enlever une fois compris.
            print(query)
            cursor.execute(query)
        except IntegrityError as err:
            print(f"{err} : \n{row}")
