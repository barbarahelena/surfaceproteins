process PREDICT_LOCALIZATION {
    tag "predict_localization"

    conda "conda-forge::pandas=1.4.3"
    container { workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/pandas:1.4.3' :
        'biocontainers/pandas:1.4.3' }

    input:
    path mergedtable

    output:
    path "localization.csv"        , emit: csv
    path "localization_full.csv"   , emit: full_csv
    path "localization_report.html", emit: report
    path "versions.yml"            , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    template 'predict_localization.py'

    stub:
    """
    touch localization.csv localization_full.csv localization_report.html

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
        pandas: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('pandas').version)")
    END_VERSIONS
    """
}
