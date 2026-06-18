-- =============================================================================
-- FILE: sql/01_schema.sql
-- PROJECT: Pymaceuticals Drug Efficacy Study
-- PURPOSE: Create all database tables for the study data warehouse
-- =============================================================================

-- Drop existing tables (safe re-run)
DROP TABLE IF EXISTS study_results;
DROP TABLE IF EXISTS mouse_metadata;
DROP TABLE IF EXISTS drug_regimens;
DROP TABLE IF EXISTS mouse_summary;

-- -----------------------------------------------------------------------------
-- Reference table: Drug regimens
-- -----------------------------------------------------------------------------
CREATE DATABASE PHARMA;

USE PHARMA;

CREATE TABLE drug_regimens (
    regimen_id      SERIAL PRIMARY KEY,
    regimen_name    VARCHAR(50)  NOT NULL UNIQUE,
    drug_class      VARCHAR(50),
    is_benchmark    BOOLEAN      DEFAULT FALSE,
    is_primary      BOOLEAN      DEFAULT FALSE,
    notes           TEXT
);

-- Seed reference data
INSERT INTO drug_regimens (regimen_name, drug_class, is_benchmark, is_primary, notes) VALUES
    ('Capomulin',  'Anti-angiogenic',  TRUE,  TRUE,  'Primary drug of interest'),
    ('Ramicane',   'Anti-proliferative', TRUE, FALSE, 'Benchmark comparator'),
    ('Infubinol',  'Topoisomerase inhibitor', TRUE, FALSE, 'Benchmark comparator'),
    ('Ceftamin',   'Antibiotic adjuvant', TRUE, FALSE, 'Benchmark comparator'),
    ('Propriva',   'Hormone therapy',    FALSE, FALSE, NULL),
    ('Stelasyn',   'Immunotherapy',      FALSE, FALSE, NULL),
    ('Zoniferol',  'Alkylating agent',   FALSE, FALSE, NULL),
    ('Ketapril',   'ACE inhibitor',      FALSE, FALSE, NULL),
    ('Naftisol',   'Antimetabolite',     FALSE, FALSE, NULL),
    ('Placebo',    'Control',            FALSE, FALSE, 'Negative control group');

-- -----------------------------------------------------------------------------
-- Mouse metadata table
-- -----------------------------------------------------------------------------
CREATE TABLE mouse_metadata (
    mouse_id        CHAR(4)      PRIMARY KEY,
    drug_regimen    VARCHAR(50)  NOT NULL,
    sex             VARCHAR(10)  NOT NULL CHECK (sex IN ('Male', 'Female')),
    age_months      SMALLINT     NOT NULL CHECK (age_months BETWEEN 0 AND 36),
    weight_g        NUMERIC(5,1) NOT NULL CHECK (weight_g > 0),

    -- Derived / enriched fields
    weight_category VARCHAR(20),
    age_group       VARCHAR(15),

    CONSTRAINT fk_regimen FOREIGN KEY (drug_regimen)
        REFERENCES drug_regimens (regimen_name)
);

CREATE INDEX idx_mouse_regimen ON mouse_metadata (drug_regimen);
CREATE INDEX idx_mouse_sex     ON mouse_metadata (sex);

-- -----------------------------------------------------------------------------
-- Study results table
-- -----------------------------------------------------------------------------
CREATE TABLE study_results (
    result_id           SERIAL       PRIMARY KEY,
    mouse_id            CHAR(4)      NOT NULL,
    timepoint           SMALLINT     NOT NULL CHECK (timepoint BETWEEN 0 AND 45),
    tumor_volume_mm3    NUMERIC(8,3) NOT NULL CHECK (tumor_volume_mm3 >= 0),
    metastatic_sites    SMALLINT     NOT NULL CHECK (metastatic_sites >= 0),

    -- Derived columns
    tumor_vol_change_mm3 NUMERIC(8,3),
    tumor_vol_change_pct NUMERIC(8,3),

    CONSTRAINT fk_mouse FOREIGN KEY (mouse_id)
        REFERENCES mouse_metadata (mouse_id),

    CONSTRAINT uq_mouse_timepoint UNIQUE (mouse_id, timepoint)
);

CREATE INDEX idx_results_mouse     ON study_results (mouse_id);
CREATE INDEX idx_results_timepoint ON study_results (timepoint);

-- Computed columns can be populated on insert via trigger or as a view
CREATE INDEX idx_results_tumor_vol ON study_results (tumor_volume_mm3);

-- -----------------------------------------------------------------------------
-- Mouse-level summary (materialised / precomputed)
-- -----------------------------------------------------------------------------
CREATE TABLE mouse_summary (
    mouse_id            CHAR(4)      PRIMARY KEY,
    drug_regimen        VARCHAR(50),
    sex                 VARCHAR(10),
    age_months          SMALLINT,
    weight_g            NUMERIC(5,1),
    total_timepoints    SMALLINT,
    max_timepoint       SMALLINT,
    initial_tumor_vol   NUMERIC(8,3),
    final_tumor_vol     NUMERIC(8,3),
    max_tumor_vol       NUMERIC(8,3),
    min_tumor_vol       NUMERIC(8,3),
    max_metastatic      SMALLINT,

    -- Derived
    tumor_reduction_mm3  NUMERIC(8,3)
        GENERATED ALWAYS AS (initial_tumor_vol - final_tumor_vol) STORED,
    tumor_reduction_pct  NUMERIC(8,3)
        GENERATED ALWAYS AS (
            ROUND((initial_tumor_vol - final_tumor_vol) / initial_tumor_vol * 100, 2)
        ) STORED,
    completed_study      BOOLEAN
        GENERATED ALWAYS AS (max_timepoint >= 45) STORED
);

CREATE INDEX idx_summary_regimen ON mouse_summary (drug_regimen);
