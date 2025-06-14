import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_mail import Mail
from werkzeug.security import generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
mail = Mail()
login_manager = LoginManager()

# création de l'application
app = Flask(__name__)

# --- AJOUTEZ CES LIGNES POUR LA CORRECTION DU PROXY ---
# ProxyFix va ajuster les URLs générées par url_for() et les redirections
# en se basant sur les en-têtes X-Forwarded-* envoyés par Nginx.
# x_prefix=1 indique que nous faisons confiance à l'en-tête X-Forwarded-Prefix.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1, x_prefix=1)

# Chargement des configurations depuis config.py
from config import Config
app.config.from_object(Config)

# configuration du secret_key pour les sessions
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# configuration de la base de données
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialisation des extensions
db.init_app(app)
mail.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# template filters
@app.template_filter('nl2br')
def nl2br(value):
    """Transforme les retours à la ligne en balises <br>"""
    if value:
        return value.replace('\n', '<br>')
    return ''


# user loader pour Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))


# route d'accueil
@app.route('/')
def index():
    # Récupérer la période d'inscription active
    active_period = ApplicationPeriod.query.filter_by(is_active=True).first()
    today = datetime.now().date()
    
    # Déterminer si l'inscription est ouverte
    registration_open = False
    registration_message = ""
    
    if active_period:
        if today < active_period.start_date:
            registration_message = f"Les inscriptions commenceront le {active_period.start_date.strftime('%d/%m/%Y')}"
        elif today > active_period.end_date:
            registration_message = f"Les inscriptions sont terminées depuis le {active_period.end_date.strftime('%d/%m/%Y')}"
        else:
            registration_open = True
            registration_message = f"Les inscriptions sont ouvertes jusqu'au {active_period.end_date.strftime('%d/%m/%Y')}"
    else:
        registration_message = "Aucune période d'inscription n'est actuellement active"
    
    return render_template('index.html', 
                          active_period=active_period,
                          registration_open=registration_open,
                          registration_message=registration_message)


# enregistrement des blueprints
with app.app_context():
    # Création des tables si elles n'existent pas
    from models import User, Candidate, Guardian, Application, Document, SigningProcess
    from models import MedicalInformation, PhysicalMeasurements, AppointmentSlot, AppointmentBooking, ApplicationPeriod
    
    db.create_all()
    
    # Création d'un administrateur par défaut si aucun utilisateur admin n'existe
    admin_count = User.query.filter_by(is_admin=True).count()
    if admin_count == 0:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('adminpassword'),
            is_admin=True,
            is_active=True
        )
        db.session.add(admin)
        try:
            db.session.commit()
            print("Utilisateur administrateur créé avec succès.")
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la création de l'administrateur: {e}")
    
    # Enregistrement des blueprints
    from routes.auth import auth_bp
    from routes.registration import registration_bp
    from routes.admin import admin_bp
    from routes.admin_settings import admin_settings_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(registration_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_settings_bp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)