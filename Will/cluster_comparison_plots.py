import pandas as pd
import numpy as np
import matplotlib as plt
import glob
import os

# Curtosy of Tom Tucker
def get_distance(lon1, lat1, lon2, lat2, lon_to_m, lat_to_m):

    dx = (lon1 - lon2) * lon_to_m
    dy = (lat1 - lat2) * lat_to_m

    return np.sqrt(dx**2 + dy**2)


def assign_cluster(row, centres, radius, lon_to_m, lat_to_m):

    distances = {
    name: get_distance(row["Longitude"], row["Latitude"], cr_lon, cr_lat, lon_to_m, lat_to_m)
    for name, (cr_lon, cr_lat) in centres.items()
    }

    closest_name = min(distances, key = distances.get)

    if distances[closest_name] <= radius:
        return closest_name
    
    return "Outlier"


def process_all_crime_files(folder_path, centres, radius = 1200):
    # This funct involves a lot of code from Tom. Thanks for the help Tom! 👍
    # This file classifies crime as being in one pf teh three clusters.

    all_files = glob.glob(os.path.join(folder_path, "*.csv"))

    data_frames = []

    for file in all_files:
        df = pd.read_csv(file)

        # dropping any rows with missing values in the long and lat columns
        df = df.dropna(subset=["Latitude", "Longitude"])
        
        if df.empty:
            continue

        mean_lat = df['Latitude'].mean()
        lat_to_m = 111000  # latitude rate of change is ~0 degrees per m so the distance betwen values stays the same
        lon_to_m = 111000 * np.cos(np.deg2rad(mean_lat)) # longitude obv converges on the poles. Luckily the rate of change is ~constant 

        cluster_labels = []

        for _, row in df.iterrows():
            distances = {
                name: get_distance(row["Longitude"], row["Latitude"], cr_lon, cr_lat, lon_to_m, lat_to_m)
                for name, (cr_lon, cr_lat) in centres.items()
            }
            
            closest_cluster = min(distances, key=distances.get)
            
            if distances[closest_cluster] <= radius:
                cluster_labels.append(closest_cluster)
            else:
                cluster_labels.append("Outlier")

        df["Cluster"] = cluster_labels

        # Filter out the "Outliers" (keep only classified rows)
        df_short = df[df["Cluster"] != "Outlier"].copy()
        
        # Add to our list for stacking
        data_frames.append(df_short)
        print(f"Processed {os.path.basename(file)}: Found {len(df_short)} relevant rows.")

    # Vertical stack all filtered dataframes
    if data_frames:
        final_df = pd.concat(data_frames, axis=0, ignore_index=True)
        return final_df
    return None


centres = {
    "Central": (-2.592, 51.453), 
    "East": (-2.555, 51.457), 
    "North": (-2.616, 51.479) 
}

crime_folder_path = 'TB-2/23-24_crime_data'

crime_df = process_all_crime_files(crime_folder_path, centres)

if crime_df is not None:
    print(f"\nFinal Crime DataFrame Size: {len(crime_df)} rows.")
    print('\n', crime_df.head())
    print(crime_df.columns)


# --------------------------------------------------------------------------------------------------------------------
'''
Now that the data is cleaned and sorted, we'll move on to plotting the data for the
different clusters - both crime and footfall stats over time.

Hourly data isnt available yet (I have put in a FOI request), so we'll use daily data for now.
This should still give us insight into any strong corrolations between crime and footfall.
'''
# --------------------------------------------------------------------------------------------------------------------

# Hourly data is not yet available so I have to do it on a monthly basis. SHould still be insightful.

