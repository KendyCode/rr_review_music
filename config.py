import os
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

class Config:
    # 1. Récupération des secrets
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cle-secrete-par-defaut'

    # 2. Construction de l'URL MySQL
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    host = os.environ.get('DB_HOST')
    database = os.environ.get('DB_NAME')

    # Format: mysql+pymysql://user:password@host/database
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{user}:{password}@{host}/{database}"

    # 3. Paramètres Flask-SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 4. Dossier pour tes exports CSV
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/exports')