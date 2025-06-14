from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import db
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Votre compte n\'est pas actif. Veuillez contacter l\'administrateur.', 'warning')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            next_page = request.args.get('next')
            
            if user.is_admin:
                return redirect(next_page or url_for('admin.dashboard'))
            else:
                return redirect(next_page or url_for('auth.dashboard'))
        else:
            flash('Email ou mot de passe invalide.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    # Pour les utilisateurs candidats
    if current_user.candidate:
        candidate = current_user.candidate
        return render_template(
            'auth/dashboard.html', 
            candidate=candidate,
            application_status=candidate.application_status
        )
    
    # Pour les tuteurs, montrer les candidats associés
    elif current_user.guardian:
        guardian = current_user.guardian
        candidates = []
        if guardian.candidate:
            candidates.append(guardian.candidate)
        return render_template(
            'auth/dashboard.html', 
            guardian=guardian,
            candidates=candidates
        )
    
    # Utilisateur sans rôle spécifique
    return render_template('auth/dashboard.html')