def compress_to_monthly(input_file, output_file):
    """
    Reads an hourly CSV file and saves a version aggregated by day instead of by the hour.
    We will use thsi for the footfall data so it can be related to the daily crime data.
    """
    # Load the dataset
    df = pd.read_csv(input_file)
    
    # Convert the 'date' column to datetime objects
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by the date (ignoring the time) and sum the counts
    # We specify the columns ['ped', 'car', 'cyc'] to ensure only relevant data is summed
    daily_df = df.groupby(df['date'].dt.to_period('M'))[['ped', 'car', 'cyc']].sum().reset_index()
    
    # Save the compressed data
    daily_df.to_csv(output_file, index = False)
    
    return daily_df

travel_folder_path = 'TB-2/Hourly count data'
all_travel_files = glob.glob(os.path.join(travel_folder_path, "*.csv"))

for file in all_travel_files:
    compress_to_monthly(file, f'TB-2/Monthly count data/{os.path.basename(file)}')

sensors_clustered_df = pd.read_csv("TB-2/Sensor_Location_with_clusters.csv")


sc_df = sensors_clustered_df[sensors_clustered_df['Cluster'] == 'Central']
sn_df = sensors_clustered_df[sensors_clustered_df['Cluster'] == 'North']
se_df = sensors_clustered_df[sensors_clustered_df['Cluster'] == 'East']

cc_df = crime_df[crime_df['Cluster'] == 'Central']
cn_df = crime_df[crime_df['Cluster'] == 'North']
ce_df = crime_df[crime_df['Cluster'] == 'East']

monthly_folder = "TB-2/Monthly count data"
all_monthly_files = glob.glob(os.path.join(monthly_folder, "*.csv"))

def plot_cluster(cluster_name, sensors_df, crimes_df):
    crimes_df["Month"] = pd.to_datetime(crimes_df["Month"], errors = "coerce")
    crimes_df = crimes_df.dropna(subset = ["Month"])

    crime_monthly = (
        crimes_df
        .groupby(crimes_df["Month"].dt.to_period("M"))
        .size()
        .reset_index(name="Crime_Count")
    )

    crime_monthly["Month"] = crime_monthly["Month"].dt.to_timestamp()
    cluster_sensors = set(sensors_df["SensorNumber"].astype(int).tolist())

    sensor_data = {}

    for file in all_monthly_files:
        base = os.path.splitext(os.path.basename(file))[0]

        import re
        m = re.search(r"\d+", base)
        if not m:
            continue
        sensor_id = int(m.group())

        if sensor_id in cluster_sensors:
            df = pd.read_csv(file)

            df["date"] = pd.to_datetime(df["date"], errors = "coerce")
            df["car"] = pd.to_numeric(df["car"], errors = "coerce")
            df["ped"] = pd.to_numeric(df["ped"], errors = "coerce")
            df["cyc"] = pd.to_numeric(df["cyc"], errors = "coerce")

            df = df.dropna(subset=["date"]).sort_values("date")
            sensor_data[sensor_id] = df

    print(f"Loaded {cluster_name} sensors:", sorted(sensor_data.keys()))

    fig, ax1 = plt.subplots(figsize=(12, 6))

    for sensor_id, df in sensor_data.items():
        ax1.plot(df["date"], df["car"], color = "red", linewidth = 1, alpha = 1)
        ax1.plot(df["date"], df["ped"], color = "green", linewidth = 1, alpha = 1)
        ax1.plot(df["date"], df["cyc"], color = "blue", linewidth = 1, alpha = 1)

    ax1.set_xlabel("Month")
    ax1.set_ylabel("Transport Counts")
    ax1.set_title(f"{cluster_name} Cluster: Monthly Crime vs Transport Counts")

    ax2 = ax1.twinx()
    ax2.plot(
        crime_monthly["Month"],
        crime_monthly["Crime_Count"],
        color="black",
        linewidth=2,
        label="Crime Count"
    )
    ax2.set_ylabel("Crime Count")

    plt.tight_layout()
    plt.show()


# Plot each cluster separately
plot_cluster("Central", sc_df, cc_df)
plot_cluster("North", sn_df, cn_df)
plot_cluster("East", se_df, ce_df)
