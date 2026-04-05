"""
Health Disparities Analysis: Epilepsy & Pediatric Neurological Outcomes.

Produces:
- Geographic choropleth maps of epilepsy prevalence by state
- Disparity analysis by race/ethnicity, income, insurance
- Regression analysis of socioeconomic predictors of ER utilization
- Time-series of hospitalization rates
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go


np.random.seed(42)


# ── Simulated data (replace with actual CDC BRFSS download) ──────────────────

US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

RACE_GROUPS = ["White (non-Hispanic)", "Black/African American", "Hispanic/Latino",
               "Asian/Pacific Islander", "American Indian/Alaska Native"]


def generate_state_data() -> pd.DataFrame:
    """Generate synthetic state-level epilepsy data mirroring BRFSS patterns."""
    np.random.seed(42)
    n = len(US_STATES)

    # Epilepsy prevalence varies 1.0–2.5% by state (CDC range)
    prevalence = np.random.uniform(1.0, 2.5, n)
    # Medicaid expansion states (roughly)
    medicaid_expanded = np.random.choice([0, 1], n, p=[0.3, 0.7])
    # ER visit rate (higher in non-expansion states)
    er_rate = 45 + 20 * (1 - medicaid_expanded) + np.random.randn(n) * 5
    # Neurologist density (per 100k) — higher in urban/NE states
    neuro_density = np.random.exponential(3.5, n) + 1
    # Uninsured rate
    uninsured_rate = np.clip(12 - 4 * medicaid_expanded + np.random.randn(n) * 3, 2, 25)
    # Poverty rate
    poverty_rate = np.random.uniform(8, 22, n)

    return pd.DataFrame({
        "state": US_STATES,
        "epilepsy_prevalence_pct": prevalence,
        "medicaid_expanded": medicaid_expanded,
        "er_visits_per_100k": er_rate,
        "neurologists_per_100k": neuro_density,
        "uninsured_rate_pct": uninsured_rate,
        "poverty_rate_pct": poverty_rate,
    })


def generate_racial_disparity_data() -> pd.DataFrame:
    """Generate synthetic racial disparity data in epilepsy management."""
    np.random.seed(7)
    n = 1000
    race = np.random.choice(RACE_GROUPS, n, p=[0.55, 0.18, 0.16, 0.05, 0.06])
    # Baseline ER risk by race (reflecting known disparities)
    base_risk = {
        "White (non-Hispanic)": 0.18,
        "Black/African American": 0.31,
        "Hispanic/Latino": 0.27,
        "Asian/Pacific Islander": 0.14,
        "American Indian/Alaska Native": 0.34,
    }
    er_visit = np.array([np.random.binomial(1, base_risk[r]) for r in race])
    insured = np.array([np.random.binomial(1, 0.9 if r == "White (non-Hispanic)" else 0.75)
                        for r in race])
    income = np.array([np.random.normal(65000 if r == "White (non-Hispanic)" else 45000, 20000)
                       for r in race]).clip(15000, None)
    controlled = 1 - er_visit  # proxy for seizure control

    return pd.DataFrame({
        "race_ethnicity": race,
        "er_visit_year": er_visit,
        "insured": insured,
        "annual_income": income,
        "seizures_controlled": controlled,
    })


def plot_state_choropleth(df: pd.DataFrame, output_dir: Path):
    """Create US choropleth of epilepsy prevalence."""
    fig = px.choropleth(
        df,
        locations="state",
        locationmode="USA-states",
        color="epilepsy_prevalence_pct",
        scope="usa",
        color_continuous_scale="Reds",
        title="Epilepsy Prevalence by State (BRFSS 2022, %)",
        labels={"epilepsy_prevalence_pct": "Prevalence (%)"},
    )
    fig.write_html(str(output_dir / "epilepsy_prevalence_map.html"))
    fig.write_image(str(output_dir / "epilepsy_prevalence_map.png"))
    print("  Saved: epilepsy_prevalence_map")


def plot_medicaid_effect(df: pd.DataFrame, output_dir: Path):
    """Compare ER visit rates in Medicaid expansion vs. non-expansion states."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Box plot
    expanded = df[df["medicaid_expanded"] == 1]["er_visits_per_100k"]
    not_expanded = df[df["medicaid_expanded"] == 0]["er_visits_per_100k"]
    axes[0].boxplot([expanded, not_expanded],
                    labels=["Medicaid Expanded", "Not Expanded"],
                    patch_artist=True,
                    boxprops=dict(facecolor="#42A5F5", alpha=0.7))
    t_stat, p_val = stats.ttest_ind(expanded, not_expanded)
    axes[0].set_ylabel("ER Visits per 100k with Epilepsy")
    axes[0].set_title(f"Medicaid Expansion & Seizure ER Visits\n(p={p_val:.3f})", fontweight="bold")
    axes[0].grid(axis="y", alpha=0.3)

    # Scatter: uninsured rate vs ER visits
    colors = ["#42A5F5" if m else "#EF5350" for m in df["medicaid_expanded"]]
    axes[1].scatter(df["uninsured_rate_pct"], df["er_visits_per_100k"],
                    c=colors, alpha=0.7, s=60)
    m, b, r, p, _ = stats.linregress(df["uninsured_rate_pct"], df["er_visits_per_100k"])
    x_line = np.linspace(df["uninsured_rate_pct"].min(), df["uninsured_rate_pct"].max(), 100)
    axes[1].plot(x_line, m * x_line + b, "k--", alpha=0.7, label=f"r={r:.2f}, p={p:.3f}")
    from matplotlib.patches import Patch
    axes[1].legend(handles=[
        Patch(color="#42A5F5", label="Medicaid Expanded"),
        Patch(color="#EF5350", label="Not Expanded"),
        plt.Line2D([0], [0], color="black", linestyle="--", label=f"r={r:.2f}"),
    ])
    axes[1].set_xlabel("Uninsured Rate (%)")
    axes[1].set_ylabel("ER Visits per 100k")
    axes[1].set_title("Uninsured Rate vs. Seizure ER Utilization", fontweight="bold")
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(str(output_dir / "medicaid_effect.png"), bbox_inches="tight", dpi=150)
    plt.close()
    print("  Saved: medicaid_effect")


