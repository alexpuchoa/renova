from difflib import get_close_matches

from flask import Flask, request, redirect, flash, render_template, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import pandas as pd
import chardet
import csv
import re
from flask import Flask

# Constants
SIM_PARA_AMBOS = 'Sim para ambos'
MAIOR_QUE = 'maior que'
DEVE_SER = 'deve ser'
REAL_E_POSITIVO = 'real e positivo'

app_2 = Flask(__name__)
app_2.secret_key = 'supersecretkey'
app_2.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'f:/meu drive/_develop/renova/uploads')
app_2.config['RECTIFIED_FOLDER'] = os.getenv('RECTIFIED_FOLDER', 'f:/meu drive/_develop/renova/rectified')


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
        output_path = os.path.join(app_2.config['RECTIFIED_FOLDER'], output_filename)
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

def validate_presence(value):
    return pd.notna(value)

def validate_vocabulary(value, vocabulary):
    vocab_list = vocabulary.split('|')
    return value in vocab_list

def validate_positive_integer(value):
    try:
        return int(value) > 0
    except ValueError:
        return False

def validate_real_number(value):
    try:
        return float(value) > 0
    except ValueError:
        return False

def validate_iso_format(value):
    pattern = r"^[0-9]+\s[0-9]+\s[0-9]+[NS]\s[0-9]+\s[0-9]+\s[0-9]+[EW]$"
    return re.match(pattern, str(value)) is not None

def validate_controlled_values(value, controlled_values):
    return value in controlled_values.split('|')

def validate_record(data, rule):
    column = rule['Possíveis colunas (ou campos) do arquivo coletado']
    violations = []

    if column not in data:
        if rule['Presença obrigatória da coluna/campo no arquivo'] == SIM_PARA_AMBOS:
            violations.append(f'Required column {column} is missing')
        return violations

    value = data[column]
    if rule['Presença obrigatória da coluna/campo no arquivo'] == SIM_PARA_AMBOS and not validate_presence(value):
        violations.append(f'{column} is a required field and is empty')

    if pd.notna(rule['Vocabulário controlado (ver Anexo 4 - Vocabulários Controlados)']) and not validate_vocabulary(value, rule['Vocabulário controlado (ver Anexo 4 - Vocabulários Controlados)']):
        violations.append(f'{column} has value not in controlled vocabulary')

    if pd.notna(rule['Relativo ao formato do valor']) and not validate_iso_format(value):
        violations.append(f'{column} does not match ISO 8601 format')

    if pd.notna(rule['Relativo ao valor no campo']):
        if MAIOR_QUE in rule['Relativo ao valor no campo']:
            if not validate_positive_integer(value):
                violations.append(f'{column} is not a positive integer')

    if pd.notna(rule['Regra complexa']):
        if DEVE_SER in rule['Regra complexa']:
            if REAL_E_POSITIVO in rule['Regra complexa'] and not validate_real_number(value):
                violations.append(f'{column} is not a real number')

    return violations

def apply_rules(data, rules_df):
    all_violations = []
    for index, row in data.iterrows():
        for _, rule in rules_df.iterrows():
            violations = validate_record(row, rule)
            all_violations.extend([(index, rule['Possíveis colunas (ou campos) do arquivo coletado'], violation) for violation in violations])
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

def save_violation_report(violations, report_path):
    with open(report_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(violations)

@app_2.route('/')
def index():
    return render_template('index.html')


# Module 1: Detect encoding and delimiter and rectify the file
def process_file(file, filename):
    file_path = os.path.join(app_2.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Detect encoding and delimiter
    encoding, delimiter = detect_encoding_and_delimiter(file_path)

    try:
        data = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
    except pd.errors.ParserError as e:
        flash(f'Error reading file: {e}')
        return None, None

    valid, result, header = validate_and_rectify(file_path)
    if not valid:
        flash(f'Error: {result}')
        return None, None

    return data, header

# Module 2: Allow for header terms swap and save the new version
def swap_header_terms_and_save(data, header):
    # Assuming `swap_header_terms` is a function that swaps header terms
    new_header = swap_header_terms(header, DARWIN_CORE_TERMS)
    data.columns = new_header
    new_file_path = os.path.join(app_2.config['RECTIFIED_FOLDER'], filename)
    data.to_csv(new_file_path, index=False)

    return new_file_path

# Module 3: Run the data validation according to the rules, show the results and save the report
def validate_data_and_save_report(data, rules_file_path):
    rules_df = pd.read_csv(rules_file_path, delimiter=';')
    violations = apply_rules(data, rules_df)
    report_path = os.path.join(app_2.config['RECTIFIED_FOLDER'], 'report.csv')
    save_violation_report(violations, report_path)

    return violations, report_path

@app_2.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)

        # Module 1
        data, header = process_file(file, filename)
        if data is None:
            return redirect(request.url)

        # Module 2
        new_file_path = swap_header_terms_and_save(data, header)

        # Module 3
        rules_file_path = 'f:/meu drive/_develop/renova/regras_de_qualidade 2.csv'  # Update with the actual path to the rules CSV file
        violations, report_path = validate_data_and_save_report(data, rules_file_path)

        return render_template('validation.html', validation_results=violations, file_path=new_file_path, standard_terms=DARWIN_CORE_TERMS)

    return render_template('upload.html')


def swap_header_terms(header, DARWIN_CORE_TERMS):
    new_header = []
    for term in header:
        if term in DARWIN_CORE_TERMS:
            new_header.append(term)
        else:
            matches = get_close_matches(term, DARWIN_CORE_TERMS, n=1, cutoff=0.6)
            if matches:
                new_header.append(matches[0])
            else:
                new_header.append("Keep the original term: " + term)
                new_header.extend(DARWIN_CORE_TERMS)
    return new_header

@app_2.route('/download_report/<path:filename>', methods=['GET', 'POST'])
def download_report(filename):
    return send_from_directory(directory=app_2.config['RECTIFIED_FOLDER'], path=filename)

@app_2.route('/save', methods=['POST'])
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
        output_path = os.path.join(app_2.config['RECTIFIED_FOLDER'], output_filename)
        df.to_csv(output_path, sep=';', index=False, encoding='utf-8')
        flash(f'File successfully updated and saved to {output_path}')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))


if __name__ == '__main__':
    if not os.path.exists(app_2.config['UPLOAD_FOLDER']):
        os.makedirs(app_2.config['UPLOAD_FOLDER'])
    if not os.path.exists(app_2.config['RECTIFIED_FOLDER']):
        os.makedirs(app_2.config['RECTIFIED_FOLDER'])
    app_2.run(debug=True, use_reloader=False)