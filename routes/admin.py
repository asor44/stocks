from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from models import Application, Candidate, Guardian, Document, User
from datetime import datetime
from utils.email import send_approval_email, send_rejection_email
from utils.integration import create_account_in_other_app, create_account_in_wordpress

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    # Count applications by status
    pending_count = Application.query.filter_by(status='pending').count()
    approved_count = Application.query.filter_by(status='approved').count()
    rejected_count = Application.query.filter_by(status='rejected').count()
    total_count = pending_count + approved_count + rejected_count
    
    # Get recent applications
    recent_applications = Application.query.order_by(Application.application_date.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        total_count=total_count,
        recent_applications=recent_applications
    )

@admin_bp.route('/applications')
@login_required
def applications():
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    status_filter = request.args.get('status', 'all')
    promotion_filter = request.args.get('promotion', 'all')
    
    query = Application.query
    
    # Filtre par statut
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Filtre par année de promotion
    if promotion_filter != 'all':
        try:
            promotion_year = int(promotion_filter)
            query = query.filter_by(promotion_year=promotion_year)
        except ValueError:
            pass
    
    # Récupération des applications avec tri
    applications = query.order_by(Application.application_date.desc()).all()
    
    # Récupération des années de promotion pour le filtre
    promotion_years = db.session.query(Application.promotion_year).distinct().filter(Application.promotion_year.isnot(None)).all()
    promotion_years = sorted([year[0] for year in promotion_years])
    
    return render_template(
        'admin/applications.html',
        applications=applications,
        status_filter=status_filter,
        promotion_filter=promotion_filter,
        promotion_years=promotion_years
    )

@admin_bp.route('/application/<int:application_id>')
@login_required
def application_detail(application_id):
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    application = Application.query.get_or_404(application_id)
    candidate = application.candidate
    guardians = candidate.guardians
    documents = application.documents
    
    from datetime import datetime
    
    return render_template(
        'admin/application_detail.html',
        application=application,
        candidate=candidate,
        guardians=guardians,
        documents=documents,
        now=datetime.now
    )

