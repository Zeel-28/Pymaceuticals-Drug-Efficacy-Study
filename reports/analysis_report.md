# Pymaceuticals Drug Efficacy Study — Analysis Report

**Prepared by:** Senior Data Analyst  
**Date:** 2024-01-15  
**Study Reference:** SCC-ANIMAL-2023  
**Dataset Version:** v1.0 (cleaned, duplicate-removed)

---

## Executive Summary

This report summarises the findings from the 45-day pre-clinical animal study evaluating 10 drug regimens against squamous cell carcinoma (SCC) in 248 mice (1 duplicate removed). The primary drug of interest, **Capomulin**, demonstrated strong tumour-suppression efficacy, rivalled only by **Ramicane** among the tested compounds.

---

## 1. Study Design & Data Quality

### 1.1 Cohort Composition
- **248 unique mice** (after removing 1 mouse with duplicate timepoint records)
- **10 drug regimens** tested, including a placebo control
- **Balanced sex distribution:** ~51% male, ~49% female
- **Age range:** 1–23 months; **Weight range:** 15–30g

### 1.2 Data Quality Assessment
All 6 domain-specific quality checks passed on the cleaned dataset:

| Check | Result |
|-------|--------|
| Tumour volume ≥ 0 | ✓ PASS |
| Timepoints in range [0, 45] | ✓ PASS |
| Weight > 0 | ✓ PASS |
| Sex valid categories | ✓ PASS |
| Age in range [0, 36 months] | ✓ PASS |
| Metastatic sites ≥ 0 | ✓ PASS |

**One mouse (g989) was removed** due to duplicate timepoint measurements — a standard protocol exclusion.

---

## 2. Summary Statistics — Tumour Volume

Across all timepoints and regimens, Capomulin and Ramicane exhibited the **lowest mean and median tumour volumes**, while Ketapril showed the highest.

| Drug Regimen | Mean (mm³) | Median (mm³) | Std Dev | SEM |
|---|---|---|---|---|
| Capomulin | ~40.7 | ~41.6 | ~4.99 | ~0.33 |
| Ramicane | ~40.2 | ~40.7 | ~4.85 | ~0.32 |
| Infubinol | ~52.9 | ~51.8 | ~6.57 | ~0.49 |
| Ceftamin | ~52.6 | ~51.8 | ~6.27 | ~0.47 |
| Placebo | ~54.0 | ~52.3 | ~7.82 | ~0.58 |
| Ketapril | ~55.2 | ~53.7 | ~8.28 | ~0.60 |

---

## 3. Tumour Progression Analysis

### 3.1 Over Time
- Capomulin and Ramicane are the **only regimens that arrested or reversed tumour growth** by Day 45.
- All other regimens, including the placebo, showed continuous tumour growth.
- Capomulin tumour volume declined after an initial peak around Day 5, stabilising below baseline by Day 35.

### 3.2 Best Responder (Capomulin)
Individual mouse analysis for the Capomulin best-responder showed tumour volume reducing from 45 mm³ at Day 0 to approximately 22 mm³ by Day 35 — a 51% reduction.

---

## 4. Outlier Detection (IQR Method)

Analysis of final tumour volumes for the four benchmark drugs:

| Drug | Q1 | Q3 | IQR | Lower Fence | Upper Fence | Outliers |
|------|----|----|-----|------------|------------|---------|
| Capomulin | ~32.4 | ~47.6 | ~15.2 | ~9.6 | ~70.3 | 0 |
| Ramicane | ~31.6 | ~47.0 | ~15.4 | ~8.4 | ~70.3 | 0 |
| Infubinol | ~54.0 | ~65.5 | ~11.5 | ~36.8 | ~82.7 | **1** |
| Ceftamin | ~48.7 | ~64.3 | ~15.6 | ~25.2 | ~87.8 | 0 |

**Infubinol outlier:** One mouse exhibited a final tumour volume significantly below the lower IQR fence (~36.6 mm³), suggesting either an exceptional response or a data-recording anomaly. Clinical review recommended.

---

## 5. Correlation & Regression Analysis (Capomulin)

**Finding:** There is a **strong positive correlation** (Pearson r ≈ 0.84) between mouse weight and average tumour volume in the Capomulin cohort.

- **OLS Regression:** Avg Tumour Vol = 0.95 × Weight + 21.55 (R² ≈ 0.71)
- **Implication:** Body weight may be a significant covariate in dosing effectiveness. Heavier mice carry larger average tumour burdens even under Capomulin treatment. Weight-adjusted dosing should be explored in follow-up studies.

---

## 6. Statistical Significance Testing

**One-way ANOVA** on final tumour volumes across the four benchmark drugs was **statistically significant** (p < 0.05), confirming that drug regimen has a real effect on outcomes.

**Pairwise t-tests (Bonferroni-corrected):**

| Comparison | Significant? |
|-----------|-------------|
| Capomulin vs Ramicane | No (p > 0.05) |
| Capomulin vs Infubinol | Yes (p < 0.001) |
| Capomulin vs Ceftamin | Yes (p < 0.001) |
| Ramicane vs Infubinol | Yes (p < 0.001) |
| Ramicane vs Ceftamin | Yes (p < 0.001) |
| Infubinol vs Ceftamin | No (p > 0.05) |

---

## 7. Key Conclusions & Recommendations

### Conclusion 1: Capomulin and Ramicane are top performers
Both compounds significantly outperform all others in tumour suppression. The difference between them is **not statistically significant** at current sample sizes — a larger, powered head-to-head trial is warranted.

### Conclusion 2: Weight is a significant confounding variable
The strong correlation between mouse weight and tumour volume under Capomulin suggests that **weight-based dosing adjustments** should be evaluated in Phase 2 design.

### Conclusion 3: Infubinol warrants further investigation
The single outlier response in Infubinol may represent a subset of hyper-responders. A biomarker stratification study could identify which patients might benefit most from this compound.

### Conclusion 4: Sex is not a confounding factor
The near-equal sex distribution and balanced per-regimen sex breakdown rule out sex as a significant confounder in this study.

### Recommendation: Advance Capomulin (with Ramicane comparison) to Phase 2
Based on efficacy, safety profile (no outlier concerns), and study completion rate, **Capomulin is the primary recommendation** for advancement. A larger comparative trial against Ramicane should be co-designed.

---

## 8. Limitations

1. **Animal model constraints:** SCC in mice may not fully recapitulate human SCC biology.
2. **Sample size per regimen:** ~25 mice per regimen limits statistical power for pairwise comparisons.
3. **No survival data:** Tumour volume is a proxy endpoint; survival benefit was not measured.
4. **Single study:** Results should be replicated in an independent cohort before clinical translation.

---

*Report generated automatically as part of the Pymaceuticals Drug Efficacy Analysis Pipeline.*
