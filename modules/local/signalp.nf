process SIGNALP {
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
    biolib run DTU/SignalP-6 --input $faa

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        biolib: \$(echo \$(biolib --version) 2>&1)
    END_VERSIONS
    """

    stub:
    prefix = task.ext.prefix ?: "${meta.id}"
    """

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        biolib: \$(echo \$(biolib --version) 2>&1)
    END_VERSIONS
    """
}
