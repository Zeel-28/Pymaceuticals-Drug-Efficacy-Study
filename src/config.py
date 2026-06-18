"""
config.py
---------
Central configuration for the Pymaceuticals Drug Efficacy Study project.
All paths, constants, and palette settings live here.
"""

import os
from pathlib import Path

# ── Project root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Data paths ────────────────────────────────────────────────────────────────
RAW_DATA_DIR       = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

MOUSE_METADATA_FILE = RAW_DATA_DIR / "Mouse_metadata.csv"
STUDY_RESULTS_FILE  = RAW_DATA_DIR / "Study_results.csv"
MERGED_CLEAN_FILE   = PROCESSED_DATA_DIR / "merged_clean.csv"

# ── Output paths ──────────────────────────────────────────────────────────────
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
TABLES_DIR  = PROJECT_ROOT / "outputs" / "tables"

# ── Study constants ───────────────────────────────────────────────────────────
STUDY_DURATION_DAYS     = 45
INITIAL_TUMOR_VOLUME_MM3 = 45.0
PRIMARY_DRUG            = "Capomulin"
BENCHMARK_DRUGS         = ["Capomulin", "Ramicane", "Infubinol", "Ceftamin"]

# ── Plotting palette ──────────────────────────────────────────────────────────
DRUG_COLORS = {
    "Capomulin":  "#2196F3",
    "Ramicane":   "#4CAF50",
    "Infubinol":  "#FF5722",
    "Ceftamin":   "#9C27B0",
    "Propriva":   "#FF9800",
    "Stelasyn":   "#00BCD4",
    "Zoniferol":  "#795548",
    "Ketapril":   "#607D8B",
    "Naftisol":   "#E91E63",
    "Placebo":    "#9E9E9E",
}

SEX_COLORS = {"Male": "#4A90D9", "Female": "#E94F8A"}

FIGURE_DPI  = 150
FIGURE_SIZE = (10, 6)

# ── Ensure output dirs exist ─────────────────────────────────────────────────
for _dir in [PROCESSED_DATA_DIR, FIGURES_DIR, TABLES_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)
