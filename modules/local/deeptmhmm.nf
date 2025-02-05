process DEEPTMHMM {
    tag "$meta.id"

    conda "bioconda::biolib=pybiolib:1.2.347"
    container 'docker://barbarahelena/pybiolib:1.2.347'

    input:
    tuple val(meta), path(fasta), path(faa), path(gff)

    output:
    path "versions.yml"                                 , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    prefix   = task.ext.prefix ?: "${meta.id}"
    """
    biolib run DTU/DeepTMHMM:1.0.24 --input $fasta

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        biolib: 0.1.9
    END_VERSIONS
    """

    stub:
    prefix = task.ext.prefix ?: "${meta.id}"
    """

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        biolib: 0.1.9
    END_VERSIONS
    """
}
