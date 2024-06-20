# app.py

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
import pandas as pd
import chardet
import csv
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'f:/meu drive/_develop/renova/uploads/'
app.config['RECTIFIED_FOLDER'] = 'f:/meu drive/_develop/renova/rectified/'
app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB max file size

# Define allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'tsv'}

def check_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def determine_delimiter(file_path, encoding):
    with open(file_path, 'r', encoding=encoding) as csvfile:
        sample = csvfile.read(1024)
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample)
        return dialect.delimiter
    except csv.Error:
        delimiters = [',', '\t', ';', '|']
        delimiter_counts = {delim: sample.count(delim) for delim in delimiters}
        best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
        if delimiter_counts[best_delimiter] > 0:
            return best_delimiter
        else:
            return None

def validate_and_rectify(file_path):
    encoding = check_encoding(file_path)
    if encoding.lower() != 'utf-8':
        return False, "File is not encoded in UTF-8."

    delimiter = determine_delimiter(file_path, encoding)
    if delimiter is None:
        return False, "Could not determine the delimiter."

    try:
        df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
        output_filename = secure_filename(os.path.splitext(os.path.basename(file_path))[0] + "_rectified.csv")
        output_path = os.path.join(app.config['RECTIFIED_FOLDER'], output_filename)
        df.to_csv(output_path, sep=';', index=False, encoding='utf-8')
        return True, output_filename
    except Exception as e:
        return False, str(e)

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
        success, message = validate_and_rectify(file_path)
        if success:
            return redirect(url_for('validate_headers', filename=message))
        else:
            flash(message)
            return redirect(request.url)
    else:
        flash('Allowed file types are csv, tsv')
        return redirect(request.url)

@app.route('/validate_headers/<filename>', methods=['GET', 'POST'])
def validate_headers(filename):
    file_path = os.path.join(app.config['RECTIFIED_FOLDER'], filename)
    df = pd.read_csv(file_path, delimiter=';', encoding='utf-8')
    headers = list(df.columns)
    darwin_core_terms = get_darwin_core_terms()

    if request.method == 'POST':
        new_headers = request.form.getlist('headers')
        df.columns = new_headers
        updated_filename = filename.replace("_rectified", "_headers_updated")
        updated_path = os.path.join(app.config['RECTIFIED_FOLDER'], updated_filename)
        df.to_csv(updated_path, sep=';', index=False, encoding='utf-8')
        return redirect(url_for('validate_data', filename=updated_filename))

    return render_template('validate_headers.html', headers=headers, darwin_core_terms=darwin_core_terms)


@app.route('/validate_data/<filename>')
def validate_data(filename):
    file_path = os.path.join(app.config['RECTIFIED_FOLDER'], filename)
    df = pd.read_csv(file_path, delimiter=';', encoding='utf-8')
    validation_results = validate_data_records(df)
    return render_template('validation_results.html', validation_results=validation_results)

def get_darwin_core_terms():
    # Example hardcoded list of Darwin Core terms
    return [
        "scientificName", "decimalLatitude", "decimalLongitude", "eventDate",
        "basisOfRecord", "institutionCode", "collectionCode", "catalogNumber",
        "recordedBy", "individualCount"
    ]

def validate_data_records(df):
    validation_results = []
    for index, row in df.iterrows():
        errors = []
        if 'scientificName' in df.columns and pd.isna(row['scientificName']):
            errors.append("Missing scientificName")
        if 'decimalLatitude' in df.columns and not is_valid_latitude(row['decimalLatitude']):
            errors.append("Invalid decimalLatitude")
        if 'decimalLongitude' in df.columns and not is_valid_longitude(row['decimalLongitude']):
            errors.append("Invalid decimalLongitude")
        if 'eventDate' in df.columns and not is_valid_date(row['eventDate']):
            errors.append("Invalid eventDate")
        # Add more validation rules as needed
        if errors:
            validation_results.append({"record": index + 1, "errors": errors})
    return validation_results

def is_valid_latitude(value):
    try:
        lat = float(value)
        return -90 <= lat <= 90
    except ValueError:
        return False

def is_valid_longitude(value):
    try:
        lon = float(value)
        return -180 <= lon <= 180
    except ValueError:
        return False

def is_valid_date(value):
    try:
        datetime.strptime(str(value), '%Y-%m-%d')
        return True
    except ValueError:
        return False

if __name__ == '__main__':
    app.run(debug=True)
