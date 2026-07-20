#!/usr/bin/env python3
import html
import json
import re
from datetime import datetime, timezone

import pandas as pd

# ---------------------------------------------------------------------------
# Consensus localization call from SignalP / TMHMM / Phobius / PSORTb + Gram stain
# ---------------------------------------------------------------------------

def signal_subtype(row):
    probs = {
        "Sec/SPI (general secretory)": row.get("sign_sp_spI", 0),
        "Lipoprotein (SPII)": row.get("sign_lipo_spII", 0),
        "Tat/SPI (folded-protein export)": row.get("sign_tat_spI", 0),
        "Tat lipoprotein (SPII)": row.get("sign_tatlipo_spII", 0),
        "Pilin-like (SPIII)": row.get("sign_pilin_spIII", 0),
    }
    return max(probs, key=probs.get)


def classify(row):
    sp = row["sign_prediction"]
    phsp = row["phob_SP"]
    predhel = row["PredHel"]
    phtm = row["phob_TM"]
    psort = row["psort_prediction"]
    pscore = row["psort_score"]
    gram = row["gram_stain"]
    cs_prob = row["cs_prob"]

    notes = []
    has_sp_call = sp in ("SP", "LIPO")
    sp_disagree = has_sp_call and phsp == "0"
    if sp_disagree:
        notes.append(
            "SignalP predicts a cleavable signal peptide but Phobius does not "
            "(Phobius instead calls a TM helix) - signal-peptide-vs-signal-anchor disagreement"
        )
    if has_sp_call and not pd.isna(cs_prob) and cs_prob < 0.7:
        notes.append(f"SignalP cleavage-site confidence is low (Pr={cs_prob:.2f}) - signal peptide call is uncertain")

    tm_count = max(predhel, phtm)

    if predhel >= 2 and phtm >= 2:
        loc = f"Integral membrane protein (multi-pass, ~{tm_count} TM helices)"
        conf = "High"
        if predhel != phtm:
            notes.append(f"TMHMM predicts {predhel} TM helices vs Phobius {phtm} - both agree on multi-pass, exact count differs")
        if not pd.isna(psort) and psort != "CytoplasmicMembrane":
            notes.append(f'PSORTb calls "{psort}" (score {pscore}), conflicting with multi-pass TM prediction')
        elif not pd.isna(psort):
            notes.append(f"PSORTb agrees: cytoplasmic membrane (score {pscore})")
        return loc, conf, "; ".join(notes)

    if (predhel >= 2) != (phtm >= 2):
        source = "TMHMM" if predhel >= 2 else "Phobius"
        other = "Phobius" if predhel >= 2 else "TMHMM"
        loc = f"TM helices predicted by {source} only (~{tm_count}) - needs review"
        conf = "Low"
        notes.append(
            f"TMHMM calls {predhel} TM helices, Phobius calls {phtm} - only {source} supports a multi-pass "
            f"membrane topology and {other} does not. TMHMM is known to over-call helices on hydrophobic or "
            "low-complexity/coiled-coil regions, so a single-tool call is not trusted as multi-pass without "
            "independent agreement"
        )
        if not pd.isna(psort):
            notes.append(f"PSORTb: {psort} (score {pscore})")
        return loc, conf, "; ".join(notes)

    if predhel == 1 and phtm == 1:
        loc = "Membrane-anchored (signal-anchor / single-pass TM)"
        conf = "High"
        notes.append(
            "TMHMM and Phobius agree on one TM helix - likely a genuine (uncleaved) signal-anchor; "
            "protein probably stays membrane-bound rather than being released"
        )
        if not pd.isna(psort):
            notes.append(f"PSORTb: {psort} (score {pscore})")
        return loc, conf, "; ".join(notes)

    if predhel == 1 and phtm == 0:
        notes.append(
            "TMHMM calls one N-terminal TM helix, but Phobius (which jointly models signal peptides "
            "and TM helices) does not - likely TMHMM is picking up the signal peptide's hydrophobic "
            "core rather than a genuine anchor"
        )

    if has_sp_call:
        subtype = signal_subtype(row)
        conf = "Moderate"
        if gram == "negative":
            loc = (
                "Periplasmic (lipoprotein, membrane-anchored)" if sp == "LIPO"
                else "Periplasmic (Sec-dependent; may be further exported)"
            )
            if not pd.isna(psort):
                if psort == "Extracellular":
                    loc = "Extracellular (Sec-secreted, exported beyond periplasm)"
                    conf = "High" if pscore >= 9 else "Moderate"
                    notes.append(f"PSORTb supports export beyond the periplasm (score {pscore})")
                elif psort == "Periplasmic":
                    conf = "High" if pscore >= 9 else "Moderate"
                    notes.append(f"PSORTb agrees: periplasmic (score {pscore})")
                elif psort == "CytoplasmicMembrane":
                    loc = "Membrane-associated (PSORTb: cytoplasmic membrane)"
                    notes.append(f"PSORTb suggests membrane retention despite a cleavable signal peptide (score {pscore})")
                else:
                    notes.append(f"PSORTb: {psort} (score {pscore}) - conflicts with default periplasmic assignment")
        elif gram == "positive":
            loc = "Cell-surface anchored lipoprotein" if sp == "LIPO" else "Extracellular (Sec-secreted)"
            notes.append(
                "Gram-positive: no periplasm, so a cleaved signal peptide with no TM usually means full "
                "secretion; cell-wall-anchoring motifs (e.g. LPXTG) are not evaluated here"
            )
            if not pd.isna(psort):
                if psort == "Extracellular":
                    conf = "High" if pscore >= 9 else "Moderate"
                    notes.append(f"PSORTb agrees: extracellular (score {pscore})")
                elif psort == "CytoplasmicMembrane":
                    loc = "Membrane-associated (PSORTb: cytoplasmic membrane)"
                    notes.append(f"PSORTb suggests membrane retention (score {pscore})")
                elif psort == "Periplasmic":
                    notes.append(f"PSORTb calls periplasmic (score {pscore}), unusual for Gram-positive")
        else:
            loc = "Putative secreted/exported (Gram stain unknown)"
            conf = "Low"
            notes.append("Gram stain of this taxon is unknown, so localization cannot be confidently assigned")
            if not pd.isna(psort):
                notes.append(f"PSORTb: {psort} (score {pscore})")

        if sp_disagree or (predhel == 1 and phtm == 0):
            if conf == "High":
                conf = "Moderate"
        notes.append(f"Signal peptide type: {subtype}")
        return loc, conf, "; ".join(notes)

    if not pd.isna(psort) and psort == "Extracellular":
        loc = "Possible non-classical secretion"
        conf = "Low"
        notes.append(
            f"No signal peptide detected by SignalP/Phobius, but PSORTb predicts extracellular "
            f"(score {pscore}) - could reflect non-classical secretion, a moonlighting protein, or a false positive"
        )
    elif not pd.isna(psort) and psort == "CytoplasmicMembrane":
        loc = "Ambiguous (no SP/TM detected, but PSORTb: cytoplasmic membrane)"
        conf = "Low"
        notes.append(f"PSORTb calls cytoplasmic membrane (score {pscore}) despite no signal peptide or TM helix")
    else:
        loc = "Cytoplasmic"
        conf = "Moderate"
        if not pd.isna(psort):
            if psort == "Cytoplasmic":
                conf = "High" if pscore >= 9 else "Moderate"
                notes.append(f"PSORTb agrees: cytoplasmic (score {pscore})")
            else:
                conf = "Low"
                notes.append(f"PSORTb: {psort} (score {pscore})")
    return loc, conf, "; ".join(notes)


