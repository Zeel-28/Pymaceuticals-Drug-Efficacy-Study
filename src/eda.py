"""
eda.py
------
Exploratory Data Analysis module.
Produces all summary statistics, distribution plots, correlation matrices,
and drug-comparison visualisations used in the final report.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
from pathlib import Path
import logging
import warnings
warnings.filterwarnings("ignore")

from config import (
    FIGURES_DIR, TABLES_DIR, DRUG_COLORS, SEX_COLORS,
    BENCHMARK_DRUGS, PRIMARY_DRUG, FIGURE_DPI, FIGURE_SIZE
)

log = logging.getLogger(__name__)
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.05)


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def _save(fig: plt.Figure, name: str) -> None:
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  Figure saved → {path.name}")


def _export_table(df: pd.DataFrame, name: str) -> None:
    path = TABLES_DIR / f"{name}.csv"
    df.to_csv(path)
    log.info(f"  Table  saved → {path.name}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Dataset overview
# ─────────────────────────────────────────────────────────────────────────────

def dataset_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Print and export a high-level dataset summary."""
    log.info("\n[1] DATASET OVERVIEW")

    n_mice      = df["Mouse ID"].nunique()
    n_regimens  = df["Drug Regimen"].nunique()
    n_timepoints = df["Timepoint"].nunique()

    overview = {
        "Total Records":          len(df),
        "Unique Mice":            n_mice,
        "Drug Regimens":          n_regimens,
        "Timepoints":             n_timepoints,
        "Male Mice (%)":          f"{(df.drop_duplicates('Mouse ID')['Sex']=='Male').mean()*100:.1f}%",
        "Female Mice (%)":        f"{(df.drop_duplicates('Mouse ID')['Sex']=='Female').mean()*100:.1f}%",
        "Avg Age (months)":       f"{df.drop_duplicates('Mouse ID')['Age_months'].mean():.1f}",
        "Avg Weight (g)":         f"{df.drop_duplicates('Mouse ID')['Weight (g)'].mean():.1f}",
    }

    overview_df = pd.DataFrame.from_dict(overview, orient="index", columns=["Value"])
    _export_table(overview_df, "00_dataset_overview")
    print(overview_df.to_string())
    return overview_df


# ─────────────────────────────────────────────────────────────────────────────
# 2. Summary statistics per drug regimen
# ─────────────────────────────────────────────────────────────────────────────

def summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean, median, variance, std, SEM of tumour volume per regimen."""
    log.info("\n[2] SUMMARY STATISTICS — Tumour Volume by Drug Regimen")

    summary = df.groupby("Drug Regimen")["Tumor Volume (mm3)"].agg(
        Mean        = "mean",
        Median      = "median",
        Variance    = "var",
        Std_Dev     = "std",
        SEM         = "sem",
        Min         = "min",
        Max         = "max",
        Count       = "count",
    ).round(4)

    _export_table(summary, "01_summary_stats_tumor_volume")
    log.info(f"\n{summary}")
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# 3. Mouse cohort composition
# ─────────────────────────────────────────────────────────────────────────────

def cohort_plots(df: pd.DataFrame) -> None:
    """Bar chart of timepoints per regimen + pie chart of sex distribution."""
    log.info("\n[3] COHORT COMPOSITION PLOTS")
    mice = df.drop_duplicates("Mouse ID")

    # 3a. Timepoints per drug regimen
    tp_counts = df.groupby("Drug Regimen")["Timepoint"].count().sort_values(ascending=False)
    colors    = [DRUG_COLORS.get(d, "#90A4AE") for d in tp_counts.index]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    bars = ax.bar(tp_counts.index, tp_counts.values, color=colors, edgecolor="white", linewidth=0.8)
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_title("Total Observed Timepoints per Drug Regimen", fontsize=14, fontweight="bold")
    ax.set_xlabel("Drug Regimen", fontsize=11)
    ax.set_ylabel("Number of Timepoints", fontsize=11)
    ax.tick_params(axis="x", rotation=35)
    ax.set_ylim(0, tp_counts.max() * 1.12)
    fig.tight_layout()
    _save(fig, "03a_timepoints_per_regimen")

    # 3b. Sex distribution pie
    sex_counts = mice["Sex"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    wedge_props = {"linewidth": 2, "edgecolor": "white"}
    ax.pie(
        sex_counts,
        labels=sex_counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=[SEX_COLORS[s] for s in sex_counts.index],
        wedgeprops=wedge_props,
        textprops={"fontsize": 12},
    )
    ax.set_title("Sex Distribution of Study Mice", fontsize=14, fontweight="bold")
    _save(fig, "03b_sex_distribution")

    # 3c. Mice per regimen grouped by sex
    regimen_sex = mice.groupby(["Drug Regimen", "Sex"]).size().unstack(fill_value=0)
    regimen_sex.plot(
        kind="bar", color=[SEX_COLORS["Male"], SEX_COLORS["Female"]],
        figsize=FIGURE_SIZE, edgecolor="white"
    )
    plt.title("Mice per Drug Regimen by Sex", fontsize=14, fontweight="bold")
    plt.xlabel("Drug Regimen", fontsize=11)
    plt.ylabel("Number of Mice", fontsize=11)
    plt.xticks(rotation=35)
    plt.legend(title="Sex")
    plt.tight_layout()
    _save(plt.gcf(), "03c_mice_per_regimen_by_sex")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Tumour volume distributions
# ─────────────────────────────────────────────────────────────────────────────

def tumor_volume_distributions(df: pd.DataFrame) -> None:
    """Violin + box overlays; histogram; KDE per drug."""
    log.info("\n[4] TUMOUR VOLUME DISTRIBUTIONS")

    # 4a. Violin + box for all regimens
    fig, ax = plt.subplots(figsize=(13, 6))
    order = df.groupby("Drug Regimen")["Tumor Volume (mm3)"].median().sort_values().index
    palette = {d: DRUG_COLORS.get(d, "#90A4AE") for d in order}

    sns.violinplot(
        data=df, x="Drug Regimen", y="Tumor Volume (mm3)",
        order=order, palette=palette, inner=None, alpha=0.55, ax=ax
    )
    sns.boxplot(
        data=df, x="Drug Regimen", y="Tumor Volume (mm3)",
        order=order, width=0.15, fliersize=3,
        boxprops={"zorder": 2}, ax=ax, color="white"
    )
    ax.set_title("Tumour Volume Distribution by Drug Regimen", fontsize=14, fontweight="bold")
    ax.set_xlabel("Drug Regimen", fontsize=11)
    ax.set_ylabel("Tumour Volume (mm³)", fontsize=11)
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    _save(fig, "04a_tumor_violin_box_all_regimens")

    # 4b. Final tumour volume box plot (benchmark drugs only)
    benchmark_df = df[df["Drug Regimen"].isin(BENCHMARK_DRUGS)]
    last_tp = (
        benchmark_df.groupby("Mouse ID")["Timepoint"].max()
                    .reset_index().rename(columns={"Timepoint": "Last_Timepoint"})
    )
    final_df = benchmark_df.merge(last_tp, on="Mouse ID")
    final_df = final_df[final_df["Timepoint"] == final_df["Last_Timepoint"]]

    fig, ax = plt.subplots(figsize=(9, 6))
    for i, drug in enumerate(BENCHMARK_DRUGS):
        sub = final_df[final_df["Drug Regimen"] == drug]["Tumor Volume (mm3)"]
        q1, q3 = sub.quantile(0.25), sub.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = sub[(sub < lower) | (sub > upper)]

        bp = ax.boxplot(
            sub, positions=[i], widths=0.5,
            patch_artist=True,
            boxprops={"facecolor": DRUG_COLORS[drug], "alpha": 0.7},
            medianprops={"color": "black", "linewidth": 2},
            whiskerprops={"linestyle": "--"},
            flierprops={"marker": "o", "markersize": 0},
        )
        ax.scatter(
            [i] * len(outliers), outliers,
            color="red", zorder=5, s=60, label="Outlier" if i == 0 else ""
        )

    ax.set_xticks(range(len(BENCHMARK_DRUGS)))
    ax.set_xticklabels(BENCHMARK_DRUGS, fontsize=11)
    ax.set_title("Final Tumour Volume — Benchmark Drug Regimens", fontsize=14, fontweight="bold")
    ax.set_ylabel("Final Tumour Volume (mm³)", fontsize=11)
    handles = [mpatches.Patch(color=DRUG_COLORS[d], label=d) for d in BENCHMARK_DRUGS]
    handles.append(plt.Line2D([0], [0], marker="o", color="w",
                              markerfacecolor="red", markersize=8, label="Outlier"))
    ax.legend(handles=handles, loc="upper right")
    fig.tight_layout()
    _save(fig, "04b_final_tumor_boxplot_benchmark")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Tumour progression over time
# ─────────────────────────────────────────────────────────────────────────────

def tumor_progression(df: pd.DataFrame) -> None:
    """Mean tumour volume over time per regimen (with SEM band)."""
    log.info("\n[5] TUMOUR PROGRESSION OVER TIME")

    progression = (
        df.groupby(["Drug Regimen", "Timepoint"])["Tumor Volume (mm3)"]
          .agg(["mean", "sem"])
          .reset_index()
    )
    progression.columns = ["Drug Regimen", "Timepoint", "Mean_TV", "SEM_TV"]

    fig, ax = plt.subplots(figsize=(12, 6))
    for drug, grp in progression.groupby("Drug Regimen"):
        color = DRUG_COLORS.get(drug, "#90A4AE")
        lw    = 2.5 if drug in BENCHMARK_DRUGS else 1.0
        alpha = 0.9 if drug in BENCHMARK_DRUGS else 0.4
        ax.plot(grp["Timepoint"], grp["Mean_TV"], label=drug, color=color, lw=lw, alpha=alpha)
        if drug in BENCHMARK_DRUGS:
            ax.fill_between(
                grp["Timepoint"],
                grp["Mean_TV"] - grp["SEM_TV"],
                grp["Mean_TV"] + grp["SEM_TV"],
                color=color, alpha=0.15,
            )

    ax.set_title("Mean Tumour Volume Over Time by Drug Regimen", fontsize=14, fontweight="bold")
    ax.set_xlabel("Timepoint (Days)", fontsize=11)
    ax.set_ylabel("Mean Tumour Volume (mm³)", fontsize=11)
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.set_xlim(0, 45)
    fig.tight_layout()
    _save(fig, "05_tumor_progression_over_time")

    # 5b. Single mouse line plot (best Capomulin responder)
    capo = df[df["Drug Regimen"] == PRIMARY_DRUG]
    final = capo.groupby("Mouse ID")["Tumor Volume (mm3)"].last()
    best_mouse = final.idxmin()
    mouse_data = capo[capo["Mouse ID"] == best_mouse].sort_values("Timepoint")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(mouse_data["Timepoint"], mouse_data["Tumor Volume (mm3)"],
            marker="o", color=DRUG_COLORS[PRIMARY_DRUG], lw=2, ms=5)
    ax.set_title(f"Tumour Volume Over Time — Mouse {best_mouse} (Capomulin Best Responder)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Timepoint (Days)", fontsize=11)
    ax.set_ylabel("Tumour Volume (mm³)", fontsize=11)
    ax.set_xlim(0, 45)
    fig.tight_layout()
    _save(fig, "05b_single_mouse_capomulin")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Outlier analysis
# ─────────────────────────────────────────────────────────────────────────────

def outlier_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """IQR-based outlier detection for benchmark drugs. Returns summary table."""
    log.info("\n[6] OUTLIER ANALYSIS (IQR Method)")
    records = []

    benchmark_df = df[df["Drug Regimen"].isin(BENCHMARK_DRUGS)]
    last_tp = (
        benchmark_df.groupby("Mouse ID")["Timepoint"].max()
                    .reset_index().rename(columns={"Timepoint": "Last_Timepoint"})
    )
    final_df = benchmark_df.merge(last_tp, on="Mouse ID")
    final_df = final_df[final_df["Timepoint"] == final_df["Last_Timepoint"]]

    for drug in BENCHMARK_DRUGS:
        sub = final_df[final_df["Drug Regimen"] == drug]["Tumor Volume (mm3)"]
        q1, q3 = sub.quantile(0.25), sub.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = sub[(sub < lower) | (sub > upper)]
        records.append({
            "Drug Regimen":  drug,
            "Q1 (mm³)":      round(q1, 2),
            "Q3 (mm³)":      round(q3, 2),
            "IQR (mm³)":     round(iqr, 2),
            "Lower Fence":   round(lower, 2),
            "Upper Fence":   round(upper, 2),
            "Outlier Count": len(outliers),
            "Outlier Values": list(outliers.round(2).values),
        })
        log.info(f"  {drug}: {len(outliers)} outlier(s) — lower={lower:.2f}, upper={upper:.2f}")

    outlier_df = pd.DataFrame(records).set_index("Drug Regimen")
    _export_table(outlier_df, "06_outlier_analysis")
    return outlier_df


# ─────────────────────────────────────────────────────────────────────────────
# 7. Correlation & regression
# ─────────────────────────────────────────────────────────────────────────────

def correlation_regression(df: pd.DataFrame) -> None:
    """Pearson correlation + OLS regression: weight vs avg tumour vol (Capomulin)."""
    log.info("\n[7] CORRELATION & REGRESSION — Weight vs Avg Tumour Volume (Capomulin)")

    capo = df[df["Drug Regimen"] == PRIMARY_DRUG]
    avg_tv = capo.groupby("Mouse ID").agg(
        Weight        = ("Weight (g)", "mean"),
        Avg_Tumor_Vol = ("Tumor Volume (mm3)", "mean"),
    ).reset_index()

    r, p = stats.pearsonr(avg_tv["Weight"], avg_tv["Avg_Tumor_Vol"])
    slope, intercept, r2, p2, se = stats.linregress(avg_tv["Weight"], avg_tv["Avg_Tumor_Vol"])

    log.info(f"  Pearson r = {r:.4f}   p-value = {p:.4e}")
    log.info(f"  OLS slope = {slope:.4f}   intercept = {intercept:.4f}   R² = {r2**2:.4f}")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(avg_tv["Weight"], avg_tv["Avg_Tumor_Vol"],
               color=DRUG_COLORS[PRIMARY_DRUG], alpha=0.75, edgecolors="white", s=80)
    x_line = np.linspace(avg_tv["Weight"].min(), avg_tv["Weight"].max(), 100)
    ax.plot(x_line, slope * x_line + intercept, color="firebrick", lw=2,
            label=f"OLS: y = {slope:.2f}x + {intercept:.2f}\nR² = {r2**2:.3f},  p = {p:.2e}")
    ax.set_title("Mouse Weight vs Avg Tumour Volume (Capomulin)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Mouse Weight (g)", fontsize=11)
    ax.set_ylabel("Avg Tumour Volume (mm³)", fontsize=11)
    ax.legend(fontsize=10)
    fig.tight_layout()
    _save(fig, "07_correlation_regression_capomulin")

    corr_result = pd.DataFrame([{
        "Drug": PRIMARY_DRUG,
        "Pearson r":    round(r, 4),
        "p-value":      round(p, 6),
        "OLS Slope":    round(slope, 4),
        "OLS Intercept": round(intercept, 4),
        "R²":           round(r2**2, 4),
    }])
    _export_table(corr_result, "07_correlation_regression_results")


# ─────────────────────────────────────────────────────────────────────────────
# 8. Statistical significance tests
# ─────────────────────────────────────────────────────────────────────────────

def statistical_tests(df: pd.DataFrame) -> pd.DataFrame:
    """
    One-way ANOVA + Tukey HSD pairwise comparisons on final tumour volumes
    for the four benchmark drugs.
    """
    log.info("\n[8] STATISTICAL SIGNIFICANCE TESTS")

    benchmark_df = df[df["Drug Regimen"].isin(BENCHMARK_DRUGS)]
    last_tp = (
        benchmark_df.groupby("Mouse ID")["Timepoint"].max()
                    .reset_index().rename(columns={"Timepoint": "Last_Timepoint"})
    )
    final_df = benchmark_df.merge(last_tp, on="Mouse ID")
    final_df = final_df[final_df["Timepoint"] == final_df["Last_Timepoint"]]

    groups = [
        final_df[final_df["Drug Regimen"] == d]["Tumor Volume (mm3)"].dropna()
        for d in BENCHMARK_DRUGS
    ]
    f_stat, p_anova = stats.f_oneway(*groups)
    log.info(f"  One-way ANOVA: F = {f_stat:.4f}, p = {p_anova:.4e}")

    # Pairwise t-tests with Bonferroni correction
    pairs = []
    from itertools import combinations
    for a, b in combinations(BENCHMARK_DRUGS, 2):
        ga = final_df[final_df["Drug Regimen"] == a]["Tumor Volume (mm3)"].dropna()
        gb = final_df[final_df["Drug Regimen"] == b]["Tumor Volume (mm3)"].dropna()
        t, p_t = stats.ttest_ind(ga, gb)
        pairs.append({
            "Drug A":    a,
            "Drug B":    b,
            "t-stat":    round(t, 4),
            "p-value":   round(p_t, 6),
            "Significant (α=0.05)": "Yes" if p_t < 0.05 else "No",
        })

    pairs_df = pd.DataFrame(pairs)
    _export_table(pairs_df, "08_pairwise_ttest_results")
    log.info(f"\n  ANOVA p = {p_anova:.4e} — {'significant' if p_anova < 0.05 else 'not significant'}")
    log.info(f"\n{pairs_df.to_string(index=False)}")
    return pairs_df


# ─────────────────────────────────────────────────────────────────────────────
# 9. Correlation heatmap
# ─────────────────────────────────────────────────────────────────────────────

def correlation_heatmap(df: pd.DataFrame) -> None:
    """Heatmap of numeric feature correlations."""
    log.info("\n[9] CORRELATION HEATMAP")
    num_cols = ["Age_months", "Weight (g)", "Timepoint",
                "Tumor Volume (mm3)", "Metastatic Sites",
                "Tumor_Volume_Change_mm3", "Tumor_Volume_Change_pct"]

    corr_matrix = df[num_cols].corr()
    _export_table(corr_matrix, "09_correlation_matrix")

    fig, ax = plt.subplots(figsize=(9, 7))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(
        corr_matrix, annot=True, fmt=".2f", cmap="coolwarm",
        mask=mask, center=0, square=True, linewidths=0.5,
        cbar_kws={"shrink": 0.8}, ax=ax,
    )
    ax.set_title("Correlation Matrix — Numeric Features", fontsize=13, fontweight="bold")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    _save(fig, "09_correlation_heatmap")


# ─────────────────────────────────────────────────────────────────────────────
# 10. Metastatic progression
# ─────────────────────────────────────────────────────────────────────────────

def metastatic_progression(df: pd.DataFrame) -> None:
    """Mean metastatic sites over time for benchmark drugs."""
    log.info("\n[10] METASTATIC PROGRESSION")

    benchmark_df = df[df["Drug Regimen"].isin(BENCHMARK_DRUGS)]
    meta_prog = (
        benchmark_df.groupby(["Drug Regimen", "Timepoint"])["Metastatic Sites"]
                    .mean().reset_index()
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    for drug, grp in meta_prog.groupby("Drug Regimen"):
        ax.plot(grp["Timepoint"], grp["Metastatic Sites"],
                marker="o", label=drug, color=DRUG_COLORS[drug], ms=4)
    ax.set_title("Mean Metastatic Sites Over Time — Benchmark Drugs", fontsize=13, fontweight="bold")
    ax.set_xlabel("Timepoint (Days)", fontsize=11)
    ax.set_ylabel("Avg Metastatic Sites", fontsize=11)
    ax.legend()
    ax.set_xlim(0, 45)
    fig.tight_layout()
    _save(fig, "10_metastatic_progression")


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_eda_pipeline(df: pd.DataFrame) -> None:
    """Execute all EDA steps sequentially."""
    log.info("=" * 60)
    log.info("PYMACEUTICALS — EDA PIPELINE")
    log.info("=" * 60)

    dataset_overview(df)
    summary_statistics(df)
    cohort_plots(df)
    tumor_volume_distributions(df)
    tumor_progression(df)
    outlier_analysis(df)
    correlation_regression(df)
    statistical_tests(df)
    correlation_heatmap(df)
    metastatic_progression(df)

    log.info("=" * 60)
    log.info("EDA PIPELINE COMPLETE")
    log.info("=" * 60)


if __name__ == "__main__":
    from config import MERGED_CLEAN_FILE
    df = pd.read_csv(MERGED_CLEAN_FILE)
    run_eda_pipeline(df)