@admin_bp.route('/application/<int:application_id>/approve', methods=['POST'])
@login_required
def approve_application(application_id):
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    application = Application.query.get_or_404(application_id)
    candidate = application.candidate
    guardians = candidate.guardians
    
    # Update application status
    application.status = 'approved'
    application.review_date = datetime.utcnow()
    application.reviewed_by = current_user.id
    application.notes = request.form.get('notes', '')
    
    # Créer un nom d'utilisateur et vérifier les doublons
    username = f"{candidate.first_name.lower()}.{candidate.last_name.lower()}"
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        # Ajouter un suffixe numérique pour éviter les doublons
        import random
        username = f"{username}{random.randint(1, 999)}"
    
    # Create user account for candidate
    candidate_password = generate_random_password()
    candidate_user = User(
        username=username,
        email=candidate.email,
        password_hash=generate_password_hash(candidate_password),
        is_active=True
    )
    db.session.add(candidate_user)
    db.session.flush()
    
    # Link user to candidate
    candidate.user_id = candidate_user.id
    
    # Créer un compte dans l'autre application
    try:
        other_app_user_data = {
            'username': username,
            'email': candidate.email,
            'password': candidate_password,
            'first_name': candidate.first_name,
            'last_name': candidate.last_name,
            'role': 'candidate'
        }
        other_app_result = create_account_in_other_app(other_app_user_data)
        if not other_app_result['success']:
            print(f"Erreur lors de la création du compte dans l'autre application: {other_app_result['message']}")
    except Exception as e:
        print(f"Exception lors de la création du compte dans l'autre application: {str(e)}")
    
    # Créer un compte WordPress
    try:
        wp_user_data = {
            'username': username,
            'email': candidate.email,
            'password': candidate_password,
            'first_name': candidate.first_name,
            'last_name': candidate.last_name,
            'roles': ['subscriber']
        }
        wp_result = create_account_in_wordpress(wp_user_data)
        if not wp_result['success']:
            print(f"Erreur lors de la création du compte WordPress: {wp_result['message']}")
    except Exception as e:
        print(f"Exception lors de la création du compte WordPress: {str(e)}")
    
    # Create user accounts for guardians
    guardian_accounts = []
    for guardian in guardians:
        # Créer un nom d'utilisateur et vérifier les doublons
        guardian_username = f"{guardian.first_name.lower()}.{guardian.last_name.lower()}"
        existing_guardian_user = User.query.filter_by(username=guardian_username).first()
        if existing_guardian_user:
            # Ajouter un suffixe numérique pour éviter les doublons
            import random
            guardian_username = f"{guardian_username}{random.randint(1, 999)}"
            
        guardian_password = generate_random_password()
        guardian_user = User(
            username=guardian_username,
            email=guardian.email,
            password_hash=generate_password_hash(guardian_password),
            is_active=True
        )
        db.session.add(guardian_user)
        db.session.flush()
        
        # Link user to guardian
        guardian.user_id = guardian_user.id
        
        guardian_accounts.append({
            'guardian': guardian,
            'password': guardian_password
        })
        
        # Créer un compte dans l'autre application pour le tuteur
        try:
            other_app_guardian_data = {
                'username': guardian_username,
                'email': guardian.email,
                'password': guardian_password,
                'first_name': guardian.first_name,
                'last_name': guardian.last_name,
                'role': 'guardian'
            }
            other_app_result = create_account_in_other_app(other_app_guardian_data)
            if not other_app_result['success']:
                print(f"Erreur lors de la création du compte tuteur dans l'autre application: {other_app_result['message']}")
        except Exception as e:
            print(f"Exception lors de la création du compte tuteur dans l'autre application: {str(e)}")
        
        # Créer un compte WordPress pour le tuteur
        try:
            wp_guardian_data = {
                'username': guardian_username,
                'email': guardian.email,
                'password': guardian_password,
                'first_name': guardian.first_name,
                'last_name': guardian.last_name,
                'roles': ['subscriber']
            }
            wp_result = create_account_in_wordpress(wp_guardian_data)
            if not wp_result['success']:
                print(f"Erreur lors de la création du compte WordPress pour le tuteur: {wp_result['message']}")
        except Exception as e:
            print(f"Exception lors de la création du compte WordPress pour le tuteur: {str(e)}")
    
    db.session.commit()
    
    # Send approval email
    send_approval_email(
        candidate=candidate,
        candidate_password=candidate_password,
        guardian_accounts=guardian_accounts
    )
    
    flash(f'La candidature de {candidate.first_name} {candidate.last_name} a été approuvée. Des comptes ont été créés à la fois dans cette application, dans l\'autre application et sur WordPress.', 'success')
    return redirect(url_for('admin.application_detail', application_id=application_id))

@admin_bp.route('/application/<int:application_id>/reject', methods=['POST'])
@login_required
def reject_application(application_id):
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    application = Application.query.get_or_404(application_id)
    candidate = application.candidate
    
    # Update application status
    application.status = 'rejected'
    application.review_date = datetime.utcnow()
    application.reviewed_by = current_user.id
    application.notes = request.form.get('notes', '')
    
    db.session.commit()
    
    # Send rejection email
    send_rejection_email(
        candidate=candidate,
        rejection_reason=application.notes
    )
    
    flash(f'La candidature de {candidate.first_name} {candidate.last_name} a été rejetée.', 'warning')
    return redirect(url_for('admin.application_detail', application_id=application_id))

@admin_bp.route('/document/<int:document_id>')
@login_required
def view_document(document_id):
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    document = Document.query.get_or_404(document_id)
    
    # Get the directory and filename
    directory = current_app.config['UPLOAD_FOLDER']
    filename = document.filename
    
    return send_from_directory(directory, filename, as_attachment=True, download_name=document.original_filename)