REVIEW_BUCKET = "TM helices - single tool only (needs review)"

BUCKET_ORDER = [
    "Cytoplasmic",
    "Membrane-associated / ambiguous",
    "Integral membrane (multi-pass)",
    "Membrane-anchored (single-pass)",
    "Lipoprotein (membrane-anchored)",
    "Periplasmic",
    "Extracellular / secreted",
    "Unknown / unclassified",
]
BUCKET_COLOR_VAR = {name: f"--cat{i + 1}" for i, name in enumerate(BUCKET_ORDER)}
BUCKET_COLOR_VAR[REVIEW_BUCKET] = "--neutral"


def bucket(loc):
    text = loc.lower()
    if "needs review" in text:
        return REVIEW_BUCKET
    if text.startswith("cytoplasmic"):
        return "Cytoplasmic"
    if "integral membrane" in text:
        return "Integral membrane (multi-pass)"
    if "signal-anchor" in text or text.startswith("membrane-anchored"):
        return "Membrane-anchored (single-pass)"
    if "lipoprotein" in text:
        return "Lipoprotein (membrane-anchored)"
    if "membrane-associated" in text or "ambiguous" in text:
        return "Membrane-associated / ambiguous"
    if "periplasmic" in text:
        return "Periplasmic"
    if "non-classical secretion" in text or "extracellular" in text:
        return "Extracellular / secreted"
    return "Unknown / unclassified"


