import sqlite3

# Fonction permettant d'exécuter toutes les requêtes sql d'un fichier
# Elles doivent être séparées par un point-virgule
def updateDBfile(data:sqlite3.Connection, file, trigger=False):

    # Lecture du fichier et placement des requêtes dans un tableau
    createFile = open(file, 'r')
    createSql = createFile.read()
    createFile.close()

    # Séparateur ; pour les requêtes classiques et / pour les triggers
    if trigger is False:
        sqlQueries = createSql.split(";")
    else:
        sqlQueries = createSql.split("/")

    # Exécution de toutes les requêtes du tableau
    cursor = data.cursor()
    for query in sqlQueries:
        cursor.execute(query)