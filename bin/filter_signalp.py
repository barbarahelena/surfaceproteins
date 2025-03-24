#!/usr/bin/env python

import pandas as pd
import sys
import os

def filter_proteins(input_filename):
    # Read the CSV file
    df = pd.read_csv(input_filename, sep="\t")

    # Filter the dataframe to exclude proteins labeled as OTHER in the Prediction column
    filtered_df = df[df['Prediction'] != 'OTHER']

    # Create the output filename
    base, ext = os.path.splitext(input_filename)
    output_filename = f"{base}_filtered{ext}"

    # Save the filtered dataframe to a new CSV file
    filtered_df.to_csv(output_filename, index=False, sep="\t")
    print(f"Filtered file saved as {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python filter_signalp.py <input_filename>", file=sys.stderr)
        sys.exit(1)

    input_filename = sys.argv[1]
    filter_proteins(input_filename)