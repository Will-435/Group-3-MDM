import pandas as pd
import numpy as np
from astral import LocationInfo
from astral.sun import elevation
import datetime

# Defining the location for astral sunset calculations
bristol = LocationInfo("Bristol", "England", "Europe/London", 51.4545, -2.5879)

# This function mirrors the approach of the example study in the brief
# This function has been built with the help of Gemini AI
def get_light_condition(dt):
    """
    Evaluates the solar altitude across the hour to determine light condition.
    Samples at the 0, 30, and 59-minute marks to ensure strict adherence.
    Solar altitude < -6 deg --> darkness.
    """
    times = [dt, dt + pd.Timedelta(minutes=30), dt + pd.Timedelta(minutes=59)]
    elevations = [elevation(bristol.observer, t) for t in times]
    
    # Daylight requires a solar altitude > 0° for the duration of the hour
    if all(e > 0 for e in elevations):
        return 'Daylight'
    # Darkness requires a solar altitude < -6° for the duration of the hour
    elif all(e < -6 for e in elevations):
        return 'Darkness'
    # If the hour contains any civil twilight, it must be excluded
    else:
        return 'Exclude' 
    

def calculate_cluster_or(cluster_df, case_hour, control_hour):
    """
    Calculates the Odds Ratio (OR) for a specific case and control hour pair within a cluster.
    """
    case_df = cluster_df[cluster_df['date'].dt.hour == case_hour]
    control_df = cluster_df[cluster_df['date'].dt.hour == control_hour]
    
    A = case_df[case_df['light_condition'] == 'Daylight']['cyc'].sum()
    B = case_df[case_df['light_condition'] == 'Darkness']['cyc'].sum()
    
    daylight_dates = case_df[case_df['light_condition'] == 'Daylight']['date'].dt.date
    darkness_dates = case_df[case_df['light_condition'] == 'Darkness']['date'].dt.date
    
    C = control_df[control_df['date'].dt.date.isin(daylight_dates)]['cyc'].sum()
    D = control_df[control_df['date'].dt.date.isin(darkness_dates)]['cyc'].sum()
    
    if 0 in [A, B, C, D]:
        return A, B, C, D, None 
        
    R_odds = (A / B) / (C / D)
    return A, B, C, D, R_odds


def calculate_mh_pooled_or(cluster_results):
    """
    Calculates the Mantel-Haenszel pooled Odds Ratio across all clusters.
    """
    numerator = 0
    denominator = 0
    
    for A, B, C, D in cluster_results:
        if None in [A, B, C, D]: continue
        N = A + B + C + D
        if N == 0: continue
        
        numerator += (A * D) / N
        denominator += (B * C) / N
        
    if denominator == 0: return None
    return numerator / denominator


# Load traffic data
# ** Update this with your local filepath if pulling from git **
df_traffic = pd.read_csv('TB-2/all_sensors.csv')
df_traffic['date'] = pd.to_datetime(df_traffic['date'])

# Load cluster designations
# **Update this with your local filepath if pulling from git**
df_clusters = pd.read_csv('TB-2/Sensor_Location_with_clusters.csv') 
# Merging the datasets. Sensor_id and SensorNumber are
# the same so they must be mapped to one another.
df = pd.merge(df_traffic, df_clusters[['SensorNumber', 'Cluster']], 
              left_on='sensor_id', right_on='SensorNumber', how='inner')

print("Computing solar altitudes")
# Calculate the condition once per unique hour and map it back for efficiency
# This block is also Gemini AI assisted.
unique_hours = pd.DataFrame({'date': df['date'].dt.floor('h').unique()})
unique_hours['light_condition'] = unique_hours['date'].apply(get_light_condition)
df = df.merge(unique_hours, on='date', how='left')


case_hr = 18   # 18:00 - 18:59. This hour is dark in wirnter, and light in summer
control_hr = 14 # Example 14:00 - 14:59. This time of day is consitently light.
cluster_metrics = []

# Group by the 'Cluster' column
for cluster_name, cluster_data in df.groupby("Cluster"):
    # Skip any sensors flagged as Outliers by Tom's spatial logic
    if cluster_name == "Outlier":
        continue
        
    A, B, C, D, OR = calculate_cluster_or(cluster_data, case_hr, control_hr)
    
    if OR is not None:
        print(f"Cluster: {cluster_name:<10} | Local OR: {OR:.3f}")
        cluster_metrics.append((A, B, C, D))
    else:
         print(f"Cluster: {cluster_name:<10} | Local OR: Insufficient Data (Div by 0)")

overall_bristol_or = calculate_mh_pooled_or(cluster_metrics)
if overall_bristol_or is not None:
    print(f"\n Mantel-Haenszel Pooled OR for Bristol: {overall_bristol_or:.3f}")
else:
    print("\n Insufficient data to calculate a pooled OR.")