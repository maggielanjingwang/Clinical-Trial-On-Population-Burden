# Plan: Clinical Trial Alignment Platform

## Context

This project builds a data monitoring and visualization platform that evaluates whether cardiovascular clinical research attention aligns with population-level cardiometabolic disease burden in the U.S. Two data sources are integrated: IHME GBD 2023 (population burden) and ClinicalTrials.gov (research attention). The core output is a 4-module interactive React dashboard plus academic writing deliverables.

**Current state:**
- Project spec complete: `project_overview.md`
- IHME data ready: `IHME-GBD_2023_DATA-8217dd7a-1/IHME-GBD_2023_DATA-8217dd7a-1.xlsx` (sheet: "Cardiovascular diseases"), 1.3 MB
- CTG data ready: `ctg-studies-cvd.csv`, ~3,182 rows (pre-filter; ~850 after applying inclusion criteria)
- No code exists yet

**Key data note:** The CTG file's column is named `Conditions` (not `Disease` as in the spec). All other columns match.

---

## Build Order

1. **Python preprocessing pipeline** → outputs `processed_data.json`
2. **React single-file dashboard** → embeds `processed_data.json`
3. **Academic writing outputs** (deferred)

---

## Phase 1 — Python Data Processing Pipeline

**File:** `process_data.py`
**Dependencies:** `pandas`, `openpyxl`, `scipy`
**Output:** `processed_data.json`

### Step 1: Read IHME GBD XLSX

```
pd.read_excel("IHME-GBD_2023_DATA-8217dd7a-1/IHME-GBD_2023_DATA-8217dd7a-1.xlsx",
              sheet_name="Cardiovascular diseases")
```

**Filters applied:**
- `measure_name == "Deaths"`
- `sex_name == "Both"`
- `age_name == "All ages"`
- `cause_name == "Cardiovascular diseases"`
- `metric_name == "Number"`

**Aggregations:**
- `gbd_summary`: group by `rei_name` → sum `death_val`, compute `burden_share`
- `gbd_by_state`: group by `location_name` + `rei_name` → sum `death_val` (for choropleth)
- `gbd_by_year`: group by `year` + `rei_name` → sum `death_val`

### Step 2: Read & Filter Clinical Trials

**File:** `ctg-studies-cvd.csv`

**Inclusion filters:**
| Column | Criteria |
|--------|----------|
| `Study Status` | `== "COMPLETED"` |
| `Study Type` | `== "INTERVENTIONAL"` |
| `Age` | contains `"ADULT"` or `"OLDER_ADULT"` |
| `Phases` | in `{EARLY_PHASE1, PHASE1, PHASE2, PHASE3}` |
| `Start Date` | year `>= 2020` |

**Derived fields:**

| Derived | Source | Logic |
|---------|--------|-------|
| `trial_id` | `NCT Number` | direct rename |
| `study_start_year` | `Start Date` | extract year |
| `sponsor_type` | `Funder Type` | `INDUSTRY` → "Industry"; `NIH`, `FED` → "Government/NIH"; else → "Academic/Other" |
| `intervention_type` | `Interventions` | prefix match: `DRUG` → "Pharmacologic"; `BEHAVIORAL` → "Behavioral"; `DEVICE` → "Device"; else → "Lifestyle/Other" |

### Step 3: Risk Factor Keyword Mapping

Source columns (checked in order): `Primary Outcome Measures`, `Secondary Outcome Measures`, `Brief Summary`

A trial may map to **multiple** risk factors (one row per mapping).

