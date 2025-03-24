#!/usr/bin/env python3
import sys
import pandas as pd

def parse_annotation(file_path):
    """Parses the TMHMM .annotation file and extracts sequence composition details."""
    data = []
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    sequence = ""
    results = {}
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('>'):
            if sequence:
                inside_count = sequence.count('i') + sequence.count('I')
                outside_count = sequence.count('o') + sequence.count('O')
                membrane_count = sequence.count('m') + sequence.count('M')
                total = inside_count + outside_count + membrane_count
                
                inside_prop = inside_count / total if total > 0 else 0
                outside_prop = outside_count / total if total > 0 else 0
                membrane_prop = membrane_count / total if total > 0 else 0
                
                results[protein_ID] = [protein_ID, protein_name, inside_count, outside_count, membrane_count, 
                                       inside_prop, outside_prop, membrane_prop]
            
            # Extract protein_ID and protein_name
            header_parts = line[1:].split(' ', 1)
            protein_ID = header_parts[0]
            protein_name = header_parts[1] if len(header_parts) > 1 else "unknown"
            
            # Prepare to collect sequence
            sequence = ""
        elif line:
            sequence += line
        
        # If end of file, process the collected sequence
        if i == len(lines) - 1 and sequence:
            inside_count = sequence.count('i') + sequence.count('I')
            outside_count = sequence.count('o') + sequence.count('O')
            membrane_count = sequence.count('m') + sequence.count('M')
            total = inside_count + outside_count + membrane_count
            
            inside_prop = inside_count / total if total > 0 else 0
            outside_prop = outside_count / total if total > 0 else 0
            membrane_prop = membrane_count / total if total > 0 else 0
            
            results[protein_ID] = [protein_ID, protein_name, inside_count, outside_count, membrane_count, 
                                   inside_prop, outside_prop, membrane_prop]
    
    return results

def parse_summary(file_path):
    """Parses the summary file and extracts PredHel and TM_60."""
    summary_data = {}
    try:
        df = pd.read_csv(file_path, sep='\t', header=None, names=["protein_ID", "PredHel", "TM_60"])
        
        # Convert columns to numeric
        df["PredHel"] = pd.to_numeric(df["PredHel"], errors='coerce').fillna(0).astype(int)
        df["TM_60"] = pd.to_numeric(df["TM_60"], errors='coerce').fillna(0).astype(int)
        
        for _, row in df.iterrows():
            protein_ID = row["protein_ID"]
            summary_data[protein_ID] = {
                "PredHel": int(row["PredHel"]),
                "TM_60": int(row["TM_60"])
            }
    except Exception as e:
        print(f"Error in parse_summary: {e}")
        # Return empty dict if file parsing failed
    
    return summary_data

def merge_results(annotation_data, summary_data, output_path):
    """Merges annotation and summary data and writes to a TSV file."""
    df = pd.DataFrame(annotation_data.values(), columns=["protein_ID", "protein_name", "inside_count", "outside_count", 
                                                         "membrane_count", "inside_prop", "outside_prop", "membrane_prop"])
    
    # Map PredHel and TM_60 counts and ensure they're numeric
    df["PredHel"] = df["protein_ID"].map(lambda x: summary_data.get(x, {}).get("PredHel", 0))
    df["PredHel"] = pd.to_numeric(df["PredHel"], errors='coerce').fillna(0).astype(int)
    
    df["TM_60"] = df["protein_ID"].map(lambda x: summary_data.get(x, {}).get("TM_60", 0))
    df["TM_60"] = pd.to_numeric(df["TM_60"], errors='coerce').fillna(0).astype(int)
    
    # Ensure membrane_prop is numeric
    df["membrane_prop"] = pd.to_numeric(df["membrane_prop"], errors='coerce').fillna(0)
    
    # Create a new column that flags proteins with transmembrane helices
    df["has_TM"] = (df["PredHel"] > 0) | (df["membrane_prop"] > 0.05)  # Consider membrane proportion > 5% as having TM
    
    # Save complete data
    df.to_csv(output_path, sep='\t', index=False)
    
    # Create a filtered file with only TM-containing proteins
    tm_proteins = df[df["has_TM"]].copy()
    tm_output_path = output_path.replace('.tsv', '_tm_only.tsv')
    if not tm_output_path.endswith('.tsv'):
        tm_output_path = output_path + '.tm_only'
    tm_proteins.to_csv(tm_output_path, sep='\t', index=False)
    
    print(f"Total proteins: {len(df)}")
    print(f"Proteins with TM domains: {len(tm_proteins)}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py annotation_file summary_file output_file")
        sys.exit(1)
    
    annotation_file = sys.argv[1]
    summary_file = sys.argv[2]
    output_file = sys.argv[3]

    annotation_data = parse_annotation(annotation_file)
    summary_data = parse_summary(summary_file)
    merge_results(annotation_data, summary_data, output_file)