def build_webapp_table(df):
    out = pd.DataFrame()
    out["sample_id"] = df["sample_id"]
    out["protein_id"] = df["protein_id"]
    out["protein_name"] = df["protein_name"]
    out["species"] = df["tax_id"]
    out["gram_stain"] = df["gram_stain"]

    out["signalp_call"] = df["sign_prediction"]
    out["signalp_type"] = df.apply(
        lambda r: signal_subtype(r) if r["sign_prediction"] in ("SP", "LIPO") else "-", axis=1
    )
    out["signalp_confidence"] = df["cs_prob"].round(3)

    out["tmhmm_tm_helices"] = df["PredHel"]

    out["phobius_tm_helices"] = df["phob_TM"]
    out["phobius_signal_peptide"] = df["phob_SP"].map({"Y": "Yes", "0": "No"}).fillna(df["phob_SP"])

    out["psortb_localization"] = df["psort_prediction"]
    out["psortb_score"] = df["psort_score"]

    out["predicted_localization"] = df["predicted_localization"]
    out["localization_confidence"] = df["localization_confidence"]
    out["rationale_notes"] = df["rationale_notes"]
    return out


# ---------------------------------------------------------------------------
# Run classification
# ---------------------------------------------------------------------------

df = pd.read_csv("${mergedtable}")

required_cols = {
    "sample_id", "gram_stain", "tax_id", "protein_id", "protein_name",
    "sign_prediction", "sign_other", "sign_sp_spI", "sign_lipo_spII",
    "sign_tat_spI", "sign_tatlipo_spII", "sign_pilin_spIII", "sign_cspos",
    "PredHel", "phob_TM", "phob_SP", "psort_prediction", "psort_score",
}
missing = required_cols - set(df.columns)
if missing:
    raise SystemExit(f"ERROR: input table is missing expected columns: {sorted(missing)}")

df["cs_prob"] = df["sign_cspos"].str.extract(r"Pr:\\s*([\\d.]+)").astype(float)

results = df.apply(classify, axis=1, result_type="expand")
results.columns = ["predicted_localization", "localization_confidence", "rationale_notes"]
df = pd.concat([df, results], axis=1)
df["locus_bucket"] = df["predicted_localization"].apply(bucket)

webapp_df = build_webapp_table(df)
webapp_df.to_csv("localization.csv", index=False)
print(f"Wrote localization.csv ({len(webapp_df)} rows, {len(webapp_df.columns)} columns)")

df.drop(columns=["cs_prob", "locus_bucket"]).to_csv("localization_full.csv", index=False)
print("Wrote localization_full.csv")

MEMBRANE_BUCKETS = {"Integral membrane (multi-pass)", "Membrane-anchored (single-pass)"}
membrane_fraction = df["locus_bucket"].isin(MEMBRANE_BUCKETS).mean()
if membrane_fraction > 0.4:
    print(
        f"WARNING: {membrane_fraction:.0%} of proteins were classified as membrane "
        "(integral multi-pass or single-pass anchored). Real proteomes are typically "
        "~20-30% membrane protein; a fraction this high usually means TMHMM and/or "
        "Phobius are over-calling TM helices on this input (e.g. low-complexity or "
        "repetitive sequence) rather than reflecting genuine biology - spot-check a "
        "handful of these proteins' annotations before trusting the output."
    )

# ---------------------------------------------------------------------------
# Lightweight, self-contained HTML report (no JS/CSS frameworks, no CDN calls)
# ---------------------------------------------------------------------------

