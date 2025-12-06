import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads Gerais
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    # NOVO: Pasta de Avatares
    AVATAR_FOLDER = os.path.join(basedir, 'app/static/uploads/avatars')
    
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}