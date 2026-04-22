# Bristol Darkness Deterrence — Methods Bundle

A minimal, reproducibility-focused companion to the Group 3 MDM advisory report
*Darkness Deterrence Statistical Advisory Report*. This branch isolates only the
files required to reproduce the two methods used to **quantify the deterrence
effect of darkness on pedestrian and cyclist activity in Bristol**:

1. **Case-control matched odds ratios** (Mantel-Haenszel pooled ORs), and
2. **Negative Binomial GLM ladder** (Models 1–5), the main inferential method.

Everything here feeds one of those two pipelines. Exploratory figures, parallel
working branches, and intermediate scratch files from the wider repo are
deliberately excluded.

---

## Directory layout

```
new_branch/
├── README.md                  <- this file
├── notebooks/                 <- numbered end-to-end pipeline (01 → 10)
├── glm/                       <- GLM-focused working notebooks + model table
├── data/
│   ├── processed/             <- cleaned panel + contextual features
│   └── raw/                   <- per-sensor raw hourly CSVs
├── outputs/                   <- OR and GLM result tables
└── report/                    <- advisory report, slides, methods write-up
```

---

## What to drop into each folder

### `notebooks/` — ordered analysis pipeline

Pull these from `notebooks/` in the parent repo. They run in order and produce
the panel used by both quantification methods.

| File | Purpose |
| --- | --- |
| `01_data_engineering.ipynb` | Clean and assemble the 37-sensor hourly panel |
| `02_light_classification.ipynb` | Attach solar state; derive the `Dark` binary indicator |
| `03_exploratory_analysis.ipynb` | Raw daylight/darkness comparisons |
| `04_case_control_or.ipynb` | **Method 1** — matched case-control odds ratios |
| `05_sensor_map_clustering.ipynb` | Assign sensors to `Central` / `East` / `Outlier` |
| `06_glm_cyclists.ipynb` | **Method 2a** — NB GLM ladder, cyclist outcome |
| `07_glm_pedestrians.ipynb` | **Method 2b** — NB GLM ladder, pedestrian outcome |
| `08_glm_combined_interaction.ipynb` | Cluster / CCTV / safety / built-env interactions |
| `09_weather_processing.ipynb` | Hourly weather controls (`temp_c`, `wind_ms`) |
| `10_rain_processing.ipynb` | Hourly rain control (`rain_mm`) |

### `glm/` — GLM working notebooks

Pull from `Will-Work/` and `Karan - Notebooks and analysis/`:

- `Darkness GLM Models Will.ipynb`
- `Darkness GLM Models.ipynb`
- `Darkness Final Synthesis.ipynb`
- `Darkness OR And GLM Comparison.ipynb`
- `Reprocess OR Confirmation.ipynb`
- `darkness_glm_model_comparison.csv` (model ladder output table)

### `data/processed/` — inputs to the two methods

From `Will-Work/GLM data/` (and/or `Karan - Notebooks and analysis/Processed Data/`):

- `big_table_weather_rain_clusters_safety.csv` — master hourly panel feeding the GLMs
- `all_sensor_data_with_locations_and_clusters.csv` — sensor-level metadata with cluster labels
- `sensor_cctv_within_300m_clean37.csv` — CCTV count per sensor (300 m buffer)
- `sensor_ward_safety_after_dark_2024_clean37.csv` — ward-level after-dark safety %
- `businesses_per_sensor.csv` — business density per sensor
- `sensor_streetlight_freq.csv` — streetlight count per sensor

### `data/raw/` — reproducibility layer

From `Karan - Notebooks and analysis/Raw Data/`:

- All per-sensor hourly CSVs (`1.csv`, `2.csv`, … `105.csv`)
- `Sensor_Location.csv` — sensor coordinates
- `Bristol_boundary.geojson` (from repo root) — boundary for clustering/maps

### `outputs/` — results tables

From `Karan - Notebooks and analysis/Processed Data/`:

- `case_control_hour_or_by_cluster_mode_long.csv`
- `case_control_hour_or_mh_pooled_by_cluster_long.csv`
- `case_control_hour_or_pooled_ped_cyc_long.csv`
- `mh_weighted_or_by_case_hour_mode.csv`
- `mh_weighted_or_by_cluster_mode.csv`
- `mh_weighted_or_overall_by_mode.csv`
- `darkness_glm_model_comparison.csv`

### `report/` — written deliverables

From the repo root and `Will-Work/`:

- `Darkness_Deterrence_Statistical_Advisory_Report.docx`
- `Darkness_Deterrence_Advisory_Presentation.pptx`
- `darkness_method_results_discussion.md` (methods + results prose)
- `case_control_mh_interpretation.md` (OR interpretation notes)

---

## Method summary

### Method 1 — Case-control matched odds ratios

For each sensor × hour-of-day combination in the mixed hours
(`05, 06, 17, 18, 19, 20`), darkness and daylight observations are paired and
the odds of a low-activity event are compared. Sensor-specific ORs are pooled
using the Mantel-Haenszel estimator, giving cluster-level and overall pooled
ORs for pedestrians and cyclists.

### Method 2 — Negative Binomial GLM ladder

$$
\log\{E(y_{it})\} = \beta_0 + \beta_1 \mathrm{Dark}_{it} + \beta_2 \mathrm{Lag1}_{it}
+ \beta_3 \mathrm{Lag24}_{it} + \gamma_h + \delta_d + \mu_m + \theta W_t + \alpha_i
$$

- $y_{it}$ — pedestrian or cyclist count at sensor $i$, hour $t$
- $\gamma_h, \delta_d, \mu_m$ — hour, day-of-week, month fixed effects
- $W_t$ — weather controls (`temp_c`, `wind_ms`, `rain_mm`)
- $\alpha_i$ — sensor fixed effects
- Standard errors clustered by sensor; coefficients converted to percent change via $100(e^\beta - 1)$

The ladder adds interactions with `Cluster`, `cctv_z`, `safety_z`,
`businesses_z`, and `streetlights_z` across Models 2–5 to probe spatial and
contextual heterogeneity.

Restriction to the mixed hours keeps the darkness contrast within hour-of-day
and makes Method 2 directly comparable to Method 1.

---

## Headline results (from the report)

- **Pedestrians (Model 1):** $-33.3\%$, $p = 1.48 \times 10^{-9}$ — large,
  robust, broadly uniform across clusters.
- **Cyclists (Model 1):** $-4.0\%$, $p = 0.446$ — pooled null, but Model 2
  reveals strong cluster heterogeneity (Central $-20.5\%$, East $-1.6\%$,
  Outlier $+20.4\%$) and Model 4 shows a significant `Dark × safety`
  interaction ($p = 1.2 \times 10^{-4}$).

---

## Reproducing the analysis

1. Run `notebooks/01_data_engineering.ipynb` → `10_rain_processing.ipynb` in
   order to rebuild `data/processed/big_table_weather_rain_clusters_safety.csv`.
2. For **Method 1**, run `notebooks/04_case_control_or.ipynb`.
3. For **Method 2**, run `notebooks/06_glm_cyclists.ipynb`,
   `07_glm_pedestrians.ipynb`, and `08_glm_combined_interaction.ipynb`, or the
   consolidated notebooks in `glm/`.
4. Compare against the reference tables in `outputs/`.
