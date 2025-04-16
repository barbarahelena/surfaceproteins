/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { MULTIQC                } from '../modules/nf-core/multiqc/main'
include { BAKTA_BAKTADBDOWNLOAD  } from '../modules/nf-core/bakta/baktadbdownload/main.nf'
include { BAKTA_BAKTA            } from '../modules/nf-core/bakta/bakta/main.nf'
include { PROKKA                 } from '../modules/local/prokka/main'
include { SPLIT_PROTEINS         } from '../modules/local/splitproteins'
include { TMHMM_TMHMM            } from '../modules/local/tmhmm/tmhmm'
include { PARSE_TMHMM            } from '../modules/local/tmhmm/parse'
include { CONCAT_TMHMM           } from '../modules/local/tmhmm/concat'
include { PHOBIUS                } from '../modules/local/phobius'
include { SIGNALP_SIGNALP        } from '../modules/local/signalp/signalp'
include { SIGNALP_CONCAT         } from '../modules/local/signalp/concat'
include { PSORTB_PSORTB          } from '../modules/local/psortb/psortb'
include { PSORTB_PARSE           } from '../modules/local/psortb/parse'
include { MERGE_TABLES           } from '../modules/local/mergetables'
include { BOCTOPUS2_SPLIT        } from '../modules/local/boctopus2/split.nf'
include { BOCTOPUS2_SELECT       } from '../modules/local/boctopus2/select.nf'
include { BOCTOPUS2_BOCTOPUS2    } from '../modules/local/boctopus2/boctopus2'
include { BOCTOPUS2_PARSE        } from '../modules/local/boctopus2/parse.nf'
include { paramsSummaryMap       } from 'plugin/nf-schema'
include { paramsSummaryMultiqc   } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { softwareVersionsToYAML } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { methodsDescriptionText } from '../subworkflows/local/utils_nfcore_surfaceproteins_pipeline'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow SURFACEPROTEINS {

    take:
    ch_samplesheet // channel: samplesheet read in from --input
    annotation

    main:

    ch_versions = Channel.empty()
    ch_multiqc_files = Channel.empty()
    bakta_db = params.bakta_database ? Channel.fromPath( params.bakta_database ).first() : []
    boctopus_db = params.boctopus_database ? Channel.fromPath( params.boctopus_database ).first() : []

    //
    // Bakta
    //
    if ( annotation ) {
        if ( ! bakta_db ){
            BAKTA_BAKTADBDOWNLOAD()
            bakta_db = BAKTA_BAKTADBDOWNLOAD.out.db
        }         
        BAKTA_BAKTA( 
            ch_samplesheet, 
            bakta_db,
            [],
            []
        )
        ch_annotation = BAKTA_BAKTA.out.fna
                .join(BAKTA_BAKTA.out.faa)
                .join(BAKTA_BAKTA.out.gff)
        ch_versions = ch_versions.mix( BAKTA_BAKTA.out.versions )
    }

    SPLIT_PROTEINS( ch_annotation )

    SPLIT_PROTEINS.out.split_proteins
        .transpose() // This splits the tuple into individual elements
        .set { individual_split_proteins }

    //
    // TMHMM
    //
    TMHMM_TMHMM( individual_split_proteins )
    ch_versions = ch_versions.mix( TMHMM_TMHMM.out.versions )
    ch_tmhmm_results = TMHMM_TMHMM.out.catanno.join(TMHMM_TMHMM.out.catsummary)
    
    PARSE_TMHMM( ch_tmhmm_results )
    ch_versions = ch_versions.mix( PARSE_TMHMM.out.versions )
    ch_tmhmm = PARSE_TMHMM.out.csv.groupTuple(by: 0)
    
    CONCAT_TMHMM( ch_tmhmm )
    ch_versions = ch_versions.mix( CONCAT_TMHMM.out.versions )

    //
    // Phobius
    //
    PHOBIUS( ch_annotation )
    ch_versions = ch_versions.mix( PHOBIUS.out.versions )

    //
    // SignalP
    //
    SIGNALP_SIGNALP( individual_split_proteins )
    ch_versions = ch_versions.mix( SIGNALP_SIGNALP.out.versions )
    ch_output_signalp = SIGNALP_SIGNALP.out.outputtxt.groupTuple(by: 0)

    SIGNALP_CONCAT( ch_output_signalp )
    ch_versions = ch_versions.mix( SIGNALP_CONCAT.out.versions )

    //
    // PSORTB
    //
    PSORTB_PSORTB( ch_annotation )
    ch_versions = ch_versions.mix( PSORTB_PSORTB.out.versions )

    PSORTB_PARSE( PSORTB_PSORTB.out.txt )
    ch_versions = ch_versions.mix( PSORTB_PARSE.out.versions )

    // 
    // BOCTOPUS2 - Only run on Gram negative samples
    //
    ch_boctopus = ch_annotation.join(PHOBIUS.out.txt, by: [0])

    // Split into Gram-negative and Gram-positive channels
    ch_boctopus_gram_neg = ch_boctopus.branch {
        gram_neg: it[0].gram == 'gram-negative'
        gram_pos: true  // all others
    }

    // Process only Gram-negative samples
    BOCTOPUS2_SELECT(ch_boctopus_gram_neg.gram_neg)
    BOCTOPUS2_SPLIT(BOCTOPUS2_SELECT.out.proteins)

    BOCTOPUS2_SPLIT.out.split_proteins
        .transpose() // This splits the tuple into individual elements
        .set { ch_boctopus_split }
    BOCTOPUS2_BOCTOPUS2(ch_boctopus_split, boctopus_db)

    ch_output_boctopus = BOCTOPUS2_BOCTOPUS2.out.txt.groupTuple(by: 0)
    BOCTOPUS2_PARSE( ch_output_boctopus )

    // Create empty results for Gram-positive samples
    ch_boctopus_empty = ch_boctopus_gram_neg.gram_pos.map { meta, fna, faa, gff, phobius -> 
        def prefix = meta.id
        return [meta, file("${workDir}/empty_${prefix}_boctopus.tsv")]
    }

    // Combine results for downstream processing
    ch_boctopus_results = BOCTOPUS2_PARSE.out.merged.mix(ch_boctopus_empty)

    //
    // MERGE_TABLES
    //
    ch_output = SIGNALP_CONCAT.out.csv
        .join(CONCAT_TMHMM.out.csv, by: [0])
        .join(PSORTB_PARSE.out.csv, by: [0])
        .join(PHOBIUS.out.txt, by: [0])
        .join(ch_boctopus_results, by: [0])

    MERGE_TABLES( ch_output )

    //
    // Collate and save software versions
    //
    softwareVersionsToYAML(ch_versions)
        .collectFile(
            storeDir: "${params.outdir}/pipeline_info",
            name: 'nf_core_'  +  'surfaceproteins_software_'  + 'mqc_'  + 'versions.yml',
            sort: true,
            newLine: true
        ).set { ch_collated_versions }


    //
    // MODULE: MultiQC
    //
    ch_multiqc_config        = Channel.fromPath(
        "$projectDir/assets/multiqc_config.yml", checkIfExists: true)
    ch_multiqc_custom_config = params.multiqc_config ?
        Channel.fromPath(params.multiqc_config, checkIfExists: true) :
        Channel.empty()
    ch_multiqc_logo          = params.multiqc_logo ?
        Channel.fromPath(params.multiqc_logo, checkIfExists: true) :
        Channel.empty()

    summary_params      = paramsSummaryMap(
        workflow, parameters_schema: "nextflow_schema.json")
    ch_workflow_summary = Channel.value(paramsSummaryMultiqc(summary_params))
    ch_multiqc_files = ch_multiqc_files.mix(
        ch_workflow_summary.collectFile(name: 'workflow_summary_mqc.yaml'))
    ch_multiqc_custom_methods_description = params.multiqc_methods_description ?
        file(params.multiqc_methods_description, checkIfExists: true) :
        file("$projectDir/assets/methods_description_template.yml", checkIfExists: true)
    ch_methods_description                = Channel.value(
        methodsDescriptionText(ch_multiqc_custom_methods_description))

    ch_multiqc_files = ch_multiqc_files.mix(ch_collated_versions)
    ch_multiqc_files = ch_multiqc_files.mix(
        ch_methods_description.collectFile(
            name: 'methods_description_mqc.yaml',
            sort: true
        )
    )

    MULTIQC (
        ch_multiqc_files.collect(),
        ch_multiqc_config.toList(),
        ch_multiqc_custom_config.toList(),
        ch_multiqc_logo.toList(),
        [],
        []
    )

    emit:multiqc_report = MULTIQC.out.report.toList() // channel: /path/to/multiqc_report.html
    versions       = ch_versions                 // channel: [ path(versions.yml) ]

}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
