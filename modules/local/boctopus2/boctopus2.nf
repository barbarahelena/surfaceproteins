process BOCTOPUS2_BOCTOPUS2 {
    tag "$faa"

    conda ""
    container 'docker://barbarahelena/boctopus2:1.3'

    input:
    tuple val(meta), path(faa)
    path database

    output:
    tuple val(meta), path("${faa.baseName}_protein_topology_results.tsv") , emit: txt
    path "versions.yml"                                                   , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    mkdir -p matplotlib
    export MPLCONFIGDIR="\$PWD/matplotlib"

    mkdir -p \$PWD/tempfiles_${faa.baseName}
    export TMPDIR="\$PWD/tempfiles_${faa.baseName}"
    echo "Using temp dir: \$PWD/tempfiles"

    REAL_PATH=\$(readlink -f ${database})
    export HHBLITS_DB_PATH="\$REAL_PATH/uniprot20_2013_03"
    echo "Using HHBLITS_DB_PATH: \$HHBLITS_DB_PATH"
    
    python /app/boctopus2/boctopus_main.py ${faa} ${faa.baseName}

    # Base directory
    BASE_DIR="${faa.baseName}"
    OUTPUT_FILE="${faa.baseName}_protein_topology_results.tsv"

    # Write header to output file
    echo -e "protein_id\tprotein_name\tprotein_topology" > "\$OUTPUT_FILE"

    # Find all query_topologies.txt files
    find "\$BASE_DIR" -name "query_topologies.txt" | while read topology_file; do
        dir=\$(dirname "\$topology_file")
        fa_file="\$dir/query.fa"
        
        # Check if query.fa exists
        if [ -f "\$fa_file" ]; then
           seq_folder=\$(basename "\$dir")
            # Map seq_X back to original protein ID - assuming original ID is in the FASTA header
            protein_id=\$(grep "^>" "\$fa_file" | head -1 | sed 's/^>//' | awk '{print \$1}')
            protein_name=\$(grep "^>" "\$fa_file" | head -1 | sed 's/^>//' | sed 's/[^ ]* //')
            protein_topology=\$(sed -n '2p' "\$topology_file")
            
            # Write to output file
            echo -e "\$protein_id\t\$protein_name\t\$protein_topology" >> "\$OUTPUT_FILE"
        fi
    done
    echo "Results written to \$OUTPUT_FILE"
    
    rm -rf ${faa.baseName}
    rm -rf tmpfiles_${faa.baseName}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        BOCTOPUS: v2.0
    END_VERSIONS
    """

    stub:
    """
    mkdir ${faa.baseName}
    OUTPUT_FILE="${faa.baseName}_protein_topology_results.tsv"

    # Write header to output file
    echo -e "protein_id\tprotein_name\tprotein_topology" > "\$OUTPUT_FILE"

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        BOCTOPUS: v2.0
    END_VERSIONS
    """
}
