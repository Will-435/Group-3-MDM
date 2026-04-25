# Group 3 MDM Project Plan

---

## Project overview

The question is simple: does darkness reduce walking and cycling in Bristol once weather, time of day, calendar, and fixed sensor differences are stripped out? Nicolai gave us four anchors:

1. Isolate the effect of darkness with everything else held steady.
2. Use Daylight Saving and fixed clock hours so light and dark are compared at the same time of day.
3. Replicate the reference paper before doing anything new.
4. Justify the model on diagnostics, not on assumption.

The deliverable is a 10-minute recorded presentation with a short technical note, pitched as a consultancy answer to a policy audience.

---

## Phase 1, reserach and understanding contextual features

### 1.1 Darkness and footfall in similar cities

Build a short evidence base on how darkness affects walking and cycling in cities like Bristol, before we touch the data. This gives us a sense of plausible effect sizes and feeds the policy section later.

Tasks:

- Find UK or European studies on lighting, daylight saving, and active travel.
- Pull at least one comparable academic paper.
- For each finding, note the effect size, geography, and study design on a single page.
- Flag any paper using case control or quasi-experimental designs, since those line up with the replication.

> Note: agreed to replicate the breifing reference paper as the baseline first. Nicolai was firm on this.

### 1.2 Feature-level effects on footfall

Each contextual feature gets one person, one process: gather, clean, plot, overlay with footfall, push to git, present at the next meeting.

Topics:

- CCTV density (Shavarsh)
- Businesses and amenities (Tom)
- Streetlights (Karan)
- Population density (Jayden)
- Crime and safety sentiment (Will)
- Weather, including temp, wind, rain (Jayden)

> 20 Feb update: features split out one per person. Agreed standard process so the outputs stay comparable.

### 1.3 Safety sentiment data for Bristol

Pull a Bristol safety sentiment dataset together. This is the moderator most likely to get pushed back on, so it needs to be defensible.

Tasks:

- Get the most recent ward-level after-dark safety survey.
- Map ward percentages onto the sensor list.
- Z-score it so it can sit in the GLM as a moderator.
- Write down the limits of using a static, ward-level value as a sensor-level proxy.

> Note: safety write-up done as Bayesian shrinkage to handle small ward samples. Jayden owns it (agreed 2 March).

---

## Phase 2, data engineering and cleaning

A clean hourly panel underpins everything later. The pipeline lives in `new_branch/notebooks/` as `01` to `10`.

Tasks:

- Build an hourly panel of pedestrian, cyclist, and car counts per sensor.
- Attach solar altitude and derive a binary `Dark` flag tracking local sunrise and sunset.
- Merge in hourly temp, wind, and rain.
- Merge sensor-level CCTV (300 m), business density (300 m), streetlight density (50 m), and ward-level safety percentage.
- Drop any sensor with seven or more consecutive days of missing data, leaving 37 sensors.
- Sweep alternative removal thresholds against a loss function internally, but keep this out of the final report so the choice does not look forced.
- Build one-hour and twenty-four-hour lags before any hour filtering, so the lags keep their meaning.

> 24 March: agreed the 7-day missing data threshhold after testing alternatives. Karan owns the cleaning slide and is adding a small bar chart to show the impact of removing the outlier sensors.

---

## Phase 3, replicating the odds ratio baseline

The first analytical deliverable is a faithful replication of the reference paper applied to Bristol. Nicolai asked for this explicitly.

Tasks:

- Restrict the sample to the mixed clock hours that switch between daylight and darkness over the year (`05, 06, 17, 18, 19, 20`).
- For each sensor and hour-of-day, pair darkness and daylight observations and compute the odds of a low-activity event.
- Pool sensor odds ratios using the Mantel-Haenszel estimator.
- Produce three pooled summaries: overall by mode, by cluster and mode, and by case-hour and mode.
- Cross-check the pooled overall figure against the Oscar reference paper.

> 30 March: agreed to benchmark the case-control results against the Oscar report, pending Oscar's confirmation that this is academiclly fine.

Output tables are in `new_branch/outputs/` as `case_control_*.csv` and `mh_weighted_or_*.csv`.

---

## Phase 4, building the Negative Binomial GLM

Once the baseline is settled, the GLM ladder is the project's distinguishing contribution. Nicolai was clear that the GLM has to do real analytical work the case control cannot, otherwise its inclusion is not justified.

Tasks:

- Fit Model 1 as a Negative Binomial GLM with log link: `Dark`, lags, hour, day-of-week, month, weather, sensor fixed effects.
- Cluster standard errors by sensor.
- Fit Models 2 to 5 by interacting `Dark` with `Cluster`, `cctv_z`, `safety_z`, `businesses_z`, and `streetlights_z`.
- Keep moderators only as interactions with `Dark`, since their main effects are absorbed by the sensor fixed effects.
- Restrict the sample to the same mixed hours as the case control method so the two stay comparable.
- Report coefficients as per cent changes via $100(e^\beta - 1)$.
- Run an evaluation pass: Pearson dispersion at each rung, AIC across the ladder, Poisson vs Negative Binomial likelihood ratio on Model 1.

