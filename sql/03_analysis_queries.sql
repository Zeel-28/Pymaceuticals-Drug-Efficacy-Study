-- =============================================================================
-- FILE: sql/03_analysis_queries.sql
-- PROJECT: Pymaceuticals Drug Efficacy Study
-- PURPOSE: Core analytical SQL queries — mirrors every section in eda.py
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 1: Dataset Overview
-- ─────────────────────────────────────────────────────────────────────────────

-- 1.1  High-level study metrics
SELECT
    COUNT(DISTINCT sr.mouse_id)         AS unique_mice,
    COUNT(DISTINCT m.drug_regimen)      AS drug_regimens,
    COUNT(DISTINCT sr.timepoint)        AS unique_timepoints,
    COUNT(*)                            AS total_observations,
    ROUND(AVG(m.age_months)::NUMERIC, 1) AS avg_age_months,
    ROUND(AVG(m.weight_g)::NUMERIC, 2)  AS avg_weight_g,
    SUM(CASE WHEN m.sex = 'Male'   THEN 1 ELSE 0 END) AS male_mice,
    SUM(CASE WHEN m.sex = 'Female' THEN 1 ELSE 0 END) AS female_mice
FROM study_results  sr
JOIN mouse_metadata m ON sr.mouse_id = m.mouse_id;


-- 1.2  Mice per drug regimen with sex breakdown
SELECT
    m.drug_regimen,
    COUNT(DISTINCT m.mouse_id)                                        AS total_mice,
    SUM(CASE WHEN m.sex = 'Male'   THEN 1 ELSE 0 END)               AS male_mice,
    SUM(CASE WHEN m.sex = 'Female' THEN 1 ELSE 0 END)               AS female_mice,
    ROUND(100.0 * SUM(CASE WHEN m.sex='Male' THEN 1 ELSE 0 END)
          / COUNT(DISTINCT m.mouse_id), 1)                            AS pct_male
FROM mouse_metadata m
GROUP BY m.drug_regimen
ORDER BY total_mice DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 2: Summary Statistics — Tumour Volume per Drug Regimen
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    m.drug_regimen,
    COUNT(*)                                                AS n_observations,
    ROUND(AVG(sr.tumor_volume_mm3)::NUMERIC, 4)            AS mean_tumor_vol,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
          (ORDER BY sr.tumor_volume_mm3)::NUMERIC, 4)      AS median_tumor_vol,
    ROUND(VAR_SAMP(sr.tumor_volume_mm3)::NUMERIC, 4)       AS variance,
    ROUND(STDDEV_SAMP(sr.tumor_volume_mm3)::NUMERIC, 4)    AS std_dev,
    ROUND((STDDEV_SAMP(sr.tumor_volume_mm3)
           / SQRT(COUNT(*)))::NUMERIC, 4)                   AS sem,
    ROUND(MIN(sr.tumor_volume_mm3)::NUMERIC, 2)            AS min_tumor_vol,
    ROUND(MAX(sr.tumor_volume_mm3)::NUMERIC, 2)            AS max_tumor_vol
FROM study_results  sr
JOIN mouse_metadata m ON sr.mouse_id = m.mouse_id
GROUP BY m.drug_regimen
ORDER BY mean_tumor_vol;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 3: Duplicate Detection
-- ─────────────────────────────────────────────────────────────────────────────

-- 3.1  Find mouse IDs with duplicate (mouse_id, timepoint) pairs
SELECT
    mouse_id,
    timepoint,
    COUNT(*) AS duplicate_count
FROM study_results
GROUP BY mouse_id, timepoint
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, mouse_id;


-- 3.2  Flag all records for duplicated mice
SELECT
    sr.*,
    m.drug_regimen,
    m.sex
FROM study_results sr
JOIN mouse_metadata m ON sr.mouse_id = m.mouse_id
WHERE sr.mouse_id IN (
    SELECT mouse_id
    FROM study_results
    GROUP BY mouse_id, timepoint
    HAVING COUNT(*) > 1
)
ORDER BY sr.mouse_id, sr.timepoint;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 4: Tumour Progression Over Time
-- ─────────────────────────────────────────────────────────────────────────────

-- 4.1  Mean tumour volume at each timepoint per regimen
SELECT
    m.drug_regimen,
    sr.timepoint,
    COUNT(*)                                                AS n_mice,
    ROUND(AVG(sr.tumor_volume_mm3)::NUMERIC, 4)            AS mean_tumor_vol,
    ROUND(STDDEV_SAMP(sr.tumor_volume_mm3)::NUMERIC, 4)    AS std_dev,
    ROUND((STDDEV_SAMP(sr.tumor_volume_mm3)
           / SQRT(COUNT(*)))::NUMERIC, 4)                   AS sem