def svg_bar_chart(entries, color_vars, width=640, bar_h=26, gap=10, label_w=230):
    n = len(entries)
    max_val = max((v for _, v in entries), default=1) or 1
    height = n * (bar_h + gap) + gap
    plot_w = width - label_w - 60
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="bar chart" class="chart-svg">']
    for i, (label, val) in enumerate(entries):
        y = gap + i * (bar_h + gap)
        bar_w = max(2.0, (val / max_val) * plot_w)
        color_var = color_vars[i]
        esc_label = html.escape(str(label))
        parts.append(
            "<g>"
            f"<title>{esc_label}: {val}</title>"
            f'<text x="{label_w - 10}" y="{y + bar_h / 2 + 4}" text-anchor="end" class="bar-label">{esc_label}</text>'
            f'<rect x="{label_w}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="4" style="fill:var({color_var})"></rect>'
            f'<text x="{label_w + bar_w + 8:.1f}" y="{y + bar_h / 2 + 4}" class="bar-value">{val}</text>'
            "</g>"
        )
    parts.append("</svg>")
    return "".join(parts)


CONF_ORDER = ["High", "Moderate", "Low"]
CONF_COLOR_VAR = {"High": "--seq-high", "Moderate": "--seq-mod", "Low": "--seq-low"}
GRAM_ORDER = ["negative", "positive", "unknown"]
GRAM_LABEL = {"negative": "Gram-negative", "positive": "Gram-positive", "unknown": "Unknown"}
GRAM_COLOR_VAR = {"negative": "--cat1", "positive": "--cat2", "unknown": "--neutral"}

CSS = """
:root {
  color-scheme: light;
  --surface: #fcfcfb;
  --page: #f9f9f7;
  --ink-primary: #0b0b0b;
  --ink-secondary: #52514e;
  --ink-muted: #898781;
  --gridline: #e1e0d9;
  --baseline: #c3c2b7;
  --border: rgba(11,11,11,0.10);
  --neutral: #c3c2b7;
  --cat1: #2a78d6;
  --cat2: #008300;
  --cat3: #e87ba4;
  --cat4: #eda100;
  --cat5: #1baf7a;
  --cat6: #eb6834;
  --cat7: #4a3aa7;
  --cat8: #e34948;
  --seq-low: #9ec5f4;
  --seq-mod: #5598e7;
  --seq-high: #184f95;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --surface: #1a1a19;
    --page: #0d0d0d;
    --ink-primary: #ffffff;
    --ink-secondary: #c3c2b7;
    --ink-muted: #898781;
    --gridline: #2c2c2a;
    --baseline: #383835;
    --border: rgba(255,255,255,0.10);
    --neutral: #383835;
    --cat1: #3987e5;
    --cat2: #008300;
    --cat3: #d55181;
    --cat4: #c98500;
    --cat5: #199e70;
    --cat6: #d95926;
    --cat7: #9085e9;
    --cat8: #e66767;
    --seq-low: #6da7ec;
    --seq-mod: #3987e5;
    --seq-high: #2a78d6;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px;
  background: var(--page);
  color: var(--ink-primary);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 14px;
  line-height: 1.5;
}
h1 { font-size: 20px; margin: 0 0 4px; }
h2 { font-size: 15px; margin: 0 0 12px; color: var(--ink-primary); }
.meta { color: var(--ink-secondary); font-size: 13px; margin-bottom: 24px; }
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}
.stat-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
}
.stat-tile {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 20px;
  min-width: 140px;
  flex: 1;
}
.stat-tile .value { font-size: 24px; font-weight: 600; font-variant-numeric: tabular-nums; }
.stat-tile .label { font-size: 12px; color: var(--ink-secondary); margin-top: 2px; }
.chart-row { display: flex; flex-wrap: wrap; gap: 20px; }
.chart-row .card { flex: 1; min-width: 320px; }
.chart-svg { overflow: visible; }
.bar-label { font-size: 12px; fill: var(--ink-secondary); }
.bar-value { font-size: 12px; fill: var(--ink-primary); font-variant-numeric: tabular-nums; }
.controls { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
.controls input, .controls select {
  font: inherit;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--ink-primary);
}
.controls input { flex: 1; min-width: 220px; }
#row-count { color: var(--ink-secondary); font-size: 12px; }
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
th, td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--gridline);
  vertical-align: top;
}
th {
  color: var(--ink-secondary);
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  position: sticky;
  top: 0;
  background: var(--surface);
}
th.sort-asc::after { content: " ↑"; }
th.sort-desc::after { content: " ↓"; }
td.rationale { max-width: 360px; color: var(--ink-secondary); }
.table-wrap { max-height: 640px; overflow: auto; border: 1px solid var(--border); border-radius: 8px; }
"""

