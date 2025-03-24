#!/usr/bin/env python

import sys
import pandas as pd

def process_signal_peptides(meta_id, input_file):
    protein_id = None
    protein_name = None
    header_line = None
    data_lines = []

    # Read the file
    with open(input_file, 'r') as f:
        for line in f:
            if line.startswith("# Name="):
                parts = line.strip().split("=", 1)  # Ensure we only split at the first "="
                protein_info = parts[1].strip()  # Remove any leading/trailing spaces
                protein_id = protein_info.split(" ", 1)[0]  # First part is the ID
                protein_name = protein_info.split(" ", 1)[1] if " " in protein_info else ""  # Everything after the first space
            elif line.startswith("# pos"):
                header_line = line.strip().split("\t")
            elif not line.startswith("#"):
                data_lines.append(line.strip().split("\t"))

    if not header_line or not data_lines:
        print(f"Error: No valid data found in the input file: {input_file}", file=sys.stderr)
        return None

    # Convert to DataFrame
    df = pd.DataFrame(data_lines, columns=header_line, dtype=str)

    # Convert numeric columns to float
    df.iloc[:, 3:] = df.iloc[:, 3:].astype(float)

    # Count values greater than 0.50 per column (excluding first 3 columns)
    counts = (df.iloc[:, 3:] > 0.50).sum()

    # Return the result as a list
    return [meta_id, protein_id, protein_name] + list(counts), df.columns[3:].to_list()  # Explicitly convert columns to list

def process_multiple_files(meta_id, output_name, input_files):
    all_results = []
    column_names = None

    for input_file in input_files:
        result, columns = process_signal_peptides(meta_id, input_file)
        if result:
            all_results.append(result)
            if column_names is None:  # Only set column names if it's not set
                column_names = columns

    if all_results and column_names:
        # Prepare the header dynamically based on the first file's columns
        header = ["meta_id", "protein_id", "protein_name"] + column_names
        result_df = pd.DataFrame(all_results, columns=header)
        output_filename = output_name + '.csv'
        result_df.to_csv(output_filename, index=False)
        print(f"Processed {len(input_files)} files and saved the results to csv.")
    else:
        print("Error: No valid results or column names found.", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_signalp.py <meta_id> <file1.txt> <file2.txt> ...", file=sys.stderr)
        sys.exit(1)

    meta_id = sys.argv[1]
    output_name = sys.argv[2]
    input_files = sys.argv[3:]

    process_multiple_files(meta_id, output_name, input_files)