> 3 Apr: GLM correctly restricted to the case-control hours. Excluding control-only hours like 03:00 stops them skewing the darkness coefficient and keeps it aligned with the OR method.
> Heads up: pedestrian drop is around 33 per cent, cyclist drop only 4 to 5 per cent overall. The cyclist story has to be split by cluster, otherwise the average buries it.

Working notebooks live in `new_branch/models/`. The consolidated coefficient table is `new_branch/models/darkness_glm_model_comparison.csv`.

---

## Phase 5, clustering decision

How sensors are grouped affects every downstream interpretation, so this was treated as a methodological decision rather than a routine step.

Tasks:

- Try clustering on activity level, then drop it because it uses the outcome variable.
- Cluster by location only: `Central`, `East`, `Outlier`, with small `North` and `South` sets later excluded for sample size reasons.
- Document the rationale for excluding `North` and `South` and add a slide on it.
- Re-run every model on the agreed cleaned dataset so results match across notebooks.

> 24 March: agreed location-only clustering. Activity-level clustering had to go because it uses the Y variable, which is circular.
> 30 March: dropped North and South, not enough sensors. Need a justification slide in the deck.

---

## Phase 6, interpreting results

This is where the analysis becomes a policy story. The PoAs from the second half of the project are clear that pedestrians and cyclists need separate framings.

Tasks:

- Pedestrians: report the headline pooled effect of about minus 33 per cent at p far below 0.001, broadly uniform across clusters.
- Cyclists: report the near-null pooled effect, then expose the heterogeneity. Roughly minus 20 per cent in `Central`, near zero in `East`, and a positive effect in `Outlier`.
- Probe the safety anomaly: lower perceived safety areas saw an *increase* in cycling after dark.
- Look at the time-of-day pattern: the largest pedestrian penalty falls at 05:00 and 06:00, while the evening commute window is barely affected.
- Rank sensors by adjusted darkness penalty for the policy section.

> 3 Apr: the safety anomaly is real, lowest-perceived-safety areas saw an increase in cycling after dark. Will doubts the reliability of qualitative sentiment data because of individual benchmarking, but agrees we should still show it with limits attached.
> 6 Apr: darkness has the biggest effect at 06:00 (leisure travel) and almost none during 17:00 to 19:00 (commuting). Worth pulling out as a finding.

---

## Phase 7, scrutinising weaknesses with Nicolai

Nicolai is treated as a recurring quality gate, not a one-off review. We come back to him at every methodological or framing step.

Recurring checks:

- Confirm the binary light or dark definition and the hour restriction.
- Validate the OR replication against the reference paper.
- Check the GLM is doing analytical work the case control cannot.
- Stress-test the clustering decision and the sensor exclusion threshold.
- Challenge the ward-level safety variable and the weak streetlight interaction before they reach the policy framing.
- Pressure-test the cyclist heterogeneity by cluster and the safety interaction.
- Make sure the GLM's linear assumptions and the flat gradients are honestly disclosed in the limitations.

> Standing note from Week 1: AI may be used for research, ideas, and code skeletoning. Implementation and figures are us. Verify references.

---

## Phase 8, policy case

The brief is consultancy-style, so the conclusions have to land as defensible recommendations, not a stats lecture.

Tasks:

- Draft the policy recommendations first, then frame the GLM results around them. Avoids restating numbers in two places.
- Anchor recommendations to named Bristol and West of England policies (Bristol Transport Strategy, Safe Systems road safety plan, the West of England LCWIP, the East Bristol Liveable Neighbourhood, Victoria Street improvements, King Street pedestrianisation, the LED street-lighting upgrade programme).
- Pedestrian recommendations: broad, corridor-led, since the effect is widespread.
- Cyclist recommendations: route-specific, audit-led, since the effect is heterogeneous.
- State plainly that the streetlight interaction is not direct evidence for lighting upgrades, but it is consistent with the council's existing programme.
- Give the council two options to choose between, not one inflexible ask.

> 6 Apr: adaptive LEDs sounded nice but we have no luminosity data, so the argument is weak. Streetlight density is more defendable.
> Targeting agreed 6 Apr: focus on the 05:00 to 06:00 drop-off, find low-light areas, push upgrades there rather than blanketing the city.

---

## Phase 9, building the presentation

The presentation is the primary deliverable. The technical note is the appendix. Structure is policy-led, with data and methods supporting the policy rather than the other way round.

Tasks:

- Open with motivation and the research question.
- Introduce the data and what the sensors physically look like, then point the audience at the technical note for reproducibility.
- Cover cleaning quickly, with the bar chart of the outlier impact.
- Explain the case control method, define an odds ratio in plain terms, give one comparison slide against the reference paper.
- Transition to the GLM as an extension that fixes the case control's weaknesses, not as a separate exercise.
- Present pedestrians and cyclists separately, since the stories diverge.
- Cover real-world implications and the two policy options.
- Close with limitations, split into statistical vs physical.
- Minimum-text slide design, charts and maps doing the work.