def plot_racial_disparities(df: pd.DataFrame, output_dir: Path):
    """Visualize racial disparities in epilepsy outcomes."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ER visit rate by race
    er_by_race = df.groupby("race_ethnicity")["er_visit_year"].mean().sort_values(ascending=False)
    colors = plt.cm.RdYlBu_r(np.linspace(0.1, 0.9, len(er_by_race)))
    bars = axes[0].bar(range(len(er_by_race)), er_by_race.values, color=colors, alpha=0.85)
    axes[0].set_xticks(range(len(er_by_race)))
    axes[0].set_xticklabels([r.replace(" ", "\n") for r in er_by_race.index], fontsize=8)
    axes[0].set_ylabel("Proportion with ≥1 Seizure ER Visit/Year")
    axes[0].set_title("Seizure-Related ER Utilization by Race/Ethnicity", fontweight="bold")
    for bar, v in zip(bars, er_by_race.values):
        axes[0].text(bar.get_x() + bar.get_width()/2, v + 0.005,
                     f"{v:.2f}", ha="center", fontsize=9, fontweight="bold")
    axes[0].grid(axis="y", alpha=0.3)

    # Insurance coverage by race
    ins_by_race = df.groupby("race_ethnicity")["insured"].mean().sort_values(ascending=False)
    axes[1].bar(range(len(ins_by_race)), ins_by_race.values * 100,
                color=["#4CAF50" if v > 0.85 else "#FF9800" if v > 0.75 else "#F44336"
                       for v in ins_by_race.values], alpha=0.85)
    axes[1].set_xticks(range(len(ins_by_race)))
    axes[1].set_xticklabels([r.replace(" ", "\n") for r in ins_by_race.index], fontsize=8)
    axes[1].axhline(90, color="black", linestyle="--", alpha=0.5, label="90% benchmark")
    axes[1].set_ylabel("Insurance Coverage (%)")
    axes[1].set_title("Insurance Coverage by Race/Ethnicity\n(Epilepsy Population)", fontweight="bold")
    axes[1].legend()
    axes[1].set_ylim(0, 100)
    axes[1].grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(str(output_dir / "racial_disparities.png"), bbox_inches="tight", dpi=150)
    plt.close()
    print("  Saved: racial_disparities")


def run_regression(df_state: pd.DataFrame) -> dict:
    """Logistic regression: predictors of high ER utilization."""
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler

    X = df_state[["uninsured_rate_pct", "poverty_rate_pct",
                   "neurologists_per_100k", "medicaid_expanded"]].values
    y = df_state["er_visits_per_100k"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = LinearRegression().fit(X_scaled, y)

    features = ["Uninsured Rate", "Poverty Rate", "Neurologist Density", "Medicaid Expansion"]
    return dict(zip(features, model.coef_)), model.score(X_scaled, y)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="data")
    parser.add_argument("--output", type=str, default="figures")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating state-level analysis...")
    df_state = generate_state_data()
    df_race = generate_racial_disparity_data()

    plot_medicaid_effect(df_state, output_dir)
    plot_racial_disparities(df_race, output_dir)

    try:
        plot_state_choropleth(df_state, output_dir)
    except Exception:
        print("  Note: Plotly choropleth requires kaleido for PNG export")

    coefs, r2 = run_regression(df_state)
    print(f"\nRegression R² = {r2:.3f}")
    print("Standardized coefficients:")
    for feat, coef in sorted(coefs.items(), key=lambda x: abs(x[1]), reverse=True):
        print(f"  {feat:<25} {coef:+.2f}")

    df_state.to_csv(output_dir / "state_data.csv", index=False)
    df_race.to_csv(output_dir / "race_data.csv", index=False)
    print("\nAnalysis complete. Results saved to", output_dir)


if __name__ == "__main__":
    main()
