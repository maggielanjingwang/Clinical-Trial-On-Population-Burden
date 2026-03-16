# Clinical Trial Research Alignment with Population Cardiometabolic Risk Burden

## Project Overview

This project develops a **data monitoring and visualization platform** that evaluates whether clinical research activity aligns with **population-level cardiometabolic risk burden** in the United States.

The platform integrates two major data sources:

- **Population-level disease burden data** from the *Institute for Health Metrics and Evaluation (IHME) Global Burden of Disease (GBD)* dataset
  - Source: https://vizhub.healthdata.org/gbd-results/
  - File: `IHME-GBD_2023_DATA-8217dd7a-1.xlsx` in "/Users/maggie/Desktop/UW/Winter 2026/public_health/IHME-GBD_2023_DATA-8217dd7a-1/" folder · Sheet: *Cardiovascular diseases*

- **Clinical trial registry data** from *ClinicalTrials.gov*
  - File: `ctg-studies-cvd.csv`

The primary goal is to assess whether **clinical research investments focus on the cardiovascular risk factors responsible for the greatest population disease burden**.

The core comparison framework is:

> **Population Risk Burden vs. Clinical Trial Research Attention**

The platform calculates an **alignment score** to identify **understudied, balanced, or overstudied research domains**.

---

## Data Sources

### Population-Level Data

**Source:** IHME Global Burden of Disease (GBD)

**Outcome Measure:** Deaths attributable to cardiovascular disease risk factors

**Disease Category:** Cardiovascular diseases

**Risk Factors Included:**

- High systolic blood pressure
- High LDL cholesterol
- High fasting plasma glucose
- High body-mass index
- Metabolic risks
- Kidney dysfunction

**GBD Dataset Variables:**

| Variable | Type | Role | Description |
|----------|------|------|-------------|
| `population_group_id` | integer | display | Numeric ID for population group |
| `population_group_name` | string | display | Population group label |
| `measure_id` | integer | filter | Numeric ID for outcome measure |
| `measure_name` | string | filter | Outcome measure label — filter: *Deaths* |
| `location_id` | integer | display | Numeric ID for U.S. state |
| `location_name` | string | **analytical** | U.S. state name — used in geographic module |
| `sex_id` | integer | filter | Numeric ID for sex |
| `sex_name` | string | filter | Sex category — filter: *Both* |
| `age_id` | integer | filter | Numeric ID for age group |
| `age_name` | string | filter | Age group label — filter: *All Ages* |
| `cause_id` | integer | filter | Numeric ID for disease category |
| `cause_name` | string | filter | Disease category — filter: *Cardiovascular diseases* |
| `rei_id` | integer | display | Numeric ID for risk factor |
| `rei_name` | string | **analytical** | Risk factor label — maps to platform risk factor taxonomy |
| `metric_id` | integer | filter | Numeric ID for metric type |
| `metric_name` | string | filter | Metric type — filter: *Number* (raw deaths) |
| `year` | integer | **analytical** | Observation year — used in time trend module |
| `death_val` | float | **analytical** | Point estimate of risk-attributable deaths — primary burden measure |
| `death_upper` | float | analytical | Upper bound of uncertainty interval |
| `death_lower` | float | analytical | Lower bound of uncertainty interval |

---

### Clinical Trial Data

**Source:** ClinicalTrials.gov

**Search Criteria:**

- Condition: Cardiovascular Diseases
- Study Type: Interventional Studies
- Status: Completed
- Population: Adults (18–64) · Older adults (65+)
- Phase: Early Phase 1 · Phase 1 · Phase 2 · Phase 3
- Study start date: on or after January 1, 2020

**Current dataset size:** 850 clinical trials

**ClinicalTrials.gov Dataset Variables:**

| Variable | Type | Role | Description |
|----------|------|------|-------------|
| `NCT Number` | string | ID | Unique trial identifier (e.g., NCT04123456) |
| `Study Title` | string | display | Full trial title |
| `Study URL` | string | display | Direct link to ClinicalTrials.gov record |
| `Acronym` | string | display | Trial acronym if assigned |
| `Study Status` | categorical | filter | Filter: *Completed* |
| `Brief Summary` | string | NLP / mapping | Secondary risk factor keyword source |
| `Study Results` | boolean | filter | Results posted indicator |
| `Disease` | string | filter | Filter: *Cardiovascular Diseases* |
| `Interventions` | string | analytical | Maps to `intervention_type` |
| `Primary Outcome Measures` | string | **NLP / mapping** | Primary keyword mapping source |
| `Secondary Outcome Measures` | string | NLP / mapping | Supplementary keyword mapping |
| `Other Outcome Measures` | string | analytical | Additional endpoints |
| `Sponsor` | string | analytical | Maps to `sponsor_type` |
| `Collaborators` | string | analytical | Co-sponsors and partners |
| `Sex` | categorical | filter | Participant sex eligibility |
| `Age` | categorical | filter | Filter: *Adults (18–64)*, *Older Adults (65+)* |
| `Phases` | categorical | analytical | Filter: *Early Phase 1 – Phase 3* |
| `Enrollment` | integer | analytical | Number of participants enrolled |
| `Funder Type` | categorical | analytical | Funding source category |
| `Study Type` | categorical | filter | Filter: *Interventional* |
| `Study Design` | string | analytical | Allocation, masking, and intervention model details |
| `Other IDs` | string | display | Secondary identifiers |
| `Start Date` | date | analytical | Filter: *≥ Jan 1, 2020* · maps to `study_start_year` |
| `Primary Completion Date` | date | analytical | Primary data collection end date |
| `Completion Date` | date | analytical | Full study completion date |
| `First Posted` | date | display | Date first registered on ClinicalTrials.gov |
| `Results First Posted` | date | display | Date results first published |
| `Last Update Posted` | date | display | Most recent registry update |
| `Locations` | string | analytical | Trial sites — enables geographic analysis |
| `Study Documents` | string | display | Links to protocols, ICFs, or results documents |

