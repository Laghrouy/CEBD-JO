-- =====================================================================
-- VUES DEMANDEES
-- =====================================================================
DROP VIEW IF EXISTS LesAgesSportifs;
CREATE VIEW LesAgesSportifs AS
SELECT
    s.numSp,
    s.nomSp,
    s.prenomSp,
    s.pays,
    s.categorieSp,
    s.dateNaisSp,
    CAST((julianday('now') - julianday(s.dateNaisSp)) / 365.25 AS INTEGER) AS ageSp
FROM LesSportifs s;

-- =====================================================================
DROP VIEW IF EXISTS LesNbsEquipiers;
CREATE VIEW LesNbsEquipiers AS
SELECT e.numEq, COALESCE(COUNT(a.numSp), 0) AS nbEquipiersEq
FROM Equipe e
LEFT JOIN AppartientA a ON a.numEq = e.numEq
GROUP BY e.numEq;

-- =====================================================================
DROP VIEW IF EXISTS AgesMoyensEquipesOr;
CREATE VIEW AgesMoyensEquipesOr AS
SELECT
    ie.numEq,
    ROUND(AVG(DISTINCT (julianday('now') - julianday(s.dateNaisSp)) / 365.25), 2) AS ageMoyEqOr
FROM "Or" o
JOIN Inscription i ON i.numIn = o.numIn AND i.numEp = o.numEp
JOIN InscriptionEquipe ie ON ie.numIn = i.numIn AND ie.numEp = i.numEp
JOIN AppartientA a ON a.numEq = ie.numEq
JOIN LesSportifs s ON s.numSp = a.numSp
GROUP BY ie.numEq;

-- =====================================================================
DROP VIEW IF EXISTS ClassementPaysMedaille;
CREATE VIEW ClassementPaysMedaille AS
WITH medals AS (
    SELECT 'or' AS type, o.numEp, o.numIn,
           COALESCE(eq.pays, sp.pays) AS pays
    FROM "Or" o
    JOIN Inscription i ON i.numIn = o.numIn AND i.numEp = o.numEp
    LEFT JOIN InscriptionEquipe ie ON ie.numIn = i.numIn AND ie.numEp = i.numEp
    LEFT JOIN Equipe eq ON eq.numEq = ie.numEq
    LEFT JOIN InscriptionIndiv ii ON ii.numIn = i.numIn AND ii.numEp = i.numEp
    LEFT JOIN LesSportifs sp ON sp.numSp = ii.numSp
    UNION ALL
    SELECT 'argent' AS type, a.numEp, a.numIn,
           COALESCE(eq.pays, sp.pays) AS pays
    FROM "Argent" a
    JOIN Inscription i ON i.numIn = a.numIn AND i.numEp = a.numEp
    LEFT JOIN InscriptionEquipe ie ON ie.numIn = i.numIn AND ie.numEp = i.numEp
    LEFT JOIN Equipe eq ON eq.numEq = ie.numEq
    LEFT JOIN InscriptionIndiv ii ON ii.numIn = i.numIn AND ii.numEp = i.numEp
    LEFT JOIN LesSportifs sp ON sp.numSp = ii.numSp
    UNION ALL
    SELECT 'bronze' AS type, b.numEp, b.numIn,
           COALESCE(eq.pays, sp.pays) AS pays
    FROM "Bronze" b
    JOIN Inscription i ON i.numIn = b.numIn AND i.numEp = b.numEp
    LEFT JOIN InscriptionEquipe ie ON ie.numIn = i.numIn AND ie.numEp = i.numEp
    LEFT JOIN Equipe eq ON eq.numEq = ie.numEq
    LEFT JOIN InscriptionIndiv ii ON ii.numIn = i.numIn AND ii.numEp = i.numEp
    LEFT JOIN LesSportifs sp ON sp.numSp = ii.numSp
), agg AS (
    SELECT
        pays,
        COUNT(CASE WHEN type = 'or' THEN 1 END) AS nbOr,
        COUNT(CASE WHEN type = 'argent' THEN 1 END) AS nbArgent,
        COUNT(CASE WHEN type = 'bronze' THEN 1 END) AS nbBronze,
        COUNT(*) AS totalMed
    FROM medals
    GROUP BY pays
)
SELECT
    pays,
    nbOr,
    nbArgent,
    nbBronze,
    totalMed,
    RANK() OVER (ORDER BY nbOr DESC, nbArgent DESC, nbBronze DESC, totalMed DESC, pays ASC) AS rang
FROM agg;
-- =====================================================================
