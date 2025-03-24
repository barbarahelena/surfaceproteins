#!/usr/bin/env python

import pandas as pd
import sys

def merge_files(meta_id, tax_id, output_filename, input_files):
    # List to hold dataframes
    df_list = []

    # Process each input file
    for i, input_file in enumerate(input_files):
        # Read the file, skipping comment lines (lines starting with '#')
        # Read the file normally, and just skip the first line with '#'
        df = pd.read_csv(input_file, sep="\t", skiprows=1)

        # Add meta_id and tax_id columns as the first columns
        df.insert(0, 'meta_id', meta_id)
        df.insert(1, 'tax_id', tax_id)

        # Append the dataframe to the list
        df_list.append(df)

    # Concatenate all dataframes into one
    merged_df = pd.concat(df_list, ignore_index=True)

    # Write the merged dataframe to a CSV file, including the header
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