@admin_bp.route('/application/<int:application_id>/delete', methods=['POST'])
@login_required
def delete_application(application_id):
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    application = Application.query.get_or_404(application_id)
    candidate = application.candidate
    
    # Supprimer d'abord les documents associés
    for document in application.documents:
        # Supprimer le fichier du stockage
        try:
            import os
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier {document.filename}: {str(e)}")
        
        # Supprimer les processus de signature associés s'ils existent
        from models import SigningProcess
        signing_processes = SigningProcess.query.filter_by(document_id=document.id).all()
        for signing_process in signing_processes:
            db.session.delete(signing_process)
        
        # Supprimer le document de la base de données
        db.session.delete(document)
    
    # Supprimer l'application
    db.session.delete(application)
    
    # Supprimer les comptes utilisateurs associés (optionnel selon le paramètre)
    if request.form.get('delete_candidate', 'false') == 'true':
        # Importer les fonctions d'intégration
        from utils.integration import delete_account_in_other_app, delete_account_in_wordpress
        from models import MedicalInformation, PhysicalMeasurements, AppointmentBooking
        
        # Supprimer les informations médicales associées
        medical_info = MedicalInformation.query.filter_by(candidate_id=candidate.id).first()
        if medical_info:
            db.session.delete(medical_info)
        
        # Supprimer les mesures physiques associées
        measurements = PhysicalMeasurements.query.filter_by(candidate_id=candidate.id).first()
        if measurements:
            db.session.delete(measurements)
        
        # Supprimer les rendez-vous associés
        bookings = AppointmentBooking.query.filter_by(candidate_id=candidate.id).all()
        for booking in bookings:
            db.session.delete(booking)
        
        # Supprimer les comptes des gardiens
        for guardian in candidate.guardians:
            # Supprimer le compte utilisateur du gardien dans la seconde application
            if guardian.user:
                try:
                    delete_result = delete_account_in_other_app(guardian.user.username)
                    if not delete_result['success']:
                        print(f"Erreur lors de la suppression du compte guardien dans l'autre application: {delete_result['message']}")
                except Exception as e:
                    print(f"Exception lors de la suppression du compte guardien dans l'autre application: {str(e)}")
                
                # Supprimer le compte WordPress du gardien
                try:
                    wp_delete_result = delete_account_in_wordpress(guardian.user.username)
                    if not wp_delete_result['success']:
                        print(f"Erreur lors de la suppression du compte WordPress du gardien: {wp_delete_result['message']}")
                except Exception as e:
                    print(f"Exception lors de la suppression du compte WordPress du gardien: {str(e)}")
                
                # Supprimer le compte utilisateur local du gardien
                db.session.delete(guardian.user)
            
            # Supprimer le gardien
            db.session.delete(guardian)
        
        # Supprimer le compte du candidat dans la seconde application
        if candidate.user:
            try:
                delete_result = delete_account_in_other_app(candidate.user.username)
                if not delete_result['success']:
                    print(f"Erreur lors de la suppression du compte candidat dans l'autre application: {delete_result['message']}")
            except Exception as e:
                print(f"Exception lors de la suppression du compte candidat dans l'autre application: {str(e)}")
            
            # Supprimer le compte WordPress du candidat
            try:
                wp_delete_result = delete_account_in_wordpress(candidate.user.username)
                if not wp_delete_result['success']:
                    print(f"Erreur lors de la suppression du compte WordPress du candidat: {wp_delete_result['message']}")
            except Exception as e:
                print(f"Exception lors de la suppression du compte WordPress du candidat: {str(e)}")
            
            # Supprimer le compte utilisateur local du candidat
            db.session.delete(candidate.user)
        
        # Supprimer le candidat
        db.session.delete(candidate)
    
    db.session.commit()
    
    flash(f'La candidature #{application_id} a été supprimée avec succès.', 'success')
    return redirect(url_for('admin.applications'))

@admin_bp.route('/application/<int:application_id>/update-promotion', methods=['POST'])
@login_required
def update_application_promotion(application_id):
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('index'))
    
    application = Application.query.get_or_404(application_id)
    
    try:
        promotion_year = int(request.form.get('promotion_year', 0))
        if promotion_year > 0:
            application.promotion_year = promotion_year
            db.session.commit()
            flash(f'La candidature a été classée dans la promotion {promotion_year}.', 'success')
        else:
            flash('Année de promotion invalide.', 'danger')
    except ValueError:
        flash('Année de promotion invalide.', 'danger')
    
    return redirect(url_for('admin.application_detail', application_id=application_id))

def generate_random_password(length=12):
    import random
    import string
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))
