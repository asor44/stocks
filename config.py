import os

class Config:
    # Database Configuration
    DB_TYPE = os.environ.get('DB_TYPE', 'postgresql').lower()  # postgresql ou mysql
    
    # Configuration PostgreSQL (par défaut)
    if DB_TYPE == 'postgresql':
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    # Configuration MySQL
    elif DB_TYPE == 'mysql':
        mysql_user = os.environ.get('MYSQL_USER', 'root')
        mysql_password = os.environ.get('MYSQL_PASSWORD', '')
        mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
        mysql_port = os.environ.get('MYSQL_PORT', '3306')
        mysql_database = os.environ.get('MYSQL_DATABASE', 'acadef_db')
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Mail Configuration - Azure SMTP
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.office365.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME', 'noreply@example.com'))
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    
    # Application Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Create upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Configuration pour que Flask génère des URLs avec un préfixe
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '/') 

    # Configuration pour l'intégration avec d'autres applications
    OTHER_APP_API_URL = os.environ.get('OTHER_APP_API_URL')
    OTHER_APP_API_KEY = os.environ.get('OTHER_APP_API_KEY')
    WP_API_URL = os.environ.get('WP_API_URL')
    WP_API_USERNAME = os.environ.get('WP_API_USERNAME')
    WP_API_PASSWORD = os.environ.get('WP_API_PASSWORD')