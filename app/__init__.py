from flask import Flask

app = Flask(__name__, template_folder='f:/meu drive/_develop/renova/templates')
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'f:/meu drive/_develop/renova/uploads/'
app.config['RECTIFIED_FOLDER'] = 'f:/meu drive/_develop/renova/rectified/'
app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB max file size

from app import routes
