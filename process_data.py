"""
process_data.py
Preprocessing pipeline for the Clinical Trial Alignment Platform.

Inputs:
  - IHME-GBD_2023_DATA-8217dd7a-1/IHME-GBD_2023_DATA-8217dd7a-1.xlsx
  - ctg-studies-cvd.csv

Output:
  - processed_data.json
"""

import json
import re
import pandas as pd
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
# 1. IHME GBD DATA
# ---------------------------------------------------------------------------

gbd_raw = pd.read_excel(
    "IHME-GBD_2023_DATA-8217dd7a-1/IHME-GBD_2023_DATA-8217dd7a-1.xlsx",
    sheet_name=0,  # "Cardiovascular diseases"
)

# Apply inclusion filters
gbd = gbd_raw[
    (gbd_raw["measure_name"] == "Deaths")
    & (gbd_raw["metric_name"] == "Number")
    & (gbd_raw["sex_name"] == "Both")
    & (gbd_raw["age_name"] == "All ages")
    & (gbd_raw["cause_name"] == "Cardiovascular diseases")
].copy()

# --- gbd_summary: national aggregate per risk factor ---
gbd_summary_df = (
    gbd.groupby("rei_name", as_index=False)["death_val"]
    .sum()
    .rename(columns={"rei_name": "risk_factor"})
)
total_deaths = gbd_summary_df["death_val"].sum()
gbd_summary_df["burden_share"] = gbd_summary_df["death_val"] / total_deaths
gbd_summary_df = gbd_summary_df.sort_values("death_val", ascending=False)

# --- gbd_by_state: state-level per risk factor (for choropleth) ---
gbd_by_state_df = (
    gbd.groupby(["location_name", "rei_name"], as_index=False)["death_val"]
    .sum()
    .rename(columns={"rei_name": "risk_factor"})
)

# --- gbd_by_year: year × risk_factor (only 2023 in dataset; kept for extensibility) ---
gbd_by_year_df = (
    gbd.groupby(["year", "rei_name"], as_index=False)["death_val"]
    .sum()
    .rename(columns={"rei_name": "risk_factor"})
)

# ---------------------------------------------------------------------------
# 2. CLINICAL TRIALS DATA
# ---------------------------------------------------------------------------

ctg_raw = pd.read_csv("ctg-studies-cvd.csv")

# --- Inclusion filters ---
# Age: must include ADULT or OLDER_ADULT
ctg = ctg_raw[
    ctg_raw["Age"].str.contains("ADULT|OLDER_ADULT", na=False)
].copy()

# Start Date year >= 2020
ctg["study_start_year"] = pd.to_datetime(ctg["Start Date"], errors="coerce").dt.year
ctg = ctg[ctg["study_start_year"] >= 2020].copy()

# Phases: include any row whose Phases field contains a valid phase
VALID_PHASES = {"EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3"}
def has_valid_phase(phase_str):
    if pd.isna(phase_str):
        return False
    parts = set(phase_str.strip().split("|"))
    return bool(parts & VALID_PHASES)

ctg = ctg[ctg["Phases"].apply(has_valid_phase)].copy()

# Rename trial ID
ctg = ctg.rename(columns={"NCT Number": "trial_id"})

# --- Derived: sponsor_type ---
def classify_sponsor(funder):
    if pd.isna(funder):
        return "Academic/Other"
    funder = str(funder).strip().upper()
    if funder == "INDUSTRY":
        return "Industry"
    if funder in ("NIH", "FED"):
        return "Government/NIH"
    return "Academic/Other"

ctg["sponsor_type"] = ctg["Funder Type"].apply(classify_sponsor)

# --- Derived: intervention_type ---
def classify_intervention(interventions):
    if pd.isna(interventions):
        return "Lifestyle/Other"
    s = str(interventions).upper()
    if "DRUG:" in s or "BIOLOGICAL:" in s:
        return "Pharmacologic"
    if "BEHAVIORAL:" in s:
        return "Behavioral"
    if "DEVICE:" in s:
        return "Device"
    return "Lifestyle/Other"

ctg["intervention_type"] = ctg["Interventions"].apply(classify_intervention)

# --- Normalised phase label ---
def normalise_phase(phase_str):
    if pd.isna(phase_str):
        return "Unknown"
    # For combined phases (e.g. PHASE1|PHASE2), use the later phase
    parts = phase_str.strip().split("|")
    order = {"EARLY_PHASE1": 0, "PHASE1": 1, "PHASE2": 2, "PHASE3": 3}
    valid = [p for p in parts if p in order]
    if not valid:
        return "Unknown"
    return max(valid, key=lambda x: order[x])

ctg["phase"] = ctg["Phases"].apply(normalise_phase)

# ---------------------------------------------------------------------------
# 3. RISK FACTOR KEYWORD MAPPING
# ---------------------------------------------------------------------------

