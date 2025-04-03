#!/usr/bin/env python3

import os
import sys
import glob
import pandas as pd
import re
import argparse

def analyze_topology(topology):
    """Analyze topology string and extract key metrics"""
    # Count occurrences of each topology element
    boct_inner_loop = topology.count('I')
    boct_outer_loop = topology.count('O')
    boct_pore_facing = topology.count('i')
    boct_lipid_facing = topology.count('o')
    
    boct_total_length = len(topology)
    
    # Calculate proportions
    boct_inner_loop_prop = boct_inner_loop / boct_total_length if boct_total_length > 0 else 0
    boct_outer_loop_prop = boct_outer_loop / boct_total_length if boct_total_length > 0 else 0
    boct_pore_facing_prop = boct_pore_facing / boct_total_length if boct_total_length > 0 else 0
    boct_lipid_facing_prop = boct_lipid_facing / boct_total_length if boct_total_length > 0 else 0
    
    # Find transmembrane segments (runs of 'i' and 'o')
    tm_segments = re.findall(r'[io]+', topology)
    
    # Count alternating i/o patterns which indicate beta strands
    boct_beta_strands = 0
    for segment in tm_segments:
        if len(segment) >= 5:  # Typical beta strand is at least 5 residues
            alternating = sum(1 for i in range(len(segment) - 1) if segment[i] != segment[i + 1])
            if alternating >= len(segment) * 0.6:  # Allow some imperfections
                boct_beta_strands += 1
    
    # Beta-barrel proteins typically have 8-22 beta strands
    boct_is_beta_barrel = boct_beta_strands >= 8
    
    return {
        'boct_inner_count': boct_inner_loop,
        'boct_outer_count': boct_outer_loop,
        'boct_pore_facing_count': boct_pore_facing,
        'boct_lipid_facing_count': boct_lipid_facing,
        'boct_inner_prop': round(boct_inner_loop_prop, 3),
        'boct_outer_prop': round(boct_outer_loop_prop, 3),
        'boct_pore_facing_prop': round(boct_pore_facing_prop, 3),
        'boct_lipid_facing_prop': round(boct_lipid_facing_prop, 3),
        'boct_membrane_residues': boct_pore_facing + boct_lipid_facing,
        'boct_membrane_prop': round((boct_pore_facing + boct_lipid_facing) / boct_total_length, 3) if boct_total_length > 0 else 0,
        'boct_beta_strands': boct_beta_strands,
        'boct_is_beta_barrel': boct_is_beta_barrel,
        'boct_topology_summary': f"Inner: {boct_inner_loop_prop:.2f}, Outer: {boct_outer_loop_prop:.2f}, Membrane: {(boct_pore_facing_prop + boct_lipid_facing_prop):.2f}, Strands: {boct_beta_strands}"
    }

def merge_boctopus_files(input_files, output_file):
    """Merge multiple BOCTOPUS2 output files and add topology analysis"""
    all_proteins = []
    file_count = 0
    
    print(f"Processing {len(input_files)} input files...")
    
    for file_path in input_files:
        try:
            print(f"Processing file: {file_path}")  # Debugging statement
            
            # Skip empty files
            if os.path.getsize(file_path) == 0:
                print(f"Skipping empty file: {file_path}")
                continue
            
            # Read the BOCTOPUS2 output file into a DataFrame
            try:
                df = pd.read_csv(file_path, sep='\t')
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue
            
            # Check if the DataFrame is empty or missing required columns
            if df.empty or not all(col in df.columns for col in ['protein_id', 'protein_name', 'protein_topology']):
                print(f"Skipping {file_path} due to missing data or incorrect format.")
                print(f"Columns in file: {df.columns}")  # Debugging statement
                continue
            
            print(f"Number of rows in file {file_path}: {len(df)}")  # Debugging statement
            
            # Analyze each protein's topology
            for _, row in df.iterrows():
                protein_id = row['protein_id']
                protein_name = row['protein_name']
                topology = row['protein_topology']
                
                # Skip proteins with no topology data
                if not isinstance(topology, str) or len(topology) == 0:
                    continue
                
                # Analyze the topology
                metrics = analyze_topology(topology)
                
                # Append the metrics to the list, including the protein_id and protein_name
                all_proteins.append({
                    'protein_id': protein_id,
                    'protein_name': protein_name,
                    'boct_inner_count': metrics['boct_inner_count'],
                    'boct_outer_count': metrics['boct_outer_count'],
                    'boct_pore_facing_count': metrics['boct_pore_facing_count'],
                    'boct_lipid_facing_count': metrics['boct_lipid_facing_count'],
                    'boct_inner_prop': metrics['boct_inner_prop'],
                    'boct_outer_prop': metrics['boct_outer_prop'],
                    'boct_pore_facing_prop': metrics['boct_pore_facing_prop'],
                    'boct_lipid_facing_prop': metrics['boct_lipid_facing_prop'],
                    'boct_membrane_residues': metrics['boct_membrane_residues'],
                    'boct_membrane_prop': metrics['boct_membrane_prop'],
                    'boct_beta_strands': metrics['boct_beta_strands'],
                    'boct_is_beta_barrel': metrics['boct_is_beta_barrel'],
                    'boct_topology_summary': metrics['boct_topology_summary']
                })
            
            file_count += 1
        
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    # Check if any proteins were processed
    if not all_proteins:
        print("No valid proteins found to process.")
        return
    
    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(all_proteins)
    
    # Remove duplicates based on 'protein_id'
    df = df.drop_duplicates(subset=['protein_id'], keep='first')
    
    # Save the merged data to the output file
    df.to_csv(output_file, index=False)
    print(f"Successfully processed {file_count} files. Output saved to {output_file}.")

def main():
    """Main function to handle command-line arguments"""
    parser = argparse.ArgumentParser(description="Merge BOCTOPUS2 output files and add topology analysis")
    parser.add_argument("output_file", help="Path to the output CSV file")
    parser.add_argument("input_files_str", help="Paths to the input BOCTOPUS2 output files (space-separated)")
    
    args = parser.parse_args()
    
    input_files_str = args.input_files_str
    input_files = input_files_str.split()  # Split the string into a list
    output_file = args.output_file
    
    merge_boctopus_files(input_files, output_file)

if __name__ == "__main__":
    main()