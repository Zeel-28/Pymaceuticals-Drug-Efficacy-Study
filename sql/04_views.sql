-- =============================================================================
-- FILE: sql/04_views.sql
-- PROJECT: Pymaceuticals Drug Efficacy Study
-- PURPOSE: Reusable analytical views for BI tools / dashboards
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- VIEW 1: Full denormalized study view (one row per observation)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_study_full AS
SELECT
    sr.result_id,
    sr.mouse_id,
    m.drug_regimen,
    m.sex,
    m.age_months,
    m.age_group,
    m.weight_g,
    m.weight_category,
    sr.timepoint,
    sr.tumor_volume_mm3,
    sr.tumor_vol_change_mm3,
    sr.tumor_vol_change_pct,
    sr.metastatic_sites,
    dr.is_benchmark,
    dr.is_primary
FROM study_results  sr
JOIN mouse_metadata m  ON sr.mouse_id    = m.mouse_id
JOIN drug_regimens  dr ON m.drug_regimen = dr.regimen_name;


-- ─────────────────────────────────────────────────────────────────────────────
-- VIEW 2: Drug regimen efficacy summary
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_regimen_efficacy AS
SELECT
    m.drug_regimen,
    dr.is_benchmark,
    dr.is_primary,
    COUNT(DISTINCT ms.mouse_id)                                         AS n_mice,
    ROUND(AVG(ms.final_tumor_vol)::NUMERIC, 2)                         AS avg_final_tumor_vol,
    ROUND(AVG(ms.tumor_reduction_mm3)::NUMERIC, 2)                     AS avg_reduction_mm3,
    ROUND(AVG(ms.tumor_reduction_pct)::NUMERIC, 2)                     AS avg_reduction_pct,
    ROUND(100.0 * SUM(CASE WHEN ms.tumor_reduction_mm3 > 0 THEN 1 ELSE 0 END)
          / COUNT(*), 1)                                                AS responder_rate_pct,
    ROUND(AVG(ms.max_metastatic)::NUMERIC, 2)                          AS avg_max_metastatic,
    ROUND(100.0 * SUM(ms.completed_study::INT) / COUNT(*), 1)          AS study_completion_pct,
    DENSE_RANK() OVER (ORDER BY AVG(ms.final_tumor_vol))               AS efficacy_rank
FROM mouse_summary  ms
JOIN mouse_metadata m  ON ms.mouse_id    = m.mouse_id
JOIN drug_regimens  dr ON m.drug_regimen = dr.regimen_name
GROUP BY m.drug_regimen, dr.is_benchmark, dr.is_primary;


-- ─────────────────────────────────────────────────────────────────────────────
-- VIEW 3: Tumour progression timeline (mean + SEM per regimen per timepoint)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_tumor_progression AS
SELECT
    m.drug_regimen,
    sr.timepoint,
    COUNT(*)                                                            AS n_mice,
    ROUND(AVG(sr.tumor_volume_mm3)::NUMERIC, 4)                        AS mean_tumor_vol,
    ROUND(STDDEV_SAMP(sr.tumor_volume_mm3)::NUMERIC, 4)                AS std_dev,
    ROUND((STDDEV_SAMP(sr.tumor_volume_mm3) / SQRT(COUNT(*)))
          ::NUMERIC, 4)                                                 AS sem,
    ROUND(MIN(sr.tumor_volume_mm3)::NUMERIC, 2)                        AS min_tumor_vol,
    ROUND(MAX(sr.tumor_volume_mm3)::NUMERIC, 2)                        AS max_tumor_vol
FROM study_results  sr
JOIN mouse_metadata m ON sr.mouse_id = m.mouse_id
GROUP BY m.drug_regimen, sr.timepoint;


-- ─────────────────────────────────────────────────────────────────────────────
-- VIEW 4: Individual mouse final outcomes
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_mouse_outcomes AS
SELECT
    ms.mouse_id,
    m.drug_regimen,
    m.sex,
    m.age_months,
    m.age_group,
    m.weight_g,
    m.weight_category,
    ms.total_timepoints,
    ms.max_timepoint,
    ms.completed_study,
    ms.initial_tumor_vol,
    ms.final_tumor_vol,
    ms.tumor_reduction_mm3,
    ms.tumor_reduction_pct,
    ms.max_tumor_vol,
    ms.min_tumor_vol,
    ms.max_metastatic,
    CASE
        WHEN ms.tumor_reduction_mm3 > 0 THEN 'Responder'
        ELSE 'Non-Responder'
    END AS response_status,
    DENSE_RANK() OVER (
        PARTITION BY m.drug_regimen
        ORDER BY ms.tumor_reduction_pct DESC
    ) AS within_regimen_rank
FROM mouse_summary  ms
JOIN mouse_metadata m ON ms.mouse_id = m.mouse_id;


-- ─────────────────────────────────────────────────────────────────────────────
-- VIEW 5: Sex-stratified regimen comparison
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_sex_stratified AS
SELECT
    m.drug_regimen,
    m.sex,
    COUNT(DISTINCT ms.mouse_id)                                         AS n_mice,
    ROUND(AVG(ms.final_tumor_vol)::NUMERIC, 2)                         AS avg_final_tv,
    ROUND(AVG(ms.tumor_reduction_pct)::NUMERIC, 2)                     AS avg_reduction_pct,
    ROUND(100.0 * SUM(CASE WHEN ms.tumor_reduction_mm3 > 0 THEN 1 ELSE 0 END)
          / COUNT(*), 1)                                                AS responder_rate_pct
FROM mouse_summary  ms
JOIN mouse_metadata m ON ms.mouse_id = m.mouse_id
GROUP BY m.drug_regimen, m.sex;
