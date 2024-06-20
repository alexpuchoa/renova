import chardet
import csv
import pandas as pd
import os
from werkzeug.utils import secure_filename
from app import app

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