RISK_FACTOR_KEYWORDS = {
    "High systolic blood pressure": [
        "systolic blood pressure", "sbp", "blood pressure", r"\bbp\b",
        "hypertension", r"\bhtn\b", "antihypertensive", "diastolic", r"\bdbp\b",
        r"\bmap\b", "mean arterial pressure", r"\bmmhg\b", "pulse pressure",
        "raas", "renin-angiotensin", "ace inhibitor", r"\bacei\b", r"\barb\b",
        "beta-blocker", "calcium channel blocker", r"\bccb\b",
        "diuretic", "resistant hypertension",
        "sacubitril", "valsartan", "entresto", "amlodipine", "losartan",
        "candesartan", "olmesartan", "telmisartan", "irbesartan",
        "lisinopril", "ramipril", "perindopril", "enalapril",
        "carvedilol", "bisoprolol", "nebivolol", "metoprolol",
        "chlorthalidone", "hydrochlorothiazide", "indapamide", "spironolactone",
        "aldosterone antagonist", "mineralocorticoid receptor",
        "finerenone", "eplerenone",
    ],
    "High LDL cholesterol": [
        r"\bldl\b", "ldl-c", "low-density lipoprotein", "cholesterol",
        r"\btc\b", "total cholesterol", "statin", "dyslipidemia",
        "hyperlipidemia", "hypercholesterolemia", r"\blipid\b", "lipid-lowering",
        "triglyceride", r"\btg\b", r"\bpcsk9\b", r"\bhdl\b", "non-hdl",
        "apolipoprotein", r"\bapob\b", r"\bapoa\b", "lipoprotein",
        "atorvastatin", "rosuvastatin", "ezetimibe", "evolocumab", "alirocumab",
        "bempedoic", "inclisiran", "obicetrapib", "lomitapide", "mipomersen",
        r"\bniacin\b", "fenofibrate", r"\bfibrate\b", "omega-3", "fish oil",
        "pitavastatin", "pravastatin", "simvastatin", "fluvastatin",
        "lovastatin", "cerivastatin",
    ],
    "High fasting plasma glucose": [
        r"\bhba1c\b", r"\ba1c\b", "hemoglobin a1c", "glycated hemoglobin",
        "fasting glucose", r"\bfpg\b", "blood glucose", r"\bbg\b",
        "glycemia", r"\bdiabetes\b", r"\bt2dm\b", "type 2 diabetes",
        r"\bdm\b", "diabetes mellitus", "prediabetes", "insulin resistance",
        r"\bir\b", "homa-ir", r"\bogtt\b", "oral glucose tolerance",
        "postprandial glucose", "hyperglycemia", "glucagon",
        "glp-1", r"\bsglt2\b", "metformin", "insulin sensitivity",
        "semaglutide", "liraglutide", "dulaglutide", "tirzepatide",
        "exenatide", "albiglutide", "empagliflozin", "dapagliflozin",
        "canagliflozin", "ertugliflozin", "sitagliptin", "saxagliptin",
        "alogliptin", "linagliptin", r"\bdpp-4\b", "dipeptidyl peptidase",
        "pioglitazone", "rosiglitazone", "acarbose", "miglitol",
        "sulfonylurea", "glipizide", "glyburide", "glimepiride",
    ],
    "High body-mass index": [
        r"\bbmi\b", "body mass index", "weight loss", r"\bobesity\b",
        r"\bobese\b", r"\bwc\b", "waist circumference", "body weight",
        "adiposity", "overweight", "fat mass", "lean mass", "body fat",
        r"\badipose\b", "abdominal obesity", "central obesity",
        "visceral fat", "bariatric", "weight reduction",
        "weight management", "caloric restriction",
        "orlistat", "phentermine", "naltrexone-bupropion",
        "contrave", "saxenda", "wegovy", "mounjaro", "zepbound",
    ],
    "Metabolic risks": [
        "metabolic syndrome", r"\bmets\b", "metabolic risk",
        r"\binsulin\b", "adipokine", r"\binflammation\b",
        r"\bcrp\b", "c-reactive protein", r"\bhscrp\b",
        "high-sensitivity crp", r"\bmace\b",
        "major adverse cardiovascular events",
        r"\bascvd\b", "atherosclerosis", "atherosclerotic",
        "cardiovascular risk", "cardiovascular risk score",
        "framingham", "cardiometabolic", "oxidative stress",
        "endothelial function", "vascular inflammation",
        # Heart failure and cardiac function (broad CVD outcomes)
        "heart failure", r"\bhf\b", "ejection fraction", r"\blvef\b",
        r"\bef\b", r"\bbnp\b", "nt-probnp", "natriuretic peptide",
        r"\btroponin\b", "myocardial infarction", r"\bmi\b",
        "cardiac output", "cardiac function", "myocardial",
        "atrial fibrillation", r"\baf\b", r"\bafib\b",
        "arrhythmia", "coronary artery", r"\bcad\b",
        # Thrombosis / platelet / anticoagulation
        r"\bplatelet\b", "antiplatelet", "thrombosis", "thrombotic",
        "anticoagulant", "anticoagulation", "coagulation",
        r"\bfibrinogen\b", r"\bpai-1\b",
        "ticagrelor", "clopidogrel", "prasugrel", "aspirin",
        "rivaroxaban", "apixaban", "dabigatran", "edoxaban",
        "warfarin", "heparin",
        # Inflammation / biomarkers
        "interleukin", r"\bil-6\b", r"\btnf\b", "tumor necrosis factor",
        "mpo", "myeloperoxidase", "lipoprotein-associated phospholipase",
        r"\blp-pla2\b",
    ],
    "Kidney dysfunction": [
        r"\begfr\b", "estimated glomerular filtration rate", r"\bgfr\b",
        r"\bcreatinine\b", "serum creatinine", "kidney function",
        "renal function", r"\bproteinuria\b", r"\balbuminuria\b",
        "microalbuminuria", "macroalbuminuria", r"\buacr\b",
        "urine albumin-creatinine ratio", r"\bckd\b",
        "chronic kidney disease", r"\bnephropathy\b",
        "diabetic nephropathy", r"\baki\b", "acute kidney injury",
        r"\besrd\b", "end-stage renal disease", r"\bdialysis\b",
        "renal insufficiency",
        "cardiorenal", "cardio-renal",
        "atrasentan", "bardoxolone",
    ],
}

