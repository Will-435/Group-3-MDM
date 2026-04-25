"""
ROI_Calculations.py
────────────────────
Estimates the pedestrian-count return from increasing streetlight density
per geographic cluster, using the darkness negative-binomial GLM framework.

Outputs
-------
1. Which cluster is most affected by darkness (pedestrians)
2. Bar chart of average streetlight density per cluster (with network mean line)
3. Expected % change in total pedestrian counts per cluster if streetlight
   density is increased by 1 SD — printed to console

Methodology matches 'Darkness GLM Models Will.ipynb' (Models 2 & 5).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from pathlib import Path
import time

# ── File paths ───────────────────────────────────────────────────────────────
DATA_DIR       = Path(__file__).parent / 'GLM data'
PANEL_PATH     = DATA_DIR / 'all_sensor_data_with_locations_and_clusters.csv'
WEATHER_PATH   = DATA_DIR / 'big_table_weather_rain_clusters_safety.csv'
STREETLIGHT_PATH = DATA_DIR / 'sensor_streetlight_freq.csv'
BUSINESS_PATH  = DATA_DIR / 'businesses_per_sensor.csv'
OUTPUT_DIR     = Path(__file__).parent

MIXED_HOURS = [5, 6, 17, 18, 19, 20]
CLUSTERS    = ['Central', 'East', 'Outlier']

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING & PREPARATION
# ══════════════════════════════════════════════════════════════════════════════

print('Loading data ...')
t0 = time.time()

# Panel data — base hourly counts with cluster labels (37 sensors)
panel = pd.read_csv(PANEL_PATH, parse_dates=['date'])
panel.rename(columns={'date': 'datetime'}, inplace=True)

# Weather from big_table — unique datetime → weather lookup
weather = (
    pd.read_csv(WEATHER_PATH, usecols=['datetime', 'temp_c', 'wind_ms', 'rain_mm'])
    .drop_duplicates('datetime')
    .dropna(subset=['datetime'])
)
# Strip timezone suffix so keys match the panel's tz-naive datetimes
weather['datetime'] = pd.to_datetime(
    weather['datetime'].str.replace(r'\+00:00$', '', regex=True)
)
panel = panel.merge(weather, on='datetime', how='left')
del weather

# Sensor-level streetlight and business counts
streetlights = pd.read_csv(STREETLIGHT_PATH)[['SensorNumber', 'streetlights_50m']]
businesses   = pd.read_csv(BUSINESS_PATH)[['SensorNumber', 'Businesses_within_300m']]

print(f'  Loaded in {time.time() - t0:.1f}s')

# ── Time variables & lag variables (on full series before filtering) ─────────
panel['hour']  = panel['datetime'].dt.hour
panel['dow']   = panel['datetime'].dt.dayofweek
panel['month'] = panel['datetime'].dt.month

panel = panel.sort_values(['SensorNumber', 'datetime']).reset_index(drop=True)
panel['ped_lag1']  = panel.groupby('SensorNumber')['ped'].shift(1)
panel['ped_lag24'] = panel.groupby('SensorNumber')['ped'].shift(24)
panel['cyc_lag1']  = panel.groupby('SensorNumber')['cyc'].shift(1)
panel['cyc_lag24'] = panel.groupby('SensorNumber')['cyc'].shift(24)

# ── Restrict to mixed hours & exclude twilight ───────────────────────────────
analysis = panel.loc[
    (panel['light_class'] != 'twilight') & panel['hour'].isin(MIXED_HOURS)
].copy()
del panel

analysis['Cluster'] = pd.Categorical(analysis['Cluster'], categories=CLUSTERS)

# ── Merge & z-standardise sensor-level context ───────────────────────────────
analysis = (
    analysis
    .merge(streetlights, on='SensorNumber', how='left')
    .merge(businesses, on='SensorNumber', how='left')
)

sensor_ctx = (
    analysis[['SensorNumber', 'streetlights_50m', 'Businesses_within_300m']]
    .drop_duplicates('SensorNumber')
)
SL_MEAN  = sensor_ctx['streetlights_50m'].mean()
SL_STD   = sensor_ctx['streetlights_50m'].std()
BIZ_MEAN = sensor_ctx['Businesses_within_300m'].mean()
BIZ_STD  = sensor_ctx['Businesses_within_300m'].std()

analysis['streetlights_z'] = (analysis['streetlights_50m'] - SL_MEAN) / SL_STD
analysis['businesses_z']   = (analysis['Businesses_within_300m'] - BIZ_MEAN) / BIZ_STD

# Drop rows with any missing required variables
required = [
    'ped', 'Dark', 'Cluster', 'ped_lag1', 'ped_lag24',
    'hour', 'dow', 'month', 'temp_c', 'wind_ms', 'rain_mm',
    'SensorNumber', 'streetlights_z', 'businesses_z', 'streetlights_50m',
]
analysis = analysis.dropna(subset=required).copy()

print(f'  Analysis sample: {len(analysis):,} rows · {analysis["SensorNumber"].nunique()} sensors\n')


# ══════════════════════════════════════════════════════════════════════════════
# PART A — Which cluster is most affected by darkness? (pedestrians)
# ══════════════════════════════════════════════════════════════════════════════

print('=' * 70)
print(' PART A: Pedestrian Darkness Effect by Cluster  (Model 2)')
print('=' * 70)

print('  Fitting NB GLM (Dark × Cluster interaction) ... ', end='', flush=True)
t0 = time.time()

model2 = sm.GLM.from_formula(
    "ped ~ Dark + Dark:C(Cluster, Treatment(reference='Central'))"
    " + ped_lag1 + ped_lag24 + C(hour) + C(dow) + C(month)"
    " + temp_c + wind_ms + rain_mm + C(SensorNumber)",
    data=analysis,
    family=sm.families.NegativeBinomial(),
).fit()

print(f'done  ({time.time() - t0:.0f}s)')

# Per-cluster darkness coefficients
dark_base = model2.params['Dark']
east_term    = [t for t in model2.params.index
                if 'Dark:C(Cluster' in t and 'East' in t][0]
outlier_term = [t for t in model2.params.index
                if 'Dark:C(Cluster' in t and 'Outlier' in t][0]

cluster_dark = {
    'Central': dark_base,
    'East':    dark_base + model2.params[east_term],
    'Outlier': dark_base + model2.params[outlier_term],
}

print('\n  Cluster      β_dark    % change in ped counts')
print('  ' + '─' * 45)
for c in CLUSTERS:
    pct = 100 * (np.exp(cluster_dark[c]) - 1)
    print(f'  {c:10s}   {cluster_dark[c]:+.4f}    {pct:+.1f}%')

most_affected = min(cluster_dark, key=cluster_dark.get)
worst_pct = 100 * (np.exp(cluster_dark[most_affected]) - 1)
print(f'\n  ► Most affected cluster: {most_affected}  ({worst_pct:+.1f}%)')


# ══════════════════════════════════════════════════════════════════════════════
# PART B — Streetlight density bar chart
# ══════════════════════════════════════════════════════════════════════════════

print('\n' + '=' * 70)
print(' PART B: Average Streetlight Density by Cluster')
print('=' * 70)

sensor_sl = (
    analysis[['SensorNumber', 'Cluster', 'streetlights_50m']]
    .drop_duplicates('SensorNumber')
)
cluster_sl  = sensor_sl.groupby('Cluster', observed=True)['streetlights_50m'].mean()
network_mean = sensor_sl['streetlights_50m'].mean()

for c in CLUSTERS:
    print(f'  {c:10s}:  {cluster_sl[c]:5.1f}  streetlights within 50 m')
print(f'  {"Network":10s}:  {network_mean:5.1f}  (mean)')

# ── Bar chart ────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
bar_colours = ['#2196F3', '#4CAF50', '#FF9800']

bars = ax.bar(
    CLUSTERS,
    [cluster_sl[c] for c in CLUSTERS],
    color=bar_colours, edgecolor='black', linewidth=0.8,
)

ax.axhline(
    network_mean, color='red', linestyle='--', linewidth=1.5,
    label=f'Network mean ({network_mean:.1f})',
)

for bar in bars:
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2, h + 0.3,
        f'{h:.1f}', ha='center', va='bottom', fontsize=11, fontweight='bold',
    )

ax.set_ylabel('Mean Streetlights within 50 m')
ax.set_title('Average Streetlight Density by Cluster')
ax.legend()
ax.set_ylim(0, max(cluster_sl) * 1.25)
plt.tight_layout()

chart_path = OUTPUT_DIR / 'streetlight_density_by_cluster.png'
fig.savefig(chart_path, dpi=150)
print(f'\n  Chart saved → {chart_path.name}')


# ══════════════════════════════════════════════════════════════════════════════
# PART C — ROI:  expected ped uplift from +1 SD streetlight density
# ══════════════════════════════════════════════════════════════════════════════

print('\n' + '=' * 70)
print(' PART C: Expected Pedestrian Change from +1 SD Streetlight Density')
print('=' * 70)

print('  Fitting NB GLM (Dark × streetlights_z interaction) ... ',
      end='', flush=True)
t0 = time.time()

model5 = sm.GLM.from_formula(
    "ped ~ Dark + Dark:businesses_z + Dark:streetlights_z"
    " + ped_lag1 + ped_lag24 + C(hour) + C(dow) + C(month)"
    " + temp_c + wind_ms + rain_mm + C(SensorNumber)",
    data=analysis,
    family=sm.families.NegativeBinomial(),
).fit()

print(f'done  ({time.time() - t0:.0f}s)')

sl_coef = model5.params['Dark:streetlights_z']
sl_pval = model5.pvalues['Dark:streetlights_z']
dark_uplift_pct = 100 * (np.exp(sl_coef) - 1)

print(f'\n  Dark × streetlights_z  coef = {sl_coef:+.4f}   (p = {sl_pval:.3f})')
print(f'  → +1 SD in streetlight density changes dark-hour ped counts '
      f'by {dark_uplift_pct:+.1f}%')
print(f'  (1 SD = {SL_STD:.1f} streetlights within 50 m;  '
      f'network mean = {SL_MEAN:.1f})')

# ── Per-cluster breakdown ────────────────────────────────────────────────────
print(f'\n  {"Cluster":10s} {"Dark peds":>12s} {"Total peds":>12s} '
      f'{"Dark share":>11s}  {"Δ (% of total)":>14s}')
print('  ' + '─' * 65)

for c in CLUSTERS:
    cdf = analysis.loc[analysis['Cluster'] == c]
    dark_ped  = cdf.loc[cdf['Dark'] == 1, 'ped'].sum()
    total_ped = cdf['ped'].sum()
    dark_share = dark_ped / total_ped

    # Multiplicative uplift applies only to dark-hour pedestrian volume
    delta_ped   = dark_ped * (np.exp(sl_coef) - 1)
    pct_of_total = delta_ped / total_ped * 100

    print(f'  {c:10s} {dark_ped:12,.0f} {total_ped:12,.0f} '
          f'{100 * dark_share:10.1f}%  {pct_of_total:+13.2f}%')

print(f'\n  1 SD = {SL_STD:.1f} streetlights within 50 m  '
      f'(network mean = {SL_MEAN:.1f})')
if sl_pval > 0.05:
    print(f'  Note: Dark × streetlights_z interaction p = {sl_pval:.3f} '
          f'(suggestive, not significant at α = 0.05).')


# ══════════════════════════════════════════════════════════════════════════════
# PART D — Policy evidence: the case for prioritising Central
# ══════════════════════════════════════════════════════════════════════════════
#
# The seven points below assemble the quantitative evidence from Parts A–C
# (and new calculations) into a coherent argument for focusing streetlight
# investment on the Central cluster.
# ══════════════════════════════════════════════════════════════════════════════

print('\n' + '=' * 70)
print(' PART D: Policy Evidence — Why Prioritise Central?')
print('=' * 70)


# ── Point 1: Central carries the highest absolute pedestrian volume ──────────

print('\n  ── Point 1: Central carries the highest absolute pedestrian volume')
print('  ' + '─' * 65)

for c in CLUSTERS:
    cdf = analysis.loc[analysis['Cluster'] == c]
    daylight = cdf.loc[cdf['Dark'] == 0, 'ped']
    total    = cdf['ped'].sum()
    n_sensors = cdf['SensorNumber'].nunique()
    print(f'  {c:10s}:  mean daylight ped/sensor-hour = {daylight.mean():6.1f}  |  '
          f'total mixed-hour peds = {total:>12,.0f}  |  {n_sensors} sensors')

central_total = analysis.loc[analysis['Cluster'] == 'Central', 'ped'].sum()
east_total    = analysis.loc[analysis['Cluster'] == 'East',    'ped'].sum()
outlier_total = analysis.loc[analysis['Cluster'] == 'Outlier', 'ped'].sum()

print(f'\n  Central total is {central_total / east_total:.1f}x East '
      f'and {central_total / outlier_total:.1f}x Outlier.')
print('  → Any percentage improvement yields far more people walking in Central.')


# ── Point 2: Central's darkness penalty is substantial ───────────────────────
# (Uses Model 2 results from Part A above)

print('\n  ── Point 2: Central\'s darkness penalty is substantial and robust')
print('  ' + '─' * 65)
print('  (From Part A — Model 2 NB GLM with Dark × Cluster interaction)')

for c in CLUSTERS:
    cdf = analysis.loc[analysis['Cluster'] == c]
    dark_ped  = cdf.loc[cdf['Dark'] == 1, 'ped'].sum()
    light_ped = cdf.loc[cdf['Dark'] == 0, 'ped'].sum()
    pct = 100 * (np.exp(cluster_dark[c]) - 1)
    print(f'  {c:10s}:  adjusted penalty = {pct:+.1f}%  |  '
          f'dark-hour peds = {dark_ped:>12,.0f}  |  '
          f'daylight peds = {light_ped:>12,.0f}')

central_dark = analysis.loc[
    (analysis['Cluster'] == 'Central') & (analysis['Dark'] == 1), 'ped'
].sum()
print(f'\n  Central\'s {central_dark:,.0f} dark-hour pedestrians represent the '
      f'largest pool of suppressed activity to recover.')


# ── Point 3: +1 SD streetlights recovers the most pedestrians in Central ────
# (Uses Model 5 results from Part C above)

print('\n  ── Point 3: +1 SD streetlight increase recovers most peds in Central')
print('  ' + '─' * 65)
print('  (From Part C — Model 5: Dark × streetlights_z interaction)')

cluster_deltas = {}
for c in CLUSTERS:
    cdf = analysis.loc[analysis['Cluster'] == c]
    dark_ped  = cdf.loc[cdf['Dark'] == 1, 'ped'].sum()
    total_ped = cdf['ped'].sum()
    delta = dark_ped * (np.exp(sl_coef) - 1)
    pct   = delta / total_ped * 100
    cluster_deltas[c] = delta
    print(f'  {c:10s}:  +{delta:>10,.0f} additional dark-hour ped trips  '
          f'({pct:+.2f}% of cluster total)')

print(f'\n  Central delivers {cluster_deltas["Central"] / cluster_deltas["East"]:.1f}x '
      f'more pedestrians than East and '
      f'{cluster_deltas["Central"] / cluster_deltas["Outlier"]:.1f}x more than Outlier')
print('  from the same +1 SD streetlight intervention.')


# ── Point 4: CMS infrastructure and per-lamppost cost ────────────────────────
# Bristol Council's £12M LED upgrade covers ~29,000 streetlights (lantern
# heads only, not columns). Includes a Central Management System (CMS)
# for remote corridor-by-corridor, hour-by-hour dimming/brightening.
# Source: bristol.gov.uk/residents/streets-travel/upgrading-to-led-street-lighting
# See also: darkness_scalar_field_map.py for per-sensor spatial effects.

print('\n  ── Point 4: CMS infrastructure and per-lamppost cost')
print('  ' + '─' * 65)

LED_BUDGET     = 12_000_000   # £12 million
N_LAMPS_LOW    = 29_000       # most-cited figure (council/press)
N_LAMPS_HIGH   = 36_000       # expanded scope figure (later sources)
cost_low  = LED_BUDGET / N_LAMPS_HIGH
cost_high = LED_BUDGET / N_LAMPS_LOW

print(f'  Bristol LED programme:  £{LED_BUDGET / 1e6:.0f}M budget  '
      f'|  {N_LAMPS_LOW:,}–{N_LAMPS_HIGH:,} streetlights')
print(f'  Per-lamppost cost:     £{cost_low:,.0f} – £{cost_high:,.0f}')
print(f'  Annual energy saving:  ~£1.8M – £2.0M  '
      f'(~13,000 t CO₂ over 10 years)')

# Hypothetical Central infill: 1 SD = SL_STD extra lights per sensor corridor
central_sensors = analysis.loc[
    analysis['Cluster'] == 'Central', 'SensorNumber'
].nunique()
extra_lights = int(round(SL_STD)) * central_sensors
infill_cost_low  = extra_lights * cost_low
infill_cost_high = extra_lights * cost_high

print(f'\n  Hypothetical Central +1 SD infill:')
print(f'    {central_sensors} corridors × {int(round(SL_STD))} extra lights '
      f'= {extra_lights} new luminaires')
print(f'    Estimated cost: £{infill_cost_low:,.0f} – £{infill_cost_high:,.0f}')
print(f'    Expected uplift: +{cluster_deltas["Central"]:,.0f} dark-hour ped trips '
      f'(mixed-hour sample)')
print('  The CMS allows brightening during high-penalty hours (05:00–07:00)')
print('  offset by deeper dimming during low-footfall hours (23:00–04:00).')


# ── Point 5: Central is where cycling deterrence concentrates ────────────────

print('\n  ── Point 5: Cycling deterrence concentrates in Central')
print('  ' + '─' * 65)

# Fit Model 2 for cyclists (same structure as pedestrian Model 2)
cyc_cols = ['cyc', 'Dark', 'Cluster', 'cyc_lag1', 'cyc_lag24',
            'hour', 'dow', 'month', 'temp_c', 'wind_ms', 'rain_mm',
            'SensorNumber']
cyc_analysis = analysis.dropna(subset=cyc_cols).copy()

print('  Fitting NB GLM for cyclists (Dark × Cluster) ... ', end='', flush=True)
t0 = time.time()

model2_cyc = sm.GLM.from_formula(
    "cyc ~ Dark + Dark:C(Cluster, Treatment(reference='Central'))"
    " + cyc_lag1 + cyc_lag24 + C(hour) + C(dow) + C(month)"
    " + temp_c + wind_ms + rain_mm + C(SensorNumber)",
    data=cyc_analysis,
    family=sm.families.NegativeBinomial(),
).fit()

print(f'done  ({time.time() - t0:.0f}s)')

cyc_dark_base = model2_cyc.params['Dark']
cyc_east_term = [t for t in model2_cyc.params.index
                 if 'Dark:C(Cluster' in t and 'East' in t][0]
cyc_out_term  = [t for t in model2_cyc.params.index
                 if 'Dark:C(Cluster' in t and 'Outlier' in t][0]

cyc_cluster_dark = {
    'Central': cyc_dark_base,
    'East':    cyc_dark_base + model2_cyc.params[cyc_east_term],
    'Outlier': cyc_dark_base + model2_cyc.params[cyc_out_term],
}

cyc_p_values = {
    'Central': model2_cyc.pvalues['Dark'],
    'East':    model2_cyc.pvalues[cyc_east_term],
    'Outlier': model2_cyc.pvalues[cyc_out_term],
}

for c in CLUSTERS:
    pct = 100 * (np.exp(cyc_cluster_dark[c]) - 1)
    p = cyc_p_values[c]
    sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else ''))
    print(f'  {c:10s}:  cyclist darkness penalty = {pct:+.1f}%  '
          f'(p = {p:.4f}){sig}')

print('\n  → Streetlight investment in Central addresses both pedestrian AND')
print('    cyclist active travel simultaneously.')


# ── Point 6: Central's streetlight density is uneven ─────────────────────────
# (Extends Part B — streetlight density bar chart)

print('\n  ── Point 6: Central\'s streetlight density is uneven')
print('  ' + '─' * 65)
print('  (Extends Part B — streetlight density analysis)')

for c in CLUSTERS:
    c_sl = sensor_sl.loc[sensor_sl['Cluster'] == c, 'streetlights_50m']
    below = (c_sl < network_mean).sum()
    total = len(c_sl)
    print(f'  {c:10s}:  mean = {c_sl.mean():5.1f}  |  '
          f'{below} of {total} sensors below network mean ({network_mean:.1f})')

central_below = sensor_sl.loc[
    (sensor_sl['Cluster'] == 'Central') &
    (sensor_sl['streetlights_50m'] < network_mean)
]
if len(central_below) > 0:
    print(f'\n  Under-lit Central sensors:')
    for _, row in central_below.iterrows():
        print(f'    Sensor {int(row["SensorNumber"]):>3d}:  '
              f'{row["streetlights_50m"]:.0f} streetlights within 50 m')
    print('  → These under-lit Central corridors are where marginal returns '
          'are highest.')


# ── Point 7: Morning commute is the key window ──────────────────────────────

print('\n  ── Point 7: The morning commute is the key window')
print('  ' + '─' * 65)

# Raw darkness penalty by hour and cluster
morning_hours = [5, 6]
evening_hours = [17, 18, 19, 20]

print(f'\n  {"Hour":>6s}', end='')
for c in CLUSTERS:
    print(f'  {c:>10s}', end='')
print()
print('  ' + '─' * 40)

hour_penalties = {}
for h in MIXED_HOURS:
    hour_penalties[h] = {}
    print(f'  {h:02d}:00 ', end='')
    for c in CLUSTERS:
        hdf = analysis.loc[(analysis['Cluster'] == c) & (analysis['hour'] == h)]
        day_mean  = hdf.loc[hdf['Dark'] == 0, 'ped'].mean()
        dark_mean = hdf.loc[hdf['Dark'] == 1, 'ped'].mean()
        if day_mean > 0:
            raw_pct = (dark_mean - day_mean) / day_mean * 100
        else:
            raw_pct = np.nan
        hour_penalties[h][c] = raw_pct
        print(f'  {raw_pct:+9.1f}%', end='')
    print()

# Morning vs evening average penalty for Central
central_morning = np.mean([hour_penalties[h]['Central'] for h in morning_hours])
central_evening = np.mean([hour_penalties[h]['Central'] for h in evening_hours])
ratio = abs(central_morning) / abs(central_evening) if central_evening != 0 else np.nan

print(f'\n  Central morning avg penalty: {central_morning:+.1f}%')
print(f'  Central evening avg penalty: {central_evening:+.1f}%')
print(f'  Morning penalty is {ratio:.1f}x more severe than evening.')
print('\n  → Smart brightening during 05:00–07:00 on Central\'s commuter')
print('    corridors directly addresses the largest darkness gap in the network.')
# See also: darkness_scalar_field_map.py — Centre_Scalar_Map.png shows the
# spatial distribution of per-sensor darkness effects within Central.


# ── Point 8: Central average ped counts by hour (for ROI uplift calc) ────────

print('\n  ── Point 8: Central avg ped counts by hour (daylight vs darkness)')
print('  ' + '─' * 65)
print('  (Use with Dark × streetlights_z uplift to estimate expected increase)')

ROI_HOURS = [5, 6, 17, 18, 19]
central_df = analysis.loc[analysis['Cluster'] == 'Central']

print(f'\n  {"Hour":>6s}  {"Daylight":>10s}  {"Darkness":>10s}  '
      f'{"Dark penalty":>13s}  {"Expected +1SD uplift":>20s}')
print('  ' + '─' * 67)

for h in ROI_HOURS:
    hdf = central_df.loc[central_df['hour'] == h]
    day_mean  = hdf.loc[hdf['Dark'] == 0, 'ped'].mean()
    dark_mean = hdf.loc[hdf['Dark'] == 1, 'ped'].mean()
    # Expected dark-hour count after +1 SD streetlights
    uplift_mean = dark_mean * np.exp(sl_coef)
    print(f'  {h:02d}:00  {day_mean:10.1f}  {dark_mean:10.1f}  '
          f'{dark_mean - day_mean:+12.1f}  '
          f'{uplift_mean:10.1f}  (+{uplift_mean - dark_mean:.1f})')

print(f'\n  Dark × streetlights_z coefficient = {sl_coef:+.4f}  →  '
      f'multiplicative uplift = ×{np.exp(sl_coef):.4f}  ({dark_uplift_pct:+.1f}%)')
print('  To compute expected increase: dark-hour count × '
      f'(exp({sl_coef:.4f}) − 1) = dark-hour count × {np.exp(sl_coef) - 1:.4f}')

# (a) Total additional raw pedestrian count in Central from +1 SD
total_extra = 0.0
print(f'\n  (a) Raw additional pedestrians per sensor-hour in Central (+1 SD):')
print(f'      {"Hour":>6s}  {"Current dark":>13s}  {"After +1SD":>11s}  {"Extra peds":>11s}')
print('      ' + '─' * 47)
for h in ROI_HOURS:
    hdf = central_df.loc[central_df['hour'] == h]
    dark_mean = hdf.loc[hdf['Dark'] == 1, 'ped'].mean()
    extra = dark_mean * (np.exp(sl_coef) - 1)
    total_extra += extra
    print(f'      {h:02d}:00  {dark_mean:13.1f}  {dark_mean + extra:11.1f}  {extra:+11.1f}')

print(f'      {"Total":>6s}  {"":>13s}  {"":>11s}  {total_extra:+11.1f}')
print(f'\n  → Across these 5 hours, +1 SD streetlights adds ~{total_extra:+.0f} '
      f'pedestrians per sensor-hour in Central during darkness.')

# (b) Difference in darkness penalty: Central vs East
# (Uses Model 2 cluster-specific coefficients from Part A)
print(f'\n  (b) Darkness penalty comparison — Central vs East:')
central_pct = 100 * (np.exp(cluster_dark['Central']) - 1)
east_pct    = 100 * (np.exp(cluster_dark['East']) - 1)
diff_pct    = central_pct - east_pct

print(f'      Central adjusted darkness penalty:  {central_pct:+.1f}%')
print(f'      East adjusted darkness penalty:     {east_pct:+.1f}%')
print(f'      Difference (Central − East):        {diff_pct:+.1f} pp')

# Also show as raw hourly counts for each mixed hour
print(f'\n      {"Hour":>6s}  {"Central dark":>13s}  {"East dark":>10s}  '
      f'{"Central day":>12s}  {"East day":>9s}  '
      f'{"Central drop":>13s}  {"East drop":>10s}  {"Diff":>8s}')
print('      ' + '─' * 95)
for h in ROI_HOURS:
    c_hdf = analysis.loc[(analysis['Cluster'] == 'Central') & (analysis['hour'] == h)]
    e_hdf = analysis.loc[(analysis['Cluster'] == 'East')    & (analysis['hour'] == h)]
    c_day  = c_hdf.loc[c_hdf['Dark'] == 0, 'ped'].mean()
    c_dark = c_hdf.loc[c_hdf['Dark'] == 1, 'ped'].mean()
    e_day  = e_hdf.loc[e_hdf['Dark'] == 0, 'ped'].mean()
    e_dark = e_hdf.loc[e_hdf['Dark'] == 1, 'ped'].mean()
    c_drop = c_dark - c_day
    e_drop = e_dark - e_day
    print(f'      {h:02d}:00  {c_dark:13.1f}  {e_dark:10.1f}  '
          f'{c_day:12.1f}  {e_day:9.1f}  '
          f'{c_drop:+13.1f}  {e_drop:+10.1f}  {c_drop - e_drop:+8.1f}')

print(f'\n  → Central loses {abs(diff_pct):.1f} percentage points more of its '
      f'pedestrian count to darkness than East.')


# ══════════════════════════════════════════════════════════════════════════════
# PART E — Estimating total streetlights in the Central cluster
# ══════════════════════════════════════════════════════════════════════════════
# The only streetlight data in the project is sensor_streetlight_freq.csv,
# which records *how many streetlights fall within 10 m, 25 m, and 50 m of
# each sensor*.  There is no raw point-location dataset of individual lamps.
#
# Method:
#   1. Sum the 50 m counts for Central sensors (lower-bound estimate of
#      streetlights near monitored corridors).
#   2. Check inter-sensor distances for 50 m buffer overlap — if two
#      sensors are < 100 m apart their 50 m buffers overlap and some
#      lamps may be double-counted.
#   3. Extrapolate from sampled area to the full Central cluster area
#      (circle of radius 1.2 km centred on -2.592, 51.453) to give a
#      rough estimate of total streetlights in the city centre.

print('\n' + '=' * 70)
print(' PART E: Estimated Streetlights in the Central Cluster')
print('=' * 70)

SENSOR_LOC_PATH = Path(__file__).parent / 'Sensor_Location.csv'
sensor_locs = pd.read_csv(SENSOR_LOC_PATH)

# Streetlight counts for the full set of sensors (already loaded)
sl_full = pd.read_csv(STREETLIGHT_PATH)

# Central sensor list (from the analysis panel)
central_sensor_ids = (
    analysis.loc[analysis['Cluster'] == 'Central', 'SensorNumber']
    .unique()
)
central_sl = (
    sl_full[sl_full['SensorNumber'].isin(central_sensor_ids)]
    .merge(sensor_locs, on='SensorNumber', how='left')
)

print(f'\n  Central sensors: {len(central_sl)}')
print(f'\n  {"Sensor":>8s}  {"SL 10m":>7s}  {"SL 25m":>7s}  {"SL 50m":>7s}  '
      f'{"Longitude":>10s}  {"Latitude":>10s}')
print('  ' + '─' * 57)
for _, r in central_sl.sort_values('SensorNumber').iterrows():
    print(f'  {int(r["SensorNumber"]):>8d}  {int(r["streetlights_10m"]):>7d}  '
          f'{int(r["streetlights_25m"]):>7d}  {int(r["streetlights_50m"]):>7d}  '
          f'{r["Longitude"]:>10.5f}  {r["Latitude"]:>10.5f}')

sum_50m = central_sl['streetlights_50m'].sum()
sum_25m = central_sl['streetlights_25m'].sum()
sum_10m = central_sl['streetlights_10m'].sum()
print(f'\n  Totals:          {int(sum_10m):>7d}  {int(sum_25m):>7d}  {int(sum_50m):>7d}')

# ── Check for 50 m buffer overlap between Central sensors ────────────────────
def haversine_m(lon1, lat1, lon2, lat2):
    """Great-circle distance in metres between two points."""
    R = 6_371_000
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2))
         * np.sin(dlon / 2) ** 2)
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

print('\n  Inter-sensor distances (pairs < 100 m → potential 50 m overlap):')
overlap_pairs = []
ids  = central_sl['SensorNumber'].values
lons = central_sl['Longitude'].values
lats = central_sl['Latitude'].values
for i in range(len(ids)):
    for j in range(i + 1, len(ids)):
        d = haversine_m(lons[i], lats[i], lons[j], lats[j])
        if d < 100:
            overlap_pairs.append((int(ids[i]), int(ids[j]), d))
            print(f'    Sensors {int(ids[i]):>3d} & {int(ids[j]):>3d}:  '
                  f'{d:.0f} m apart  ← buffers overlap')

if not overlap_pairs:
    print('    None — all Central sensors are > 100 m apart.')
    print(f'\n  → Sum of 50 m counts ({int(sum_50m)}) has no double-counting.')
else:
    print(f'\n  → {len(overlap_pairs)} pair(s) with potential overlap; '
          f'raw sum of {int(sum_50m)} may include some double-counted lamps.')

# ── Extrapolate to full Central cluster area ─────────────────────────────────
CLUSTER_RADIUS_M = 1200  # 1.2 km
buffer_radius_m  = 50
cluster_area_km2 = np.pi * (CLUSTER_RADIUS_M / 1000) ** 2
sensor_area_km2  = np.pi * (buffer_radius_m / 1000) ** 2
sampled_area_km2 = sensor_area_km2 * len(central_sl)
coverage_pct     = sampled_area_km2 / cluster_area_km2 * 100

# Density from sampled area
density_per_km2  = sum_50m / sampled_area_km2
extrapolated     = density_per_km2 * cluster_area_km2

print(f'\n  Extrapolation to full Central cluster (r = {CLUSTER_RADIUS_M} m):')
print(f'    Cluster area:         {cluster_area_km2:.2f} km²')
print(f'    Sampled area (9×50m): {sampled_area_km2:.4f} km²  '
      f'({coverage_pct:.1f}% of cluster)')
print(f'    Observed density:     {density_per_km2:.0f} streetlights / km²')
print(f'    Extrapolated total:   ~{extrapolated:,.0f} streetlights in Central cluster')
print(f'\n  Caveat: sensors are placed on busy corridors, so streetlight density')
print(f'  near sensors is likely higher than the cluster-wide average.')
print(f'  The extrapolated figure is therefore an upper-bound estimate.')


# ══════════════════════════════════════════════════════════════════════════════
print('\n' + '=' * 70)
print(' Summary')
print('=' * 70)
print('  Parts A–C: Model fitting and ROI calculations')
print('  Part D (Points 1–7): Policy evidence for prioritising Central')
print('  Part E: Estimated streetlights in Central cluster')
print('  Spatial evidence: Centre_Scalar_Map.png (from darkness_scalar_field_map.py)')
print('  Streetlight density chart: streetlight_density_by_cluster.png')
print('=' * 70)

plt.show()