JS = """
var DATA = JSON.parse(document.getElementById("protein-data").textContent);
var COLUMNS = [
  ["sample_id", "Sample"],
  ["protein_id", "Protein ID"],
  ["protein_name", "Protein"],
  ["species", "Species"],
  ["gram_stain", "Gram"],
  ["signalp_call", "SignalP"],
  ["signalp_type", "SignalP type"],
  ["tmhmm_tm_helices", "TMHMM TM"],
  ["phobius_tm_helices", "Phobius TM"],
  ["psortb_localization", "PSORTb"],
  ["predicted_localization", "Predicted localization"],
  ["localization_confidence", "Confidence"],
  ["rationale_notes", "Rationale"]
];

var state = { sortKey: "predicted_localization", sortDir: 1, search: "", confidence: "All" };

function renderTable() {
  var rows = DATA.filter(function (row) {
    if (state.confidence !== "All" && row.localization_confidence !== state.confidence) {
      return false;
    }
    if (state.search) {
      var haystack = ((row.protein_id || "") + " " + (row.protein_name || "") + " " + (row.species || "")).toLowerCase();
      if (haystack.indexOf(state.search) === -1) {
        return false;
      }
    }
    return true;
  });

  rows.sort(function (a, b) {
    var av = a[state.sortKey];
    var bv = b[state.sortKey];
    if (av === null || av === undefined) av = "";
    if (bv === null || bv === undefined) bv = "";
    if (av < bv) return -1 * state.sortDir;
    if (av > bv) return 1 * state.sortDir;
    return 0;
  });

  var tbody = document.getElementById("protein-rows");
  tbody.innerHTML = "";
  rows.forEach(function (row) {
    var tr = document.createElement("tr");
    COLUMNS.forEach(function (col) {
      var td = document.createElement("td");
      var value = row[col[0]];
      td.textContent = (value === null || value === undefined || value === "") ? "-" : value;
      if (col[0] === "rationale_notes") {
        td.className = "rationale";
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  document.getElementById("row-count").textContent = rows.length + " of " + DATA.length + " proteins";
}

document.querySelectorAll("th[data-key]").forEach(function (th) {
  th.addEventListener("click", function () {
    var key = th.getAttribute("data-key");
    if (state.sortKey === key) {
      state.sortDir = -state.sortDir;
    } else {
      state.sortKey = key;
      state.sortDir = 1;
    }
    document.querySelectorAll("th[data-key]").forEach(function (h) {
      h.classList.remove("sort-asc", "sort-desc");
    });
    th.classList.add(state.sortDir === 1 ? "sort-asc" : "sort-desc");
    renderTable();
  });
});

document.getElementById("search-box").addEventListener("input", function (e) {
  state.search = e.target.value.toLowerCase();
  renderTable();
});

document.getElementById("confidence-filter").addEventListener("change", function (e) {
  state.confidence = e.target.value;
  renderTable();
});

renderTable();
"""

table_header_cells = "".join(f'<th data-key="{key}">{html.escape(label)}</th>' for key, label in [
    ("sample_id", "Sample"),
    ("protein_id", "Protein ID"),
    ("protein_name", "Protein"),
    ("species", "Species"),
    ("gram_stain", "Gram"),
    ("signalp_call", "SignalP"),
    ("signalp_type", "SignalP type"),
    ("tmhmm_tm_helices", "TMHMM TM"),
    ("phobius_tm_helices", "Phobius TM"),
    ("psortb_localization", "PSORTb"),
    ("predicted_localization", "Predicted localization"),
    ("localization_confidence", "Confidence"),
    ("rationale_notes", "Rationale"),
])

