# -*- coding: utf-8 -*-
"""
Created on Tue May 28 18:05:45 2024

@author: alexu
"""
import pandas as pd
import chardet
import csv
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
    "identifiedBy", "dateIdentified", "identificationRemarks"]
DARWIN_CORE_TERMS.sort()

CONTROLLED_VOCABULARY = {
    'vocab_basisOfRecord': ['PreservedSpecimen',   'FossilSpecimen',  'LivingSpecimen',  'MaterialSample',  'Event',  'HumanObservation',  'MachineObservation',  'Taxon',  'Occurrence',  'MaterialCitation'],
    'institutionID': ['REN'],
    'institutionCode': ['RENOVA'],
    'rightsHolder': ['Fundação Renova'],
    'continent': ['América do Sul'],
    'country': ['Brasil'],
    'countryCode': ['BR'],
    'vocab_type': ['Imagem estática',  'Imagem em movimento',  'Som',  'Objeto físico',  'Evento',  'Texto'],
    'vocab_language': ['en-us', 'es', 'pt-br', 'pt', 'en'],
    'vocab_sex': ['fêmea', 'macho', 'hermafrodita'],
    'vocab_georeferenceVerificationStatus': ['incapaz de georreferenciar',  'requer georreferenciação',  'requer verificação',  'verificado pelo custodiante dos dados',  'verificado pelo contribuidor'],
    'vocab_lifeStage': ['zigoto',  'larva',  'juvenil',  'adulto',  'plantinha',  'floração',  'frutificação'],
    'vocab_reproductiveCondition': ['não reprodutivo',  'grávida',  'em flor',  'frutífero'],
    'vocab_disposition': ['na coleção',  'ausente',  'comprovante em outro lugar',  'duplicados em outro lugar'],
    'vocab_continent': ['África',  'Antártica',  'Ásia',  'Europa',  'América do Norte',  'Oceânia',  'América do Sul'],
    'vocab_island': ['Fernando de Noronha',  'Ilha de Marajó',  'Morro de São Paulo',  'Delta do Parnaiba',  'Arquipélago de Anavilhanas', 'Ilha de Boipeba',  'Ilha do Mel',  'Ilha Grande',  'Ilha do Guajiru',  'Alter do Chão',  'Ilha Bela',  'Abrolhos'],
    'vocab_verbatimCoordinateSystem': ['graus decimais',  'graus minutos decimais',  'Graus / minutos / segundos',  'UTM'],
    'vocab_taxonRank': ['subespécies', 'varietas', 'forma', 'espécies', 'gênero'],
    'vocab_establishmentMeans': ['nativo',  'nativoReintroduzido',  'introduzido',  'introduçãoColonização assistida',  'vagabundo',  'incerto']}

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

def validate_presence(value):
    return bool(value)

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
            datetime.strptime(str(value), iso_format)
            return True
        except ValueError:
            continue
    return False

def validate_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def validate_positive_integer(value):
    try:
        return int(value) > 0
    except ValueError:
        return False

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

def validate_record(data, rule):
    column = rule['Possíveis colunas (ou campos) do arquivo coletado']
    violations = []

    if column not in data:
        if rule['Presença obrigatória da coluna/campo no arquivo'] == 'Sim para ambos':
            violations.append(f'Required column {column} is missing')
        return violations

    value = data[column]
    if rule['Presença obrigatória da coluna/campo no arquivo'] == 'Sim para ambos' and not validate_presence(value):
        violations.append(f'{column} is a required field and is empty')

    if pd.notna(rule['Vocabulário controlado (ver Anexo 4 - Vocabulários Controlados)']) and not validate_vocabulary(value, rule['Vocabulário controlado (ver Anexo 4 - Vocabulários Controlados)']):
        violations.append(f'{column} has value not in controlled vocabulary')

    if pd.notna(rule['Relativo ao formato do valor']) and not validate_iso_format(str(value)):
        violations.append(f'{column} does not match ISO 8601 format')

    if pd.notna(rule['Relativo ao valor no campo']):
        if 'maior que' in rule['Relativo ao valor no campo']:
            if not validate_positive_integer(value):
                violations.append(f'{column} is not a positive integer')
        # Add other specific value validations here

    if pd.notna(rule['Regra complexa']):
        if 'deve ser' in rule['Regra complexa']:
            if 'real e positivo' in rule['Regra complexa'] and not validate_real_number(value):
                violations.append(f'{column} is not a real number')
        # Add other complex rule validations here

    return violations

