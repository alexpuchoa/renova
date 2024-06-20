# -*- coding: utf-8 -*-
"""
Created on Tue May 28 18:05:45 2024

@author: alexu
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import os
import csv
import chardet
import pandas as pd
from werkzeug.utils import secure_filename
from difflib import get_close_matches

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'f:/_develop/renova/uploads/'
app.config['RECTIFIED_FOLDER'] = 'f:/_develop/renova/rectified/'
app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB max file size

ALLOWED_EXTENSIONS = {'csv', 'tsv', 'txt'}
DARWIN_CORE_TERMS = [
    "basisOfRecord", "modified", "datasetName", "type", "language", "institutionID", 
    "institutionCode", "collectionCode", "license", "references", "rightsHolder", 
    "dynamicProperties", "occurrenceID", "catalogNumber", "otherCatalogNumbers", 
    "recordedBy", "recordNumber", "individualCount", "organismQuantity", 
    "organismQuantityType", "establishmentMeans", "georeferenceVerificationStatus", 
    "sex", "lifeStage", "reproductiveCondition", "preparations", "disposition", 
    "associatedTaxa", "associatedReferences", "associatedMedia", "associatedSequences", 
    "occurrenceRemarks", "organismID", "eventDate", "eventTime", "endDayOfYear", 
    "year", "month", "day", "verbatimEventDate", "habitat", "samplingProtocol", 
    "samplingEffort", "eventRemarks", "higherGeography", "continent", "country", 
    "countryCode", "stateProvince", "county", "municipality", "island", "islandGroup", 
    "waterBody", "locality", "verbatimLocality", "locationAccordingTo", "locationRemarks", 
    "minimumElevationInMeters", "maximumElevationInMeters", "minimumDepthInMeters", 
    "maximumDepthInMeters", "verbatimLatitude", "verbatimLongitude", "decimalLatitude", 
    "decimalLongitude", "coordinateUncertaintyInMeters", "verbatimCoordinates", 
    "verbatimCoordinateSystem", "geodeticDatum", "georeferenceProtocol", 
    "georeferenceSources", "georeferencedBy", "georeferencedDate", "georeferenceRemarks", 
    "kingdom", "phylum", "class", "order", "family", "genus", "specificEpithet", 
    "infraspecificEpithet", "scientificName", "scientificNameAuthorship", "taxonRank", 
    "vernacularName", "taxonRemarks", "identificationQualifier", "typeStatus", 
    "identifiedBy", "dateIdentified", "identificationRemarks"
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        return True, output_path, df.columns.tolist()
    except Exception as e:
        return False, str(e), None

def validate_header(header):
    validation_results = []
    for term in header:
        if term in DARWIN_CORE_TERMS:
            validation_results.append((term, True, []))
        else:
            similar_terms = get_close_matches(term, DARWIN_CORE_TERMS, n=5, cutoff=0.6)
            validation_results.append((term, False, similar_terms))
    return validation_results

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

        valid, result, header = validate_and_rectify(file_path)
        if valid:
            validation_results = validate_header(header)
            return render_template('validation.html', validation_results=validation_results, file_path=file_path, standard_terms=DARWIN_CORE_TERMS)
        else:
            flash(f'Error: {result}')
            return redirect(url_for('index'))

@app.route('/save', methods=['POST'])
def save_file():
    file_path = request.form['file_path']
    encoding = check_encoding(file_path)
    delimiter = determine_delimiter(file_path, encoding)

    try:
        df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
        new_columns = []
        for col in df.columns:
            new_column = request.form.get(f'mapping_{col}', col)
            new_columns.append(new_column)
        df.columns = new_columns
        output_filename = secure_filename(os.path.splitext(os.path.basename(file_path))[0] + "_final.csv")
        output_path = os.path.join(app.config['RECTIFIED_FOLDER'], output_filename)
        df.to_csv(output_path, sep=';', index=False, encoding='utf-8')
        flash(f'File successfully updated and saved to {output_path}')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['RECTIFIED_FOLDER']):
        os.makedirs(app.config['RECTIFIED_FOLDER'])
    app.run(debug=True, use_reloader=False)
