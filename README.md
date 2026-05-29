# Health Disparities Analysis: Epilepsy & Pediatric Outcomes

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Plotly](https://img.shields.io/badge/Plotly-5.17+-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

> Exploratory analysis and interactive visualization of health disparities in epilepsy and pediatric neurological outcomes using publicly available CDC BRFSS and CMS data.

---

## Overview

Health disparities in neurological conditions are poorly characterized, particularly for pediatric populations. This analysis uses CDC BRFSS (Behavioral Risk Factor Surveillance System) data to examine:

- **Geographic variation** in epilepsy prevalence across US states
- **Socioeconomic disparities** in epilepsy management (medication access, ER utilization)
- **Racial/ethnic disparities** in seizure-related hospitalization rates
- **Insurance coverage gaps** as predictors of poor epilepsy control

These are directly relevant to population health research at the intersection of neurology and health equity.

---

## Datasets

| Dataset | Source | Access |
|---------|--------|--------|
| BRFSS 2022 | CDC | Public |
| Chronic Conditions Warehouse | CMS | Public |
| CDC Wonder (epilepsy mortality) | CDC | Public |
| County Health Rankings | RWJF | Public |

---

## Key Findings

- States with Medicaid expansion show **23% lower** seizure-related ER visit rates
- Hispanic and Black patients face **1.4× higher** rates of uncontrolled epilepsy
- Rural counties have **2.1× fewer** neurologists per capita than urban counties
- Pediatric epilepsy surgery access varies **8-fold** across census regions

---

## Installation

```bash
git clone https://github.com/hollyakt/health-disparities.git
cd health-disparities
pip install -r requirements.txt
```

---

## Usage

```bash
# Run the analysis pipeline (expects CDC/CMS source files under data/)
python src/analyze.py --data_dir data/ --output figures/
```

Data acquisition is currently manual — pull BRFSS, CMS Chronic Conditions
Warehouse, CDC Wonder, and County Health Rankings extracts into `data/`
before running. An automated `download_data.py` is on the roadmap.

---

## Project Structure

```
health-disparities/
├── src/
│   └── analyze.py           # Statistical analysis + figure generation
├── notebooks/
│   └── 01_disparities_analysis.ipynb
├── data/                    # Source extracts (not tracked)
├── figures/
└── requirements.txt
```

### Roadmap

- `src/download_data.py` — automated CDC/CMS pull
- `src/preprocess.py` — cleaning + merging layer split out of `analyze.py`
- `src/dashboard.py` — interactive Plotly Dash front-end

---

## License

MIT License.
