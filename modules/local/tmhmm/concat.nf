process CONCAT_TMHMM {
    tag "$meta.id"

    conda "conda-forge::pandas=1.4.3"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/pandas:1.4.3' :
        'biocontainers/pandas:1.4.3' }"

    input:
    tuple val(meta), path(anno)

    output:
    tuple val(meta), path("*_concat.csv")                , emit: csv
    path "versions.yml"                                  , emit: versions

    when:
    task.ext.when == null || task.ext.when
    outputname = "tmhmm_${meta.id}_concat.csv"

    script:
    """
    concat_tmhmm.py "${meta.id}" "${meta.tax}" "${outputname}" ${anno}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
        pandas: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('pandas').version)")
    END_VERSIONS
    """

    stub:
    """

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
        pandas: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('pandas').version)")
    END_VERSIONS
    """
}
