from flask import render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import os
import pandas as pd

from app import app
from app.rectification import validate_and_rectify, allowed_file
from app.headers import get_darwin_core_terms
from app.validation import validate_data_records

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
    validation_results = validate_data_records(df, filename)

    #updated_filename = filename.replace("_headers_updated", "_verified")
    #file_path = os.path.join(app.config['RECTIFIED_FOLDER'], updated_filename)
    validated_filename = os.path.join(app.config['RECTIFIED_FOLDER'], 'validated_file.csv')
    # Save the corrected file    
    df.to_csv(validated_filename, sep=';', index=False, encoding='utf-8')  # Save the corrected file

    # Check if the file was saved correctly
    if os.path.exists(validated_filename):
        print("File saved successfully")
    else:
        print("Error saving file")

    report_filename = filename.replace("_headers_updated", "_validation_report")
    file_path = os.path.join(app.config['RECTIFIED_FOLDER'], report_filename) # Save the report
    with open(file_path, 'w') as file:
        for result in validation_results:
            for term, error in result['errors'].items():
                record = f"Registro: {result['record']}: {term}: {error['rule']}, Valor inválido: {error['value']}"
                if 'corrected' in error and error['corrected']:
                    record += f", Corrigido para: {error['value']}"                
                file.write(f"{record}\n")

    return render_template('validation_results.html', validation_results=validation_results, validated_filename=validated_filename)

def save():
    validated_filename = request.form['validated_filename']
    return redirect(url_for('download_file', filename=validated_filename))

@app.route('/download')
def download_file():
    filename = request.args.get('filename')
    file_path = filename
    # Debugging print statements to check file path
    print(f"Attempting to send file from path: {file_path}")
    if os.path.exists(file_path):
        print(f"File exists at path: {file_path}")
    else:
        print(f"File does not exist at path: {file_path}")
    return send_file(file_path, as_attachment=True)