FROM study_results  sr
JOIN mouse_metadata m ON sr.mouse_id = m.mouse_id
GROUP BY m.drug_regimen, sr.timepoint
ORDER BY m.drug_regimen, sr.timepoint;


-- 4.2  Tumour volume change from baseline (timepoint 0) per mouse per regimen
WITH baseline AS (
    SELECT mouse_id, tumor_volume_mm3 AS baseline_vol
    FROM study_results
    WHERE timepoint = 0
),
final AS (
    SELECT
        sr.mouse_id,
        sr.tumor_volume_mm3 AS final_vol,
        sr.timepoint        AS final_tp
    FROM study_results sr
    JOIN (
        SELECT mouse_id, MAX(timepoint) AS last_tp
        FROM study_results
        GROUP BY mouse_id
    ) ltp ON sr.mouse_id = ltp.mouse_id AND sr.timepoint = ltp.last_tp
)
SELECT
    m.drug_regimen,
    b.mouse_id,
    m.sex,
    ROUND(b.baseline_vol::NUMERIC, 2)                              AS baseline_vol_mm3,
    ROUND(f.final_vol::NUMERIC, 2)                                 AS final_vol_mm3,
    ROUND((f.final_vol - b.baseline_vol)::NUMERIC, 2)             AS change_mm3,
    ROUND(((f.final_vol - b.baseline_vol) / b.baseline_vol * 100)
          ::NUMERIC, 2)                                             AS change_pct,
    CASE
        WHEN f.final_vol < b.baseline_vol THEN 'Responder'
        ELSE 'Non-Responder'
    END                                                             AS response_status
FROM baseline b
JOIN final          f ON b.mouse_id = f.mouse_id
JOIN mouse_metadata m ON b.mouse_id = m.mouse_id
ORDER BY m.drug_regimen, change_pct;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 5: Quartile & Outlier Analysis (Benchmark Drugs)
-- ─────────────────────────────────────────────────────────────────────────────

WITH final_volumes AS (
    SELECT
        sr.mouse_id,
        m.drug_regimen,
        sr.tumor_volume_mm3
    FROM study_results sr
    JOIN mouse_metadata m ON sr.mouse_id = m.mouse_id
    JOIN (
        SELECT mouse_id, MAX(timepoint) AS last_tp
        FROM study_results GROUP BY mouse_id
    ) ltp ON sr.mouse_id = ltp.mouse_id AND sr.timepoint = ltp.last_tp
    WHERE m.drug_regimen IN ('Capomulin','Ramicane','Infubinol','Ceftamin')
),
quartiles AS (
    SELECT
        drug_regimen,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY tumor_volume_mm3) AS q1,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY tumor_volume_mm3) AS median,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY tumor_volume_mm3) AS q3
    FROM final_volumes
    GROUP BY drug_regimen
)
SELECT
    q.drug_regimen,
    ROUND(q.q1::NUMERIC, 2)                                   AS q1_mm3,
    ROUND(q.median::NUMERIC, 2)                               AS median_mm3,
    ROUND(q.q3::NUMERIC, 2)                                   AS q3_mm3,
    ROUND((q.q3 - q.q1)::NUMERIC, 2)                         AS iqr_mm3,
    ROUND((q.q1 - 1.5*(q.q3 - q.q1))::NUMERIC, 2)           AS lower_fence,
    ROUND((q.q3 + 1.5*(q.q3 - q.q1))::NUMERIC, 2)           AS upper_fence,
    SUM(CASE
        WHEN fv.tumor_volume_mm3 < q.q1 - 1.5*(q.q3-q.q1)
          OR fv.tumor_volume_mm3 > q.q3 + 1.5*(q.q3-q.q1)
        THEN 1 ELSE 0
    END)                                                       AS outlier_count
FROM quartiles q
JOIN final_volumes fv USING (drug_regimen)
GROUP BY q.drug_regimen, q.q1, q.median, q.q3
ORDER BY q.drug_regimen;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 6: Drug Efficacy Ranking
-- ─────────────────────────────────────────────────────────────────────────────

-- 6.1  Responder rate per regimen (tumour volume reduced vs baseline)
WITH response AS (
    SELECT
        m.drug_regimen,
        COUNT(*)                                            AS total_mice,
        SUM(CASE WHEN ms.tumor_reduction_mm3 > 0 THEN 1 ELSE 0 END) AS responders
    FROM mouse_summary ms
    JOIN mouse_metadata m ON ms.mouse_id = m.mouse_id
    GROUP BY m.drug_regimen
)
SELECT
    drug_regimen,
    total_mice,
    responders,
    ROUND(100.0 * responders / total_mice, 1)  AS responder_rate_pct
FROM response
ORDER BY responder_rate_pct DESC;


