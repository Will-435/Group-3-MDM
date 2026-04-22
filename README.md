# Bristol Darkness Deterrence — Methods Bundle

This branch is a self-contained companion to the Group 3 MDM advisory report
*Darkness Deterrence Statistical Advisory Report*. It collects the notebooks,
data, and result tables behind the two methods used to **quantify the
deterrence effect of darkness on pedestrian and cyclist activity in Bristol**:

1. **Case-control matched odds ratios** (Mantel-Haenszel pooled ORs).
2. **Negative Binomial GLM ladder** (Models 1–5) — the main inferential method.

Exploratory figures, parallel working branches, and intermediate scratch files
from the wider project repository are deliberately excluded. Everything here
feeds one of the two quantification pipelines.

---

## Repository layout

```
new_branch/
├── README.md                  overview of this branch (you are here)
├── notebooks/                 ordered 01–10 analysis pipeline
├── glm/                       GLM-focused notebooks and the model-ladder table
├── data/
│   ├── processed/             cleaned panel and contextual features
│   └── raw/                   per-sensor raw hourly CSVs and spatial files
├── outputs/                   odds-ratio and GLM result tables
└── report/                    advisory report and methods write-ups
```

### `models/` — GLM working notebooks

Consolidated GLM work and comparisons against the case-control estimates:

- `Darkness GLM Models Will.ipynb`
- `Reprocess OR Confirmation.ipynb`
- `darkness_glm_model_comparison.csv` — model ladder output table
- `Draft_1_glm_(Pre_Easter)/` — earlier draft GLM notebooks kept for provenance

### `notebooks/` — ordered analysis pipeline

The numbered notebooks build the 37-sensor hourly panel and run both
quantification methods end-to-end.

| File | Purpose |
| --- | --- |
| `01_data_engineering.ipynb` | Cleans and assembles the 37-sensor hourly panel |
| `02_light_classification.ipynb` | Attaches solar state and derives the `Dark` binary indicator |
| `03_exploratory_analysis.ipynb` | Raw daylight/darkness comparisons |
| `04_case_control_or.ipynb` | **Method 1** — matched case-control odds ratios |
| `05_sensor_map_clustering.ipynb` | Assigns sensors to `Central` / `East` / `Outlier` clusters |
| `06_glm_cyclists.ipynb` | **Method 2a** — NB GLM ladder, cyclist outcome |
| `07_glm_pedestrians.ipynb` | **Method 2b** — NB GLM ladder, pedestrian outcome |
| `08_glm_combined_interaction.ipynb` | Cluster / CCTV / safety / built-environment interactions |
| `09_weather_processing.ipynb` | Hourly weather controls (`temp_c`, `wind_ms`) |
| `10_rain_processing.ipynb` | Hourly rain control (`rain_mm`) |

### `data/processed/` — inputs to the two methods

- `big_table_weather_rain_clusters_safety.csv` — master hourly panel feeding the GLMs
- `all_sensor_data_with_locations_and_clusters.csv` — sensor-level metadata with cluster labels
- `sensor_cctv_within_300m_clean37.csv` — CCTV count per sensor (300 m buffer)
- `sensor_ward_safety_after_dark_2024_clean37.csv` — ward-level after-dark safety percentage
- `businesses_per_sensor.csv` — business density per sensor
- `sensor_streetlight_freq.csv` — streetlight count per sensor

### `data/raw/` — reproducibility layer

- Per-sensor hourly CSVs (`1.csv`, `2.csv`, … `105.csv`) for the 37-sensor clean set and its exclusions
- `Sensor_Location.csv` — sensor coordinates
- `Bristol_boundary.geojson` — Bristol local authority boundary used for clustering and maps

### `outputs/` — result tables

Case-control (Mantel-Haenszel) odds ratios:

