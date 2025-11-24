-- =====================================================================
-- -------------------------TRIGGERS -----------------------------------
-- =====================================================================

-- 1) Interdire les inscriptions individuelles sur des épreuves non individuelles
--    et vérifier la cohérence de catégorie (mixte autorise tout)
CREATE TRIGGER trg_insc_indiv_validate
BEFORE INSERT ON InscriptionIndiv
FOR EACH ROW
BEGIN
    -- Refuser si l'épreuve n'est pas individuelle
    SELECT RAISE(ABORT, 'Inscription individuelle interdite pour cette épreuve')
    WHERE EXISTS (
        SELECT 1
        FROM Inscription i
        JOIN LesEpreuves e ON e.numEp = i.numEp
        WHERE i.numIn = NEW.numIn
          AND e.formeEp <> 'individuelle'
    );

    -- Refuser si la catégorie ne correspond pas (sauf mixte)
    SELECT RAISE(ABORT, 'Catégorie incompatible entre sportif et épreuve')
    WHERE EXISTS (
        SELECT 1
        FROM Inscription i
        JOIN LesEpreuves e ON e.numEp = i.numEp
        JOIN LesSportifs s ON s.numSp = NEW.numSp
        WHERE i.numIn = NEW.numIn
          AND e.categorieEp <> 'mixte'
          AND e.categorieEp <> s.categorieSp
    );
END;

/

-- 2) Interdire les inscriptions d'équipe sur des épreuves individuelles
--    et imposer la taille d'équipe adaptée (par couple = 2, par équipe = nbSportifsEp si renseigné)
CREATE TRIGGER trg_insc_equipe_validate
BEFORE INSERT ON InscriptionEquipe
FOR EACH ROW
BEGIN
    -- Refuser si l'épreuve est individuelle
    SELECT RAISE(ABORT, 'Inscription équipe interdite pour une épreuve individuelle')
    WHERE EXISTS (
        SELECT 1
        FROM Inscription i
        JOIN LesEpreuves e ON e.numEp = i.numEp
        WHERE i.numIn = NEW.numIn
          AND e.formeEp = 'individuelle'
    );

    -- Si par couple: l'équipe doit contenir exactement 2 membres
    SELECT RAISE(ABORT, 'Equipe doit avoir exactement 2 membres pour une épreuve par couple')
    WHERE EXISTS (
        SELECT 1
        FROM Inscription i
        JOIN LesEpreuves e ON e.numEp = i.numEp
        WHERE i.numIn = NEW.numIn
          AND e.formeEp = 'par couple'
          AND (SELECT COUNT(*) FROM AppartientA a WHERE a.numEq = NEW.numEq) <> 2
    );

    -- Si par équipe et nbSportifsEp est renseigné: taille équipe doit correspondre
    SELECT RAISE(ABORT, 'Taille de l''équipe différente de nbSportifsEp pour cette épreuve')
    WHERE EXISTS (
        SELECT 1
        FROM Inscription i
        JOIN LesEpreuves e ON e.numEp = i.numEp
        WHERE i.numIn = NEW.numIn
          AND e.formeEp = 'par equipe'
          AND e.nbSportifsEp IS NOT NULL
          AND (SELECT COUNT(*) FROM AppartientA a WHERE a.numEq = NEW.numEq) <> e.nbSportifsEp
    );
END;

-- =====================================================================