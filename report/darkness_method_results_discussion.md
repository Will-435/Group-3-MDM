## Methods

### Data and analytical sample

The analysis used the cleaned Bristol hourly traffic-sensor panel developed in the project notebooks. After data cleaning, the final panel contained **37 sensors** and **325,008 hourly observations**. The Generalized Linear Model (GLM) analysis was restricted to the **mixed hours** used in the case-control design, namely `05:00`, `06:00`, `17:00`, `18:00`, `19:00`, and `20:00`, because these are the hours that switch between daylight and darkness over the year. This restriction makes the time-series analysis directly comparable to the matched odds-ratio approach while keeping the identification of darkness as clean as possible. Rows classified as `twilight` were excluded, so the main contrast was strictly **darkness versus daylight**.

The study question was whether darkness is associated with lower **pedestrian** and **cyclist** counts. These outcomes were modelled separately using the hourly `ped` and `cyc` counts. Darkness was represented by a binary `Dark` indicator derived from the solar classification already attached to each row. The analysis also included hourly weather controls (`temp_c`, `wind_ms`, `rain_mm`), calendar structure (`C(hour)`, `C(dow)`, `C(month)`), and short-run temporal dependence using lagged counts at one hour and twenty-four hours (`lag1`, `lag24`).

### Main modelling strategy

Because both outcomes are non-negative counts and the data are overdispersed, the main models were estimated as **Negative Binomial GLMs** with a log link. Standard errors were clustered by sensor. The baseline specification for each mode can be written as

$$
\log\{E(y_{it})\} =
\beta_0 + \beta_1 Dark_{it} + \beta_2 Lag1_{it} + \beta_3 Lag24_{it}
+ \gamma_h + \delta_d + \mu_m + \theta W_t + \alpha_i,
$$

where $y_{it}$ is either pedestrian count or cyclist count at sensor $i$ and hour $t$, $W_t$ is the weather vector, $\gamma_h$ are hour fixed effects, $\delta_d$ are day-of-week fixed effects, $\mu_m$ are month fixed effects, and $\alpha_i$ are sensor fixed effects. The sensor fixed effects absorb all time-invariant differences between sensors, including baseline location differences. Coefficients were converted to percentage changes using $100 \times (e^\beta - 1)$.

### Model ladder

Five related models were used.

| Model | Purpose | Additional terms beyond the baseline |
| --- | --- | --- |
| Model 1 | Main pooled darkness effect | `Dark` only |
| Model 2 | Spatial heterogeneity | `Dark × Cluster` |
| Model 3 | CCTV moderation | `Dark × cctv_z` |
| Model 4 | Safety moderation | `Dark × safety_z` |
| Model 5 | Built-environment moderation | `Dark × businesses_z` and `Dark × streetlights_z` |

In Models 2 to 5, the contextual variables were entered only through interactions with `Dark`. Their main effects were not separately estimated because they are time-invariant at sensor level and are therefore absorbed by the sensor fixed effects.

The final estimation sample for the main GLMs was **70,836 hourly rows** across the same **37 sensors** for both pedestrians and cyclists. The contextual variables were available for the full cleaned sensor set, so Models 3 to 5 used the same number of rows as the main model.

### Exploratory follow-up analyses

Two additional follow-up steps were used to support interpretation.

1. A **targeted pedestrian follow-up** examined hour-by-cluster pedestrian changes and ranked sensors by the size of their adjusted pedestrian darkness penalty.
2. A **deeper cyclist follow-up** examined sensor-level cyclist darkness effects, raw cyclist changes by cluster and hour, and within-cluster safety/context models for `East` and `Outlier`.

These follow-up checks were used to explain the fitted patterns rather than to replace the main model ladder.

## Results

### Initial descriptive signal

