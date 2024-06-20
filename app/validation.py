import pandas as pd
from datetime import datetime
import re
from dateutil import parser
import json



def load_validation_rules(validation_rules_file):
    """Load validation rules from a JSON file."""
    with open(validation_rules_file, 'r', encoding='utf-8') as file:
        validation_rules = json.load(file)
    return validation_rules

# Path to the validation rules file
VALIDATION_RULES_FILE = 'f:/meu drive/_develop/renova/validation_rules.json'
validation_rules = load_validation_rules(VALIDATION_RULES_FILE)

def validate_and_correct_date(value):
    """Validate and correct the date to the standard format."""
    try:
        if not isinstance(value, str):
            return True, value
        
        # Attempt to parse the date
        parsed_date = parser.parse(value)
        # Convert to standard format
        corrected_date = parsed_date.strftime('%Y-%m-%d')
        return False, corrected_date
    except (ValueError, OverflowError):
        return True, None

def validate_and_correct_delimiters(value, value_check):
    """Validate and correct the delimiters in the string."""
    if not isinstance(value, str):
        return True, value # Delimiter error
    
    allowed_delimiters = value_check.get("allowed_delimiters", ["-", "|", ";"])
    correct_delimiter = value_check.get("correct_delimiter", "|")

    # Create a regex pattern to match any of the allowed delimiters
    delimiter_pattern = re.compile('|'.join(map(re.escape, allowed_delimiters)))
    
    # Split the string by the allowed delimiters
    parts = delimiter_pattern.split(value)
    
    # Trim whitespace around each part
    parts = [part.strip() for part in parts]
    
    # Join the parts with the correct delimiter
    corrected_value = correct_delimiter.join(parts)
    
    return False, corrected_value # Delimiter corrected

def validate_format(value, format_check):
    """Validate if the value matches the given regex format."""
    if format_check and isinstance(value, str) and not re.match(format_check, value):
        return True, None  # Format error
    return False, value  # No error

def validate_value(value, value_check, filename):
    """Validate the value based on the value_check rules."""
    if value_check:
        if 'type' in value_check and value_check['type'] == 'range':
            try:
                num = float(value)
                if 'min' in value_check.keys():
                    min_val = float(value_check['min']) if 'min' in value_check else float('-inf')
                    if num < min_val:
                        return True, None # Value error                
                if 'max' in value_check.keys():
                    max_val = float(value_check['max']) if 'max' in value_check else float('inf')
                    if num > max_val:
                        return True, None # Value error  
            except ValueError:
                return True, None # Value error
        elif 'type' in value_check and value_check['type'] == 'integer_range':
            try:
                num = int(value)
                if 'min' in value_check.keys():
                    min_val = int(value_check['min']) if 'min' in value_check else float('-inf')
                    if num < min_val:
                        return True, None # Value error                
                if 'max' in value_check.keys():
                    max_val = int(value_check['max']) if 'max' in value_check else float('inf')
                    if num > max_val:
                        return True, None # Value error                

            except ValueError:
                return True, None # Value error
        elif 'type' in value_check and value_check['type'] == 'delimiter_check':
            return validate_and_correct_delimiters(value, value_check)
        elif 'type' in value_check and value_check['type'] == 'filename_if_blank':
            if pd.isna(value) or value == '':
                return False, filename
    return False, value

def validate_data_records(df, filename):
    validation_results = []
    for index, row in df.iterrows():
        errors = {}
        for term, rules in validation_rules.items():
            if term in df.columns:
                value = row[term]
                rule_number = rules['rule_number']
                
                # Skip non-required blank fields
                if pd.isna(value) and not rules['mandatory']:
                    continue
                
                # Ensure value is a string for validation
                if pd.notna(value):
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                    else:
                        value = str(value)
                
                # Check mandatory fields
                if rules['mandatory'] and pd.isna(value):
                    errors[term] = {"rule": rule_number, "value": "blank"}
                    continue
                
                # Date validation and correction
                if 'date' in term.lower() or term == 'modified':
                    date_error, corrected_date = validate_and_correct_date(value)
                    if date_error:
                        errors[term] = {"rule": rule_number, "value": value}
                    elif corrected_date:
                        df.at[index, term] = corrected_date
                        errors[term] = {"rule": rule_number, "value": corrected_date, "corrected": True}
                
                # Format validation
                if rules['format_check']:
                    format_error, corrected_value = validate_format(value, rules['format_check'])
                    if format_error:
                        errors[term] = {"rule": rule_number, "value": value}
                
                # Value validation and correction
                if rules['value_check']:
                    value_error, corrected_value = validate_value(value, rules['value_check'], filename)
                    if value_error:
                        errors[term] = {"rule": rule_number, "value": value}
                    elif corrected_value != value:
                        if corrected_value is None:
                            corrected_value = float('nan')
                        df.at[index, term] = corrected_value
                        errors[term] = {"rule": rule_number, "value": corrected_value, "corrected": True}
        
        if errors:
            validation_results.append({"record": index + 1, "errors": errors})

    return validation_results