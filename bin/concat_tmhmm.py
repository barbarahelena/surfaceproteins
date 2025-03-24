#!/usr/bin/env python

import pandas as pd
import sys

def merge_files(meta_id, tax_id, output_filename, input_files):
    df_list = []

    # Process each input file
    for input_file in input_files:
        df = pd.read_csv(input_file, sep="\t", dtype=str)  # Read without skipping the header
        df.insert(0, 'meta_id', meta_id)
        df.insert(1, 'tax_id', tax_id)
        df_list.append(df)

    # Concatenate all dataframes, ensuring columns align
    merged_df = pd.concat(df_list, ignore_index=True)

    # Save the merged file with headers
    merged_df.to_csv(output_filename, index=False, sep="\t")
    print(f"Merged file saved as {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python merge_files.py <meta_id> <tax_id> <output_filename> <input_files>", file=sys.stderr)
        sys.exit(1)

    meta_id = sys.argv[1]
    tax_id = sys.argv[2]
    output_filename = sys.argv[3]
    input_files = sys.argv[4:]

    merge_files(meta_id, tax_id, output_filename, input_files)