| Risk Factor | Keywords (case-insensitive) |
|-------------|----------------------------|
| High systolic blood pressure | systolic blood pressure, SBP, blood pressure, BP, hypertension, HTN, antihypertensive, diastolic, DBP, MAP, mean arterial pressure, mmHg, pulse pressure, RAAS, renin-angiotensin, ACE inhibitor, ACEi, ARB, beta-blocker, calcium channel blocker, CCB, diuretic, resistant hypertension |
| High LDL cholesterol | LDL, LDL-C, low-density lipoprotein, cholesterol, TC, total cholesterol, statin, dyslipidemia, hyperlipidemia, hypercholesterolemia, lipid, lipid-lowering, triglyceride, TG, PCSK9, HDL, non-HDL, apolipoprotein, ApoB, ApoA, lipoprotein, atorvastatin, rosuvastatin, ezetimibe, evolocumab, alirocumab |
| High fasting plasma glucose | HbA1c, A1C, hemoglobin A1c, glycated hemoglobin, fasting glucose, FPG, blood glucose, BG, glycemia, diabetes, T2DM, type 2 diabetes, DM, diabetes mellitus, prediabetes, insulin resistance, IR, HOMA-IR, OGTT, oral glucose tolerance, postprandial glucose, hyperglycemia, glucagon, GLP-1, SGLT2, metformin, insulin sensitivity |
| High body-mass index | BMI, body mass index, weight loss, obesity, obese, WC, waist circumference, body weight, adiposity, overweight, fat mass, lean mass, body fat, adipose, abdominal obesity, central obesity, visceral fat, bariatric, weight reduction, weight management, caloric restriction |
| Metabolic risks | metabolic syndrome, MetS, metabolic risk, insulin, adipokine, inflammation, CRP, C-reactive protein, hsCRP, high-sensitivity CRP, MACE, major adverse cardiovascular events, ASCVD, atherosclerosis, atherosclerotic, cardiovascular risk, cardiovascular risk score, Framingham, cardiometabolic, oxidative stress, endothelial function, vascular inflammation |
| Kidney dysfunction | eGFR, estimated glomerular filtration rate, GFR, creatinine, serum creatinine, kidney function, renal function, proteinuria, albuminuria, microalbuminuria, macroalbuminuria, UACR, urine albumin-creatinine ratio, CKD, chronic kidney disease, nephropathy, diabetic nephropathy, AKI, acute kidney injury, ESRD, end-stage renal disease, dialysis, renal insufficiency |

### Step 4: Compute Analytical Variables

```python
# Per risk factor (latest year or all-years aggregate)
burden_share    = death_val / sum(death_val across all risk factors)
trial_share     = trial_count / sum(trial_count across all risk factors)
alignment_score = trial_share / burden_share
priority_gap    = burden_share - trial_share
```

### Step 4b: Correlation Analysis

Tests whether clinical trial research intensity is proportional to disease burden.

```python
from scipy.stats import spearmanr

rho, p_value = spearmanr(alignment_df['trial_count'], alignment_df['death_val'])
# Output: spearman_rho, p_value, and plain-language interpretation
```

| rho range | Interpretation |
|-----------|---------------|
| ≥ 0.8 | Strong alignment between research and burden |
| 0.5–0.8 | Moderate alignment |
| < 0.5 | Weak alignment — research does not track burden |

Exported in JSON as:
```json
"correlation": {
  "spearman_rho": 0.xx,
  "p_value": 0.xx,
  "n": 6,
  "interpretation": "..."
}
```

### Step 5: Export JSON

**Output file:** `processed_data.json`

```json
{
  "gbd_summary":           [...],   // rei_name, death_val, burden_share
  "gbd_by_state":          [...],   // location_name, rei_name, death_val
  "gbd_by_year":           [...],   // year, rei_name, death_val
  "trials_by_risk_factor": [...],   // risk_factor, trial_count, trial_share
  "trials_by_phase":       [...],   // risk_factor, phase, count
  "trials_by_sponsor":     [...],   // risk_factor, sponsor_type, count
  "trials_by_year":        [...],   // year, risk_factor, count
  "alignment":             [...],   // risk_factor, burden_share, trial_share, alignment_score, priority_gap
  "correlation":           {...},   // spearman_rho, p_value, n, interpretation
  "sankey_nodes":          [...],
  "sankey_links":          [...]    // trial_count -> risk_factor -> death_val edges
}
```

---

## Phase 2 — React Single-File Dashboard

**File:** `dashboard.html`
**CDN libs:** React, ReactDOM, Recharts, D3.js, Tailwind CSS
**Data:** `processed_data.json` embedded as a `const DATA = {...}` block at top of script

### Components