The first step was to establish whether the raw mixed-hour data showed any clear daylight-darkness contrast before statistical adjustment. This initial comparison already suggested a substantial darkness penalty for walking and a weaker, less stable pattern for cycling. Mean pedestrian counts were **116.9 in daylight** and **62.3 in darkness**, while mean cyclist counts were **27.2 in daylight** and **17.6 in darkness**. At sensor level, **36 of 37 sensors** showed lower average pedestrian counts in darkness, whereas cyclist responses were more mixed: **10 of 37 sensors** showed higher average cyclist counts in darkness.

At this stage, the pedestrian and cyclist patterns already began to diverge. The pedestrian drop was remarkably similar across the three broad cluster groups: approximately **-45.8% in Central**, **-47.1% in East**, and **-49.7% in Outlier**. By contrast, raw cyclist change varied much more sharply by cluster: **-49.2% in Central**, **-24.4% in East**, and **+16.6% in Outlier**. This contrast in the raw data is important because it signalled, even before modelling, that pedestrians might admit a relatively simple city-wide explanation whereas cyclists might require a deeper heterogeneity analysis.

### Main adjusted result

The next step was to test whether the raw differences survived once regular time structure, weather, short-run persistence, and fixed sensor differences were controlled for. Figure 1 summarises the directly comparable main darkness effects across the pooled models.

![Figure 1. Comparable main darkness effects across pooled models.](./glm_main_darkness_effects.png)

The strongest result in the entire analysis is the pedestrian darkness effect. In **Model 1**, the fitted pedestrian darkness effect was **-33.3%** with **p = 1.48e-09**. This means that, after controlling for hour, day of week, month, weather, lagged counts, and fixed sensor differences, pedestrian counts were estimated to be about one-third lower in darkness than in daylight during the mixed hours. In other words, the pedestrian darkness penalty was not explained away by commuter timing, seasonality, or obvious sensor-level differences.

The cyclist result was much weaker. In **Model 1**, the fitted cyclist darkness effect was **-4.0%** with **p = 0.446**, providing little evidence of a single pooled city-wide darkness penalty for cyclists once the same controls were introduced.

This contrast between a strong pedestrian coefficient and a weak pooled cyclist coefficient is what motivated the remainder of the results section. The key question became: is cycling simply less affected by darkness, or is the pooled cyclist estimate hiding strongly different local responses?

### What the model ladder added

To answer that question, the analysis moved from the baseline pooled model to the full model ladder. Table 1 summarises the main findings.

| Model | Pedestrians | Cyclists | Interpretation |
| --- | --- | --- | --- |
| Model 1 | `-33.3%`, `p = 1.48e-09` | `-4.0%`, `p = 0.446` | Strong pooled pedestrian penalty; weak pooled cyclist effect |
| Model 2 | Central `-32.6%`, East `-27.3%`, Outlier `-48.3%`; interaction p-values weak (`0.711`, `0.411`) | Central `-20.5%`, East `-1.6%`, Outlier `+20.4%`; `Dark × East p = 0.045` | Pedestrian effect broadly similar across clusters; cyclist effect heterogeneous by cluster |
| Model 3 | `-33.3%`, `p = 7.91e-10`; `Dark × CCTV p = 0.948` | `-3.9%`, `p = 0.448`; `Dark × CCTV p = 0.941` | CCTV does not explain much of the darkness pattern |
| Model 4 | `-34.3%`, `p = 2.01e-09`; `Dark × safety p = 0.160` | `-4.1%`, `p = 0.356`; `Dark × safety p = 0.000121` | Pedestrian result remains stable; cyclist darkness varies with safety context |
| Model 5 | `-33.8%`, `p = 1.33e-08`; `Dark × businesses p = 0.597`; `Dark × streetlights p = 0.118` | `-3.7%`, `p = 0.495`; `Dark × businesses p = 0.472`; `Dark × streetlights p = 0.835` | Built-environment terms do not materially change the main story |

The pedestrian result was stable across all pooled specifications. The darkness coefficient remained close to one-third lower counts in Models 1, 3, 4, and 5, which suggests that the main walking result is robust to the addition of CCTV, safety, and built-environment moderators. Model 2 pointed in the same direction: all three pedestrian cluster-specific effects remained negative, and the cluster interaction p-values were weak. In report terms, this was the first strong sign that pedestrian darkness behaves like a broadly similar network-wide phenomenon rather than a sharply place-specific one.

