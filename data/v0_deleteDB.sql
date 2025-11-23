-- Ordre de suppression respectant les dépendances (FK) :
-- Vues -> Médailles -> Sous-classes -> Inscription -> Associations -> Entités de base.

DROP VIEW IF EXISTS LesAgesSportifs;
DROP VIEW IF EXISTS LesNbsEquipiers;
DROP VIEW IF EXISTS AgesMoyensEquipesOr;
DROP VIEW IF EXISTS ClassementPaysMedaille;

DROP TABLE IF EXISTS "Or";
DROP TABLE IF EXISTS "Argent";
DROP TABLE IF EXISTS "Bronze";

DROP TABLE IF EXISTS "InscriptionIndiv";
DROP TABLE IF EXISTS "InscriptionEquipe";
DROP TABLE IF EXISTS "Inscription";

DROP TABLE IF EXISTS "AppartientA";
DROP TABLE IF EXISTS "LesSportifs";
DROP TABLE IF EXISTS "Equipe";
DROP TABLE IF EXISTS "LesEpreuves";
DROP TABLE IF EXISTS "Discipline";

-- =====================================================================