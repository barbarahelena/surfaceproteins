#!/usr/bin/env python3

import os
import sys
import glob
import pandas as pd
import re

def analyze_topology(topology):
    """Analyze topology string and extract key metrics"""
    # Count occurrences of each topology element
    inner_loop = topology.count('I')
    outer_loop = topology.count('O')
    pore_facing = topology.count('i')
    lipid_facing = topology.count('o')
    
    total_length = len(topology)
    
    # Calculate proportions
    inner_loop_prop = inner_loop / total_length if total_length > 0 else 0
    outer_loop_prop = outer_loop / total_length if total_length > 0 else 0
    pore_facing_prop = pore_facing / total_length if total_length > 0 else 0
    lipid_facing_prop = lipid_facing / total_length if total_length > 0 else 0
    
    # Find transmembrane segments (runs of 'i' and 'o')
    tm_segments = re.findall(r'[io]+', topology)
    
    # Count alternating i/o patterns which indicate beta strands
    beta_strands = 0
    for segment in tm_segments:
        if len(segment) >= 5:  # Typical beta strand is at least 5 residues
            # Check for alternating pattern
            alternating = sum(1 for i in range(len(segment)-1) if segment[i] != segment[i+1])
            if alternating >= len(segment) * 0.6:  # Allow some imperfections
                beta_strands += 1
    
    # Beta-barrel proteins typically have 8-22 beta strands
    is_beta_barrel = beta_strands >= 8
    
    return {
        'inner_count': inner_loop,
        'outer_count': outer_loop,
        'pore_facing_count': pore_facing,
        'lipid_facing_count': lipid_facing,
        'inner_prop': round(inner_loop_prop, 3),
        'outer_prop': round(outer_loop_prop, 3),
        'pore_facing_prop': round(pore_facing_prop, 3),
        'lipid_facing_prop': round(lipid_facing_prop, 3),
        'membrane_residues': pore_facing + lipid_facing,
        'membrane_prop': round((pore_facing + lipid_facing) / total_length, 3) if total_length > 0 else 0,
        'beta_strands': beta_strands,
        'is_beta_barrel': is_beta_barrel,
        'topology_summary': f"Inner: {inner_loop_prop:.2f}, Outer: {outer_loop_prop:.2f}, Membrane: {(pore_facing_prop + lipid_facing_prop):.2f}, Strands: {beta_strands}"
    }

def merge_boctopus_files(input_files, output_file):
    """Merge multiple BOCTOPUS2 output files and add topology analysis"""
    all_proteins = []
    file_count = 0
    
    print(f"Processing {len(input_files)} input files...")
    
    for file_path in input_files:
        try:
            # Skip empty files
            if os.path.getsize(file_path) == 0:
                print(f"Skipping empty file: {file_path}")
                continue
                
            # Read the BOCTOPUS2 output file
            df = pd.read_csv(file_path, sep='\t')
            
            # Skip files without required columns
            if 'protein_id' not in df.columns or 'protein_topology' not in df.columns:
                print(f"Warning: File {file_path} missing required columns. Skipping.")
                continue
                
            file_count += 1
            all_proteins.append(df)
            
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
    
    if file_count == 0:
        print("No valid files found to process.")
        return
        
    # Combine all data
    merged_data = pd.concat(all_proteins, ignore_index=True)
    
    # Remove duplicates
    merged_data = merged_data.drop_duplicates(subset=['protein_id'])
    
    # Analyze each protein's topology
    print(f"Analyzing topology for {len(merged_data)} proteins...")
    
    # Apply the analysis function to each topology
    results = []
    for idx, row in merged_data.iterrows():
        protein_id = row['protein_id']
        protein_name = row['protein_name']
        topology = row['protein_topology']
        
        # Skip proteins with no topology data
        if not isinstance(topology, str) or len(topology) == 0:
            continue
            
        # Analyze the topology
        metrics = analyze_topology(topology)
        
        # Create result row
        result = {
            'protein_id': protein_id,
            'protein_name': protein_name,
            'topology_length': len(topology),
            'inner_count': metrics['inner_count'],
            'outer_count': metrics['outer_count'],
            'pore_facing_count': metrics['pore_facing_count'],
            'lipid_facing_count': metrics['lipid_facing_count'],
            'inner_prop': metrics['inner_prop'],
            'outer_prop': metrics['outer_prop'],
            'pore_facing_prop': metrics['pore_facing_prop'],
            'lipid_facing_prop': metrics['lipid_facing_prop'],
            'membrane_residues': metrics['membrane_residues'],
            'membrane_prop': metrics['membrane_prop'],
            'beta_strands': metrics['beta_strands'],
            'is_beta_barrel': metrics['is_beta_barrel'],
            'topology_summary': metrics['topology_summary'],
            'protein_topology': topology
        }
        
        results.append(result)
    
    # Create the output DataFrame
    result_df = pd.DataFrame(results)
    
    # Sort by protein_id
    result_df = result_df.sort_values('protein_id')
    
    # Write to output file
    result_df.to_csv(output_file, sep='\t', index=False)
    print(f"Merged {file_count} files with {len(result_df)} unique proteins")
    print(f"Results written to: {output_file}")
    
    # Create a filtered file with only beta-barrel proteins
    beta_barrel_df = result_df[result_df['is_beta_barrel']]
    beta_barrel_output = output_file.replace('.tsv', '_beta_barrel.tsv')
    if not beta_barrel_output.endswith('.tsv'):
        beta_barrel_output += '_beta_barrel.tsv'
    beta_barrel_df.to_csv(beta_barrel_output, sep='\t', index=False)
    print(f"Identified {len(beta_barrel_df)} potential beta-barrel proteins")
    print(f"Beta-barrel proteins written to: {beta_barrel_output}")
    
    # Create a file with just protein IDs for easier downstream processing
    with open(output_file.replace('.tsv', '_ids.txt'), 'w') as id_file:
        for protein_id in result_df['protein_id']:
            id_file.write(f"{protein_id}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: ./parse_boctopus2.py <output_file> <input_file1> [input_file2] [...]")
        print("       OR")
        print("Usage: ./parse_boctopus2.py <output_file> --glob '<pattern>'")
        print("       OR")
        print("Usage: ./parse_boctopus2.py <output_file> \"space separated file list\"")
        sys.exit(1)
    
    output_file = sys.argv[1]
    
    # Check if using glob pattern
    if len(sys.argv) >= 4 and sys.argv[2] == "--glob":
        input_files = glob.glob(sys.argv[3])
        if not input_files:
            print(f"No files found matching pattern: {sys.argv[3]}")
            sys.exit(1)
    elif len(sys.argv) == 3:
        # Handle space-separated file list (like what Nextflow would expand from ${boctopus_files})
        input_files = sys.argv[2].split()
    else:
        # Handle explicit list of files
        input_files = sys.argv[2:]
    
    merge_boctopus_files(input_files, output_file)

if __name__ == "__main__":
    main()