> 30 March: pitching as consultants, not students. Frame the work as a self-inspired investigation driven by the data. Slides keep minimum text and lean on visuals plus dynamic morph transitions.

---

## Phase 10, redrafting the presentation

After the first walkthrough, the redraft is about flow and signposting, not new analysis.

Tasks:

- Trim the opening slides, re-record the first spoken slide.
- Merge limitations and results into one narrative.
- Move implementation content to the back and shorten it.
- Condense the data science section.
- Add citation footers to every slide using external data or method.
- Smooth presenter hand-offs so they do not feel abrupt.
- Fully label every figure, rehearse guiding the audience through them.
- Remove repeated results across slides.

> 16 Apr: first two slides cut, third re-recorded. References go on as small footers per slide, not one list at the end. Implications section too long, needs trimming. Some on-screen content has nobody talking to it, that goes.

---

## Phase 11, building the technical note

Up to five pages of LaTeX in self-contained sections, where the reproducibility detail lives.

Tasks:

- Section on data engineering and the clean 37-sensor sample, including the seven-day rule.
- Section on the case control method, with the Mantel-Haenszel pooling formula and the validation against the reference paper.
- Section on the Negative Binomial GLM, with the full mean equation, the moderator z-scoring, and the clustered standard errors.
- Short model-evaluation paragraph: AIC across the five rungs, dispersion at each rung, Poisson vs Negative Binomial likelihood ratio on Model 1.
- Section on results, mirroring the presentation but with full coefficient tables.
- Section on limitations, split statistical vs physical.
- Link to `new_branch` of the project Git repo, with a short description of each subdirectory.
- Reference the README in that branch as the entry point for the marker.

> Reminder: filename has to be `Group3-DarknessDeterrence-TechNote.pdf`. Anything we link from the report needs to be well commented and the repo needs a clear README.

---

## Phase 12, final redraft and submission

A final pass after the technical note is done, since writing the note tends to surface small inconsistencies in the slides.

Tasks:

- Walk the slides one more time, checking every number on a slide is backed by the technical note.
- Re-record any slide where the script has drifted from the slide content.
- Tidy any cluttered slides flagged in the second review.
- Render the final video with the required filename and resolution.
- Compile the technical note PDF with the required filename.
- Bundle the video and the note into `Group3-DarknessDeterrence-All.zip`.
- Upload via Browse Cloud Storage on Blackboard, with plenty of lead time.
- Email the one-page management report to the unit director and the supervisor within a week of submitting.

> Heads up: Blackboard uploads are slow without Cloud Storage, can take ~20 mins on a normal connection for a 10-min video. Use the Browse Cloud Storage option.

---

## Project flow chart

```mermaid
flowchart TD
    A[Phase 1.1: Evidence on darkness and footfall<br/>in similar cities and countries] --> B[Phase 1.2: Feature evidence notes<br/>crime, businesses, CCTV, streetlights, weather]
    B --> C[Phase 1.3: Bristol safety sentiment data]
    C --> D[Phase 2: Data engineering and cleaning<br/>37-sensor hourly panel]
    D --> E[Phase 3: Replicate odds ratio baseline<br/>Mantel-Haenszel pooled ORs]
    E --> F[Phase 4: Build Negative Binomial GLM ladder<br/>Models 1 to 5]
    D --> G[Phase 5: Clustering decision<br/>Central, East, Outlier, location-only]
    G --> F
    F --> H[Phase 6: Interpret results<br/>pedestrians vs cyclists, time-of-day, sensor ranking]
    H --> I[Phase 8: Policy case<br/>two options anchored to named Bristol policies]
    I --> J[Phase 9: Build presentation<br/>policy-led, charts and maps]
    J --> K[Phase 10: Redraft presentation<br/>flow, signposting, citations]
    K --> L[Phase 11: Build technical note<br/>5 pages, reproducibility detail]
    L --> M[Phase 12: Final redraft and submit<br/>video, tech note, management report]

    N([Phase 7: Recurring supervisor scrutiny with Nicolai]) -.-> A
    N -.-> E
    N -.-> F
    N -.-> G
    N -.-> H
    N -.-> I
    N -.-> J
    N -.-> L

    style A fill:#e8f0e3,stroke:#274b22
    style B fill:#e8f0e3,stroke:#274b22
    style C fill:#e8f0e3,stroke:#274b22
    style D fill:#dde9f0,stroke:#1f3a52
    style E fill:#f0e6d6,stroke:#7a5b22
    style F fill:#f0e6d6,stroke:#7a5b22
    style G fill:#dde9f0,stroke:#1f3a52
    style H fill:#f0d9d9,stroke:#7a2222
    style I fill:#f0d9d9,stroke:#7a2222
    style J fill:#e2dcef,stroke:#3e2a7a
    style K fill:#e2dcef,stroke:#3e2a7a
    style L fill:#e2dcef,stroke:#3e2a7a
    style M fill:#e2dcef,stroke:#3e2a7a
    style N fill:#fff7d6,stroke:#7a6a22