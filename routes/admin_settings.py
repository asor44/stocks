from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from models import User, ApplicationPeriod
from datetime import datetime
import re

admin_settings_bp = Blueprint('admin_settings', __name__, url_prefix='/admin/settings')

@admin_settings_bp.route('/')
@login_required
def index():
    """Page d'accueil des paramètres d'administration"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin/settings/index.html')

# Gestion des utilisateurs
@admin_settings_bp.route('/users')
@login_required
def users():
    """Liste des utilisateurs du système"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.order_by(User.username).all()
    
    return render_template('admin/settings/users.html', users=users)

@admin_settings_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    """Créer un nouvel utilisateur"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = True if request.form.get('is_admin') == 'on' else False
        
        # Validation
        if not username or not email or not password:
            flash('Tous les champs sont obligatoires.', 'danger')
            return render_template('admin/settings/create_user.html')
        
        if len(password) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères.', 'danger')
            return render_template('admin/settings/create_user.html')
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Veuillez saisir une adresse email valide.', 'danger')
            return render_template('admin/settings/create_user.html')
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Un utilisateur avec ce nom d\'utilisateur ou cette adresse email existe déjà.', 'danger')
            return render_template('admin/settings/create_user.html')
        
        # Créer le nouvel utilisateur
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=is_admin,
            is_active=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'L\'utilisateur {username} a été créé avec succès.', 'success')
        return redirect(url_for('admin_settings.users'))
    
    return render_template('admin/settings/create_user.html')

# Gestion des périodes d'inscription
@admin_settings_bp.route('/application-periods')
@login_required
def application_periods():
    """Liste des périodes d'inscription"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    periods = ApplicationPeriod.query.order_by(ApplicationPeriod.start_date.desc()).all()
    
    return render_template(
        'admin/settings/application_periods.html',
        periods=periods
    )

@admin_settings_bp.route('/application-periods/add', methods=['GET', 'POST'])
@login_required
def add_application_period():
    """Ajouter une période d'inscription"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        promotion_year = request.form.get('promotion_year')
        is_active = 'is_active' in request.form
        description = request.form.get('description')
        
        # Validation
        if not name or not start_date_str or not end_date_str or not promotion_year:
            flash('Tous les champs requis doivent être remplis.', 'danger')
            return redirect(url_for('admin_settings.add_application_period'))
        
        # Conversion des dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            promotion_year = int(promotion_year)
        except (ValueError, TypeError):
            flash('Format de date ou d\'année invalide.', 'danger')
            return redirect(url_for('admin_settings.add_application_period'))
        
        # Vérifier que la date de fin est après la date de début
        if end_date <= start_date:
            flash('La date de fin doit être postérieure à la date de début.', 'danger')
            return redirect(url_for('admin_settings.add_application_period'))
        
        # Si cette période est active, désactiver les autres
        if is_active:
            active_periods = ApplicationPeriod.query.filter_by(is_active=True).all()
            for period in active_periods:
                period.is_active = False
        
        # Créer la nouvelle période
        new_period = ApplicationPeriod(
            name=name,
            start_date=start_date,
            end_date=end_date,
            promotion_year=promotion_year,
            is_active=is_active,
            description=description,
            created_by=current_user.id
        )
        
        db.session.add(new_period)
        db.session.commit()
        
        flash(f'La période d\'inscription "{name}" a été créée avec succès.', 'success')
        return redirect(url_for('admin_settings.application_periods'))
    
    # Ajouter l'année courante comme valeur par défaut
    current_year = datetime.now().year
    return render_template('admin/settings/application_period_form.html', period=None, current_year=current_year)

@admin_settings_bp.route('/application-periods/<int:period_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_application_period(period_id):
    """Modifier une période d'inscription"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    period = ApplicationPeriod.query.get_or_404(period_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        promotion_year = request.form.get('promotion_year')
        is_active = 'is_active' in request.form
        description = request.form.get('description')
        
        # Validation
        if not name or not start_date_str or not end_date_str or not promotion_year:
            flash('Tous les champs requis doivent être remplis.', 'danger')
            return redirect(url_for('admin_settings.edit_application_period', period_id=period_id))
        
        # Conversion des dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            promotion_year = int(promotion_year)
        except (ValueError, TypeError):
            flash('Format de date ou d\'année invalide.', 'danger')
            return redirect(url_for('admin_settings.edit_application_period', period_id=period_id))
        
        # Vérifier que la date de fin est après la date de début
        if end_date <= start_date:
            flash('La date de fin doit être postérieure à la date de début.', 'danger')
            return redirect(url_for('admin_settings.edit_application_period', period_id=period_id))
        
        # Si cette période est active, désactiver les autres
        if is_active and not period.is_active:
            active_periods = ApplicationPeriod.query.filter_by(is_active=True).all()
            for p in active_periods:
                p.is_active = False
        
        # Mettre à jour la période
        period.name = name
        period.start_date = start_date
        period.end_date = end_date
        period.promotion_year = promotion_year
        period.is_active = is_active
        period.description = description
        
        db.session.commit()
        
        flash(f'La période d\'inscription "{name}" a été mise à jour avec succès.', 'success')
        return redirect(url_for('admin_settings.application_periods'))
    
    # Ajouter l'année courante comme valeur par défaut
    current_year = datetime.now().year
    return render_template('admin/settings/application_period_form.html', period=period, current_year=current_year)

