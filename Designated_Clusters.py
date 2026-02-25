import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import contextily as ctx # this is the file that handles integrating a map with plt

df = pd.read_csv('Sensor_Location.csv') # Naturally change this to be your own path

centres = {
    "Central": (-2.592, 51.453), #2
    "East": (-2.555, 51.457), #42
    "North": (-2.616, 51.479) #63
}

mean_lat = df["Latitude"].mean()

lat_to_m = 111000
lon_to_m = 111000 * np.cos(np.deg2rad(mean_lat))

def distance_m(lon1, lat1, lon2, lat2):
    dx = (lon1 - lon2) * lon_to_m
    dy = (lat1 - lat2) * lat_to_m
    return np.sqrt(dx**2 + dy**2)

radius = 1200 

cluster_labels = []

for _, row in df.iterrows():
    distances = {
        name: distance_m(row["Longitude"], row["Latitude"], clon, clat)
        for name, (clon, clat) in centres.items()
    }
    
    closest_cluster = min(distances, key=distances.get)
    
    if distances[closest_cluster] <= radius:
        cluster_labels.append(closest_cluster)
    else:
        cluster_labels.append("Outlier")

df["Cluster"] = cluster_labels

# --- This is a small change to the original that turns the output to a grid plotted on a real map with contextily

for name, group in df.groupby("Cluster"):
    # I've put a white boarder around each marker
    plt.scatter(group["Longitude"], group["Latitude"], label=name, s=30, edgecolors='white', zorder=3)

theta = np.linspace(0, 2*np.pi, 200)

for name, (clon, clat) in centres.items():
    circle_lon = clon + (radius / lon_to_m) * np.cos(theta)
    circle_lat = clat + (radius / lat_to_m) * np.sin(theta)
    
    # I've inclued a small black marker in each sector
    plt.plot(circle_lon, circle_lat, color = 'red', linestyle = '--', linewidth = 2, zorder = 4)
    plt.scatter(clon, clat, marker = "x", color = 'black', s = 100, zorder = 5) 

# This fetches map tiles from openstreetmap
# crs="EPSG:4326" is just the code for the lat/long convention
# alpha is teh "translucentness" of the map
ctx.add_basemap(plt.gca(), crs = "EPSG:4326", source = ctx.providers.OpenStreetMap.Mapnik, alpha =0.8)

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Sensor Clusters: Bristol, UK")
plt.legend()
plt.grid(True, alpha=0.3) # Dimmed grid lines so they don't ruin the map
plt.gca().set_aspect("equal", adjustable="box")
plt.show()
