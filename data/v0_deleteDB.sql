-- Ordre de suppression respectant les dépendances (FK) :
-- Médailles -> Sous-classes -> Inscription -> Associations -> Entités de base.

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