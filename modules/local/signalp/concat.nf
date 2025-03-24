process SIGNALP_CONCAT {
    tag "$meta.id"

    conda "conda-forge::pandas=1.4.3"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/pandas:1.4.3' :
        'biocontainers/pandas:1.4.3' }"

    input:
    tuple val(meta), path(outputtxt)

    output:
    tuple val(meta), path("*_signalp.csv") , emit: csv
    tuple val(meta), path("*_filtered.csv"), emit: filteredresults
    path "versions.yml"                    , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    outputname   = task.ext.prefix ? "${task.ext.prefix}.csv": "${meta.id}_signalp.csv"
    """
    concat_signalp.py "${meta.id}" "${meta.tax}" ${outputname} ${outputtxt}

    filter_signalp.py ${outputname}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
        pandas: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('pandas').version)")
    END_VERSIONS
    """

    stub:
    outputname   = task.ext.prefix ? "${task.ext.prefix}.csv": "${meta.id}_signalp.csv"
    """
    touch ${outputname}
    
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
        pandas: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('pandas').version)")
    END_VERSIONS
    """
}