The cyclist result remained weak in pooled form, but this did not mean that darkness was irrelevant for cycling. Model 2 immediately suggested why the pooled estimate was small: the estimated darkness effect was **-20.5% in Central**, **-1.6% in East**, and **+20.4% in Outlier**, with a statistically meaningful `Dark × East` contrast (`p = 0.045`). Model 4 then suggested a second layer of cyclist heterogeneity, with a strong `Dark × safety` interaction (`p = 0.000121`). These two results signalled that the cyclist story should be interpreted through heterogeneity rather than through a single city-wide average.

### Pedestrian follow-up

Because the pedestrian result already looked strong and geographically widespread, the follow-up analysis for pedestrians was designed to add policy detail rather than to search for a new mechanism. The targeted pedestrian follow-up therefore asked two narrower questions: when is the walking penalty strongest, and which sites appear to be affected most severely?

The raw hour-by-cluster table showed that the pedestrian darkness penalty was strongest at the commuter-transition hours in every cluster:

- **Central:** `-63.3%` at `05:00`, `-72.7%` at `06:00`
- **East:** `-36.6%` at `05:00`, `-55.0%` at `06:00`
- **Outlier:** `-57.4%` at `05:00`, `-76.4%` at `06:00`

All three clusters remained clearly negative through the evening mixed hours as well. This matters because it sharpens the substantive interpretation: the pedestrian penalty is not just a late-night phenomenon and not just a problem in one area type. It is strongest when ordinary commuter and utility trips occur in darkness.

The adjusted sensor ranking showed that the pedestrian effect is also useful for prioritisation. The most negative adjusted pedestrian darkness effects included:

- sensor `4` in `Central`: approximately **-85.1%**
- sensor `8` in `Outlier`: approximately **-83.6%**
- sensor `22` in `East`: approximately **-66.9%**

These results suggest that the walking story is both broad and operationally useful: the council can justify network-wide concern while still identifying especially affected corridors first. The Model 5 pedestrian built-environment follow-up did not materially change that interpretation. The `Dark × businesses` interaction was weak (`p = 0.597`), and the `Dark × streetlights` interaction was positive but not statistically strong (`p = 0.118`). This means the current evidence supports a broad pedestrian darkness barrier more strongly than any one narrow environmental moderator.

### Cyclist follow-up

Figure 2 summarises the main cyclist heterogeneity findings.

![Figure 2. Cyclist heterogeneity by cluster and safety context.](./glm_cyclist_heterogeneity.png)

The cyclist follow-up was deeper because the preceding models had already shown that the pooled cyclist coefficient was concealing substantial heterogeneity. The first question was whether the cluster result from Model 2 reflected a genuine spread of sensor-level responses or just a few unusual sites. The left-hand panel of Figure 2 shows the cluster split from Model 2: the cyclist darkness effect was clearly negative in **Central** (**-20.5%**), close to zero in **East** (**-1.6%**), and positive in **Outlier** (**+20.4%**). This was not only a cluster-average artifact. In the deeper cyclist follow-up, adjusted sensor-level cyclist darkness effects were consistently negative in Central, but highly dispersed in East and Outlier.

The second question was whether the cluster split depended on time of day. The cyclist follow-up showed strong hour-by-cluster differences. Raw cyclist change by hour demonstrated that:

- `Central` was negative in every mixed hour, especially at `05:00` (`-63.1%`) and `06:00` (`-72.1%`)
- `East` was clearly negative at `06:00` (`-39.8%`) but close to flat or positive in most evening hours
- `Outlier` was positive in most mixed hours and nearly flat at `06:00` (`-0.2%`)

This suggests that the pooled cyclist coefficient washes together very different temporal and spatial responses. In other words, the weak pooled cyclist result is not simply a null finding; it is a summary of patterns that change across both space and hour.

