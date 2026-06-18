# Pymaceuticals Drug Efficacy Study
### Professional Data Analysis Project

---

## 📋 Project Overview

**Client:** Pymaceuticals Inc. — Anti-cancer Pharmaceutical Division  
**Study Type:** Pre-clinical Animal Study — Squamous Cell Carcinoma (SCC)  
**Objective:** Compare the efficacy of 10 drug regimens against tumour growth in mice over a 45-day observation window, with special focus on the primary compound **Capomulin**.

---

## 🗂️ Project Structure

```
pharma_drug_efficacy/
│
├── data/
│   ├── raw/                        # Source data (never modified)
│   │   ├── Mouse_metadata.csv
│   │   └── Study_results.csv
│   └── processed/                  # Pipeline-generated clean data
│       ├── merged_clean.csv
│       └── mouse_summary.csv
│
├── notebooks/
│   └── PymaceuticalsAnalysis.ipynb # End-to-end analysis notebook
│
├── sql/
│   ├── 01_schema.sql               # Database schema (tables + indexes)
│   ├── 02_load_data.sql            # CSV ingestion + derived columns
│   ├── 03_analysis_queries.sql     # All analytical SQL queries
│   └── 04_views.sql                # Reusable analytical views
│
├── src/
│   ├── config.py                   # Central configuration & constants
│   ├── data_preprocessing.py       # Ingestion, validation, cleaning, engineering
│   ├── eda.py                      # EDA: plots, stats, tests
│   └── run_pipeline.py             # Master script (preprocessing → EDA)
│
├── outputs/
│   ├── figures/                    # All saved plots (PNG, 150 DPI)
│   └── tables/                     # All saved tables (CSV)
│
├── reports/
│   └── analysis_report.md          # Final findings & recommendations
│
└── requirements.txt
```

---

## 📊 Dataset

| File | Rows | Columns | Description |
|------|------|---------|-------------|
| `Mouse_metadata.csv` | 249 | 5 | Mouse ID, drug, sex, age, weight |
| `Study_results.csv` | ~1,892 | 4 | Tumour volume & metastatic sites per timepoint |

**Key Variables:**
- `Drug Regimen` — 10 treatments (Capomulin, Ramicane, Infubinol, Ceftamin, + 6 others)
- `Tumor Volume (mm³)` — Primary efficacy endpoint (baseline = 45 mm³)
- `Metastatic Sites` — Secondary endpoint
- `Timepoint` — Days 0–45 (0, 5, 10, … 45)

---

## ⚙️ Setup & Execution

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the full pipeline (preprocessing + EDA)
```bash
cd src
python run_pipeline.py
```

### 3. Run individual modules
```bash
# Preprocessing only
python src/data_preprocessing.py

# EDA only (requires cleaned data)
python src/eda.py
```

### 4. Open the notebook
```bash
jupyter notebook notebooks/PymaceuticalsAnalysis.ipynb
```

### 5. SQL — PostgreSQL
```bash
psql -U your_user -d your_db -f sql/01_schema.sql
psql -U your_user -d your_db -f sql/02_load_data.sql
psql -U your_user -d your_db -f sql/03_analysis_queries.sql
psql -U your_user -d your_db -f sql/04_views.sql
```

---

## 🔬 Analysis Modules

### Data Preprocessing (`data_preprocessing.py`)
| Step | Description |
|------|-------------|
| Schema Validation | Assert required columns exist |
| Merge | Inner join on Mouse ID |
| Duplicate Detection | Remove mice with duplicate timepoints |
| Missing Value Analysis | Quantify and log null percentages |
| Data Quality Checks | 6 domain-specific assertions (tumour ≥ 0, age range, weight > 0, etc.) |
| Feature Engineering | Tumour change %, weight category, age group, study phase |
| Export | `merged_clean.csv` + `mouse_summary.csv` |

### EDA (`eda.py`)
| Section | Analysis |
|---------|----------|
| Dataset Overview | Cohort size, sex ratio, age/weight distributions |
| Summary Statistics | Mean, median, variance, std, SEM per regimen |
| Cohort Plots | Timepoints per regimen, sex pie chart, per-regimen sex breakdown |
| Tumour Distributions | Violin + box overlays, final volume box plot |
| Tumour Progression | Mean ± SEM over time, single-mouse best-responder |
| Outlier Analysis | IQR method for 4 benchmark drugs |
| Correlation & Regression | Pearson r + OLS: weight vs avg tumour vol (Capomulin) |
| Statistical Tests | One-way ANOVA + pairwise t-tests (Bonferroni) |
| Correlation Heatmap | All numeric features |
| Metastatic Progression | Mean metastatic sites over time |

---

## 🗃️ SQL Files

| File | Purpose |
|------|---------|
| `01_schema.sql` | Tables, constraints, indexes, reference data |
| `02_load_data.sql` | COPY commands + derived column population |
| `03_analysis_queries.sql` | 10 sections of analytical SQL (mirrors EDA) |
| `04_views.sql` | 5 reusable views for BI / dashboards |

---

## 📈 Key Findings

1. **Capomulin and Ramicane** are the most effective regimens, both showing mean tumour reduction across the study period — unlike all other regimens where tumours grew.

2. **Strong weight–tumour correlation in Capomulin cohort** (Pearson r ≈ 0.84): heavier mice exhibited larger average tumour volumes, suggesting body weight as a potential dosing factor.

3. **One potential outlier** was identified in the Infubinol group (tumour volume significantly below the lower IQR fence), warranting clinical investigation.

4. **Sex distribution is balanced** (~50/50 across all regimens), ruling out sex as a confounding variable.

5. **Capomulin vs Ramicane** is statistically indistinguishable at α=0.05 — further powered studies are recommended to differentiate the two leading candidates.

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| pandas | Data manipulation |
| matplotlib / seaborn | Visualisation |
| scipy / statsmodels | Statistical testing |
| scikit-learn | Regression utilities |
| PostgreSQL / DuckDB | SQL layer |
| Jupyter | Interactive notebook |

---

## 📝 Data Governance Notes

- Raw source files in `data/raw/` are **never modified**.
- All transformations are logged and reproducible via `run_pipeline.py`.
- One duplicate mouse was identified and removed per study protocol.
- Quality-check results are logged at runtime and exportable to `outputs/tables/`.
