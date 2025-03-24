process SIGNALP_SIGNALP {
    tag "$faa"

    conda "bioconda::biolib=pybiolib:1.2.347"
    container 'docker://barbarahelena/signalp:6.0.1'

    input:
    tuple val(meta), path(faa)

    output:
    tuple val(meta), path("*/*_prediction_results.txt")   , emit: outputtxt
    path "versions.yml"                                   , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    format = 'txt'
    """
    basename=\$(basename "${faa}" .faa)  # Remove the file extension
    splitname="\${basename#split_}"  # Remove the 'split_' prefix
    mkdir -p \$splitname
    outputdir="\$splitname"

    signalp6 \\
        --fastafile ${faa} \\
        --output_dir \$outputdir \\
        --mode 'slow-sequential' \\
        --organism 'other' \\
        --format ${format}

    mv "\$outputdir/prediction_results.txt" "\$outputdir/\${splitname}_prediction_results.txt"

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        signalp: \$(signalp6 --version 2>&1 | grep -oP '\\K[0-9.]*' | head -n1)
    END_VERSIONS
    """

    stub:
    """
    basename=\$(basename "${faa}" .faa)  # Remove the file extension
    splitname="\${basename#split_}"  # Remove the 'split_' prefix
    mkdir -p \$splitname
    outputdir="\$splitname"
    touch "\$outputdir/\${splitname}_prediction_results.txt"

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        signalp: \$(signalp6 --version 2>&1 | grep -oP '\\K[0-9.]*' | head -n1)
    END_VERSIONS
    """
}
