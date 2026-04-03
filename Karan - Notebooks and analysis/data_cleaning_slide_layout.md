# Slide Text For PowerPoint

## Slide 1

### Title
Spatial Clustering of Bristol Sensors

### Subtitle
Grouping sensors by location allowed us to test whether lighting effects varied across different parts of the city.

### Image To Insert
`Processed Data/bristol_cluster_cutout_kept_only.png`

### Suggested Layout
Place the title and subtitle at the top.
Use the cluster map as the main visual on the right or centre-right.
Place the bullet text on the left.
Add the short takeaway line along the bottom.

### Bullet Text For Direct Paste
We grouped sensors into spatial clusters to capture geographic variation across Bristol.
Sensors were assigned to fixed cluster centres using a 1200 metre radius, with sensors outside these areas labelled as Outliers.
This allowed us to compare whether the effect of lighting conditions differed by location rather than assuming a single city-wide pattern.
The cluster structure was then used throughout the later light versus dark odds-ratio analysis.

### Takeaway
Using clusters lets us test whether transport responses to darkness differ between Central Bristol, East Bristol, and the remaining outlying sites.

---

## Slide 2

### Title
Outlier and Missing-Data Filtering

### Subtitle
Persistently inactive sensors were removed to prevent missing or unreliable counts from biasing the final models.

### Image To Insert
`Processed Data/bristol_cluster_cutout_removed_highlighted.png`

### Suggested Layout
Use the same layout as Slide 1 so the two slides feel visually linked.
Keep the map in the same position and swap only the bullet text and image.
Use the second image to point directly to the removed sensors in red.

### Bullet Text For Direct Paste
We identified sensors with 7 or more consecutive days where the daily total count was zero across pedestrians, cars, and cyclists.
These sensors were treated as persistently inactive and removed from the merged dataset entirely.
Keeping these sensors would introduce long runs of effectively missing data and could distort both the case-control odds ratios and the negative binomial time-series GLM.
After filtering, the dataset reduced from 58 to 37 sensors, and all 5 sensors in the North cluster were removed.

### Small Table For Slide
Metric | Before | After
Sensors | 58 | 37
Hourly rows | 509,472 | 325,008

Cluster | Before | After
Central | 16 | 9
East | 27 | 20
North | 5 | 0
Outlier | 10 | 8

### Takeaway
Removing persistently inactive sensors improved data quality and reduced the risk that missing counts would bias the estimated lighting effects.

---

## Presenter Notes

For Slide 1:
Emphasise that the clusters are a way to examine whether lighting effects vary by location.
Keep the focus on spatial structure, not cleaning.

For Slide 2:
Be careful not to call these classic statistical outliers.
They are better described as persistently inactive sensors or data-quality exclusions.
Stress that the reason for removal is to avoid bias in the odds-ratio analysis and the negative binomial time-series model.
