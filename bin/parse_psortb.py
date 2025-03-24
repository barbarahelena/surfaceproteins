#!/usr/bin/env python3

import re
import csv
import sys
import os

def parse_psortb(input_file):
    # Modified regex to only capture protein ID without expecting a name
    seqid_re = re.compile(r'^SeqID:\s+(\S+)')  # Capture only Protein ID
    final_prediction_header_re = re.compile(r'^\s*Final Prediction:$')  # Header
    final_prediction_re = re.compile(r'^\s*(\S+)\s+(\d+\.\d+)$')  # Prediction + Score
    secondary_localization_header_re = re.compile(r'^\s*Secondary localization\(s\):$')  # Header
    secondary_localization_re = re.compile(r'^\s*(\S+)$')  # Capture Localization

    # Determine output file name
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}_filtered.csv"

    print(f"Processing: {input_file}")
    print(f"Writing results to: {output_file}")

    # Open input and output files
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter='\t')
        writer.writerow(['Protein ID', 'Final Prediction', 'Score', 'Secondary Localization'])

        protein_id = None
        final_prediction = None
        score = None
        secondary_localization_list = []

        final_prediction_next = False  # Track when next line is Final Prediction
        secondary_localization_next = False  # Track when reading Secondary Localizations

        for line in infile:
            line = line.strip()

            # Detect SeqID (new protein entry)
            seqid_match = seqid_re.match(line)
            if seqid_match:
                # Write previous protein entry before starting new one
                if protein_id and final_prediction:
                    secondary_localization = ", ".join(secondary_localization_list) if secondary_localization_list else "N/A"
                    writer.writerow([protein_id, final_prediction, score, secondary_localization])

                # Start new protein entry
                protein_id = seqid_match.group(1)
                final_prediction = None
                score = None
                secondary_localization_list = []

                print(f"Found Protein: {protein_id}")
                continue

            # Detect Final Prediction header
            if final_prediction_header_re.match(line):
                final_prediction_next = True
                continue

            # Capture Final Prediction
            if final_prediction_next:
                final_prediction_match = final_prediction_re.match(line)
                if final_prediction_match:
                    final_prediction = final_prediction_match.group(1)
                    score = final_prediction_match.group(2)
                    print(f"  → Final Prediction: {final_prediction} (Score: {score})")
                else:
                    print(f"  Warning: No valid Final Prediction found in line: {line}")
                final_prediction_next = False
                continue

            # Detect Secondary Localization header
            if secondary_localization_header_re.match(line):
                secondary_localization_next = True
                continue

            # Capture Secondary Localizations
            if secondary_localization_next:
                secondary_localization_match = secondary_localization_re.match(line)
                if secondary_localization_match:
                    secondary_localization_list.append(secondary_localization_match.group(1))
                    continue
                else:
                    secondary_localization_next = False  # Stop if no match

        # Write last protein entry
        if protein_id and final_prediction:
            secondary_localization = ", ".join(secondary_localization_list) if secondary_localization_list else "N/A"
            writer.writerow([protein_id, final_prediction, score, secondary_localization])
        else:
            print("No valid final prediction found for the last entry.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./parse_psortb.py <input_file>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    parse_psortb(input_file)