The final question was whether the cyclist safety result was merely another reflection of broad cluster composition. The right-hand panel of Figure 2 shows the safety interaction from Model 4. At low safety, the fitted cyclist darkness effect was **+24.6%**; at mean safety, **-4.1%**; and at high safety, **-26.2%**, with **p = 0.000121** for the interaction term. Importantly, the within-cluster follow-up suggested that this safety pattern did not disappear when East and Outlier were analysed separately:

- In `East`, the cyclist darkness effect at mean safety was about **-8.0%**, and `Dark × safety` remained significant (`p = 0.0014`)
- In `Outlier`, the interaction remained strong (`p = 2.28e-09`), though the sample was smaller and more heterogeneous

However, these safety results should be interpreted cautiously. The safety variable is a static ward-level measure and is correlated with wider place context. Within `East`, safety was moderately correlated with both business density (`r ≈ 0.47`) and streetlights (`r ≈ 0.50`); within `Outlier`, safety was strongly correlated with business density (`r ≈ 0.71`). The cyclist safety result is therefore better understood as a place-context signal than as direct evidence that perceived safety alone drives cyclist behaviour.

Overall, the sequence of the cyclist results tells a coherent story. The weak pooled cyclist coefficient led to the cluster model; the cluster model showed strong spatial divergence; that divergence then justified hour-specific and within-cluster context follow-up. Each deeper step was therefore motivated by a pattern already visible in the preceding results, rather than added speculatively.

### Reading the place context more concretely

The statistical models identify **where** and **when** darkness effects are strongest, but they do not by themselves explain the exact mechanism. To make the interpretation more concrete, Figure 3 highlights the locations of the most extreme adjusted pedestrian and cyclist sensors and labels them by ward.

![Figure 3. Location context for the most extreme adjusted darkness effects.](./glm_sensor_context_map.png)

This figure should be read cautiously, but it can still be grounded more concretely than a ward label alone. The sensor metadata include coordinates, and nearby council CCTV labels provide named reference points for several of the key sites. That means the report can reasonably describe a sensor as being **near** a named street or junction area, even though it still cannot claim a precise street-centreline match.

For pedestrians, the strongest adjusted drops were not confined to one corridor type. The most severe effect was at sensor `4` in **Central** (**-85.1%**), located close to the **Baldwin Street / Clare Street** city-centre area. Another very large effect occurred at sensor `8` in **Clifton ward** (**-83.6%**), but the coordinates place this site much closer to the **Hotwells Gyratory / Hotwell Road** side of the ward than to Whiteladies Road. A third large effect occurred at sensor `22` in **Easton** (**-66.9%**), in the wider **Barton Hill / Marsh Lane** area east of the city centre. Read together, these sites suggest that the pedestrian darkness penalty is not tied to one single neighbourhood form. It appears across city-centre public-space links, western inner-city approaches, and eastern inner-urban corridors, which fits the broader modelling result that darkness acts as a general **after-dark usability** barrier for walking rather than a narrowly local mechanism.

For cyclists, the place reading is more sharply route-specific. One of the strongest negative adjusted cyclist effects was again at sensor `4` near **Baldwin Street / Clare Street** in the city centre (**-52.6%**), while another was at sensor `9` in **Clifton ward** (**-53.7%**), located near the **Portway / Bridge Valley Road / Hotwell Road** corridor. By contrast, one of the strongest positive adjusted cyclist effects was at sensor `39` in **St George West**, close to **Chalks Road** and therefore near the wider **Church Road** corridor, and another was at sensor `26` in **Lawrence Hill**, near **Beaufort House** in the inner-east area. The two largest positive cyclist effects, sensors `16` (**+124.9%**) and `18` (**+100.2%**), were both in the **Oak House** area of south Bristol. This pattern reinforces the earlier interpretation that cyclist responses to darkness are not uniform and are likely shaped by route role, adjacent land use, and network position.