# Compile patterns once
COMPILED_KEYWORDS = {
    rf: [re.compile(kw, re.IGNORECASE) for kw in kws]
    for rf, kws in RISK_FACTOR_KEYWORDS.items()
}

def map_risk_factors(row):
    """Return list of matched risk factors for one trial row."""
    text = " ".join(
        str(row.get(col, "") or "")
        for col in ["Primary Outcome Measures", "Secondary Outcome Measures", "Brief Summary"]
    )
    matched = []
    for rf, patterns in COMPILED_KEYWORDS.items():
        if any(p.search(text) for p in patterns):
            matched.append(rf)
    return matched if matched else ["Unclassified"]

ctg["risk_factors"] = ctg.apply(map_risk_factors, axis=1)

# Explode so each trial × risk_factor is one row
ctg_exploded = ctg.explode("risk_factors").rename(columns={"risk_factors": "risk_factor"})
# Drop unclassified for analysis (keep in raw data)
ctg_classified = ctg_exploded[ctg_exploded["risk_factor"] != "Unclassified"].copy()

# ---------------------------------------------------------------------------
# 4. ANALYTICAL VARIABLES
# ---------------------------------------------------------------------------

# --- trials_by_risk_factor ---
trials_rf = (
    ctg_classified.groupby("risk_factor", as_index=False)["trial_id"]
    .nunique()
    .rename(columns={"trial_id": "trial_count"})
)
total_trials = trials_rf["trial_count"].sum()
trials_rf["trial_share"] = trials_rf["trial_count"] / total_trials

# --- trials_by_phase ---
trials_phase = (
    ctg_classified.groupby(["risk_factor", "phase"], as_index=False)["trial_id"]
    .nunique()
    .rename(columns={"trial_id": "count"})
)

# --- trials_by_sponsor ---
trials_sponsor = (
    ctg_classified.groupby(["risk_factor", "sponsor_type"], as_index=False)["trial_id"]
    .nunique()
    .rename(columns={"trial_id": "count"})
)

# --- trials_by_intervention ---
trials_intervention = (
    ctg_classified.groupby(["risk_factor", "intervention_type"], as_index=False)["trial_id"]
    .nunique()
    .rename(columns={"trial_id": "count"})
)

# --- trials_by_year ---
trials_year = (
    ctg_classified.groupby(["study_start_year", "risk_factor"], as_index=False)["trial_id"]
    .nunique()
    .rename(columns={"trial_id": "count", "study_start_year": "year"})
)
trials_year["year"] = trials_year["year"].astype(int)

# --- alignment: merge GBD summary + trial shares ---
align = gbd_summary_df.merge(
    trials_rf, on="risk_factor", how="left"
)
align["trial_count"] = align["trial_count"].fillna(0).astype(int)
align["trial_share"] = align["trial_share"].fillna(0.0)
align["alignment_score"] = align.apply(
    lambda r: (r["trial_share"] / r["burden_share"]) if r["burden_share"] > 0 else None,
    axis=1,
)
align["priority_gap"] = align["burden_share"] - align["trial_share"]

# ---------------------------------------------------------------------------
# 4b. SPEARMAN CORRELATION
# ---------------------------------------------------------------------------

