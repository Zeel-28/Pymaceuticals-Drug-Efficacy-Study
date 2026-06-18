"""
run_pipeline.py
---------------
Master script: runs preprocessing → EDA in one command.
Usage:  python run_pipeline.py
"""

import sys
import logging
from pathlib import Path

# Make src importable when called from project root
sys.path.insert(0, str(Path(__file__).parent))

from data_preprocessing import run_preprocessing_pipeline
from eda import run_eda_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  PYMACEUTICALS — FULL ANALYSIS PIPELINE")
    print("=" * 60 + "\n")

    # Step 1 — Preprocessing
    df = run_preprocessing_pipeline()

    # Step 2 — EDA
    run_eda_pipeline(df)

    print("\n" + "=" * 60)
    print("  ALL DONE — check outputs/ for figures and tables")
    print("=" * 60 + "\n")
