"""
Darkness Effect Scalar Field Map for Bristol
=============================================

Produces a static image map of Bristol showing where the largest
darkness-driven drops in pedestrian and cyclist counts occur.

The script fits a per-sensor negative binomial GLM (mirroring the
approach in Cell 32 of 'Darkness GLM Models Will.ipynb') for both
pedestrians and cyclists, then spatially interpolates the fitted
percentage effects into a translucent scalar field overlaid on
an OpenStreetMap basemap.

Requirements:
listed in imports.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolours
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.interpolate import griddata
import contextily as ctx

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*Negative binomial dispersion.*")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_DIRECTORY = Path(__file__).resolve().parent / "GLM data"
BASE_PANEL_PATH = DATA_DIRECTORY / "all_sensor_data_with_locations_and_clusters.csv"
BIG_TABLE_PATH = DATA_DIRECTORY / "big_table_weather_rain_clusters_safety.csv"
SENSOR_LOCATION_PATH = Path(__file__).resolve().parent / "Sensor_Location.csv"
OUTPUT_IMAGE_PATH = Path(__file__).resolve().parent / "darkness_scalar_field_map.png"
CENTRE_MAP_PATH = Path(__file__).resolve().parent / "Centre_Scalar_Map.png"
EAST_MAP_PATH = Path(__file__).resolve().parent / "East_Scalar_Map.png"

# Hours where both daylight and darkness observations coexist
MIXED_CASE_HOURS = [5, 6, 17, 18, 19, 20]

# Minimum number of observations required to fit a per-sensor model
MINIMUM_OBSERVATIONS_PER_SENSOR = 200

# Grid resolution for the spatial interpolation (points per axis)
INTERPOLATION_GRID_SIZE = 300

# Scalar field opacity (0 = fully transparent, 1 = fully opaque)
SCALAR_FIELD_OPACITY = 0.55

# Map centre coordinates (Bristol, UK)
BRISTOL_CENTRE_LATITUDE = 51.4575
BRISTOL_CENTRE_LONGITUDE = -2.5850
DEFAULT_ZOOM_LEVEL = 13

# Padding around sensor bounding box for the interpolation grid (degrees)
GRID_PADDING_DEGREES = 0.008


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------
def load_and_prepare_analysis_data():
    """
    Load the sensor panel and weather data, merge them, and restrict
    to the mixed-case hours used for the darkness GLM analysis.

    Returns
    -------
    pandas.DataFrame
        The analysis-ready dataframe filtered to daylight and darkness
        observations during mixed-case hours, with lag columns appended.
    """
    panel = pd.read_csv(BASE_PANEL_PATH)
    panel["datetime"] = pd.to_datetime(panel["date"], utc=True, errors="coerce")

    # Merge in hourly weather variables from the big table
    big_table = pd.read_csv(BIG_TABLE_PATH)
    big_table["datetime"] = pd.to_datetime(
        big_table["datetime"], utc=True, errors="coerce"
    )
    weather_rain = (
        big_table[["datetime", "temp_c", "wind_ms", "rain_mm"]]
        .drop_duplicates("datetime")
        .dropna(subset=["datetime"])
    )
    del big_table

    panel = panel.merge(weather_rain, on="datetime", how="left")
    panel["rain_mm"] = panel["rain_mm"].fillna(0)

    # Calendar fields
    panel["hour"] = panel["datetime"].dt.hour.astype(int)
    panel["dow"] = panel["datetime"].dt.dayofweek.astype(int)
    panel["month"] = panel["datetime"].dt.month.astype(int)

    # Sort and compute lag variables
    panel = panel.sort_values(["SensorNumber", "datetime"]).reset_index(drop=True)
    panel["ped_lag1"] = panel.groupby("SensorNumber")["ped"].shift(1)
    panel["ped_lag24"] = panel.groupby("SensorNumber")["ped"].shift(24)
    panel["cyc_lag1"] = panel.groupby("SensorNumber")["cyc"].shift(1)
    panel["cyc_lag24"] = panel.groupby("SensorNumber")["cyc"].shift(24)

    # Restrict to mixed-case hours with valid light classifications
    analysis_data = panel.loc[
        panel["light_class"].isin(["daylight", "darkness"])
        & panel["hour"].isin(MIXED_CASE_HOURS)
    ].copy()

    return analysis_data


def load_sensor_locations():
    """
    Load sensor locations from the dedicated CSV file.

    Returns
    -------
    pandas.DataFrame
        Dataframe with columns SensorNumber, Longitude, Latitude.
    """
    return pd.read_csv(SENSOR_LOCATION_PATH)


def fit_per_sensor_darkness_model(analysis_data, outcome):
    """
    Fit a negative binomial GLM per sensor to estimate the sensor-level
    darkness effect on the given outcome variable.

    For each sensor with sufficient data, the model is:

        outcome ~ Dark + lag1 + lag24 + C(hour) + C(dow) + C(month)
                  + temp_c + wind_ms + rain_mm

    Parameters
    ----------
    analysis_data : pandas.DataFrame
        The analysis panel with all required columns present.
    outcome : str
        Either 'ped' for pedestrians or 'cyc' for cyclists.

    Returns
    -------
    pandas.DataFrame
        One row per sensor with columns: SensorNumber, dark_coefficient,
        dark_percentage_change, dark_p_value.
    """
    lag1_column = f"{outcome}_lag1"
    lag24_column = f"{outcome}_lag24"
    required_columns = [
        outcome, "Dark", lag1_column, lag24_column,
        "hour", "dow", "month", "temp_c", "wind_ms", "rain_mm",
    ]

    formula = (
        f"{outcome} ~ Dark + {lag1_column} + {lag24_column}"
        f" + C(hour) + C(dow) + C(month) + temp_c + wind_ms + rain_mm"
    )

    sensor_results = []

    for sensor_id, sensor_data in analysis_data.groupby("SensorNumber"):
        model_data = sensor_data[required_columns].dropna().copy()

        # Skip sensors with too few observations or no darkness variation
        if len(model_data) < MINIMUM_OBSERVATIONS_PER_SENSOR:
            continue
        if model_data["Dark"].nunique() < 2:
            continue

        try:
            result = smf.glm(
                formula=formula,
                data=model_data,
                family=sm.families.NegativeBinomial(),
            ).fit()

            percentage_change = 100.0 * (np.exp(result.params["Dark"]) - 1.0)
            sensor_results.append({
                "SensorNumber": sensor_id,
                "dark_coefficient": result.params["Dark"],
                "dark_percentage_change": percentage_change,
                "dark_p_value": result.pvalues["Dark"],
            })
        except Exception:
            # Some sensors may fail to converge; skip them
            continue

    return pd.DataFrame(sensor_results)


def interpolate_scalar_field(longitudes, latitudes, values):
    """
    Spatially interpolate sensor-level values onto a regular grid
    covering the sensor bounding box with padding.

    Parameters
    ----------
    longitudes : array-like
        Longitude coordinates of the sensor points.
    latitudes : array-like
        Latitude coordinates of the sensor points.
    values : array-like
        The scalar values to interpolate (e.g. percentage change).

    Returns
    -------
    grid_longitudes : numpy.ndarray
        1-D array of longitude values for the grid columns.
    grid_latitudes : numpy.ndarray
        1-D array of latitude values for the grid rows.
    grid_values : numpy.ndarray
        2-D array of interpolated values (latitude x longitude).
    """
    longitude_min = np.min(longitudes) - GRID_PADDING_DEGREES
    longitude_max = np.max(longitudes) + GRID_PADDING_DEGREES
    latitude_min = np.min(latitudes) - GRID_PADDING_DEGREES
    latitude_max = np.max(latitudes) + GRID_PADDING_DEGREES

    grid_longitudes = np.linspace(
        longitude_min, longitude_max, INTERPOLATION_GRID_SIZE
    )
    grid_latitudes = np.linspace(
        latitude_min, latitude_max, INTERPOLATION_GRID_SIZE
    )

    mesh_longitudes, mesh_latitudes = np.meshgrid(grid_longitudes, grid_latitudes)

    grid_values = griddata(
        points=np.column_stack([longitudes, latitudes]),
        values=values,
        xi=(mesh_longitudes, mesh_latitudes),
        method="cubic",
    )

    return grid_longitudes, grid_latitudes, grid_values


def build_darkness_colour_map():
    """
    Create the custom green-yellow-orange-red colour map used for the
    scalar field overlay.

    The scale is inverted so that the most negative values (largest
    darkness-driven drops) appear red and the least negative appear green.

    Returns
    -------
    matplotlib.colors.LinearSegmentedColormap
        The custom colour map.
    """
    colour_stops = [
        (0.0, "#2ecc71"),   # green (least negative / positive)
        (0.33, "#f1c40f"),  # yellow
        (0.66, "#e67e22"),  # orange
        (1.0, "#e74c3c"),   # red (most negative / largest drop)
    ]
    return mcolours.LinearSegmentedColormap.from_list(
        "darkness_effect", colour_stops
    )


def plot_scalar_field_panel(
    axis, effects_data, mode_label, colour_map,
    value_min, value_max, value_median,
    label_scale=1.0,
):
    """
    Draw a single scalar field panel onto the given matplotlib axis,
    with basemap tiles, interpolated overlay, and sensor markers.

    The colour scale is centred so that the median percentage change
    maps to the midpoint of the green-yellow-orange-red gradient.

    Parameters
    ----------
    axis : matplotlib.axes.Axes
        The subplot axis to draw on.
    effects_data : pandas.DataFrame
        Per-sensor effects with Longitude, Latitude, dark_percentage_change,
        SensorNumber, and dark_p_value columns.
    mode_label : str
        Title for the panel (e.g. 'Pedestrian' or 'Cyclist').
    colour_map : matplotlib.colors.Colormap
        The colour map to use for the scalar field.
    value_min : float
        The minimum value for the shared colour scale.
    value_max : float
        The maximum value for the shared colour scale.
    value_median : float
        The median value, mapped to the midpoint of the colour scale.
    """
    longitudes = effects_data["Longitude"].values
    latitudes = effects_data["Latitude"].values
    values = effects_data["dark_percentage_change"].values

    # Interpolate the scalar field
    grid_lons, grid_lats, grid_vals = interpolate_scalar_field(
        longitudes, latitudes, values
    )

    # Two-piece linear normalisation centred on the median:
    #   value_min -> 0.0, value_median -> 0.5, value_max -> 1.0
    # Then invert so that most negative (value_min) -> 1.0 (red)
    normalised = np.where(
        grid_vals <= value_median,
        0.5 * (grid_vals - value_min) / (value_median - value_min),
        0.5 + 0.5 * (grid_vals - value_median) / (value_max - value_median),
    )
    normalised = np.clip(1.0 - normalised, 0.0, 1.0)
    rgba = colour_map(normalised)

    # Set alpha: transparent where data is missing, translucent elsewhere
    alpha_mask = ~np.isnan(grid_vals)
    rgba[..., 3] = np.where(alpha_mask, SCALAR_FIELD_OPACITY, 0.0)

    # Draw the scalar field overlay
    extent = [grid_lons[0], grid_lons[-1], grid_lats[0], grid_lats[-1]]
    axis.imshow(
        rgba, extent=extent, origin="lower",
        aspect="auto", interpolation="bilinear", zorder=2,
    )

    # Plot sensor markers with percentage labels
    for _, row in effects_data.iterrows():
        percentage = row["dark_percentage_change"]
        p_value = row["dark_p_value"]
        significance = "***" if p_value < 0.001 else (
            "**" if p_value < 0.01 else ("*" if p_value < 0.05 else "")
        )

        axis.plot(
            row["Longitude"], row["Latitude"],
            marker="o", markersize=5 * label_scale, markeredgecolor="black",
            markerfacecolor="white", markeredgewidth=0.8, zorder=4,
        )
        axis.annotate(
            f"{percentage:+.0f}%{significance}",
            xy=(row["Longitude"], row["Latitude"]),
            xytext=(4, 4), textcoords="offset points",
            fontsize=5.5 * label_scale, fontweight="bold", color="black",
            zorder=5,
            bbox=dict(
                boxstyle="round,pad=0.15", facecolor="white",
                edgecolor="none", alpha=0.7,
            ),
        )

    # Add the basemap tiles underneath the overlay
    ctx.add_basemap(
        axis, crs="EPSG:4326",
        source=ctx.providers.CartoDB.Positron, zorder=1,
    )

    axis.set_title(
        mode_label + " Darkness Effect",
        fontsize=12 * label_scale, fontweight="bold",
    )
    axis.set_xlim(extent[0] - GRID_PADDING_DEGREES, extent[1] + GRID_PADDING_DEGREES)
    axis.set_ylim(extent[2] - GRID_PADDING_DEGREES, extent[3] + GRID_PADDING_DEGREES)
    axis.set_xlabel("Longitude", fontsize=10 * label_scale)
    axis.set_ylabel("Latitude", fontsize=10 * label_scale)
    axis.tick_params(labelsize=9 * label_scale)


def build_static_map(pedestrian_effects, cyclist_effects, sensor_locations):
    """
    Construct a side-by-side static map image with scalar field overlays
    for both pedestrian and cyclist darkness effects.

    Parameters
    ----------
    pedestrian_effects : pandas.DataFrame
        Per-sensor darkness effects for pedestrians.
    cyclist_effects : pandas.DataFrame
        Per-sensor darkness effects for cyclists.
    sensor_locations : pandas.DataFrame
        Sensor coordinates (SensorNumber, Longitude, Latitude).

    Returns
    -------
    matplotlib.figure.Figure
        The assembled figure ready to be saved.
    """
    # Merge location data onto effects
    pedestrian_data = pedestrian_effects.merge(
        sensor_locations, on="SensorNumber", how="inner"
    )
    cyclist_data = cyclist_effects.merge(
        sensor_locations, on="SensorNumber", how="inner"
    )

    # Shared colour scale across both panels, centred on the median
    all_percentage_values = np.concatenate([
        pedestrian_data["dark_percentage_change"].values,
        cyclist_data["dark_percentage_change"].values,
    ])
    shared_value_min = np.nanmin(all_percentage_values)
    shared_value_max = np.nanmax(all_percentage_values)
    shared_value_median = np.nanmedian(all_percentage_values)

    colour_map = build_darkness_colour_map()

    figure, axes = plt.subplots(1, 2, figsize=(18, 10))

    # Pedestrian panel (left) and cyclist panel (right)
    for axis, effects_data, mode_label in [
        (axes[0], pedestrian_data, "Pedestrian"),
        (axes[1], cyclist_data, "Cyclist"),
    ]:
        plot_scalar_field_panel(
            axis, effects_data, mode_label,
            colour_map, shared_value_min, shared_value_max,
            shared_value_median,
        )

    # Colour bar with TwoSlopeNorm so the median sits at the midpoint.
    # Reversed colour map so the bar reads red (most negative) on the left.
    median_centred_norm = mcolours.TwoSlopeNorm(
        vcenter=shared_value_median,
        vmin=shared_value_min,
        vmax=shared_value_max,
    )
    reversed_colour_map = colour_map.reversed()
    scalar_mappable = plt.cm.ScalarMappable(
        cmap=reversed_colour_map, norm=median_centred_norm,
    )

    colour_bar = figure.colorbar(
        scalar_mappable, ax=axes, orientation="horizontal",
        fraction=0.04, pad=0.08, shrink=0.6,
    )
    colour_bar.set_label("Darkness effect on count (% change)", fontsize=11)

    figure.suptitle(
        "Spatial Distribution of Darkness Effects on Pedestrian and Cyclist Counts\n"
        "Bristol Sensor Network, Per-Sensor Negative Binomial GLM",
        fontsize=14, fontweight="bold", y=0.97,
    )
    figure.subplots_adjust(left=0.05, right=0.95, top=0.90, bottom=0.12, wspace=0.2)

    return figure


def build_cluster_map(
    pedestrian_effects, cyclist_effects, sensor_locations,
    cluster_sensors, cluster_title,
):
    """
    Build a side-by-side scalar field map for a single cluster.

    Parameters
    ----------
    pedestrian_effects, cyclist_effects : pandas.DataFrame
        Per-sensor darkness effects (network-wide).
    sensor_locations : pandas.DataFrame
        Sensor coordinates.
    cluster_sensors : array-like
        SensorNumber values belonging to this cluster.
    cluster_title : str
        Display name for the figure title (e.g. 'Centre').

    Returns
    -------
    matplotlib.figure.Figure
    """
    ped_data = (
        pedestrian_effects[pedestrian_effects["SensorNumber"].isin(cluster_sensors)]
        .merge(sensor_locations, on="SensorNumber", how="inner")
    )
    cyc_data = (
        cyclist_effects[cyclist_effects["SensorNumber"].isin(cluster_sensors)]
        .merge(sensor_locations, on="SensorNumber", how="inner")
    )

    all_vals = np.concatenate([
        ped_data["dark_percentage_change"].values,
        cyc_data["dark_percentage_change"].values,
    ])
    v_min = np.nanmin(all_vals)
    v_max = np.nanmax(all_vals)
    v_med = np.nanmedian(all_vals)

    colour_map = build_darkness_colour_map()

    figure, axes = plt.subplots(1, 2, figsize=(18, 10))

    scale = 1.8

    for axis, effects_data, mode_label in [
        (axes[0], ped_data, "Pedestrian"),
        (axes[1], cyc_data, "Cyclist"),
    ]:
        plot_scalar_field_panel(
            axis, effects_data, mode_label,
            colour_map, v_min, v_max, v_med,
            label_scale=scale,
        )

    median_centred_norm = mcolours.TwoSlopeNorm(
        vcenter=v_med, vmin=v_min, vmax=v_max,
    )
    reversed_colour_map = colour_map.reversed()
    scalar_mappable = plt.cm.ScalarMappable(
        cmap=reversed_colour_map, norm=median_centred_norm,
    )

    colour_bar = figure.colorbar(
        scalar_mappable, ax=axes, orientation="horizontal",
        fraction=0.04, pad=0.08, shrink=0.6,
    )
    colour_bar.set_label(
        "Darkness effect on count (% change)", fontsize=11 * scale,
    )
    colour_bar.ax.tick_params(labelsize=9 * scale)

    figure.suptitle(
        f"Darkness Effects — {cluster_title} Cluster\n"
        "Per-Sensor Negative Binomial GLM",
        fontsize=14 * scale, fontweight="bold", y=1.02,
    )
    figure.subplots_adjust(left=0.07, right=0.95, top=0.85, bottom=0.15, wspace=0.25)

    return figure


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    """
    Entry point. Loads data, fits per-sensor darkness models for
    pedestrians and cyclists, interpolates the results into scalar
    fields, and saves a static PNG image.
    """
    print("Loading and preparing analysis data...")
    analysis_data = load_and_prepare_analysis_data()
    sensor_locations = load_sensor_locations()

    print(
        f"Analysis sample: {len(analysis_data)} rows across "
        f"{analysis_data['SensorNumber'].nunique()} sensors"
    )

    print("Fitting per-sensor pedestrian darkness models...")
    pedestrian_effects = fit_per_sensor_darkness_model(analysis_data, "ped")
    print(f"  Successfully fitted models for {len(pedestrian_effects)} sensors")

    print("Fitting per-sensor cyclist darkness models...")
    cyclist_effects = fit_per_sensor_darkness_model(analysis_data, "cyc")
    print(f"  Successfully fitted models for {len(cyclist_effects)} sensors")

    print("Building static scalar field map...")
    figure = build_static_map(
        pedestrian_effects, cyclist_effects, sensor_locations
    )

    figure.savefig(str(OUTPUT_IMAGE_PATH), dpi=200, bbox_inches="tight")
    plt.close(figure)
    print(f"Map saved to: {OUTPUT_IMAGE_PATH}")

    # Per-cluster scalar field maps (Centre and East)
    sensor_cluster_map = (
        analysis_data[["SensorNumber", "Cluster"]]
        .drop_duplicates()
    )

    for cluster_name, output_path, display_name in [
        ("Central", CENTRE_MAP_PATH, "Centre"),
        ("East", EAST_MAP_PATH, "East"),
    ]:
        cluster_sensors = sensor_cluster_map.loc[
            sensor_cluster_map["Cluster"] == cluster_name, "SensorNumber"
        ].values
        print(f"Building {display_name} cluster scalar field map "
              f"({len(cluster_sensors)} sensors)...")
        cluster_figure = build_cluster_map(
            pedestrian_effects, cyclist_effects, sensor_locations,
            cluster_sensors, display_name,
        )
        cluster_figure.savefig(str(output_path), dpi=200, bbox_inches="tight")
        plt.close(cluster_figure)
        print(f"  Saved to: {output_path}")

    # Print a summary of the results
    print("\n--- Pedestrian Darkness Effects Summary ---")
    print(pedestrian_effects["dark_percentage_change"].describe().to_string())
    print("\n--- Cyclist Darkness Effects Summary ---")
    print(cyclist_effects["dark_percentage_change"].describe().to_string())


if __name__ == "__main__":
    main()
