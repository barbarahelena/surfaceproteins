process SPLIT_PROTEINS {
    tag "$meta.id"

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/ubuntu:22.04' :
        'nf-core/ubuntu:22.04' }"

    input:
    tuple val(meta), path(faa)

    output:
    tuple val(meta), path('split_*.faa'), emit: split_proteins

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    awk 'BEGIN {f=""} /^>/ {n++; if (n % 250 == 1) {close(f); f="split_${prefix}_" int((n-1)/250) ".faa"}} {if(f!="") print > f}' $faa

    # Count the number of output files
    num_files=\$(ls split_*.faa | wc -l)
    echo "Generated \$num_files split fasta files"
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch split_${prefix}_0.faa
    echo "Generated 1 split fasta file"
    """
}