---
#### Clinical Trial Dataset Preprocessing

#### Risk Factor Mapping

Clinical trials are mapped to population risk factors using outcome keywords. A single trial may correspond to **multiple risk factors**, leading to overlap, but its okay to overlap, just make sure we can distibgush them.

| Clinical Trial Outcome Keyword | Mapped Risk Factor |
|-------------------------------|-------------------|
| LDL reduction | High LDL cholesterol |
| Blood pressure reduction | High systolic blood pressure |
| HbA1c reduction | High fasting plasma glucose |
| Weight loss | High body-mass index |

Make sure we can identify all the risk factor by keywords as much as possible, so you need to list possible keywords to capture the risk factor by NCTID in `Primary Outcome Measures`, `Secondary Outcome Measures`, `Brief Summary` 

---

#### Derived Variables from Clinical Trial Dataset

These fields are **computed from raw columns** during data processing:

| Derived Variable | Source Column(s) | Logic |
|-----------------|-----------------|-------|
| `trial_id` | `NCT Number` | Direct rename |
| `study_start_year` | `Start Date` | Extract year |
| `sponsor_type` | `Sponsor`, `Funder Type` | Classify: industry / other / government = nih |
| `risk_factor` | `Primary Outcome Measures`, `Secondary Outcome Measures`, `Brief Summary` | Keyword mapping to GBD risk factor taxonomy |

#### Field Role Legend