# Apply rules to a dataset
def apply_rules(data, rules_df):
    all_violations = []
    for index, row in data.iterrows():
        for _, rule in rules_df.iterrows():
            violations = validate_record(row, rule)
            for violation in violations:
                all_violations.append((index, rule['Possíveis colunas (ou campos) do arquivo coletado'], violation))
    return all_violations

def detect_encoding_and_delimiter(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    with open(file_path, 'r', encoding=encoding) as f:
        sample = ''.join([f.readline() for _ in range(5)])
        try:
            dialect = csv.Sniffer().sniff(sample)
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ','
    return encoding, delimiter

# Save violation report to a file
def save_violation_report(violations, report_path):
    with open(report_path, 'w') as f:
        for violation in violations:
            f.write(f"Record {violation[0]}, Column {violation[1]}, Issue: {violation[2]}\n")

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

    if request.method == 'POST':
        new_headers = request.form.getlist('headers')
        df.columns = new_headers
        updated_filename = filename.replace("_rectified", "_headers_updated")
        updated_path = os.path.join(app.config['RECTIFIED_FOLDER'], updated_filename)
        df.to_csv(updated_path, sep=';', index=False, encoding='utf-8')
        return redirect(url_for('validate_data', filename=updated_filename))

    return render_template('validate_headers.html', headers=headers, darwin_core_terms=DARWIN_CORE_TERMS)

@app.route('/validate_data/<filename>')
def validate_data(filename):
    file_path = os.path.join(app.config['RECTIFIED_FOLDER'], filename)
    df = pd.read_csv(file_path, delimiter=';', encoding='utf-8')
    validation_results = validate_data_records(df)
    df.to_csv(file_path, sep=';', index=False, encoding='utf-8')  # Save the corrected file
    return render_template('validation_results.html', validation_results=validation_results)

def validate_data_records(df):
    validation_results = []
    for index, row in df.iterrows():
        errors = []
        if 'scientificName' in df.columns and pd.isna(row['scientificName']):
            errors.append({"term": "scientificName", "rule": 1, "value": row['scientificName']})
        if 'decimalLatitude' in df.columns and not is_valid_latitude(row['decimalLatitude']):
            errors.append({"term": "decimalLatitude", "rule": 2, "value": row['decimalLatitude']})
        if 'decimalLongitude' in df.columns and not is_valid_longitude(row['decimalLongitude']):
            errors.append({"term": "decimalLongitude", "rule": 3, "value": row['decimalLongitude']})
        if 'eventDate' in df.columns:
            date_error, adjusted_date = validate_and_correct_date(row['eventDate'])
            if date_error:
                errors.append({"term": "eventDate", "rule": 4, "value": row['eventDate'], "adjusted": adjusted_date})
            elif adjusted_date:
                df.at[index, 'eventDate'] = adjusted_date  # Correct the date in the dataframe
                errors.append({"term": "eventDate", "rule": 4, "value": adjusted_date, "corrected": True})
        # Add more validation rules as needed
        if errors:
            validation_results.append({"record": index + 1, "errors": errors})
    return validation_results

def validate_and_correct_date(value):
    try:
        datetime.strptime(str(value), '%Y-%m-%d')
        return False, None  # No error, no adjustment needed
    except ValueError:
        # Try to correct the date format
        try:
            corrected_date = datetime.strptime(str(value), '%d/%m/%Y').strftime('%Y-%m-%d')
            return False, corrected_date  # Error, but adjustment possible
        except ValueError:
            return True, None  # Error, and no adjustment possible

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

@app.route('/download_report/<path:filename>', methods=['GET', 'POST'])
def download_report(filename):
    return send_from_directory(directory=app.config['RECTIFIED_FOLDER'], path=filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['RECTIFIED_FOLDER']):
        os.makedirs(app.config['RECTIFIED_FOLDER'])
    app.run(debug=True, use_reloader=False)
