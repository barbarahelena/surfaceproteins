process PSORTB_PSORTB {
    tag "$faa"

    conda ""
    container 'docker://barbarahelena/psortb:1.1'

    input:
    tuple val(meta), path(faa)

    output:
    tuple val(meta), path("*_psortb.txt")   , emit: txt
    path "versions.yml"                     , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    prefix = task.ext.prefix ?: faa.baseName
    mode     = meta.gram == "gram-positive" ? "--positive" : "--negative"
    """
    simplify_headers.sh ${faa} ${faa.baseName}_simplified.faa
    psortb ${mode} -v --seq ${faa.baseName}_simplified.faa --outdir output_${faa.baseName}

    mv output_${faa.baseName}/*_psortb_*.txt ${prefix}_psortb.txt
    rm -rf output_${faa.baseName}
    
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        PSORTb: \$(psortb --version 2>&1 | grep -oP 'PSORTb version \\K[0-9.]+')
    END_VERSIONS
    """

    stub:
    prefix = task.ext.prefix ?: faa.baseName
    """
    touch ${prefix}_psortb.txt
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        PSORTb: \$(/usr/local/psortb/bin/psort --version 2>&1 | grep -oP 'PSORTb version \\K[0-9.]+')
    END_VERSIONS
    """
}
