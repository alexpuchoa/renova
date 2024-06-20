# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 18:51:22 2024

@author: alexu
"""

import pandas as pd
import json

def excel_to_json(excel_file_path, json_file_path):
    # Read the Excel file
    df = pd.read_csv(excel_file_path, sep=';')
    
    # Initialize an empty dictionary to hold the validation rules
    validation_rules = {}

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        term = row['term']
        rule_number = row['rule_number']
        
        # Extract value_check related fields
        value_check = {
            "type": row['type'] if not pd.isna(row['type']) else None,
            "allowed_delimiters": row['allowed_delimiter'].split(",") if not pd.isna(row['allowed_delimiter']) else None,
            "corrected_delimiter": row['corrected_delimiter'] if not pd.isna(row['corrected_delimiter']) else None,
            "min": row['min'] if not pd.isna(row['min']) else None,
            "max": row['max'] if not pd.isna(row['max']) else None,
            "required": row['required'] if not pd.isna(row['required']) else None,
            "consistent": row['consistent'] if not pd.isna(row['consistent']) else None,
            "unique": row['unique'] if not pd.isna(row['unique']) else None,
        }
        
        # Remove None values from value_check
        value_check = {k: v for k, v in value_check.items() if v is not None}
        
        # If value_check is empty, set it to None
        if not value_check:
            value_check = None
        
        validation_rules[term] = {
            "rule_number": rule_number,
            "mandatory": row['mandatory'] if not pd.isna(row['mandatory']) else None,
            "format_check": row['format_check'] if not pd.isna(row['format_check']) else None,
            "allowed_characters": row['allowed_characters'] if not pd.isna(row['allowed_characters']) else None,
            "controlled_vocabulary": row['controlled_vocabulary'] if not pd.isna(row['controlled_vocabulary']) else None,
            "value_check": value_check
        }
    
    # Write the validation rules to a JSON file
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(validation_rules, json_file, ensure_ascii=False, indent=4)
        
# Example usage
excel_file_path = 'f:/meu drive/_develop/renova/regras_de_qualidade 2.csv'
json_file_path = 'f:/meu drive/_develop/renova/validation_rules.json'
excel_to_json(excel_file_path, json_file_path)
