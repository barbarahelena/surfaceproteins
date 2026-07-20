# nf-core/surfaceproteins: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.0.0dev - [date]

Initial release of nf-core/surfaceproteins, created with the [nf-core](https://nf-co.re/) template.

### `Added`

- `COLLATE_MERGEDTABLES`: automatically concatenates every sample's merged table into `mergedtables/all_samples_mergedtable.csv`, adding `sample_id` and `gram_stain` (from the samplesheet's `gram` column) - previously a manual, out-of-pipeline step.
- `PREDICT_LOCALIZATION`: consensus localization call per protein from SignalP, TMHMM, Phobius, PSortB and Gram stain, with a confidence level and rationale. Outputs `localization/localization.csv`, `localization_full.csv` and a self-contained HTML report. See [docs/localization-logic.md](docs/localization-logic.md).
- `PREDICT_LOCALIZATION` now prints a `WARNING` to the process log if more than 40% of a run's proteins are classified as membrane protein, as a sanity check against systematic TM over-calling.
- `PREDICT_LOCALIZATION` writes one `localization_report_<sample_id>.html` per sample instead of a single `localization_report.html` once a run exceeds 1000 proteins in total, so the HTML report doesn't balloon in size on large runs.
- `PREDICT_LOCALIZATION` now recognizes PSortB's `OuterMembrane` category and classifies those as `Outer membrane protein (beta-barrel, PSORTb-supported)`, taking priority over TMHMM/Phobius TM-helix logic - those tools only model alpha-helical membrane proteins and are not valid for beta-barrel outer-membrane proteins (common in Gram-negative Bacteroidetes). See [docs/localization-logic.md](docs/localization-logic.md).

### `Fixed`

- `PREDICT_LOCALIZATION`'s multi-pass transmembrane rule required only TMHMM *or* Phobius to call ≥2 helices, not both. TMHMM over-calls TM helices on hydrophobic/low-complexity/coiled-coil regions; at genome scale (tested on a 16,597-protein run) this misclassified 97% of proteins as multi-pass membrane protein instead of the correct ~14%. Now requires both tools to agree; single-tool-only calls get a distinct, `Low`-confidence "needs review" bucket instead of being silently trusted.
- `TMHMM_TMHMM` container bumped to `barbarahelena/tmhmm:2.1`, fixing a bug where per-protein `.summary`/`.annotation` files could bleed topology data across proteins in the same batch, producing implausible TM-helix counts (seen up to 300+ on a single protein).
- The localization report's bar-chart labels (e.g. long PSortB/bucket names) could overflow past the chart's left edge and get clipped. The label column now sizes itself to the longest label actually present in each chart, and label text is a point smaller.

### `Dependencies`

### `Deprecated`
