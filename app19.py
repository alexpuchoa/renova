# -*- coding: utf-8 -*-
"""
Created on Tue May 28 18:05:45 2024

@author: alexu
"""

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'f:/meu drive/_develop/renova/uploads/'
app.config['RECTIFIED_FOLDER'] = 'f:/meu drive/_develop/renova/rectified/'
app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB max file size

# Define allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'tsv', 'txt'}

# Save violation report to a file
def save_violation_report(violations, report_path):
    with open(report_path, 'w') as f:
        for violation in violations:
            f.write(f"Record {violation[0]}, Column {violation[1]}, Issue: {violation[2]}\n")

# Define validation functions
def validate_presence(value):
    return value != ''

def validate_vocabulary(value, vocabulary):
    vocab_list = vocabulary.split('|')
    return value in vocab_list

def validate_date_range(value, start_date='2010-01-01', end_date=datetime.today().strftime('%Y-%m-%d')):
    try:
        date_value = datetime.strptime(value, '%Y-%m-%d')
        return start_date <= date_value.strftime('%Y-%m-%d') <= end_date
    except ValueError:
        return False

def validate_iso_format(value):
    iso_formats = [
        "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"
    ]
    for iso_format in iso_formats:
        try:
            datetime.strptime(value, iso_format)
            return True
        except ValueError:
            continue
    return False

def validate_integer(value):
    return value.isdigit()

def validate_positive_integer(value):
    return value.isdigit() and int(value) > 0

def validate_real_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def validate_latitude(value):
    try:
        lat = float(value)
        return -90 <= lat <= 90
    except ValueError:
        return False

def validate_longitude(value):
    try:
        lon = float(value)
        return -180 <= lon <= 180
    except ValueError:
        return False

def validate_verbatim_format(value):
    # Assuming verbatim format is some kind of coordinate format
    # This is a placeholder function and should be adjusted based on actual format rules
    pattern = r"^[0-9]+\s[0-9]+\s[0-9]+[NS]\s[0-9]+\s[0-9]+\s[0-9]+[EW]$"
    return re.match(pattern, value) is not None

def validate_controlled_values(value, controlled_values):
    return value in controlled_values.split('|')

# Apply rules to a dataset
def apply_rules(data, rules_df):
    violations = []
    for index, row in data.iterrows():
        for _, rule in rules_df.iterrows():
            column = rule['Possíveis colunas (ou campos) do arquivo coletado']
            if column in data.columns:
                value = row[column]
                if rule['Presença obrigatória da coluna/campo no arquivo'] == 'Sim para ambos' and not validate_presence(value):
                    violations.append((index, column, 'Required field is empty'))
                if pd.notna(rule['Vocabulário controlado (ver Anexo 4 - Vocabulários Controlados)']) and not validate_vocabulary(value, rule['Vocabulário controlado (ver Anexo 4 - Vocabulários Controlados)']):
                    violations.append((index, column, 'Value not in controlled vocabulary'))
                if pd.notna(rule['Relativo ao formato do valor']) and not validate_iso_format(value):
                    violations.append((index, column, 'Value does not match ISO 8601 format'))
                if pd.notna(rule['Relativo ao valor no campo']) and 'maior que' in rule['Relativo ao valor no campo']:
                    if not validate_positive_integer(value):
                        violations.append((index, column, 'Value is not a positive integer'))
                if pd.notna(rule['Regra complexa']) and 'deve ser' in rule['Regra complexa']:
                    if 'real e positivo' in rule['Regra complexa'] and not validate_real_number(value):
                        violations.append((index, column, 'Value is not a real number'))
            elif rule['Presença obrigatória da coluna/campo no arquivo'] == 'Sim para ambos':
                violations.append((index, column, 'Required column is missing'))
    return violations

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        data = pd.read_csv(file_path)
        # Load rules from CSV
        rules_file_path = 'f:/meu drive/_develop/renova/regras_de_qualidade 2.csv'  # Update with the actual path to the rules CSV file
        rules_df = pd.read_csv(rules_file_path, delimiter=';')
        
        violations = apply_rules(data, rules_df)
        report_path = os.path.join(app.config['RECTIFIED_FOLDER'], 'violation_report.txt')
        save_violation_report(violations, report_path)
        
        return render_template('validation_results.html', violations=violations, report_path=report_path)
    else:
        flash('Invalid file format')
        return redirect(request.url)

@app.route('/download_report/<path:filename>', methods=['GET', 'POST'])
def download_report(filename):
    return send_from_directory(directory=app.config['RECTIFIED_FOLDER'], path=filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['RECTIFIED_FOLDER']):
        os.makedirs(app.config['RECTIFIED_FOLDER'])
    app.run(debug=True, use_reloader=False)
