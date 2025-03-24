process MERGE_TABLES {
    tag "$meta.id"

    conda "bioconda::r-dplyr bioconda::r-tidyr bioconda::r-forcats"
    container "docker://barbarahelena/phylomodule:1.6"

    input:
    tuple val(meta), path(signalp), path(tmhmm), path(psortb), path(phobius), path(boctopus)

    output:
    tuple val(meta), path('*.csv'), emit: mergedtable

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    #!/usr/bin/env Rscript
    library(dplyr)
    library(stringr)

    phob <- read.table("${phobius}", sep = "", fill = TRUE, header = FALSE, skip = 1)
    colnames(phob) <- c("protein_id", "phob_TM", "phob_SP", "phob_prediction")

    psort <- read.csv("${psortb}", sep = "\\t")
    colnames(psort) <- c("protein_id", "psort_prediction", "psort_score", "psort_secondaryloc")

    sign <- read.csv("${signalp}", sep = "\\t")
    sign <- sign %>% mutate(protein_id = word(X..ID, 1), protein_name = str_remove(X..ID, str_c(protein_id, " ")))
    colnames(sign) <- c("meta_id", "tax_id", "protein_full", "sign_prediction", "sign_other", "sign_sp_spI", "sign_lipo_spII",
                        "sign_tat_spI", "sign_tatlipo_spII", "sign_pilin_spIII", "sign_cspos", "protein_id", "protein_name")

    tmhmm <- read.csv("${tmhmm}", sep = "\\t", skip = 1, header = FALSE)
    colnames(tmhmm) <- c("meta_id", "tax_id", "protein_id", "protein_name", "tmhmm_inside_count", "tmhmm_outside_count",
                        "tmhmm_membrane_count", "tmhmm_inside_prop", "tmhmm_outside_prop", "tmhmm_membrane_prop",
                        "topology_summary", "PredHel", "TM_60")

    # Only add psortb if there is output
    if(nrow(psort) > 0){
        tot <- left_join(sign, tmhmm) %>% left_join(., phob) %>% left_join(., psort)
    } else{
        tot <- left_join(sign, tmhmm) %>% left_join(., phob)
    }

    # Check if BOCTOPUS2 results exist
    has_boctopus <- file.exists("${boctopus}") && file.size("${boctopus}") > 0
    # Use BOCTOPUS2 results only if they exist
    if (has_boctopus) {
        # Process with BOCTOPUS2 data
    } else {
        # Process without BOCTOPUS2 data
    }
    
    write.csv(tot, file = "${meta.id}_mergedtable.csv")
    """

    stub:
    """
    touch ${meta.id}_mergedtable.csv
    """
}