- `case_control_hour_or_pooled_ped_cyc_long.csv` — pooled OR by hour, pedestrians vs cyclists
- `case_control_hour_or_by_cluster_mode_long.csv` — OR by hour × cluster × mode
- `case_control_hour_or_mh_pooled_by_cluster_long.csv` — MH-pooled OR by cluster
- `mh_weighted_or_overall_by_mode.csv` — overall weighted OR per mode
- `mh_weighted_or_by_cluster_mode.csv` — weighted OR by cluster × mode
- `mh_weighted_or_by_case_hour_mode.csv` — weighted OR by case hour × mode

GLM ladder:

- `darkness_glm_model_comparison.csv` — Models 1–5 coefficients, percent changes, p-values

### `report/` — written deliverables

- `Darkness_Deterrence_Statistical_Advisory_Report.docx` — full advisory report
- `darkness_method_results_discussion.md` — methods and results write-up in markdown
- `case_control_mh_interpretation.md` — interpretation notes for the MH odds-ratio results

---

## Methods

### Method 1 — Case-control matched odds ratios

For each sensor × hour-of-day combination within the mixed hours
(`05, 06, 17, 18, 19, 20`) — the hours that switch between daylight and
darkness over the year — darkness and daylight observations are paired, and
the odds of a low-activity event are compared. Sensor-specific odds ratios
are pooled using the Mantel-Haenszel estimator, producing cluster-level and
overall pooled ORs for pedestrians and cyclists.

### Method 2 — Negative Binomial GLM ladder

$$
\log\{E(y_{it})\} = \beta_0 + \beta_1 \mathrm{Dark}_{it} + \beta_2 \mathrm{Lag1}_{it}
+ \beta_3 \mathrm{Lag24}_{it} + \gamma_h + \delta_d + \mu_m + \theta W_t + \alpha_i
$$

- $y_{it}$ — pedestrian or cyclist count at sensor $i$, hour $t$
- $\gamma_h, \delta_d, \mu_m$ — hour, day-of-week, and month fixed effects
- $W_t$ — weather controls (`temp_c`, `wind_ms`, `rain_mm`)
- $\alpha_i$ — sensor fixed effects
- Standard errors clustered by sensor; coefficients are reported as percent changes via $100(e^\beta - 1)$.

The ladder extends this baseline with interactions on `Cluster`, `cctv_z`,
`safety_z`, `businesses_z`, and `streetlights_z` across Models 2–5 to probe
spatial and contextual heterogeneity. Restricting the sample to the mixed
hours keeps the darkness contrast within hour-of-day and makes Method 2
directly comparable to Method 1.

---

## Headline results

Drawn from the advisory report:

- **Pedestrians (Model 1):** $-33.3\%$, $p = 1.48 \times 10^{-9}$ — a large,
  robust penalty that is broadly uniform across clusters. Raw counts fall in
  darkness at 36 of 37 sensors.
- **Cyclists (Model 1):** $-4.0\%$, $p = 0.446$ — the pooled estimate is
  near-null, but Model 2 reveals strong cluster heterogeneity (Central
  $-20.5\%$, East $-1.6\%$, Outlier $+20.4\%$), and Model 4 shows a
  statistically meaningful `Dark × safety` interaction ($p = 1.2 \times 10^{-4}$).

See `report/` for the full advisory document and `outputs/darkness_glm_model_comparison.csv`
for the complete coefficient table.

---

## Reproducing the analysis

The pipeline is designed to run top-to-bottom:

1. `notebooks/01_data_engineering.ipynb` → `10_rain_processing.ipynb` rebuild
   `data/processed/big_table_weather_rain_clusters_safety.csv`.
2. **Method 1** is produced by `notebooks/04_case_control_or.ipynb`.
3. **Method 2** is produced by `notebooks/06_glm_cyclists.ipynb`,
   `07_glm_pedestrians.ipynb`, and `08_glm_combined_interaction.ipynb`, with
   consolidated versions in `glm/`.
4. Reference outputs for comparison are provided in `outputs/`.