| Role | Meaning |
|------|---------|
| **ID** | Unique row identifier |
| **filter** | Applied during data ingestion to scope the dataset |
| **analytical** | Used in platform calculations, visualizations, or mapping |
| **Keyword mapping** | Free-text fields parsed for risk factor keyword assignment (we don't use NLP or LLM) |
| display | Retained for UI drill-down or linking; not computed |

---

## Core Analytical Framework

### Population Burden

```
burden_share = death_val / sum(death_val across all risk factors)
```

| Risk Factor | Attributable Deaths | Burden Share |
|-------------|--------------------:|-------------:|

### Clinical Research Attention

```
trial_share = trial_count / sum(trial_count across all risk factors)
```

| Risk Factor | Trial Count | Trial Share |
|-------------|------------:|------------:|

### Alignment Score

```
alignment_score = trial_share / burden_share
```

| Alignment Score | Interpretation |
|----------------|---------------|
| < 1 | Understudied |
| = 1 | Balanced |
| > 1 | Overstudied |

### Research Priority Gap

```
priority_gap = burden_share − trial_share
```

| Gap Value | Meaning |
|----------|---------|
| Positive | Understudied risk factor |
| Negative | Overstudied risk factor |

---

### Correlation analysis

## Clinical Trial Analytics

**Risk Factors Included:**

- High systolic blood pressure
- High LDL cholesterol
- High fasting plasma glucose
- High body-mass index
- Metabolic risks
- Kidney dysfunction


### Trial Count by Risk Factor
```
count(trial) by risk_factor
```
Measures **research attention** toward each risk domain.

### Trial Phase Distribution
```
count(phase) by risk_factor
```
Describes the **clinical development pipeline**.

| Risk Factor | Early Phase 1 | Phase 1 | Phase 2 | Phase 3 |
|-------------|:-------------:|:-------:|:-------:|:-------:|

### Intervention Type Distribution
```
count(intervention_type) by risk_factor
```
Intervention types: pharmacologic · behavioral · device · lifestyle

### Sponsor Distribution
```
count(sponsor_type) by risk_factor
```
Sponsor types: Industry · Academic · Government / NIH

### Time Trend Analysis
```
count(trials) by risk_factor by year
```
Reveals **changes in research focus over time**.

---

## Platform Dashboard

### Module 1 — Population Risk Landscape

Displays the **population burden of cardiovascular risk factors**.

| Visualization | Data | Key Variables |
|--------------|------|---------------|
| Bar chart | GBD | `rei_name`, `death_val` |
| U.S. choropleth map | GBD | `location_name`, `death_val` |

Identifies **high-burden risk factors** and **high-risk geographic regions** at the state level.

---

### Module 2 — Clinical Research Pipeline

Displays clinical trial distribution across risk factors.

| Visualization | Data | Key Variables |
|--------------|------|---------------|
| Stacked bar chart | ClinicalTrials.gov | `risk_factor`, `trial_count`, `phase` |

---

### Module 3 — Risk Factor Flow Visualization

Shows the relationship between clinical trials, risk factors, and population burden.

| Visualization | Data | Key Variables |
|--------------|------|---------------|
| Sankey diagram | GBD + ClinicalTrials.gov | `trial_count` → `risk_factor` → `death_val` |

---

### Module 4 — Alignment Analysis *(Core Analysis)*

| Visualization | X-axis | Y-axis | Reference |
|--------------|--------|--------|-----------|
| Scatter plot | `burden_share` | `trial_share` | 45° line = perfect alignment |

- **Below the line** → understudied
- **Above the line** → overstudied

---

## Output Format Specifications

### Output 1 — Interactive Visualization Platform

**Delivery format:** React/HTML artifact rendered in Claude

**Architecture:** Single-file React component with all logic, state, and styling self-contained. No external backend or API calls. All data embedded as static JSON within the artifact.

**Library dependencies** (CDN-loaded within artifact):

| Library | Purpose |
|---------|---------|
| `React` + `ReactDOM` | Component rendering and state management |
| `Recharts` | Bar charts, scatter plots, stacked bar charts |
| `D3.js` | Sankey diagram, choropleth U.S. map |
| `Tailwind CSS` | Layout and styling |

**Platform Module Components:**

| Module | Visualization Type | React Component | Key Props |
|--------|-------------------|-----------------|-----------|
| Population Risk Landscape | Bar chart + U.S. choropleth | `<RiskLandscape />` | `gbd_data`, `selected_year` |
| Clinical Research Pipeline | Stacked bar chart | `<TrialPipeline />` | `trial_data`, `group_by: phase` |
| Risk Factor Flow | Sankey diagram | `<RiskFlowSankey />` | `nodes`, `links` |
| Alignment Analysis | Scatter plot + 45° reference line | `<AlignmentScatter />` | `burden_share`, `trial_share`, `risk_factor` |

**Interactivity requirements:**

- Year filter (slider or dropdown) affecting all modules
- Risk factor toggle (checkbox group) for filtering displayed factors
- Hover tooltips on all chart elements showing underlying values
- Click-to-drill on risk factor → filters pipeline and flow modules

---

### Output 2 — Academic Writing Documentation

#### 2a. Technical Report / White Paper

**Structure:**

1. Introduction — cardiovascular disease burden and research gap rationale
2. Data Sources — GBD and ClinicalTrials.gov dataset descriptions
3. Methods — risk factor mapping, alignment score, priority gap calculation
4. Results — per-module findings with embedded visualizations
5. Discussion — policy implications of understudied vs. overstudied domains
6. Appendix — variable codebook, keyword mapping rules

**Style:** Professional, accessible. Terms defined on first use. Tables and figures numbered and captioned.

---

#### 2b. Methods Section (Journal Paper)

**Structure:**

1. **Study Design** — cross-sectional alignment analysis
2. **Data Sources** — GBD (outcome: risk-attributable cardiovascular deaths) and ClinicalTrials.gov (n = 850 interventional trials, 2020–present)
3. **Risk Factor Classification** — six GBD-derived categories; keyword mapping from `Primary Outcome Measures` and `Secondary Outcome Measures` fields
4. **Analytical Variables** — `burden_share`, `trial_share`, `alignment_score`, `priority_gap` (formulas defined)
5. **Statistical Approach** — descriptive; no inferential testing; alignment score thresholds defined a priori
6. **Visualization** — four platform modules described with data inputs

**Style:** Passive voice, past tense, precise operational definitions. Suitable for a public health informatics or epidemiology journal.

---

#### 2c. Abstract

**Structure:** Structured abstract —
`Background` · `Objective` · `Data Sources` · `Methods` · `Results` · `Conclusions`

**Target length:** 250–300 words

**Style:** Dense, no jargon without definition, results framed around alignment score findings.

---

## Expected Insights

This platform enables evaluation of:

- Whether clinical trials target the **highest-burden cardiovascular risk factors**
- Which risk factors are **underrepresented in research**
- How research priorities evolve over time
- Whether research investment aligns with **population health priorities**

The platform serves as a **public health informatics monitoring tool** to support **research prioritization and health policy decision-making**.

---

*This document serves three purposes: a React build spec for the platform artifact, a methods and reporting template for academic writing, and a data contract for processing the raw datasets.*