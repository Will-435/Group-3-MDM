# Paper-Style Weighted Mantel-Haenszel OR Interpretation

This note accompanies [Reprocess OR Confirmation.ipynb](/Users/karandama/Documents/School%20stuff/Uni%20Shit/Y2/MDM2/Group-3-MDM/main/Karan%20-%20Notebooks%20and%20analysis/Reprocess%20OR%20Confirmation.ipynb) and documents the paper-style weighted Mantel-Haenszel approach used to produce one headline odds ratio per mode and one cluster breakdown.

## Method Summary

This mirrors the approach used in Fotios et al. (2024) for pooling across the full case-hour / control-hour matrix.

For each valid hour pair we define:

- `A`: counts in the case hour when that hour is in daylight
- `B`: counts in the case hour when that hour is in darkness
- `C`: counts in the control hour during the daylight-case periods
- `D`: counts in the control hour during the dark-case periods

For each hour pair, `N = A + B + C + D`.

The pooled weighted odds ratio is:

`MHw_OR = sum((A * D) / N) / sum((B * C) / N)`

This is different from pooling clusters for a fixed hour pair. Here the summation runs across the **hour matrix** itself, so the output is one weighted pooled OR summarising all valid hour choices at once.

The notebook applies this in two ways:

- **Overall by mode:** first aggregate counts across all cleaned sensors for each hour pair, then pool across the 60 hour pairs
- **By cluster and mode:** repeat the same weighted pooling separately within `Central`, `East`, and `Outlier`

The 95% confidence intervals use the Robins-Breslow-Greenland variance formula reported alongside Eq. 3 in the PLOS One paper.

## Results: One Headline Figure Per Mode

The paper-style pooled-hours results are:

Mode | MHw_OR | 95% CI | Effect size
Pedestrians | 1.387 | 1.385 to 1.388 | Small
Cars | 1.078 | 1.077 to 1.079 | Negligible
Cyclists | 1.155 | 1.153 to 1.157 | Negligible

### Plain-English Reading

- **Pedestrians:** this is the clearest result. The pooled-hours OR is well above 1, and all 60 hour-pair ORs are above 1. In plain English, walking counts are consistently lower after dark across the whole hour matrix, not just for one hand-picked hour comparison.
- **Cars:** the pooled-hours OR is very close to 1. That means darkness does not produce a strong practical shift in car counts in this case-control framework.
- **Cyclists:** the pooled-hours OR is above 1 overall, but only modestly so. Many hour pairs still show lower cycling after dark, but the effect is much less stable than for pedestrians.

## Results: Cluster Breakdown

The cluster-specific weighted pooled-hours results are:

Cluster | Mode | MHw_OR | 95% CI | Effect size
Central | Pedestrians | 1.385 | 1.384 to 1.387 | Small
East | Pedestrians | 1.391 | 1.389 to 1.393 | Small
Outlier | Pedestrians | 1.382 | 1.379 to 1.385 | Small
Central | Cars | 1.059 | 1.058 to 1.060 | Negligible
East | Cars | 1.084 | 1.083 to 1.085 | Negligible
Outlier | Cars | 1.004 | 1.001 to 1.006 | Negligible
Central | Cyclists | 1.371 | 1.367 to 1.374 | Small
East | Cyclists | 1.046 | 1.043 to 1.049 | Negligible
Outlier | Cyclists | 0.735 | 0.731 to 0.739 | Small, reverse direction

### Plain-English Reading

- **Pedestrians:** the pooled-hours pedestrian OR is remarkably consistent across all three clusters. That means the main walking result is geographically robust rather than being driven by just one part of Bristol.
- **Cars:** every cluster stays very close to 1.0, especially `Outlier`. So the practical story for cars remains weak everywhere.
- **Cyclists:** this is where the real heterogeneity appears. `Central` shows a clear deterrence pattern, `East` is close to neutral, and `Outlier` is below 1.0. In plain English, the cyclist darkness effect is not uniform across place types.

## Main Conclusion

If the goal is to mirror the paper, the most appropriate headline summary is the **paper-style weighted MH OR pooled across all valid hour pairs**.

For these Bristol data, that pooled-hours summary suggests:

- a strong and consistent darkness effect for **pedestrians**
- only a weak near-neutral overall effect for **cars**
- a modest overall effect for **cyclists**, with an important warning that the cyclist result varies a lot by cluster

So the cleanest reporting strategy is:

- use the **overall pooled-hours MH OR** as the headline summary for each mode
- immediately follow it with the **cluster breakdown** to show that pedestrians are stable but cyclists are heterogeneous

## Additional View: Pooling Across All Control Hours for Each Case Hour

The notebook also now includes a second weighted MH summary that fixes one **case hour** at a time and pools across all 10 control hours.

The formula is the same weighted MH structure as before:

`MHw_OR(case hour i) = sum_j((A_ij * D_ij) / N_ij) / sum_j((B_ij * C_ij) / N_ij)`

where:

- `i` is the fixed case hour
- `j` indexes the control hours
- `N_ij = A_ij + B_ij + C_ij + D_ij`

So the only difference is the summation index. Instead of summing across the whole case-hour / control-hour matrix, we now sum across the **control hours only** for one chosen case hour.

This is useful because it shows whether the overall pooled-hours result is being driven mainly by one specific transition hour, especially the morning `06:00` period.

### Results by Case Hour

Mode | Case hour | MHw_OR | 95% CI
Pedestrians | 05:00 | 2.207 | 2.200 to 2.214
Pedestrians | 06:00 | 2.847 | 2.840 to 2.855
Pedestrians | 17:00 | 1.194 | 1.191 to 1.196
Pedestrians | 18:00 | 1.168 | 1.166 to 1.170
Pedestrians | 19:00 | 1.218 | 1.216 to 1.220
Pedestrians | 20:00 | 1.288 | 1.285 to 1.290
Cars | 05:00 | 1.522 | 1.520 to 1.525
Cars | 06:00 | 1.725 | 1.723 to 1.728
Cars | 17:00 | 0.989 | 0.988 to 0.991
Cars | 18:00 | 0.923 | 0.922 to 0.924
Cars | 19:00 | 0.860 | 0.859 to 0.861
Cars | 20:00 | 0.931 | 0.930 to 0.932
Cyclists | 05:00 | 1.239 | 1.233 to 1.246
Cyclists | 06:00 | 1.963 | 1.954 to 1.971
Cyclists | 17:00 | 1.091 | 1.086 to 1.096
Cyclists | 18:00 | 0.969 | 0.965 to 0.973
Cyclists | 19:00 | 0.990 | 0.986 to 0.994
Cyclists | 20:00 | 1.010 | 1.006 to 1.014

### Plain-English Reading

- **Pedestrians:** every case hour remains above 1, which means the darkness effect is not limited to one narrow comparison. The strongest signal is clearly at `06:00`, but the evening mixed hours still point in the same direction.
- **Cars:** the story changes by case hour. The morning case hours (`05:00` and `06:00`) are above 1, but the evening case hours are around or below 1. That means the car result is not a single stable darkness effect across the day.
- **Cyclists:** `06:00` stands out as the main source of the cyclist pooled-hours result. Outside that morning transition, the cyclist case-hour summaries are much closer to 1, so the overall cyclist effect is less uniform than the pedestrian effect.

### Why This Section Matters

The full pooled-hours MH OR is still the best single headline measure if the goal is to mirror the paper. But this case-hour version is a useful diagnostic because it shows **where the pooled effect is coming from**.

For these data:

- the pedestrian result is broad and consistent, but strongest at `06:00`
- the cyclist result is driven mainly by `06:00`
- the car result changes sign between morning and evening