rho, p_value = spearmanr(align["trial_count"], align["death_val"])

if abs(rho) >= 0.8:
    interp = "Strong alignment: research intensity closely tracks disease burden."
elif abs(rho) >= 0.5:
    interp = "Moderate alignment: research partially tracks disease burden."
else:
    interp = "Weak alignment: research does not closely track disease burden."

correlation_result = {
    "spearman_rho": round(float(rho), 4),
    "p_value": round(float(p_value), 4),
    "n": int(len(align)),
    "interpretation": interp,
}

# ---------------------------------------------------------------------------
# 5. SANKEY NODES & LINKS
# ---------------------------------------------------------------------------

# Nodes: trials (by intervention type) → risk factors → burden (GBD)
intervention_types = ["Pharmacologic", "Behavioral", "Device", "Lifestyle/Other"]
risk_factors_ordered = gbd_summary_df["risk_factor"].tolist()

sankey_nodes = (
    [{"id": iv, "type": "intervention"} for iv in intervention_types]
    + [{"id": rf, "type": "risk_factor"} for rf in risk_factors_ordered]
    + [{"id": "CVD Burden", "type": "burden"}]
)

node_index = {n["id"]: i for i, n in enumerate(sankey_nodes)}

# Links: intervention → risk_factor
links_iv_rf = (
    ctg_classified.groupby(["intervention_type", "risk_factor"], as_index=False)["trial_id"]
    .nunique()
    .rename(columns={"trial_id": "value"})
)
sankey_links = [
    {
        "source": node_index[row["intervention_type"]],
        "target": node_index[row["risk_factor"]],
        "value": int(row["value"]),
    }
    for _, row in links_iv_rf.iterrows()
    if row["intervention_type"] in node_index and row["risk_factor"] in node_index
]

# Links: risk_factor → CVD Burden (weight by death_val)
burden_cvd_idx = node_index["CVD Burden"]
for _, row in gbd_summary_df.iterrows():
    if row["risk_factor"] in node_index:
        sankey_links.append({
            "source": node_index[row["risk_factor"]],
            "target": burden_cvd_idx,
            "value": int(row["death_val"]),
        })

# ---------------------------------------------------------------------------
# 6. EXPORT JSON
# ---------------------------------------------------------------------------

def df_to_records(df):
    return json.loads(df.to_json(orient="records"))

output = {
    "gbd_summary": df_to_records(
        gbd_summary_df[["risk_factor", "death_val", "burden_share"]]
    ),
    "gbd_by_state": df_to_records(
        gbd_by_state_df[["location_name", "risk_factor", "death_val"]]
    ),
    "gbd_by_year": df_to_records(
        gbd_by_year_df[["year", "risk_factor", "death_val"]]
    ),
    "trials_by_risk_factor": df_to_records(
        trials_rf[["risk_factor", "trial_count", "trial_share"]]
    ),
    "trials_by_phase": df_to_records(trials_phase),
    "trials_by_sponsor": df_to_records(trials_sponsor),
    "trials_by_intervention": df_to_records(trials_intervention),
    "trials_by_year": df_to_records(trials_year),
    "alignment": df_to_records(
        align[[
            "risk_factor", "death_val", "burden_share",
            "trial_count", "trial_share", "alignment_score", "priority_gap",
        ]]
    ),
    "correlation": correlation_result,
    "sankey_nodes": sankey_nodes,
    "sankey_links": sankey_links,
}

with open("processed_data.json", "w") as f:
    json.dump(output, f, indent=2)

# --- Summary report ---
print("=" * 60)
print("PIPELINE COMPLETE — processed_data.json written")
print("=" * 60)
print(f"\nGBD data: {len(gbd)} rows after filtering")
print(f"  Risk factors: {gbd_summary_df['risk_factor'].tolist()}")
print(f"\nCTG data: {len(ctg)} trials after inclusion filters")
print(f"  Classified trial-risk_factor pairs: {len(ctg_classified)}")
print(f"  Unique trials with a risk factor: {ctg_classified['trial_id'].nunique()}")
print(f"  Unclassified trials: {(ctg_exploded['risk_factor']=='Unclassified').sum()}")

print(f"\nAlignment table:")
for _, r in align.iterrows():
    score = f"{r['alignment_score']:.2f}" if r['alignment_score'] is not None else "N/A"
    print(
        f"  {r['risk_factor']:<35} burden={r['burden_share']:.3f}  "
        f"trials={r['trial_count']:>3}  trial_share={r['trial_share']:.3f}  "
        f"score={score}"
    )

print(f"\nSpearman correlation (trial_count vs death_val):")
print(f"  rho = {rho:.4f},  p = {p_value:.4f}")
print(f"  {interp}")
print(f"\nSankey: {len(sankey_nodes)} nodes, {len(sankey_links)} links")
