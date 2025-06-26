# surfaceproteins: Usage

## Introduction

The surfaceproteins pipeline is designed to analyze bacterial genome assemblies for surface protein prediction. The pipeline performs genome annotation using Bakta and then applies multiple surface protein prediction tools including SignalP, TMHMM, PSortB, and Phobius to identify and characterize proteins with signal peptides, transmembrane domains, and specific subcellular localizations.

## Samplesheet input

You will need to create a samplesheet with information about the bacterial genome assemblies you would like to analyse before running the pipeline. Use this parameter to specify its location. It has to be a comma-separated file with 2 columns, and a header row as shown in the examples below.

```bash
--input '[path to samplesheet file]'
```

### Samplesheet format

The samplesheet should contain information about the genome assembly files you want to analyze. The pipeline expects genome assemblies in FASTA format.

```csv title="samplesheet.csv"
sample,assembly
SAMPLE_1,/path/to/sample1_assembly.fasta
SAMPLE_2,/path/to/sample2_assembly.fasta
SAMPLE_3,/path/to/sample3_assembly.fasta
```

| Column     | Description                                                                                                                                                                            |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sample`   | Custom sample name. This entry will be used as the sample identifier throughout the pipeline. Spaces in sample names are automatically converted to underscores (`_`).              |
| `assembly` | Full path to the bacterial genome assembly file in FASTA format (`.fasta`, `.fa`, `.fna`).                |

### Full samplesheet example

A complete samplesheet file may look something like the one below:

```csv title="samplesheet.csv"
sample,assembly
E_coli_K12,/data/assemblies/ecoli_k12_mg1655.fasta
S_aureus_MRSA,/data/assemblies/saureus_mrsa252.fasta
P_aeruginosa_PAO1,/data/assemblies/paeruginosa_pao1.fna
B_subtilis_168,/data/assemblies/bsubtilis_168.fasta
```

An [example samplesheet](../assets/samplesheet.csv) has been provided with the pipeline.

## Running the pipeline

The typical command for running the pipeline is as follows:

```bash
nextflow run barbarahelena/surfaceproteins --input ./samplesheet.csv --outdir ./results -profile docker
```

This will launch the pipeline with the `docker` configuration profile. See below for more information about profiles.

Note that the pipeline will create the following files in your working directory:

```bash
work                # Directory containing the nextflow working files
<OUTDIR>            # Finished results in specified location (defined with --outdir)
.nextflow_log       # Log file from Nextflow
# Other nextflow hidden files, eg. history of pipeline runs and old logs.
```

### Pipeline parameters

The pipeline includes several optional parameters that can be used to customize the analysis:

- `--bakta_db`: Path to Bakta database (if not provided, the pipeline will download it)
- `--skip_bakta`: Skip Bakta annotation step

Example with custom parameters:

```bash
nextflow run barbarahelena/surfaceproteins \
  --input ./samplesheet.csv \
  --outdir results \
  -profile docker
```

If you wish to repeatedly use the same parameters for multiple runs, rather than specifying each flag in the command, you can specify these in a params file.

Pipeline settings can be provided in a `yaml` or `json` file via `-params-file <file>`.

> [!WARNING]
> Do not use `-c <file>` to specify parameters as this will result in errors. Custom config files specified with `-c` must only be used for [tuning process resource specifications](https://nf-co.re/docs/usage/configuration#tuning-workflow-resources), other infrastructural tweaks (such as output directories), or module arguments (args).

The above pipeline run specified with a params file in yaml format:

```bash
nextflow run barbarahelena/surfaceproteins -profile docker -params-file params.yaml
```

with:

```yaml title="params.yaml"
input: './samplesheet.csv'
outdir: './results/'
psortb_type: 'gram-'
signalp_model: 'gram-'
<...>
```

### Updating the pipeline

When you run the above command, Nextflow automatically pulls the pipeline code from GitHub and stores it as a cached version. When running the pipeline after this, it will always use the cached version if available - even if the pipeline has been updated since. To make sure that you're running the latest version of the pipeline, make sure that you regularly update the cached version of the pipeline:

```bash
nextflow pull barbarahelena/surfaceproteins
```

### Reproducibility

It is a good idea to specify the pipeline version when running the pipeline on your data. This ensures that a specific version of the pipeline code and software are used when you run your pipeline. If you keep using the same tag, you'll be running the same version of the pipeline, even if there have been changes to the code since.

First, go to the [barbarahelena/surfaceproteins releases page](https://github.com/barbarahelena/surfaceproteins/releases) and find the latest pipeline version - numeric only (eg. `1.3.1`). Then specify this when running the pipeline with `-r` (one hyphen) - eg. `-r 1.3.1`. Of course, you can switch to another version by changing the number after the `-r` flag.

This version number will be logged in reports when you run the pipeline, so that you'll know what you used when you look back in the future. For example, at the bottom of the MultiQC reports.

To further assist in reproducibility, you can use share and reuse [parameter files](#running-the-pipeline) to repeat pipeline runs with the same settings without having to write out a command with every single parameter.

## Core Nextflow arguments

> [!NOTE]
> These options are part of Nextflow and use a _single_ hyphen (pipeline parameters use a double-hyphen)

### `-profile`

Use this parameter to choose a configuration profile. Profiles can give configuration presets for different compute environments. Several generic profiles are bundled with the pipeline which instruct the pipeline to use software packaged using different methods (Docker, Singularity, Podman, Shifter, Charliecloud, Apptainer, Conda) - see below.

- `test`
  - A profile with a complete configuration for automated testing
  - Includes links to test data so needs no other parameters
- `docker`
  - A generic configuration profile to be used with [Docker](https://docker.com/)
- `singularity`
  - A generic configuration profile to be used with [Singularity](https://sylabs.io/docs/)
- `apptainer`
  - A generic configuration profile to be used with [Apptainer](https://apptainer.org/)

> [!IMPORTANT]
> Note that this pipeline cannot be run with the `conda` profile, as not all tools had available conda packages.

The pipeline also dynamically loads configurations from [https://github.com/nf-core/configs](https://github.com/nf-core/configs) when it runs, making multiple config profiles for various institutional clusters available at run time. For more information and to check if your system is supported, please see the [nf-core/configs documentation](https://github.com/nf-core/configs#documentation).

If `-profile` is not specified, the pipeline will run locally and expect all software to be installed and available on the `PATH`. This is _not_ recommended, since it can lead to different results on different machines dependent on the computer environment.

### `-resume`

Specify this when restarting a pipeline. Nextflow will use cached results from any pipeline steps where the inputs are the same, continuing from where it got to previously. For input to be considered the same, not only the names must be identical but the files' contents as well. For more info about this parameter, see [this blog post](https://www.nextflow.io/blog/2019/demystifying-nextflow-resume.html).

You can also supply a run name to resume a specific run: `-resume [run-name]`. Use the `nextflow log` command to show previous run names.


## Nextflow memory requirements

In some cases, the Nextflow Java virtual machines can start to request a large amount of memory.
We recommend adding the following line to your environment to limit this (typically in `~/.bashrc` or `~./bash_profile`):

```bash
NXF_OPTS='-Xms1g -Xmx4g'
```