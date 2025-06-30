process PHOBIUS {
    tag "$faa"

    conda ""
    container 'docker://barbarahelena/phobius:1.01'

    input:
    tuple val(meta), path(faa)

    output:
    tuple val(meta), path("*_summary.txt")   , emit: txt
    tuple val(meta), path("*_long.txt")      , emit: txtlong
    path "versions.yml"                      , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    prefix   = task.ext.prefix ?: "${faa.baseName}"
    """
    phobius ${faa} -short > ${prefix}_summary.txt
    phobius ${faa} -long > ${prefix}_long.txt

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        phobius: \$(phobius --help 2>&1 | grep -oP 'Phobius ver \\K[0-9.]+')
    END_VERSIONS
    """

    stub:
    prefix = task.ext.prefix ?: "${meta.id}"
    """

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        phobius: \$(phobius --help 2>&1 | grep -oP 'Phobius ver \\K[0-9.]+')
    END_VERSIONS
    """
}