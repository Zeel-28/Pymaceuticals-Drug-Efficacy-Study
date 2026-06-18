"""
data_preprocessing.py
---------------------
All data ingestion, validation, cleaning, and export logic.
Run this module first to produce the canonical cleaned dataset.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from config import (
    MOUSE_METADATA_FILE, STUDY_RESULTS_FILE,
    MERGED_CLEAN_FILE, PROCESSED_DATA_DIR
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ── 1. Load raw data ──────────────────────────────────────────────────────────

def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load Mouse_metadata and Study_results CSVs with dtype enforcement."""
    log.info("Loading Mouse_metadata …")
    mouse_dtype = {
        "Mouse ID":       "string",
        "Drug Regimen":   "category",
        "Sex":            "category",
        "Age_months":     "Int64",
        "Weight (g)":     "float64",
    }
    metadata = pd.read_csv(MOUSE_METADATA_FILE, dtype=mouse_dtype)
    metadata.columns = metadata.columns.str.strip()

    log.info("Loading Study_results …")
    study_dtype = {
        "Mouse ID":            "string",
        "Timepoint":           "Int64",
        "Tumor Volume (mm3)":  "float64",
        "Metastatic Sites":    "Int64",
    }
    results = pd.read_csv(STUDY_RESULTS_FILE, dtype=study_dtype)
    results.columns = results.columns.str.strip()

    log.info(f"  Mouse metadata shape : {metadata.shape}")
    log.info(f"  Study results shape  : {results.shape}")
    return metadata, results


# ── 2. Schema validation ──────────────────────────────────────────────────────

def validate_schema(metadata: pd.DataFrame, results: pd.DataFrame) -> None:
    """Assert required columns exist in both tables."""
    required_meta   = {"Mouse ID", "Drug Regimen", "Sex", "Age_months", "Weight (g)"}
    required_study  = {"Mouse ID", "Timepoint", "Tumor Volume (mm3)", "Metastatic Sites"}

    missing_meta  = required_meta  - set(metadata.columns)
    missing_study = required_study - set(results.columns)

    if missing_meta:
        raise ValueError(f"Mouse_metadata missing columns: {missing_meta}")
    if missing_study:
        raise ValueError(f"Study_results missing columns: {missing_study}")

    log.info("Schema validation passed.")


# ── 3. Merge ──────────────────────────────────────────────────────────────────

