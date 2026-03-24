# MDM Consolidate Error Handling + General Plan
*24 March 2026*

---

## Agenda
Error consolidation approach, GLM integration, clustering methodology, and presentation structure planning.

---

## Key Decisions

1. **Sensor removal threshold** — A 7-day consecutive missing data threshold will be used to remove unreliable sensors.
2. **Internal loop analysis** — The loop testing different removal thresholds against the loss function will be run internally but excluded from the final report to avoid the appearance of forcing results.
3. **GLM as the unique focus** — The GLM must be the project's distinguishing contribution; safety factors are to be included in the analysis.
4. **Data consistency** — All GLM analyses must be rerun on the same consistent dataset. Shavash's GLM notebook needs updating to match.
5. **Clustering by location only** — Clustering by activity level is flawed (it uses the Y variable); the team will cluster solely by location going forward.
6. **Presentation structure** — Lead with the baseline case control method and its limitations, then transition to the GLM as an extension that addresses those limitations.
7. **Slide assignments** confirmed (see actions below); bullet points/draft scripts due by the weekend.
8. **Next meeting** — Monday 30th at 1:00 PM.

---

## Actions

### Karan Dama
- Rerun odds ratio analysis per cluster using the 7-day sensor removal threshold
- Coordinate with Shavash to obtain his GLM data and apply his model to the consistent dataset
- Prepare content for **Slide 3 — Data Cleaning**
- Share updated presentation plan with the team
- Send Gemini meeting notes to Will for cross-reference

### Will
- Create a plan of action document, condense AI meeting notes, and upload both to GitHub
- Prepare content for **Slide 4 — Case Control Method**
- Assist Jayden with Slides 1 & 2

### Thomas Tucker
- Prepare content for **Slide 5 — Results**, including the qualitative transition to the GLM

### Jayden Chew
- Prepare content for **Slides 1 & 2 — Introduction & Motivation/Application** (with support from Will)

### All
- Complete assigned slide bullet points/draft scripts by the **weekend**
- Regroup **Monday 30th at 1:00 PM** to review progress on the first 5–6 slides
