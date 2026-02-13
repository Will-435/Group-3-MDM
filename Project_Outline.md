# Project notes, courtesy of Nicolai

## 1. Project Aim & Objectives
* Determine if walking counts change in the dark versus light, whilst keeping other factors steady.
* Focus only on Bristol data to measure the specific effect of darkness.
* Use Daylight Saving Time to compare light and dark conditions at the same time of day.
* Clearly define what counts as "light" or "dark" (e.g. sunset times) and justify the choice.

## 2. Practical Implications
* Guide decisions on street lighting investment.
* Improve urban planning and public safety perception.
* Support schemes to encourage active travel behaviour.
* Reveal if lighting stops people from walking.

## 3. Benchmarking
* Start by replicating the method from the reference paper.
* Set a solid baseline to compare against before trying new models.

## 4. Using AI
* AI may be used for research, ideas, and code 'skeleton-ing'.
* **Strict Constraints:**
    * Do not rely generated code.
    * Verify references.
    * Implementation and the creation of figures should be done by us.

## 5. Video
* The presentation must be interpretable without reading the full report (but we can refer to the report)
* **Content:**
    * High-level overview of the research question and model.
    * Focus on visualisation and key findings.
    * Avoid a lot of mathematical detail.
* Introduce relevance in the motivation and revisit it in the conclusion.

## 6. Actions
### Modelling Strategy
* **Time-Series Models:**
    * GLM Poisson is a natural start for count data but we need to handle many zero counts (at night) and overdispersion.
    * Account for temporal dependence and are a valid modelling family to research.
    * ML also presents an alternative approach that could work
* **Selection:** There is no single "correct" model; the choice must be justified based on the objective and diagnostic performance.

###  To do 
* **Research:** Decie on either Stats or ML.
* **Definition:** Agree definition of light and dark.
* **Replication:** Replicate the baseline method from the reference paper.
* **Timeline:** Aim to strat on Monday