def merge_datasets(metadata: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    """Inner join on Mouse ID."""
    merged = pd.merge(metadata, results, on="Mouse ID", how="inner")
    log.info(f"Merged dataset shape: {merged.shape}")
    return merged


# ── 4. Duplicate detection & removal ─────────────────────────────────────────

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify mice with duplicate (Mouse ID, Timepoint) pairs.
    Drop ALL records for those mice (standard protocol for this study).
    """
    dup_mask   = df.duplicated(subset=["Mouse ID", "Timepoint"], keep=False)
    dup_mice   = df.loc[dup_mask, "Mouse ID"].unique()

    log.info(f"Duplicate timepoint mice found : {len(dup_mice)}  →  {list(dup_mice)}")

    if len(dup_mice) > 0:
        df = df[~df["Mouse ID"].isin(dup_mice)].copy()
        log.info(f"After duplicate removal shape : {df.shape}")

    return df, dup_mice


# ── 5. Missing-value analysis ─────────────────────────────────────────────────

def analyse_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Return a tidy DataFrame summarising nulls per column."""
    null_counts  = df.isnull().sum()
    null_pct     = (null_counts / len(df) * 100).round(2)
    summary      = pd.DataFrame({"null_count": null_counts, "null_pct_%": null_pct})
    summary      = summary[summary["null_count"] > 0]

    if summary.empty:
        log.info("No missing values detected.")
    else:
        log.warning(f"Missing values found:\n{summary}")

    return summary


# ── 6. Data-quality checks ────────────────────────────────────────────────────

def data_quality_checks(df: pd.DataFrame) -> dict:
    """
    Run a battery of domain-specific quality checks.
    Returns a dict of {check_name: (passed, detail)}.
    """
    checks = {}

    # 6a. Tumour volume ≥ 0
    neg_tv = (df["Tumor Volume (mm3)"] < 0).sum()
    checks["tumor_volume_non_negative"] = (neg_tv == 0, f"{neg_tv} negative values")

    # 6b. Timepoints within [0, 45]
    invalid_tp = df["Timepoint"].between(0, 45, inclusive="both")
    n_invalid  = (~invalid_tp).sum()
    checks["timepoints_in_range"] = (n_invalid == 0, f"{n_invalid} out-of-range timepoints")

    # 6c. Weight > 0
    bad_weight = (df["Weight (g)"] <= 0).sum()
    checks["weight_positive"] = (bad_weight == 0, f"{bad_weight} non-positive weights")

    # 6d. Sex categories
    valid_sex = {"Male", "Female"}
    bad_sex   = (~df["Sex"].isin(valid_sex)).sum()
    checks["sex_valid_categories"] = (bad_sex == 0, f"{bad_sex} invalid sex values")

    # 6e. Age reasonable (0–36 months)
    bad_age = (~df["Age_months"].between(0, 36)).sum()
    checks["age_in_range"] = (bad_age == 0, f"{bad_age} out-of-range ages")

    # 6f. Metastatic sites ≥ 0
    neg_meta = (df["Metastatic Sites"] < 0).sum()
    checks["metastatic_sites_non_negative"] = (neg_meta == 0, f"{neg_meta} negative values")

    for name, (passed, detail) in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        log.info(f"  [{status}] {name:45s} – {detail}")

    return checks


# ── 7. Feature engineering ────────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns useful for downstream analysis."""
    # Tumour volume change from baseline (Timepoint 0 = 45 mm³)
    df = df.copy()
    df["Tumor_Volume_Change_mm3"] = df["Tumor Volume (mm3)"] - 45.0
    df["Tumor_Volume_Change_pct"] = ((df["Tumor Volume (mm3)"] - 45.0) / 45.0 * 100).round(2)

    # Weight categories
    df["Weight_Category"] = pd.cut(
        df["Weight (g)"],
        bins=[0, 17, 22, 30],
        labels=["Light (<17g)", "Medium (17–22g)", "Heavy (>22g)"],
        right=True,
    )

    # Age group
    df["Age_Group"] = pd.cut(
        df["Age_months"].astype(float),
        bins=[0, 6, 12, 24, 36],
        labels=["0–6 mo", "7–12 mo", "13–24 mo", "25–36 mo"],
        right=True,
    )

    # Study phase buckets
    df["Study_Phase"] = pd.cut(
        df["Timepoint"].astype(float),
        bins=[-1, 10, 25, 45],
        labels=["Early (0–10)", "Mid (11–25)", "Late (26–45)"],
    )

    log.info("Feature engineering complete. New columns: Tumor_Volume_Change_mm3, "
             "Tumor_Volume_Change_pct, Weight_Category, Age_Group, Study_Phase")
    return df


# ── 8. Export ─────────────────────────────────────────────────────────────────

def export_clean_data(df: pd.DataFrame) -> None:
    """Save the cleaned, feature-enriched dataset."""
    df.to_csv(MERGED_CLEAN_FILE, index=False)
    log.info(f"Cleaned dataset saved → {MERGED_CLEAN_FILE}  ({len(df):,} rows)")

    # Also export a mouse-level summary for SQL ingestion
    mouse_summary = (
        df.groupby(["Mouse ID", "Drug Regimen", "Sex", "Age_months", "Weight (g)"])
          .agg(
              total_timepoints   = ("Timepoint",           "count"),
              max_timepoint      = ("Timepoint",           "max"),
              initial_tumor_vol  = ("Tumor Volume (mm3)",  "first"),
              final_tumor_vol    = ("Tumor Volume (mm3)",  "last"),
              max_tumor_vol      = ("Tumor Volume (mm3)",  "max"),
              min_tumor_vol      = ("Tumor Volume (mm3)",  "min"),
              max_metastatic     = ("Metastatic Sites",    "max"),
          )
          .reset_index()
    )
    mouse_summary.to_csv(PROCESSED_DATA_DIR / "mouse_summary.csv", index=False)
    log.info(f"Mouse summary saved → {PROCESSED_DATA_DIR / 'mouse_summary.csv'}")


# ── Pipeline entry point ──────────────────────────────────────────────────────

def run_preprocessing_pipeline() -> pd.DataFrame:
    """Execute the full preprocessing pipeline and return clean DataFrame."""
    log.info("=" * 60)
    log.info("PYMACEUTICALS — DATA PREPROCESSING PIPELINE")
    log.info("=" * 60)

    metadata, results = load_raw_data()
    validate_schema(metadata, results)

    merged = merge_datasets(metadata, results)

    df, dup_mice = remove_duplicates(merged)

    missing_summary = analyse_missing(df)

    quality_results = data_quality_checks(df)
    all_passed = all(v[0] for v in quality_results.values())
    if not all_passed:
        log.warning("One or more quality checks FAILED. Review before proceeding.")

    df = engineer_features(df)

    export_clean_data(df)

    log.info("=" * 60)
    log.info(f"Pipeline complete. Final dataset: {df.shape[0]:,} rows × {df.shape[1]} cols")
    log.info("=" * 60)

    return df


if __name__ == "__main__":
    run_preprocessing_pipeline()