@admin_settings_bp.route('/application-periods/<int:period_id>/delete', methods=['POST'])
@login_required
def delete_application_period(period_id):
    """Supprimer une période d'inscription"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    period = ApplicationPeriod.query.get_or_404(period_id)
    
    name = period.name
    db.session.delete(period)
    db.session.commit()
    
    flash(f'La période d\'inscription "{name}" a été supprimée.', 'success')
    return redirect(url_for('admin_settings.application_periods'))

@admin_settings_bp.route('/application-periods/<int:period_id>/toggle', methods=['POST'])
@login_required
def toggle_application_period(period_id):
    """Activer/désactiver une période d'inscription"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    period = ApplicationPeriod.query.get_or_404(period_id)
    
    # Si on active cette période, désactiver les autres
    if not period.is_active:
        active_periods = ApplicationPeriod.query.filter_by(is_active=True).all()
        for p in active_periods:
            p.is_active = False
    
    period.is_active = not period.is_active
    db.session.commit()
    
    status = "activée" if period.is_active else "désactivée"
    flash(f'La période d\'inscription "{period.name}" a été {status}.', 'success')
    return redirect(url_for('admin_settings.application_periods'))

# Gestion des utilisateurs administratifs
@admin_settings_bp.route('/admin-users')
@login_required
def admin_users():
    """Liste des utilisateurs administratifs"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    admin_users = User.query.filter_by(is_admin=True).all()
    
    return render_template(
        'admin/settings/admin_users.html',
        admin_users=admin_users
    )

@admin_settings_bp.route('/admin-users/add', methods=['GET', 'POST'])
@login_required
def add_admin_user():
    """Ajouter un utilisateur administratif"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation
        if not username or not email or not password:
            flash('Tous les champs sont requis.', 'danger')
            return redirect(url_for('admin_settings.add_admin_user'))
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Un utilisateur avec cette adresse email existe déjà.', 'danger')
            return redirect(url_for('admin_settings.add_admin_user'))
        
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash('Un utilisateur avec ce nom d\'utilisateur existe déjà.', 'danger')
            return redirect(url_for('admin_settings.add_admin_user'))
        
        # Créer le nouvel utilisateur administratif
        new_admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True,
            is_active=True
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash(f'L\'administrateur {username} a été créé avec succès.', 'success')
        return redirect(url_for('admin_settings.admin_users'))
    
    return render_template('admin/settings/admin_user_form.html', user=None)

@admin_settings_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Modifier un utilisateur"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Empêcher la modification de son propre compte pour éviter de se bloquer
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier votre propre compte par cette interface.', 'danger')
        return redirect(url_for('admin_settings.users'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = True if request.form.get('is_admin') == 'on' else False
        is_active = True if request.form.get('is_active') == 'on' else False
        
        # Validation
        if not username or not email:
            flash('Le nom d\'utilisateur et l\'email sont requis.', 'danger')
            return redirect(url_for('admin_settings.edit_user', user_id=user_id))
        
        # Vérifier si l'utilisateur existe déjà (autre que celui-ci)
        existing_user = User.query.filter(User.email == email, User.id != user_id).first()
        if existing_user:
            flash('Un utilisateur avec cette adresse email existe déjà.', 'danger')
            return redirect(url_for('admin_settings.edit_user', user_id=user_id))
        
        existing_username = User.query.filter(User.username == username, User.id != user_id).first()
        if existing_username:
            flash('Un utilisateur avec ce nom d\'utilisateur existe déjà.', 'danger')
            return redirect(url_for('admin_settings.edit_user', user_id=user_id))
        
        # Mettre à jour l'utilisateur
        user.username = username
        user.email = email
        user.is_admin = is_admin
        user.is_active = is_active
        
        # Mettre à jour le mot de passe uniquement s'il est fourni
        if password:
            user.password_hash = generate_password_hash(password)
        
        db.session.commit()
        
        flash(f'L\'utilisateur {username} a été mis à jour avec succès.', 'success')
        return redirect(url_for('admin_settings.users'))
    
    return render_template('admin/settings/edit_user.html', user=user)

@admin_settings_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Supprimer un utilisateur"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Empêcher la suppression de son propre compte
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('admin_settings.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'L\'utilisateur {username} a été supprimé avec succès.', 'success')
    return redirect(url_for('admin_settings.users'))