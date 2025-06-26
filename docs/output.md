# surfaceproteins: Output

## Introduction

This document describes the output produced by the pipeline. Most of the plots are taken from the MultiQC report, which summarises results at the end of the pipeline.

The directories listed below will be created in the results directory after the pipeline has finished. All paths are relative to the top-level results directory.

## Pipeline overview

The pipeline is built using [Nextflow](https://www.nextflow.io/) and processes bacterial genome assemblies using the following steps:

- [Bakta](#bakta) - Rapid bacterial genome annotation
- [SignalP](#signalp) - Signal peptide prediction
- [TMHMM](#tmhmm) - Transmembrane helix prediction
- [PSortB](#psortb) - Bacterial protein subcellular localization prediction
- [Phobius](#phobius) - Combined signal peptide and transmembrane topology prediction
- [MultiQC](#multiqc) - Aggregate report describing results and QC from the whole pipeline
- [Pipeline information](#pipeline-information) - Report metrics generated during the workflow execution

### Bakta

<details markdown="1">
<summary>Output files</summary>

- `bakta/`
  - `*.gff3`: Annotation in GFF3 format
  - `*.gbff`: Annotation in GenBank format
  - `*.embl`: Annotation in EMBL format
  - `*.fna`: Nucleotide sequences of the assembly
  - `*.faa`: Amino acid sequences of predicted proteins
  - `*.ffn`: Nucleotide sequences of predicted genes
  - `*.tsv`: Summary of annotations in TSV format
  - `*.txt`: Detailed annotation report
  - `*.hypotheticals.tsv`: Summary of hypothetical proteins
  - `*.hypotheticals.faa`: Amino acid sequences of hypothetical proteins

</details>

[Bakta](https://github.com/oschwengers/bakta) is a tool for rapid and standardized annotation of bacterial genomes and plasmids. It provides comprehensive functional annotation including protein coding genes, tRNAs, tmRNAs, rRNAs, ncRNAs, CRISPR arrays, and oriC/oriV/oriT. The tool uses a comprehensive database for annotation and is particularly useful for high-throughput bacterial genome analysis.

### SignalP

<details markdown="1">
<summary>Output files</summary>

- `signalp/`
  - `*_signalp_summary.csv`: Combined summary of signal peptide predictions for all proteins
  - Individual prediction files for protein batches (split files)

</details>

[SignalP](https://services.healthtech.dtu.dk/service.php?SignalP) predicts the presence of signal peptides in amino acid sequences from different organisms. It distinguishes between signal peptides and transmembrane regions and provides cleavage site predictions. The pipeline splits protein sequences into batches for efficient processing and then concatenates the results.

### TMHMM

<details markdown="1">
<summary>Output files</summary>

- `tmhmm/`
  - `*_tmhmm_summary.tsv`: Combined summary of transmembrane helix predictions
  - Individual annotation and summary files for protein batches

</details>

[TMHMM](https://services.healthtech.dtu.dk/service.php?TMHMM-2.0) predicts transmembrane helices in proteins using a hidden Markov model. It provides information about the number and location of transmembrane segments, which is crucial for understanding protein topology and subcellular localization. The output includes both the number of predicted transmembrane helices and detailed topology information.

### PSortB

<details markdown="1">
<summary>Output files</summary>

- `psortb/`
  - `*.txt`: Raw PSortB output with localization predictions
  - `*_psortb_parsed.csv`: Parsed and formatted localization predictions

</details>

[PSortB](https://www.psort.org/psortb/) is a tool for predicting bacterial protein subcellular localization. It can distinguish between cytoplasmic, cytoplasmic membrane, periplasmic, outer membrane, and extracellular localizations for Gram-negative bacteria, and cytoplasmic, cytoplasmic membrane, cell wall, and extracellular for Gram-positive bacteria. The tool provides probability scores for each predicted location.

### Phobius

<details markdown="1">
<summary>Output files</summary>

- `phobius/`
  - `*.txt`: Phobius predictions combining signal peptide and transmembrane topology

</details>

[Phobius](https://phobius.sbc.su.se/) is a combined transmembrane topology and signal peptide predictor. It uses a hidden Markov model that can distinguish between transmembrane segments and signal peptides, providing a unified prediction that avoids the confusion that can arise when using separate predictors. This is particularly useful for surface protein analysis where both features may be present.

### Merged Results

<details markdown="1">
<summary>Output files</summary>

- `merged_results/`
  - `*_surface_proteins_summary.tsv`: Final integrated table combining all prediction results

</details>

The pipeline combines results from all prediction tools into a comprehensive summary table that includes:
- Protein identifiers and sequences
- Signal peptide predictions from SignalP
- Transmembrane helix predictions from TMHMM
- Subcellular localization predictions from PSortB
- Combined topology predictions from Phobius

This integrated output allows for comprehensive analysis of surface proteins and their predicted cellular locations.

### MultiQC

<details markdown="1">
<summary>Output files</summary>

- `multiqc/`
  - `multiqc_report.html`: a standalone HTML file that can be viewed in your web browser.
  - `multiqc_data/`: directory containing parsed statistics from the different tools used in the pipeline.
  - `multiqc_plots/`: directory containing static images from the report in various formats.

</details>

[MultiQC](http://multiqc.info) is a visualization tool that generates a single HTML report summarising all samples in your project. The pipeline integrates results from the various prediction tools and provides summary statistics about the number of proteins analyzed, prediction distributions, and tool versions used. For more information about how to use MultiQC reports, see <http://multiqc.info>.

### Pipeline information

<details markdown="1">
<summary>Output files</summary>

- `pipeline_info/`
  - Reports generated by Nextflow: `execution_report.html`, `execution_timeline.html`, `execution_trace.txt` and `pipeline_dag.dot`/`pipeline_dag.svg`.
  - Reports generated by the pipeline: `pipeline_report.html`, `pipeline_report.txt` and `software_versions.yml`. The `pipeline_report*` files will only be present if the `--email` / `--email_on_fail` parameter's are used when running the pipeline.
  - Reformatted samplesheet files used as input to the pipeline: `samplesheet.valid.csv`.
  - Parameters used by the pipeline run: `params.json`.

</details>

[Nextflow](https://www.nextflow.io/docs/latest/tracing.html) provides excellent functionality for generating various reports relevant to the running and execution of the pipeline. This will allow you to troubleshoot errors with the running of the pipeline, and also provide you with other information such as launch commands, run times and resource usage.