| Component | Visualization | Library |
|-----------|--------------|---------|
| `<RiskLandscape />` | Bar chart (burden by risk factor) + U.S. choropleth by state | Recharts + D3 |
| `<TrialPipeline />` | Stacked bar chart: trials × phase per risk factor | Recharts |
| `<RiskFlowSankey />` | Sankey: trial_count → risk_factor → death_val | D3 Sankey |
| `<AlignmentScatter />` | Scatter plot with 45° reference line | Recharts |

### Global Interactivity

- **Year filter** (slider/dropdown) — drives all 4 modules
- **Risk factor toggles** (checkbox group) — show/hide individual factors
- **Hover tooltips** — all chart elements expose underlying values
- **Click-to-drill** on risk factor — filters Pipeline and Sankey to selected factor

---

## Change Log

### Dashboard (`dashboard.html` / `generate_dashboard.py`)

#### Bug Fixes
- **Blank page on load** — Added `prop-types` CDN script before Recharts. Recharts UMD requires `window.PropTypes` to be defined; without it the bundle fails silently and `window.Recharts` is never set, causing a `ReferenceError` that prevented React from mounting.
- **Scatter plot (Alignment Analysis) — Overstudied/Understudied regions inverted** — X-axis = Burden Share, Y-axis = Trial Share. Points *above* the 45° line have Trial Share > Burden Share = Overstudied (upper-left); points *below* = Understudied (lower-right). Three things were all swapped and corrected:
  - Background polygon fills: upper-left → blue (`#eff6ff`), lower-right → red (`#fef2f2`)
  - Region text labels repositioned to correct triangles
  - Fill colors on labels corrected (blue for Overstudied, red for Understudied)
- **Risk Factor Flow — "Total CVD Burden" / "CVD Burden" label clipped** — `RIGHT_MARGIN` was set to 20px, causing the label text to overflow the SVG width. Increased to 72px so the node and its label fit within the drawable area.

#### Visual Improvements
- **Risk Factor Flow redesigned as true Sankey diagram** — Replaced thin stroked lines with filled cubic-bezier ribbon bands:
  - Col 1 → Col 2 (Trial Count → GBD Deaths): filled band colored by alignment score (blue/green/orange); score label centered inside band
  - Col 2 → Col 3 (GBD Deaths → CVD Burden): filled bands in each risk factor's color, fanning into and stacking on the CVD Burden node
  - Node heights proportional to magnitude; value labels below each node
  - "CVD Burden" label placed above the node (centered) instead of to its right
- **Navigation label** — "Research Pipeline" renamed to "Clinical Trial Research Pipeline"

---

## Skills & Tools Relevant to This Project

| Tool/Skill | Use |
|------------|-----|
| **xlsx skill** | If XLSX reading needs troubleshooting or sheet-level inspection before Python pipeline |
| **clinical-trials MCP** | `search_trials`, `analyze_endpoints` — validate or supplement ClinicalTrials.gov dataset; also useful for cross-checking keyword mappings |
| **context7 MCP** | Fetch Recharts / D3 docs for correct API usage in dashboard |

---

## Critical Files

| File | Role |
|------|------|
| `project_overview.md` | Full spec — source of truth |
| `IHME-GBD_2023_DATA-8217dd7a-1/IHME-GBD_2023_DATA-8217dd7a-1.xlsx` | Population burden input |
| `ctg-studies-cvd.csv` | Clinical trial input (col: `Conditions`, not `Disease`) |
| `process_data.py` | **To create** — preprocessing pipeline |
| `processed_data.json` | **To create** — pipeline output / dashboard input |
| `dashboard.html` | **To create** — React visualization platform |

---

## Verification

1. Run `python process_data.py` — should produce `processed_data.json` with no errors
2. Inspect JSON: confirm ~850 trials after filtering; all 6 risk factors present; `alignment_score` and `priority_gap` populated
3. Open `dashboard.html` in browser — all 4 modules render with data
4. Test year filter and risk factor toggles — all charts update correctly
5. Test hover tooltips and click-to-drill on risk factor names
6. Cross-check: `sum(burden_share)` across risk factors ≈ 1.0; same for `trial_share`
