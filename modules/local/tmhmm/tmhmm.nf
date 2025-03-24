process TMHMM_TMHMM {
    tag "$faa"

    conda ""
    container 'docker://barbarahelena/tmhmm:2.0'

    input:
    tuple val(meta), path(faa)

    output:
    tuple val(meta), path("*_modified.faa")  , emit: modfasta
    tuple val(meta), path("*.annotation")    , emit: anno
    tuple val(meta), path("*.summary")       , emit: summary
    tuple val(meta), path("*_cat.txt")       , emit: catanno
    tuple val(meta), path("*_summary.tsv")   , emit: catsummary
    tuple val(meta), path("filter_fasta.log"), emit: log
    path "versions.yml"                      , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    # Define allowed amino acid characters - excluding X
    allowed_chars="ACDEFGHIKLMNPQRSTWVYBZ"

    # Use awk to process the FASTA file - remove any characters not in allowed set
    awk -v allowed="\$allowed_chars" '
    BEGIN { 
        removedCount = 0; 
        totalSeqs = 0;
        totalRemoved = 0;
    }  
    /^>/ { 
        print  # Print header as-is
        totalSeqs++;
        next
    }
    {
        removed = 0
        output = ""
        orig_len = length(\$0)
        
        for (i=1; i<=orig_len; i++) {
            c = substr(\$0, i, 1)
            
            # Replace U with C (special case)
            if (c == "U") {
                printf "Replacing U with C\\n" >> "filter_fasta.log"
                output = output "C"
            }
            # Only keep characters in the allowed set
            else if (index(allowed, c) > 0) {
                output = output c
            }
            else {
                # Character removed
                removed++
                totalRemoved++
            }
        }
        
        print output
        
        # If any characters were removed, count this sequence
        if (removed > 0) {
            removedCount++
            printf "Removed %d characters from sequence %d\\n", removed, totalSeqs >> "filter_fasta.log"
        }
    }
    END {
        print "Modified " removedCount " out of " totalSeqs " sequences" > "filter_fasta.log"
        print "Total characters removed: " totalRemoved > "filter_fasta.log"
        print "Average removed per affected sequence: " (removedCount > 0 ? totalRemoved/removedCount : 0) > "filter_fasta.log"
    }
    ' "${faa}" > "${faa.baseName}_modified.faa"

    echo 'Now we run tmhmm..'
    # Run TMHMM on the modified FASTA file
    tmhmm -f ${faa.baseName}_modified.faa -m ${projectDir}/assets/TMHMM2.0.model
    
    # Combine all .annotation files into one output
    echo '..concatenate the annotation files..'
    cat *.annotation > ${faa.baseName}_cat.txt

    # Combine summary files into a tidy table (done here because reasonably fast)
    echo '..parse the summary files..'
    echo "DEBUG: Creating summary file: ${faa.baseName}_summary.tsv"
    echo -e "protein_ID\tPredHel\tTM_60" > "${faa.baseName}_summary.tsv"
    
    for file in *.summary; do
        echo "DEBUG: Processing file: \$file"
        echo "DEBUG: File contents:"
        cat "\$file"
        
        protein_id=\$(basename "\$file" .summary)
        echo "DEBUG: Protein ID: \$protein_id"
        
        # Count transmembrane helices
        pred_hel=\$(awk '/transmembrane helix/ {count++} END {print count+0}' "\$file")
        echo "DEBUG: Found \$pred_hel transmembrane helices"
        
        echo "DEBUG: Calculating TM_60 for \$file"
        tm_60=\$(awk '
            BEGIN {s=0}
            \$3 == "transmembrane" && \$4 == "helix" {
                start = \$1
                end = \$2
                if (start < 60) {
                    end = (end < 60 ? end : 60)
                    len = end - start + 1
                    s += len
                }
            }
            END {
                print s+0
            }
        ' "\$file")
        echo "DEBUG: TM_60 value: \$tm_60"
        
        # Handle case where no transmembrane regions found
        if [ -z "\$tm_60" ]; then
            tm_60=0
            echo "DEBUG: No TM regions found, setting TM_60 to 0"
        fi
        
        echo -e "\$protein_id\t\$pred_hel\t\$tm_60" >> "${faa.baseName}_summary.tsv"
        echo "DEBUG: Added entry to summary file"
    done

    # Debug: Show final summary file content
    echo "DEBUG: Final summary file contents:"
    cat "${faa.baseName}_summary.tsv"

    # In the parsing script, the annotation and summary tables get merged after calculating some more metrics

    echo 'Finished process!'

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        biolib: 0.1.9
    END_VERSIONS
    """

    stub:
    """
    touch ${faa.baseName}_modified.faa
    touch ${faa.baseName}.annotation
    touch ${faa.baseName}.summary
    touch ${faa.baseName}_cat.txt
    touch ${faa.baseName}_summary.tsv
    touch filter_fasta.log

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        biolib: 0.1.9
    END_VERSIONS
    """
}