-- 6.2  Overall efficacy dashboard: avg final tumour vol + % reduction
SELECT
    m.drug_regimen,
    COUNT(DISTINCT ms.mouse_id)                                         AS n_mice,
    ROUND(AVG(ms.final_tumor_vol)::NUMERIC, 2)                         AS avg_final_tv,
    ROUND(AVG(ms.tumor_reduction_mm3)::NUMERIC, 2)                     AS avg_reduction_mm3,
    ROUND(AVG(ms.tumor_reduction_pct)::NUMERIC, 2)                     AS avg_reduction_pct,
    ROUND(AVG(ms.max_metastatic)::NUMERIC, 2)                          AS avg_max_metastatic,
    ROUND(100.0 * SUM(ms.completed_study::INT) / COUNT(*), 1)          AS study_completion_pct,
    DENSE_RANK() OVER (ORDER BY AVG(ms.final_tumor_vol))               AS efficacy_rank
FROM mouse_summary  ms
JOIN mouse_metadata m ON ms.mouse_id = m.mouse_id
GROUP BY m.drug_regimen
ORDER BY efficacy_rank;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 7: Correlation — Weight vs Avg Tumour Volume (Capomulin)
-- ─────────────────────────────────────────────────────────────────────────────

WITH capo_agg AS (
    SELECT
        sr.mouse_id,
        m.weight_g,
        AVG(sr.tumor_volume_mm3) AS avg_tumor_vol
    FROM study_results  sr
    JOIN mouse_metadata m ON sr.mouse_id = m.mouse_id
    WHERE m.drug_regimen = 'Capomulin'
    GROUP BY sr.mouse_id, m.weight_g
)
SELECT
    ROUND(CORR(weight_g, avg_tumor_vol)::NUMERIC, 4)       AS pearson_r,
    ROUND(REGR_SLOPE(avg_tumor_vol, weight_g)::NUMERIC, 4) AS ols_slope,
    ROUND(REGR_INTERCEPT(avg_tumor_vol, weight_g)::NUMERIC, 4) AS ols_intercept,
    ROUND(REGR_R2(avg_tumor_vol, weight_g)::NUMERIC, 4)    AS r_squared
FROM capo_agg;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 8: Metastatic Sites Progression
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    m.drug_regimen,
    sr.timepoint,
    ROUND(AVG(sr.metastatic_sites)::NUMERIC, 4)  AS avg_metastatic_sites,
    COUNT(*)                                       AS n_mice
FROM study_results  sr
JOIN mouse_metadata m ON sr.mouse_id = m.mouse_id
WHERE m.drug_regimen IN ('Capomulin','Ramicane','Infubinol','Ceftamin')
GROUP BY m.drug_regimen, sr.timepoint
ORDER BY m.drug_regimen, sr.timepoint;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 9: Age & Weight Stratified Analysis
-- ─────────────────────────────────────────────────────────────────────────────

-- 9.1  Tumour response by age group
SELECT
    m.age_group,
    m.drug_regimen,
    COUNT(DISTINCT ms.mouse_id)                                     AS n_mice,
    ROUND(AVG(ms.final_tumor_vol)::NUMERIC, 2)                     AS avg_final_tv,
    ROUND(AVG(ms.tumor_reduction_pct)::NUMERIC, 2)                 AS avg_reduction_pct
FROM mouse_summary  ms
JOIN mouse_metadata m ON ms.mouse_id = m.mouse_id
GROUP BY m.age_group, m.drug_regimen
ORDER BY m.drug_regimen, m.age_group;


-- 9.2  Tumour response by weight category
SELECT
    m.weight_category,
    m.drug_regimen,
    COUNT(DISTINCT ms.mouse_id)                                     AS n_mice,
    ROUND(AVG(ms.final_tumor_vol)::NUMERIC, 2)                     AS avg_final_tv,
    ROUND(AVG(ms.tumor_reduction_pct)::NUMERIC, 2)                 AS avg_reduction_pct
FROM mouse_summary  ms
JOIN mouse_metadata m ON ms.mouse_id = m.mouse_id
GROUP BY m.weight_category, m.drug_regimen
ORDER BY m.drug_regimen, m.weight_category;


-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 10: Sex-Based Subgroup Analysis
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    m.drug_regimen,
    m.sex,
    COUNT(DISTINCT ms.mouse_id)                                     AS n_mice,
    ROUND(AVG(ms.final_tumor_vol)::NUMERIC, 2)                     AS avg_final_tv,
    ROUND(AVG(ms.tumor_reduction_pct)::NUMERIC, 2)                 AS avg_reduction_pct,
    ROUND(AVG(ms.max_metastatic)::NUMERIC, 2)                      AS avg_max_metastatic
FROM mouse_summary  ms
JOIN mouse_metadata m ON ms.mouse_id = m.mouse_id
GROUP BY m.drug_regimen, m.sex
ORDER BY m.drug_regimen, m.sex;