def write_report(report_df, report_webapp_df, filename, title, extra_meta=""):
    bucket_counts = report_df["locus_bucket"].value_counts()
    bucket_entries = [(b, int(bucket_counts.get(b, 0))) for b in BUCKET_ORDER if bucket_counts.get(b, 0) > 0]
    if bucket_counts.get(REVIEW_BUCKET, 0) > 0:
        bucket_entries.append((REVIEW_BUCKET, int(bucket_counts[REVIEW_BUCKET])))
    bucket_colors = [BUCKET_COLOR_VAR[b] for b, _ in bucket_entries]
    localization_chart = svg_bar_chart(bucket_entries, bucket_colors)

    conf_counts = report_df["localization_confidence"].value_counts()
    conf_entries = [(c, int(conf_counts.get(c, 0))) for c in CONF_ORDER if conf_counts.get(c, 0) > 0]
    conf_colors = [CONF_COLOR_VAR[c] for c, _ in conf_entries]
    confidence_chart = svg_bar_chart(conf_entries, conf_colors, width=480, label_w=110)

    gram_counts = report_df["gram_stain"].value_counts()
    gram_entries = [(GRAM_LABEL[g], int(gram_counts.get(g, 0))) for g in GRAM_ORDER if gram_counts.get(g, 0) > 0]
    gram_colors = [GRAM_COLOR_VAR[g] for g in GRAM_ORDER if gram_counts.get(g, 0) > 0]
    gram_chart = svg_bar_chart(gram_entries, gram_colors, width=480, label_w=110)

    n_proteins = len(report_df)
    n_samples = report_df["sample_id"].nunique()
    n_species = report_df["tax_id"].nunique()
    n_high = int(conf_counts.get("High", 0))
    n_moderate = int(conf_counts.get("Moderate", 0))
    n_low = int(conf_counts.get("Low", 0))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    table_records = report_webapp_df.astype(object).where(pd.notnull(report_webapp_df), None).to_dict(orient="records")
    table_json = json.dumps(table_records, default=str)

    esc_title = html.escape(title)

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc_title}</title>
<style>{CSS}</style>
</head>
<body>
<h1>{esc_title}</h1>
<div class="meta">Generated {generated_at} &middot; {n_proteins} proteins &middot; {n_samples} samples &middot; {n_species} species{extra_meta}</div>

<div class="stat-row">
  <div class="stat-tile"><div class="value">{n_proteins}</div><div class="label">Proteins classified</div></div>
  <div class="stat-tile"><div class="value">{n_samples}</div><div class="label">Samples</div></div>
  <div class="stat-tile"><div class="value">{n_species}</div><div class="label">Species</div></div>
  <div class="stat-tile"><div class="value">{n_high}</div><div class="label">High confidence</div></div>
  <div class="stat-tile"><div class="value">{n_moderate}</div><div class="label">Moderate confidence</div></div>
  <div class="stat-tile"><div class="value">{n_low}</div><div class="label">Low confidence</div></div>
</div>

<div class="card">
  <h2>Predicted localization</h2>
  {localization_chart}
</div>

<div class="chart-row">
  <div class="card">
    <h2>Confidence</h2>
    {confidence_chart}
  </div>
  <div class="card">
    <h2>Gram stain</h2>
    {gram_chart}
  </div>
</div>

<div class="card">
  <h2>Per-protein calls</h2>
  <div class="controls">
    <input id="search-box" type="text" placeholder="Search protein ID, name, or species...">
    <select id="confidence-filter">
      <option>All</option>
      <option>High</option>
      <option>Moderate</option>
      <option>Low</option>
    </select>
    <span id="row-count"></span>
  </div>
  <div class="table-wrap">
    <table>
      <thead><tr>{table_header_cells}</tr></thead>
      <tbody id="protein-rows"></tbody>
    </table>
  </div>
</div>

<script type="application/json" id="protein-data">{table_json}</script>
<script>{JS}</script>
</body>
</html>
"""

    with open(filename, "w") as f:
        f.write(html_doc)
    print(f"Wrote {filename} ({n_proteins} proteins)")


REPORT_PROTEIN_THRESHOLD = 1000

if len(df) > REPORT_PROTEIN_THRESHOLD:
    total_proteins = len(df)
    total_samples = df["sample_id"].nunique()
    print(
        f"Run has {total_proteins} proteins (over the {REPORT_PROTEIN_THRESHOLD}-protein threshold) - "
        "writing one HTML report per sample instead of a single combined report to keep each file light."
    )
    for sample_id, idx in df.groupby("sample_id", sort=True).groups.items():
        safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", str(sample_id))
        write_report(
            df.loc[idx],
            webapp_df.loc[idx],
            filename=f"localization_report_{safe_id}.html",
            title=f"Surface protein localization report - {sample_id}",
            extra_meta=f" &middot; part of a {total_proteins}-protein, {total_samples}-sample run",
        )
else:
    write_report(
        df, webapp_df,
        filename="localization_report.html",
        title="Surface protein localization report",
    )

with open("versions.yml", "w") as vf:
    import sys
    vf.write('"${task.process}":\\n')
    vf.write(f"    python: {sys.version.split()[0]}\\n")
    vf.write(f"    pandas: {pd.__version__}\\n")
