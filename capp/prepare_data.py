import pandas as pd
import csv
import json
import yaml
import os

def read_data_file(file_path):
    """
    Read data file in various formats (TSV, CSV, JSON, YAML)
    Returns list of (source_text, target_text) tuples
    """
    file_extension = file_path.split('.')[-1].lower()
    pairs = []
    
    try:
        if file_extension == 'tsv':
            # Tab-separated file
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():  # Skip empty lines
                        source, target = line.strip().split('\t')
                        pairs.append((source.strip(), target.strip()))
                        
        elif file_extension == 'csv':
            # CSV file
            df = pd.read_csv(file_path)
            pairs = list(zip(df['source_text'], df['target_text']))
            
        elif file_extension == 'json':
            # JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    pairs.append((item['source'], item['target']))
                    
        elif file_extension == 'yaml' or file_extension == 'yml':
            # YAML file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                for item in data:
                    pairs.append((item['source'], item['target']))
                    
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
            
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return []
        
    return pairs

def prepare_training_data(en_sn_file, sn_zu_file):
    """
    Prepare training data from files
    Supports multiple file formats: TSV, CSV, JSON, YAML
    """
    
    # Process English-Shona data
    en_sn_data = []
    for source, target in read_data_file(en_sn_file):
        en_sn_data.append({
            'source_text': source,
            'target_text': target,
            'source_lang': 'eng_Latn',
            'target_lang': 'sna_Latn'
        })
    
    # Process Shona-Zulu data
    sn_zu_data = []
    for source, target in read_data_file(sn_zu_file):
        sn_zu_data.append({
            'source_text': source,
            'target_text': target,
            'source_lang': 'sna_Latn',
            'target_lang': 'zul_Latn'
        })
    
    # Create DataFrames
    en_sn_df = pd.DataFrame(en_sn_data)
    sn_zu_df = pd.DataFrame(sn_zu_data)
    
    # Save to CSV
    os.makedirs('data', exist_ok=True)
    en_sn_df.to_csv('data/en_sn_dataset.csv', index=False)
    sn_zu_df.to_csv('data/sn_zu_dataset.csv', index=False)
    
    print(f"Processed {len(en_sn_data)} English-Shona pairs")
    print(f"Processed {len(sn_zu_data)} Shona-Zulu pairs")

def main():
    import os
    os.makedirs('data', exist_ok=True)
    
    # You can now use files in different formats:
    prepare_training_data(
        'raw_data/en_sn_pairs.txt',  # or .csv, .json, .yaml
        'raw_data/sn_zu_pairs.txt'   # or .csv, .json, .yaml
    )

if __name__ == "__main__":
    main() 