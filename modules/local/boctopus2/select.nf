process BOCTOPUS2_SELECT {
    tag "$meta.id"

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/ubuntu:22.04' :
        'nf-core/ubuntu:22.04' }"

    input:
    tuple val(meta), path(fasta), path(faa), path(gff), path(phobius)

    output:
    tuple val(meta), path("*_tm_proteins.faa"), emit: proteins

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    # Extract protein IDs where TM > 0 directly from Phobius output
    # Skip the header line and print protein ID if TM column is > 0
    awk 'NR>1 && \$2 ~ /^[1-9][0-9]*\$/ {print \$1}' "${phobius}" > tm_proteins.txt

    # Filter the FASTA file to keep only selected proteins
    awk '
    BEGIN {
        # Read proteins to keep into an array
        while ((getline id < "tm_proteins.txt") > 0) {
            keep_ids[id] = 1
        }
        close("tm_proteins.txt")
        keep = 0
    }

    /^>/ {
        # Extract protein ID from FASTA header
        header = \$0
        sub(/^>/, "", header)
        sub(/ .*\$/, "", header)
        
        # Check if this protein should be kept
        if (header in keep_ids) {
            keep = 1
        } else {
            keep = 0
        }
    }

    {
        if (keep) print \$0
    }
    ' "${faa}" > "${prefix}_tm_proteins.faa"

    # Print statistics
    total=\$(grep -c "^>" "${faa}")
    selected=\$(grep -c "^>" "${prefix}_tm_proteins.faa")
    echo "Selected \$selected proteins with transmembrane helices out of \$total total proteins"
    """
    
    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}_tm_proteins.faa
    echo "Generated filtered protein fasta file"
    """
}
