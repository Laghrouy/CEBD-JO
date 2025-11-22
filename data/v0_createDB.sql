
-- =====================================================================
-- TABLE DISCIPLINE
-- =====================================================================

CREATE TABLE Discipline (
    nomDi text PRIMARY KEY
);
-- =====================================================================
-- TABLE LES EPREUVES
-- =====================================================================

CREATE TABLE LesEpreuves (
    numEp           serial PRIMARY KEY,
    nomEp           text NOT NULL,
    formeEp         varchar(13) NOT NULL,
    nomDi           text NOT NULL,
    categorieEp     varchar(10) NOT NULL,
    dateEp          date, -- autoriser NULL pour les épreuves sans date dans l'Excel
    nbSportifsEp    integer,
    CONSTRAINT chk_lesepreuve_forme
        CHECK (formeEp IN ('individuelle','par equipe','par couple')),
    CONSTRAINT chk_lesepreuve_categorie
        CHECK (categorieEp IN ('feminin','masculin','mixte')),
    -- Nouvelle contrainte unifiée pour éviter conflit précédent
    CONSTRAINT chk_lesepreuve_nb_sportifs
        CHECK (
            (formeEp = 'individuelle' AND nbSportifsEp IS NULL)
            OR (formeEp = 'par equipe' AND nbSportifsEp IS NULL OR nbSportifsEp > 0)
            OR (formeEp = 'par couple' AND nbSportifsEp = 2)
        ),
    CONSTRAINT fk_lesepreuve_discipline
        FOREIGN KEY (nomDi) REFERENCES "Discipline"(nomDi) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- =====================================================================
-- TABLE EQUIPE
-- =====================================================================

CREATE TABLE "Equipe" (
    numEq   integer PRIMARY KEY,
    pays    varchar(50) NOT NULL,
    CONSTRAINT chk_equipe_numEq
        CHECK (numEq BETWEEN 1 AND 100)
);


-- =====================================================================
-- TABLE LES SPORTIFS
-- =====================================================================

CREATE TABLE "LesSportifs" (
    numSp       integer PRIMARY KEY,
    nomSp       varchar(50) NOT NULL,
    prenomSp    varchar(50) NOT NULL,
    pays        varchar(50) NOT NULL,
    categorieSp varchar(10) NOT NULL,
    dateNaisSp  date NOT NULL,
    CONSTRAINT chk_lessportifs_numSp
        CHECK (numSp BETWEEN 1000 AND 1500),
    CONSTRAINT chk_lessportifs_categorieSp
        CHECK (categorieSp IN ('feminin','masculin'))
);


-- =====================================================================
-- TABLE APPARTIENTA (association explicite sportif - equipe)
-- =====================================================================

CREATE TABLE "AppartientA" (
    numSp   integer NOT NULL,
    numEq   integer NOT NULL,
    PRIMARY KEY (numSp, numEq),
    CONSTRAINT fk_appartienta_sportif
        FOREIGN KEY (numSp) REFERENCES "LesSportifs"(numSp) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_appartienta_equipe
        FOREIGN KEY (numEq) REFERENCES "Equipe"(numEq) ON UPDATE CASCADE ON DELETE CASCADE
);


-- =====================================================================
-- TABLE INSCRIPTION (super-classe)
-- =====================================================================

CREATE TABLE "Inscription" (
    numIn   serial,
    numEp   integer NOT NULL,
    PRIMARY KEY (numIn, numEp),
    CONSTRAINT uq_inscription_numIn UNIQUE (numIn),
    CONSTRAINT fk_inscription_epreuve
        FOREIGN KEY (numEp) REFERENCES "LesEpreuves"(numEp) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- =====================================================================
-- TABLE INSCRIPTION INDIVIDUELLE (sous-classe)
-- =====================================================================

CREATE TABLE "InscriptionIndiv" (
    numIn   integer NOT NULL,
    numEp   integer NOT NULL,
    numSp   integer NOT NULL,
    PRIMARY KEY (numIn, numEp),
    CONSTRAINT fk_insc_indiv_inscription
        FOREIGN KEY (numIn, numEp) REFERENCES "Inscription"(numIn, numEp) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_insc_indiv_sportif
        FOREIGN KEY (numSp) REFERENCES "LesSportifs"(numSp) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- =====================================================================
-- TABLE INSCRIPTION EQUIPE (sous-classe)
-- =====================================================================

CREATE TABLE "InscriptionEquipe" (
    numIn   integer NOT NULL,
    numEp   integer NOT NULL,
    numEq   integer NOT NULL,
    PRIMARY KEY (numIn, numEp),
    CONSTRAINT fk_insc_eq_inscription
        FOREIGN KEY (numIn, numEp) REFERENCES "Inscription"(numIn, numEp) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_insc_eq_equipe
        FOREIGN KEY (numEq) REFERENCES "Equipe"(numEq) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- =====================================================================
-- MEDAILLES : OR / ARGENT / BRONZE
-- Contrainte : (numEp, numIn) doit référencer une inscription cohérente
--             (Inscription.numEp = numEp).
-- =====================================================================

CREATE TABLE "Or" (
    numEp   integer NOT NULL,
    numIn   integer NOT NULL,
    PRIMARY KEY (numEp),
    CONSTRAINT uq_or_numIn UNIQUE (numIn),
    CONSTRAINT fk_or_inscription
        FOREIGN KEY (numIn, numEp) REFERENCES "Inscription"(numIn, numEp) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE "Argent" (
    numEp   integer NOT NULL,
    numIn   integer NOT NULL,
    PRIMARY KEY (numEp),
    CONSTRAINT uq_argent_numIn UNIQUE (numIn),
    CONSTRAINT fk_argent_inscription
        FOREIGN KEY (numIn, numEp) REFERENCES "Inscription"(numIn, numEp) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE "Bronze" (
    numEp   integer NOT NULL,
    numIn   integer NOT NULL,
    PRIMARY KEY (numEp),
    CONSTRAINT uq_bronze_numIn UNIQUE (numIn),
    CONSTRAINT fk_bronze_inscription
        FOREIGN KEY (numIn, numEp) REFERENCES "Inscription"(numIn, numEp) ON UPDATE CASCADE ON DELETE CASCADE
);

-- =====================================================================