The local context counts support this cautious reading. At cluster level, **Central** has the highest average CCTV density and the highest average business density, while **Outlier** has much lower business density and lower streetlight density. At sensor level, some strongly negative cyclist sites are high-activity central locations, whereas some positive cyclist sites are lower-activity outer or mixed sites. That combination suggests that the cyclist darkness effect is not simply a matter of “more lighting” or “more CCTV”. It is more consistent with the idea that darkness interacts with the broader role of a route: commuter-heavy central corridors may lose activity in darkness, while some lower-volume or more residential routes do not show the same penalty.

This contextual reading does not prove causation, but it improves the interpretability of the findings. The pedestrian results point toward a widespread after-dark walking barrier across multiple place types, whereas the cyclist results point toward more route-specific and location-specific mechanisms.

## Discussion

### Main interpretation

Taken together, the results provide a clear answer for pedestrians and a more conditional answer for cyclists. For **pedestrians**, darkness is associated with a large and robust reduction in counts. The consistency of the effect across raw summaries, the pooled GLMs, the cluster model, and the targeted pedestrian follow-up suggests that darkness acts as a broad barrier to walking during the mixed commuter-transition hours used in this study.

For **cyclists**, the evidence does not support one simple city-wide darkness effect of the same kind. The pooled GLM is weak, but the cluster, safety, and follow-up analyses show that cyclist responses vary sharply across places and times. This means that a single average cyclist coefficient is not the most informative summary of the data.

### What the models add beyond raw comparisons

The raw data alone suggest lower activity in darkness for both modes, but the GLMs show how much of that difference survives after controlling for regular time structure, weather, lagged dependence, and fixed differences between sensors. For pedestrians, a large part of the darkness penalty remains after adjustment. For cyclists, much less remains on average, and what does remain is highly context-dependent.

This difference matters substantively. It suggests that walking behaviour responds to darkness in a more general and widespread way, whereas cycling appears to depend more strongly on the characteristics of the route and area in question.

### How the findings fit Bristol's current transport direction

The policy link can be stated much more precisely than "this fits Bristol policy". The relevant Bristol documents and schemes are:

1. the [Bristol Transport Strategy](https://www.bristol.gov.uk/council/policies-plans-and-strategies/bristol-transport-strategy), adopted in 2019, which sets out a goal of creating healthy places and increasing walking, cycling and public transport use;
2. Bristol's [A Safe Systems Approach to Road Safety: A 10 year plan, 2015 to 2024](https://www.bristol.gov.uk/residents/streets-travel/transport-plans-and-projects/road-safety-plans), which frames safe everyday movement on foot and by cycle as a public objective;
3. the [West of England Local Cycling and Walking Infrastructure Plan 2020 to 2036](https://www.westofengland-ca.gov.uk/wp-content/uploads/2021/09/West-of-England-Local-Cycling-and-Walking-Infrastructure-Plan-2020-2036.pdf), which identifies named Bristol walking and cycling priority corridors and areas.

The main pedestrian result is directly relevant to those policies. A pooled pedestrian darkness effect of **-33.3%** (`p = 1.48e-09`), together with raw pedestrian declines at **36 of 37** sensors, is not just statistically strong; it speaks to whether Bristol's existing active-travel objectives are being achieved in the after-dark periods when people actually travel to work, education and services.

The corridor alignment also needs to be stated carefully. The LCWIP identifies Bristol priority areas including **Clifton Village and Whiteladies Road**, **Fishponds and Church Road**, **Knowle and Totterdown**, **Bedminster and Southville**, and **Hartcliffe and Hengrove Park**. The sensor dataset does not contain named street segments, but for several key sites the coordinates and nearby council CCTV labels do give a usable corridor reference. The clearest match is in east Bristol: strong results around **Easton / St George West / Lawrence Hill** sit close to the **Church Road / Chalks Road / Wesley Way** geography that is already prioritised in both the LCWIP and Bristol's **East Bristol Liveable Neighbourhood**. The central results are also concrete rather than abstract: the strongest city-centre sensor sits near **Baldwin Street / Clare Street**, which places it within the same wider central movement system as the council's **Victoria Street**, **Bristol Bridge**, **King Street**, and **Queen Charlotte Street** schemes.

The Clifton evidence is more mixed and should be described honestly. The strongest sensors in **Clifton ward** are not obviously located on **Whiteladies Road** itself; the coordinate evidence places them nearer **Hotwell Road**, the **Hotwells Gyratory**, and the **Portway / Bridge Valley Road** side of the ward. That means the report should not claim a precise corridor match to the LCWIP's **Clifton Village and Whiteladies Road** area. The safer conclusion is that the western inner-city and gorge-edge approach routes in and around Clifton/Hotwells also appear sensitive to darkness, but they are not the cleanest policy match in the current dataset.

This more careful reading still supports the wider conclusion: the strongest statistical signals are appearing in places already treated by Bristol and the West of England Combined Authority as strategically important active-travel geographies, even if the exact level of alignment is clearer in east Bristol and the city centre than in Clifton.

The east Bristol connection is particularly specific. Bristol's [East Bristol Liveable Neighbourhood](https://www.bristol.gov.uk/ask/projects/east-bristol-liveable-neighbourhood/about-the-east-bristol-liveable-neighbourhood) covers **Barton Hill and parts of Redfield and St George, south of Church Road and north of the River Avon**. The council states that the area was selected partly because the **Wesley Way route, parallel to Church Road**, is already identified for investment in the regional walking and cycling plan. That matters for the present results because the `East` cyclist pattern was not simply zero; it was mixed by sensor and by hour, with a marked negative effect at `06:00` but little consistent evening penalty. That is exactly the kind of pattern that fits a corridor-specific interpretation rather than a single citywide cyclist response.

The central-city connection can also be made more concrete. Bristol's [Victoria Street improvements](https://www.bristol.gov.uk/residents/streets-travel/transport-plans-and-projects/victoria-street-improvements) are a **£5 million** project that will install a **two-way segregated cycle path between Bristol Bridge and Temple Gate**, upgrade the **Victoria Street / Counterslip junction**, enlarge bus stops, and add level crossing points. Bristol's [King Street pedestrianisation](https://www.bristol.gov.uk/residents/streets-travel/king-street-pedestrianisation) is intended to improve accessibility and the public realm while extending the segregated cycle route between **Baldwin Street and Queen Square via Queen Charlotte Street**. Because some of the strongest adjusted pedestrian and cyclist penalties occur at sensors in **Central**, these findings support the strategic logic of those exact city-centre schemes: central movement corridors and public-space links remain sensitive to after-dark conditions.

Lighting can also be linked to a named Bristol programme rather than discussed generically. Bristol's [Upgrading to LED street lighting](https://www.bristol.gov.uk/residents/streets-travel/transport-plans-and-projects/upgrading-to-led-street-lighting) programme is a citywide investment of **about £11.8 million** to convert approximately **36,000** street lights to LED units. The council states that the programme will direct light more accurately onto the **road and pavement** and improve visibility through a whiter, clearer light. In Model 5, streetlights were not a statistically strong standalone moderator. The precise conclusion is therefore not that the model proves lighting solves the problem, but that the broad pedestrian darkness penalty is consistent with the council's existing decision to treat lighting quality as one component of safer and more usable streets.

### Limitations

Several limitations should be acknowledged.

1. The analysis is observational, so coefficients should be interpreted as associations rather than definitive causal effects.
2. The GLMs were restricted to the mixed hours to preserve comparability with the case-control design and to identify darkness within hour. The findings therefore speak most directly to those commuter-transition periods, not to all hours of the day.
3. Contextual variables such as CCTV, safety, business density, and streetlight counts are time-invariant at sensor level. They are therefore useful as moderators, but they cannot capture short-term changes in local conditions.
4. The safety measure is a ward-level survey percentage rather than an hourly observed safety measure, which makes it especially important not to over-interpret the safety interaction causally.
5. The deeper sensor-level follow-up analyses are descriptive and exploratory. They are valuable for interpretation and prioritisation, but the strongest inferential conclusions remain those from the main pooled and clustered GLMs.

### Policy implications

Within those limits, the findings are still useful for policy.

First, the results support **after-dark pedestrian improvements on the named corridor areas already prioritised in Bristol policy**. The strongest evidence for this is the pooled pedestrian darkness effect of **-33.3%** (`p = 1.48e-09`), the raw pedestrian decline at **36 of 37** sensors, and the fact that the largest raw cluster penalties occur at `05:00` and `06:00` in **Central**, **East**, and **Outlier** alike. The most relevant policy frameworks are the [Bristol Transport Strategy](https://www.bristol.gov.uk/council/policies-plans-and-strategies/bristol-transport-strategy), Bristol's [Safe Systems road safety plan](https://www.bristol.gov.uk/residents/streets-travel/transport-plans-and-projects/road-safety-plans), and the LCWIP priority areas of **Clifton Village and Whiteladies Road**, **Fishponds and Church Road**, and **Hartcliffe and Hengrove Park**. The practical implication is not a vague call for "better walking", but targeted after-dark improvements to footway lighting quality, crossing legibility, wayfinding, and access to bus stops and city-centre destinations in those already-prioritised areas.

Second, the pedestrian sensor ranking supports **phased prioritisation within the policy areas that can actually be identified from the spatial evidence**. The three most severe adjusted pedestrian effects occurred near **Baldwin Street / Clare Street** in the city centre (**sensor `4`, -85.1%**), near the **Hotwells Gyratory / Hotwell Road** side of Clifton ward (**sensor `8`, -83.6%**), and in the **Barton Hill / Marsh Lane** side of Easton (**sensor `22`, -66.9%**). That is a stronger and more useful statement than simply naming wards. It implies that the most immediate project-level priorities are likely to be **central city-centre links** and the **east Bristol / Church Road / Wesley Way** geography, where the model evidence and named active-travel programmes line up most clearly, while the Clifton/Hotwells result points to a western inner-city after-dark walking issue that may need a separate corridor diagnosis rather than being folded too quickly into the Whiteladies Road narrative.

Third, the cyclist findings support **route-specific after-dark audits on named central and east Bristol corridors**, rather than a blanket citywide cyclist programme. In Model 2 the fitted cyclist darkness effect was **-20.5% in Central**, **-1.6% in East**, and **+20.4% in Outlier**. The location evidence sharpens that result. Negative cyclist sensors cluster near **Baldwin Street / Clare Street** in the centre and near the **Portway / Bridge Valley Road / Hotwell Road** corridor in Clifton ward, while positive or mixed eastern sensors appear near **Chalks Road / Church Road** and the inner-east **Lawrence Hill** area. In practical terms, that means the most directly relevant schemes are the **Victoria Street to Bristol Bridge / Temple Gate corridor**, the **Old City / King Street / Queen Charlotte Street corridor**, and the **Wesley Way / Church Road corridor** in east Bristol. The policy question on those routes is not simply whether to promote cycling, but whether after-dark junction design, route continuity, visibility and conflict points are suppressing use.

Finally, future monitoring should be aligned with both the identification strategy used here and Bristol's existing scheme-monitoring practice. Bristol already publishes monitoring for the [East Bristol Liveable Neighbourhood](https://www.bristol.gov.uk/ask/projects/east-bristol-liveable-neighbourhood/monitoring-the-liveable-neighbourhood-trial), reporting weekday increases of **22% in cycling**, **7% in walking**, and **60% in use of the Wesley Way cycle route**. The present report suggests one precise extension to that approach: future corridor and neighbourhood schemes should monitor outcomes specifically in the mixed hours where the same clock time shifts between daylight and darkness, because those are the periods where the strongest pedestrian penalties and the clearest cyclist heterogeneity appear.
