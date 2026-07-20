# nf-core/surfaceproteins: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.0.0dev - [date]

Initial release of nf-core/surfaceproteins, created with the [nf-core](https://nf-co.re/) template.

### `Added`

- `COLLATE_MERGEDTABLES`: automatically concatenates every sample's merged table into `mergedtables/all_samples_mergedtable.csv`, adding `sample_id` and `gram_stain` (from the samplesheet's `gram` column) - previously a manual, out-of-pipeline step.
- `PREDICT_LOCALIZATION`: consensus localization call per protein from SignalP, TMHMM, Phobius, PSortB and Gram stain, with a confidence level and rationale. Outputs `localization/localization.csv`, `localization_full.csv` and a self-contained `localization_report.html`. See [docs/localization-logic.md](docs/localization-logic.md).

### `Fixed`

### `Dependencies`

### `Deprecated`
