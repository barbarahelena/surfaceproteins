process COLLATE_MERGEDTABLES {
    tag "all_samples"

    conda "conda-forge::pandas=1.4.3"
    container { workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/pandas:1.4.3' :
        'biocontainers/pandas:1.4.3' }

    input:
    path manifest
    path mergedtables

    output:
    path "all_samples_mergedtable.csv", emit: csv
    path "versions.yml"                , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    template 'collate_mergedtables.py'

    stub:
    """
    touch all_samples_mergedtable.csv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
        pandas: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('pandas').version)")
    END_VERSIONS
    """
}
