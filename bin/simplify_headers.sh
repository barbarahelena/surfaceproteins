#!/bin/bash
# simplify_headers.sh - Simplifies FASTA headers for PSORTb testing

input_file="$1"
output_file="${2:-${input_file%.faa}_simplified.faa}"

if [ -z "$input_file" ]; then
    echo "Usage: $0 input.faa [output.faa]"
    exit 1
fi

if [ ! -f "$input_file" ]; then
    echo "Error: Input file '$input_file' not found"
    exit 1
fi

# Create temporary file in current directory
temp_file="./temp_simplified_$$.faa"
current_header=""
current_seq=""
total_count=0

echo "Simplifying FASTA headers (removing descriptions)..."

# Process the file line by line
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines
    [ -z "$line" ] && continue
    
    # If header line
    if [[ $line == ">"* ]]; then
        # Process previous sequence if exists
        if [ -n "$current_header" ] && [ -n "$current_seq" ]; then
            echo "$current_header" >> "$temp_file"
            echo "$current_seq" >> "$temp_file"
            total_count=$((total_count + 1))
        fi
        
        # Simplify header to just the ID (before first space)
        if [[ $line =~ ^">".+[[:space:]] ]]; then
            simplified_header="$(echo "$line" | cut -d ' ' -f1)"
            current_header="$simplified_header"
        else
            current_header="$line"
        fi
        current_seq=""
    else
        # Append to current sequence, preserving line breaks
        current_seq="$current_seq$line"
    fi
done < "$input_file"

# Process the last sequence
if [ -n "$current_header" ] && [ -n "$current_seq" ]; then
    echo "$current_header" >> "$temp_file"
    echo "$current_seq" >> "$temp_file"
    total_count=$((total_count + 1))
fi

# Move the temp file to output
mv "$temp_file" "$output_file"

echo "Processed $total_count sequences"
echo "Output saved to: $output_file"

# Clean up any leftover temp file (just in case)
[ -f "$temp_file" ] && rm -f "$temp_file"

exit 0