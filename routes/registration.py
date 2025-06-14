import os
import uuid
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session, send_file, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask_login import current_user, login_required
from app import db
from models import User, Candidate, Guardian, Application, Document, SigningProcess, MedicalInformation, PhysicalMeasurements, ApplicationPeriod
from utils.email import send_candidate_registration_email, send_approval_email, send_document_signing_request, send_guardian_signing_email
from utils.generate_documents import generate_blank_documents
from utils.pdf import generate_registration_pdf

registration_bp = Blueprint('registration', __name__, url_prefix='/registration')

# Routes pour la gestion de la signature de documents
@registration_bp.route('/document/view/<int:document_id>')
def view_document_by_id(document_id):
    """
    Affiche un document avec ses signatures
    """
    try:
        document = Document.query.get_or_404(document_id)
        print(f"DEBUG: Affichage du document ID {document_id}, type: {document.document_type}")
        print(f"DEBUG: Chemin du fichier enregistré: {document.file_path}")
        
        # Liste des emplacements possibles à vérifier
        possible_paths = [
            document.file_path,  # Chemin original enregistré
            os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', document.filename),  # Chemin absolu standard
            os.path.join(os.getcwd(), 'uploads', 'documents', document.filename),  # Chemin depuis le répertoire courant
            os.path.join(os.getcwd(), 'documents', document.filename),  # Chemin de secours
            os.path.join('/tmp/documents', document.filename)  # Chemin temporaire
        ]
        
        # Vérifier chaque chemin potentiel
        file_found = False
        valid_path = None
        
        for path in possible_paths:
            print(f"DEBUG: Vérification du chemin: {path}")
            if os.path.exists(path) and os.path.isfile(path):
                print(f"DEBUG: Fichier trouvé à {path}")
                valid_path = path
                file_found = True
                
                # Mettre à jour le chemin dans la base de données si différent de l'original
                if path != document.file_path:
                    print(f"DEBUG: Mise à jour du chemin de fichier dans la base de données")
                    document.file_path = path
                    db.session.commit()
                
                break
                
        if not file_found:
            print(f"ERREUR: Document introuvable dans tous les emplacements vérifiés")
            
            # Tenter de régénérer le document
            try:
                print(f"DEBUG: Tentative de régénération du document...")
                candidate = Candidate.query.get(document.application.candidate_id)
                application = document.application
                
                # Supprimer l'entrée existante
                db.session.delete(document)
                db.session.commit()
                
                # Générer un nouveau document du même type
                from utils.generate_documents import create_blank_pdf, SigningProcess
                
                # Créer le dossier au besoin
                upload_folder = current_app.config['UPLOAD_FOLDER']
                documents_dir = os.path.join(upload_folder, 'documents')
                os.makedirs(documents_dir, exist_ok=True)
                
                # Générer le nouveau fichier
                new_file_path = create_blank_pdf(document.document_type, candidate)
                filename = os.path.basename(new_file_path)
                
                # Créer une nouvelle entrée dans la base de données
                new_document = Document(
                    application_id=application.id,
                    filename=filename,
                    original_filename=f"{document.document_type}.pdf",
                    file_path=new_file_path,
                    document_type=document.document_type,
                    status='pending'
                )
                db.session.add(new_document)
                db.session.flush()
                
                # Créer le processus de signature
                signing_token = str(uuid.uuid4())
                signing_process = SigningProcess(
                    document_id=new_document.id,
                    signing_token=signing_token,
                    expiry_date=datetime.now() + timedelta(days=30)
                )
                db.session.add(signing_process)
                db.session.commit()
                
                print(f"DEBUG: Document régénéré avec succès à {new_file_path}")
                flash('Le document a été régénéré avec succès.', 'success')
                return send_file(new_file_path, as_attachment=False)
                
            except Exception as regen_error:
                print(f"ERREUR lors de la régénération: {str(regen_error)}")
                import traceback
                print(traceback.format_exc())
                flash('Document introuvable et impossible à régénérer. Merci de contacter l\'administrateur.', 'danger')
                return redirect(url_for('index'))
            
        # Envoi du fichier trouvé
        print(f"DEBUG: Envoi du fichier depuis {valid_path}")
        return send_file(valid_path, as_attachment=False)
        
    except Exception as e:
        print(f"ERREUR lors de l'affichage du document {document_id}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('Une erreur est survenue lors de l\'affichage du document.', 'danger')
        return redirect(url_for('index'))

@registration_bp.route('/document/sign/<int:document_id>', methods=['GET', 'POST'])
@login_required
def sign_document(document_id):
    """
    Permet à un utilisateur de signer un document
    """
    document = Document.query.get_or_404(document_id)
    signing_process = SigningProcess.query.filter_by(document_id=document.id).first()
    
    if not signing_process:
        flash('Processus de signature introuvable.', 'danger')
        return redirect(url_for('index'))
    
    # Vérifier si l'utilisateur actuel est le candidat ou un tuteur
    candidate = Candidate.query.filter_by(user_id=current_user.id).first()
    guardian = Guardian.query.filter_by(user_id=current_user.id).first()
    
    if not candidate and not guardian:
        flash('Vous n\'êtes pas autorisé à signer ce document.', 'danger')
        return redirect(url_for('index'))
    
    # Si c'est un tuteur, vérifier qu'il est bien associé au candidat
    if guardian and guardian.candidate_id != document.application.candidate_id:
        flash('Vous n\'êtes pas autorisé à signer ce document.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Signature du document
        acceptance = request.form.get('acceptance') == 'on'
        name = request.form.get('name')
        
        if not acceptance or not name:
            flash('Vous devez accepter les conditions et fournir votre nom complet pour signer.', 'warning')
            return render_template(
                'registration/sign_document.html',
                document=document,
                signing_process=signing_process
            )
        
        # Signature par le candidat ou le tuteur
        if candidate:
            signing_process.candidate_signed = True
            signing_process.candidate_signed_date = datetime.now()
            document.status = 'signed_candidate'
            
            # Vérifier s'il y a un tuteur à notifier
            guardian = Guardian.query.filter_by(candidate_id=candidate.id).first()
            if guardian and guardian.user_id:
                guardian_user = User.query.get(guardian.user_id)
                if guardian_user:
                    send_document_signing_request(guardian_user, document, signing_process)
                    flash(f'Document signé avec succès. Un email a été envoyé à {guardian.first_name} {guardian.last_name} pour signature.', 'success')
        
        elif guardian:
            signing_process.guardian_signed = True
            signing_process.guardian_signed_date = datetime.now()
            
            # Si le candidat a déjà signé, marquer comme complet
            if signing_process.candidate_signed:
                document.status = 'complete'
                flash('Document signé avec succès. Le processus de signature est maintenant complet.', 'success')
            else:
                document.status = 'signed_guardian'
                # Notification au candidat
                candidate_user = User.query.get(document.application.candidate.user_id)
                if candidate_user:
                    send_document_signing_request(candidate_user, document, signing_process)
                    flash(f'Document signé avec succès. Un email a été envoyé au candidat pour signature.', 'success')
        
        db.session.commit()
        
        # Rediriger vers l'étape 4 de l'inscription
        if candidate:
            return redirect(url_for('registration.multi_step_register', step=4, candidate_id=candidate.id))
        else:
            return redirect(url_for('index'))
    
    return render_template(
        'registration/sign_document.html',
        document=document,
        signing_process=signing_process
    )

@registration_bp.route('/generate_documents/<int:candidate_id>', methods=['GET'])
def generate_documents_manually(candidate_id):
    """
    Génère manuellement les documents pour un candidat et redirige vers l'étape 4
    """
    try:
        candidate = Candidate.query.get_or_404(candidate_id)
        application = Application.query.filter_by(candidate_id=candidate.id).first()
        
        # Si l'application n'existe pas, la créer
        if not application:
            active_period = ApplicationPeriod.query.filter_by(is_active=True).first()
            application = Application(
                candidate_id=candidate.id,
                promotion_year=active_period.promotion_year if active_period else None
            )
            db.session.add(application)
            db.session.commit()
        
        print(f"Génération manuelle des documents pour le candidat {candidate.id}")
        
        # Créer le dossier uploads/documents s'il n'existe pas
        upload_folder = current_app.config['UPLOAD_FOLDER']
        documents_dir = os.path.join(upload_folder, 'documents')
        os.makedirs(documents_dir, exist_ok=True)
        
        # Donner les permissions
        try:
            os.chmod(documents_dir, 0o777)
            print(f"Permissions accordées au dossier {documents_dir}")
        except Exception as e:
            print(f"Erreur lors de la modification des permissions: {str(e)}")
        
        # Supprimer les documents existants pour cet candidat
        documents = Document.query.filter_by(application_id=application.id).all()
        for doc in documents:
            try:
                if os.path.exists(doc.file_path):
                    os.remove(doc.file_path)
                    print(f"Fichier supprimé: {doc.file_path}")
                db.session.delete(doc)
            except Exception as e:
                print(f"Erreur lors de la suppression du document {doc.id}: {str(e)}")
        
        db.session.commit()
        
        # Générer de nouveaux documents
        from utils.generate_documents import generate_blank_documents
        new_documents = generate_blank_documents(candidate, application)
        
        if new_documents and len(new_documents) > 0:
            flash(f'Documents régénérés avec succès ({len(new_documents)} documents).', 'success')
        else:
            flash('Erreur lors de la génération des documents. Vérifiez les logs.', 'danger')
        
        return redirect(url_for('registration.multi_step_register', step=4, candidate_id=candidate.id))
    except Exception as e:
        print(f"ERREUR lors de la génération manuelle des documents: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash(f'Une erreur est survenue: {str(e)}', 'danger')
        return redirect(url_for('index'))

@registration_bp.route('/document/sign/token/<token>', methods=['GET', 'POST'])
def sign_document_with_token(token):
    """
    Permet à un utilisateur de signer un document via un token (sans authentification)
    """
    signing_process = SigningProcess.query.filter_by(signing_token=token).first_or_404()
    document = Document.query.get_or_404(signing_process.document_id)
    
    # Vérifier que le token n'est pas expiré
    if signing_process.expiry_date < datetime.now():
        flash('Le lien de signature a expiré.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Signature du document
        acceptance = request.form.get('acceptance') == 'on'
        name = request.form.get('name')
        is_guardian = request.form.get('signer_type') == 'guardian'
        
        if not acceptance or not name:
            flash('Vous devez accepter les conditions et fournir votre nom complet pour signer.', 'warning')
            return render_template(
                'registration/sign_document_token.html',
                document=document,
                signing_process=signing_process
            )
        
        # Signature par le candidat ou le tuteur selon le choix
        if is_guardian:
            signing_process.guardian_signed = True
            signing_process.guardian_signed_date = datetime.now()
            
            # Si le candidat a déjà signé, marquer comme complet
            if signing_process.candidate_signed:
                document.status = 'complete'
                flash('Document signé avec succès. Le processus de signature est maintenant complet.', 'success')
            else:
                document.status = 'signed_guardian'
        else:
            signing_process.candidate_signed = True
            signing_process.candidate_signed_date = datetime.now()
            
            # Si le tuteur a déjà signé, marquer comme complet
            if signing_process.guardian_signed:
                document.status = 'complete'
                flash('Document signé avec succès. Le processus de signature est maintenant complet.', 'success')
            else:
                document.status = 'signed_candidate'
        
        db.session.commit()
        
        return render_template('registration/signature_success.html')
    
    return render_template(
        'registration/sign_document_token.html',
        document=document,
        signing_process=signing_process
    )

@registration_bp.route('/generate-documents/<int:candidate_id>')
def generate_signing_documents(candidate_id):
    """
    Génère les documents à signer pour un candidat
    """
    candidate = Candidate.query.get_or_404(candidate_id)
    
    # Vérifier si une application existe déjà
    application = Application.query.filter_by(candidate_id=candidate.id).first()
    
    if not application:
        # Créer une application si elle n'existe pas
        application = Application(
            candidate_id=candidate.id,
            status='pending',
            promotion_year=datetime.now().year
        )
        db.session.add(application)
        db.session.commit()
    
    # Générer les documents
    documents = generate_blank_documents(candidate, application)
    
    flash('Les documents ont été générés avec succès. Vous pouvez maintenant les signer.', 'success')
    return redirect(url_for('registration.multi_step_register', step=4, candidate_id=candidate.id))

# Route pour le formulaire d'inscription en plusieurs étapes
@registration_bp.route('/multi-step-register/<int:step>', methods=['GET', 'POST'])
@registration_bp.route('/multi-step-register/<int:step>/<int:candidate_id>', methods=['GET', 'POST'])
def multi_step_register(step, candidate_id=None):
    """
    Processus d'inscription en plusieurs étapes.
    
    Args:
        step (int): L'étape actuelle du processus d'inscription (1-5)
        candidate_id (int, optional): L'ID du candidat si déjà créé
    """
    # Ajouter une fonction pour obtenir le répertoire courant
    def get_cwd():
        return os.getcwd()
    # Rendre la fonction disponible dans le template
    current_app.jinja_env.globals.update(get_cwd=get_cwd)
    if step < 1 or step > 5:
        flash('Étape invalide.', 'danger')
        return redirect(url_for('registration.multi_step_register', step=1))
    
    # Vérifier s'il existe une période d'inscription active
    # Sauf si le candidat existe déjà (permettre de continuer une candidature en cours)
    active_period = ApplicationPeriod.query.filter_by(is_active=True).first()
    today = datetime.now().date()
    
    if not candidate_id and step == 1:
        if not active_period:
            flash('Aucune période d\'inscription n\'est actuellement active. Veuillez réessayer ultérieurement.', 'danger')
            return redirect(url_for('index'))
        
        if today < active_period.start_date:
            flash(f'La période d\'inscription n\'a pas encore commencé. Les inscriptions débuteront le {active_period.start_date.strftime("%d/%m/%Y")}.', 'warning')
            return redirect(url_for('index'))
        
        if today > active_period.end_date:
            flash(f'La période d\'inscription est terminée depuis le {active_period.end_date.strftime("%d/%m/%Y")}.', 'warning')
            return redirect(url_for('index'))
        
    # Si un ID de candidat est fourni, récupérer le candidat existant
    candidate = None
    if candidate_id:
        candidate = Candidate.query.get_or_404(candidate_id)
    
    if request.method == 'POST':
        try:
            # Étape 1 - Informations personnelles
            if step == 1:
                # Vérifier que les mots de passe correspondent
                password = request.form.get('password')
                password_confirm = request.form.get('password_confirm')
                
                if password != password_confirm:
                    flash('Les mots de passe ne correspondent pas.', 'danger')
                    context = prepare_multi_step_template_context(step, candidate_id)
                    return render_template('registration/multi_step_register.html', **context)
                
                # Créer un compte utilisateur
                username = f"{request.form.get('first_name').lower()}.{request.form.get('last_name').lower()}"
                # Vérifier si l'email ou le username existent déjà
                existing_email = User.query.filter_by(email=request.form.get('email')).first()
                existing_username = User.query.filter_by(username=username).first()
                
                if existing_email:
                    flash('Cette adresse email est déjà utilisée.', 'danger')
                    context = prepare_multi_step_template_context(step, candidate_id)
                    return render_template('registration/multi_step_register.html', **context)
                    
                if existing_username:
                    # Ajouter un suffixe numérique pour éviter les doublons
                    import random
                    username = f"{username}{random.randint(1, 999)}"
                    
                user = User(
                    username=username,
                    email=request.form.get('email'),
                    password_hash=generate_password_hash(password),
                    is_active=True
                )
                db.session.add(user)
                db.session.flush()  # Pour obtenir l'ID de l'utilisateur
                
                # Créer ou mettre à jour les données du candidat
                if candidate:
                    # Mettre à jour le candidat existant
                    candidate.user_id = user.id
                    candidate.first_name = request.form.get('first_name')
                    candidate.last_name = request.form.get('last_name')
                    candidate.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d')
                    candidate.nationality = request.form.get('nationality')
                    candidate.birth_place = request.form.get('birth_place')
                    candidate.birth_place_postal_code = request.form.get('birth_place_postal_code')
                    candidate.birth_place_city = request.form.get('birth_place_city')
                    candidate.address = request.form.get('address')
                    candidate.city = request.form.get('city')
                    candidate.postal_code = request.form.get('postal_code')
                    candidate.phone = request.form.get('phone')
                    candidate.email = request.form.get('email')
                    candidate.school = request.form.get('school')
                    candidate.grade = request.form.get('grade')
                    candidate.first_aid_certified = request.form.get('first_aid_certified') == 'on'
                    candidate.application_status = 'step2'
                    
                    # Importer la fonction d'envoi d'email
                    from utils.email import send_step_completion_email
                else:
                    # Créer un nouveau candidat
                    candidate_data = {
                        'user_id': user.id,
                        'first_name': request.form.get('first_name'),
                        'last_name': request.form.get('last_name'),
                        'date_of_birth': datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d'),
                        'nationality': request.form.get('nationality'),
                        'birth_place': request.form.get('birth_place'),
                        'birth_place_postal_code': request.form.get('birth_place_postal_code'),
                        'birth_place_city': request.form.get('birth_place_city'),
                        'address': request.form.get('address'),
                        'city': request.form.get('city'),
                        'postal_code': request.form.get('postal_code'),
                        'phone': request.form.get('phone'),
                        'email': request.form.get('email'),
                        'school': request.form.get('school'),
                        'grade': request.form.get('grade'),
                        'first_aid_certified': request.form.get('first_aid_certified') == 'on',
                        'application_status': 'step2'
                    }
                    candidate = Candidate(**candidate_data)
                    db.session.add(candidate)
                    db.session.flush()  # Pour obtenir l'ID du candidat
                
                # Traiter les fichiers optionnels (à ce stade)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                
                # Lettre de motivation
                if 'motivation_letter' in request.files and request.files['motivation_letter'].filename:
                    motivation_file = request.files['motivation_letter']
                    motivation_filename = f"motivation_{candidate.id}_{uuid.uuid4().hex}.{motivation_file.filename.rsplit('.', 1)[1].lower()}"
                    motivation_path = os.path.join(upload_folder, motivation_filename)
                    motivation_file.save(motivation_path)
                    candidate.motivation_letter = motivation_filename
                
                # Carte vitale
                if 'vital_card_copy' in request.files and request.files['vital_card_copy'].filename:
                    vital_card_file = request.files['vital_card_copy']
                    vital_card_filename = f"vital_card_{candidate.id}_{uuid.uuid4().hex}.{vital_card_file.filename.rsplit('.', 1)[1].lower()}"
                    vital_card_path = os.path.join(upload_folder, vital_card_filename)
                    vital_card_file.save(vital_card_path)
                    candidate.vital_card_copy = vital_card_filename
                
                # Carte d'identité
                if 'id_card_copy' in request.files and request.files['id_card_copy'].filename:
                    id_card_file = request.files['id_card_copy']
                    id_card_filename = f"id_card_{candidate.id}_{uuid.uuid4().hex}.{id_card_file.filename.rsplit('.', 1)[1].lower()}"
                    id_card_path = os.path.join(upload_folder, id_card_filename)
                    id_card_file.save(id_card_path)
                    candidate.id_card_copy = id_card_filename
                
                # Attestation d'assurance
                if 'insurance_certificate' in request.files and request.files['insurance_certificate'].filename:
                    insurance_file = request.files['insurance_certificate']
                    insurance_filename = f"insurance_{candidate.id}_{uuid.uuid4().hex}.{insurance_file.filename.rsplit('.', 1)[1].lower()}"
                    insurance_path = os.path.join(upload_folder, insurance_filename)
                    insurance_file.save(insurance_path)
                    candidate.insurance_certificate = insurance_filename
                
                # Photo récente
                if 'recent_photo' in request.files and request.files['recent_photo'].filename:
                    photo_file = request.files['recent_photo']
                    photo_filename = f"photo_{candidate.id}_{uuid.uuid4().hex}.{photo_file.filename.rsplit('.', 1)[1].lower()}"
                    photo_path = os.path.join(upload_folder, photo_filename)
                    photo_file.save(photo_path)
                    candidate.recent_photo = photo_filename
                
                # Carte mutuelle
                if 'mutual_card_copy' in request.files and request.files['mutual_card_copy'].filename:
                    mutual_card_file = request.files['mutual_card_copy']
                    mutual_card_filename = f"mutual_card_{candidate.id}_{uuid.uuid4().hex}.{mutual_card_file.filename.rsplit('.', 1)[1].lower()}"
                    mutual_card_path = os.path.join(upload_folder, mutual_card_filename)
                    mutual_card_file.save(mutual_card_path)
                    candidate.mutual_card_copy = mutual_card_filename
                
                db.session.commit()
                return redirect(url_for('registration.multi_step_register', step=2, candidate_id=candidate.id))
            
            # Étape 2 - Mensurations
            elif step == 2:
                if not candidate:
                    flash('Veuillez compléter l\'étape 1 en premier.', 'danger')
                    return redirect(url_for('registration.multi_step_register', step=1))
                
                # Vérifier si des mensurations existent déjà
                measurements = PhysicalMeasurements.query.filter_by(candidate_id=candidate.id).first()
                
                if measurements:
                    # Mettre à jour les mensurations existantes
                    measurements.height = request.form.get('height')
                    measurements.weight = request.form.get('weight')
                    measurements.head_size = request.form.get('head_size')
                    measurements.neck_size = request.form.get('neck_size')
                    measurements.chest_size = request.form.get('chest_size')
                    measurements.waist_size = request.form.get('waist_size')
                    measurements.bust_height = request.form.get('bust_height')
                    measurements.inseam = request.form.get('inseam')
                    measurements.shoe_size = request.form.get('shoe_size')
                else:
                    # Créer de nouvelles mensurations
                    measurements_data = {
                        'candidate_id': candidate.id,
                        'height': request.form.get('height'),
                        'weight': request.form.get('weight'),
                        'head_size': request.form.get('head_size'),
                        'neck_size': request.form.get('neck_size'),
                        'chest_size': request.form.get('chest_size'),
                        'waist_size': request.form.get('waist_size'),
                        'bust_height': request.form.get('bust_height'),
                        'inseam': request.form.get('inseam'),
                        'shoe_size': request.form.get('shoe_size')
                    }
                    measurements = PhysicalMeasurements(**measurements_data)
                    db.session.add(measurements)
                
                # Mettre à jour le statut de candidature
                candidate.application_status = 'step3'
                db.session.commit()
                
                # Envoyer un email de confirmation de passage d'étape
                from utils.email import send_step_completion_email
                send_step_completion_email(candidate, 2, 3)
                print(f"Email de passage d'étape 2->3 envoyé à {candidate.email}")
                
                return redirect(url_for('registration.multi_step_register', step=3, candidate_id=candidate.id))
            
            # Étape 3 - Tuteurs et contact d'urgence
            elif step == 3:
                if not candidate:
                    flash('Veuillez compléter les étapes précédentes en premier.', 'danger')
                    return redirect(url_for('registration.multi_step_register', step=1))
                
                # Supprimer les tuteurs existants si présents
                if candidate.guardians:
                    for guardian in candidate.guardians:
                        db.session.delete(guardian)
                
                # Ajouter le premier tuteur (obligatoire) avec un compte utilisateur
                guardian1_email = request.form.get('guardian1_email')
                guardian1_first_name = request.form.get('guardian1_first_name')
                guardian1_last_name = request.form.get('guardian1_last_name')
                
                # Vérifier si un utilisateur avec cette adresse email existe déjà
                existing_user1 = User.query.filter_by(email=guardian1_email).first()
                
                if not existing_user1:
                    # Créer un mot de passe temporaire
                    temp_password1 = generate_random_password()
                    password_hash1 = generate_password_hash(temp_password1)
                    
                    # Créer un utilisateur pour le tuteur 1
                    # Vérifier que les valeurs ne sont pas None avant d'appeler lower()
                    if guardian1_first_name is None or guardian1_last_name is None:
                        # Si l'un des champs est None, utiliser des valeurs par défaut sécurisées
                        flash("Les informations du tuteur sont incomplètes. Veuillez remplir tous les champs.", "danger")
                        return render_template(
                            'registration/multi_step_register.html',
                            step=step,
                            candidate=candidate
                        )
                    
                    guardian1_username = f"{guardian1_first_name.lower()}.{guardian1_last_name.lower()}"
                    
                    # Vérifier si le nom d'utilisateur existe déjà
                    existing_username = User.query.filter_by(username=guardian1_username).first()
                    if existing_username:
                        # Ajouter un suffixe numérique pour éviter les doublons
                        import random
                        guardian1_username = f"{guardian1_username}{random.randint(1, 999)}"
                    
                    guardian1_user = User(
                        username=guardian1_username,
                        email=guardian1_email,
                        password_hash=password_hash1,
                        is_active=True
                    )
                    db.session.add(guardian1_user)
                    db.session.flush()  # Pour obtenir l'ID de l'utilisateur
                    
                    # Envoyer un email avec les identifiants temporaires
                    from utils.email import send_email
                    html_content1 = f"""
                    <h2>Bienvenue sur le portail d'inscription de l'Académie des Cadets</h2>
                    <p>Un compte tuteur a été créé pour vous. Vous pouvez vous connecter avec les identifiants suivants :</p>
                    <p><strong>Email :</strong> {guardian1_email}</p>
                    <p><strong>Mot de passe temporaire :</strong> {temp_password1}</p>
                    <p>Nous vous conseillons de changer ce mot de passe lors de votre prochaine connexion.</p>
                    <p>Pour vous connecter, cliquez sur le lien suivant :</p>
                    <p><a href="{url_for('auth.login', _external=True)}">Se connecter</a></p>
                    <p>Cordialement,<br>L'équipe de l'Académie des Cadets</p>
                    """
                    try:
                        send_result = send_email(
                            subject="Création de votre compte tuteur - Académie des Cadets",
                            recipient=guardian1_email,
                            html_body=html_content1
                        )
                        if send_result:
                            flash(f'Un compte tuteur a été créé pour {guardian1_email}. Les instructions de connexion ont été envoyées par email.', 'success')
                        else:
                            flash(f'Un compte tuteur a été créé pour {guardian1_email}, mais l\'email n\'a pas pu être envoyé. Mot de passe temporaire: {temp_password1}', 'warning')
                    except Exception as e:
                        print(f"Erreur lors de l'envoi de l'email au tuteur 1: {str(e)}")
                        flash(f'Un compte tuteur a été créé pour {guardian1_email}, mais l\'email n\'a pas pu être envoyé. Mot de passe temporaire: {temp_password1}', 'warning')
                    
                    # Créer le tuteur avec l'ID utilisateur
                    guardian1_data = {
                        'user_id': guardian1_user.id,
                        'candidate_id': candidate.id,
                        'first_name': guardian1_first_name,
                        'last_name': guardian1_last_name,
                        'relationship': request.form.get('guardian1_relationship'),
                        'email': guardian1_email,
                        'phone': request.form.get('guardian1_phone'),
                        'address': request.form.get('guardian1_address'),
                        'city': request.form.get('guardian1_city'),
                        'postal_code': request.form.get('guardian1_postal_code')
                    }
                else:
                    # Utiliser l'utilisateur existant
                    guardian1_data = {
                        'user_id': existing_user1.id,
                        'candidate_id': candidate.id,
                        'first_name': guardian1_first_name,
                        'last_name': guardian1_last_name,
                        'relationship': request.form.get('guardian1_relationship'),
                        'email': guardian1_email,
                        'phone': request.form.get('guardian1_phone'),
                        'address': request.form.get('guardian1_address'),
                        'city': request.form.get('guardian1_city'),
                        'postal_code': request.form.get('guardian1_postal_code')
                    }
                    
                guardian1 = Guardian(**guardian1_data)
                db.session.add(guardian1)
                
                # Ajouter le second tuteur si présent
                if request.form.get('has_second_guardian') == 'on' or request.form.get('add_second_guardian') == 'on':
                    guardian2_email = request.form.get('guardian2_email')
                    guardian2_first_name = request.form.get('guardian2_first_name')
                    guardian2_last_name = request.form.get('guardian2_last_name')
                    
                    # Vérifier si un utilisateur avec cette adresse email existe déjà
                    existing_user2 = User.query.filter_by(email=guardian2_email).first()
                    
                    if not existing_user2:
                        # Créer un mot de passe temporaire
                        temp_password2 = generate_random_password()
                        password_hash2 = generate_password_hash(temp_password2)
                        
                        # Créer un utilisateur pour le tuteur 2
                        # Vérifier que les valeurs ne sont pas None avant d'appeler lower()
                        if guardian2_first_name is None or guardian2_last_name is None:
                            # Si l'un des champs est None, utiliser des valeurs par défaut sécurisées
                            flash("Les informations du second tuteur sont incomplètes. Veuillez remplir tous les champs.", "danger")
                            return render_template(
                                'registration/multi_step_register.html',
                                step=step,
                                candidate=candidate
                            )
                        
                        guardian2_username = f"{guardian2_first_name.lower()}.{guardian2_last_name.lower()}"
                        
                        # Vérifier si le nom d'utilisateur existe déjà
                        existing_username2 = User.query.filter_by(username=guardian2_username).first()
                        if existing_username2:
                            # Ajouter un suffixe numérique pour éviter les doublons
                            import random
                            guardian2_username = f"{guardian2_username}{random.randint(1, 999)}"
                        
                        guardian2_user = User(
                            username=guardian2_username,
                            email=guardian2_email,
                            password_hash=password_hash2,
                            is_active=True
                        )
                        db.session.add(guardian2_user)
                        db.session.flush()  # Pour obtenir l'ID de l'utilisateur
                        
                        # Envoyer un email avec les identifiants temporaires
                        from utils.email import send_email
                        html_content2 = f"""
                        <h2>Bienvenue sur le portail d'inscription de l'Académie des Cadets</h2>
                        <p>Un compte tuteur a été créé pour vous. Vous pouvez vous connecter avec les identifiants suivants :</p>
                        <p><strong>Email :</strong> {guardian2_email}</p>
                        <p><strong>Mot de passe temporaire :</strong> {temp_password2}</p>
                        <p>Nous vous conseillons de changer ce mot de passe lors de votre prochaine connexion.</p>
                        <p>Pour vous connecter, cliquez sur le lien suivant :</p>
                        <p><a href="{url_for('auth.login', _external=True)}">Se connecter</a></p>
                        <p>Cordialement,<br>L'équipe de l'Académie des Cadets</p>
                        """
                        try:
                            send_result = send_email(
                                subject="Création de votre compte tuteur - Académie des Cadets",
                                recipient=guardian2_email,
                                html_body=html_content2
                            )
                            if send_result:
                                flash(f'Un compte tuteur a été créé pour {guardian2_email}. Les instructions de connexion ont été envoyées par email.', 'success')
                            else:
                                flash(f'Un compte tuteur a été créé pour {guardian2_email}, mais l\'email n\'a pas pu être envoyé. Mot de passe temporaire: {temp_password2}', 'warning')
                        except Exception as e:
                            print(f"Erreur lors de l'envoi de l'email au tuteur 2: {str(e)}")
                            flash(f'Un compte tuteur a été créé pour {guardian2_email}, mais l\'email n\'a pas pu être envoyé. Mot de passe temporaire: {temp_password2}', 'warning')
                        
                        # Créer le tuteur avec l'ID utilisateur
                        guardian2_data = {
                            'user_id': guardian2_user.id,
                            'candidate_id': candidate.id,
                            'first_name': guardian2_first_name,
                            'last_name': guardian2_last_name,
                            'relationship': request.form.get('guardian2_relationship'),
                            'email': guardian2_email,
                            'phone': request.form.get('guardian2_phone'),
                            'address': request.form.get('guardian2_address'),
                            'city': request.form.get('guardian2_city'),
                            'postal_code': request.form.get('guardian2_postal_code')
                        }
                    else:
                        # Utiliser l'utilisateur existant
                        guardian2_data = {
                            'user_id': existing_user2.id,
                            'candidate_id': candidate.id,
                            'first_name': guardian2_first_name,
                            'last_name': guardian2_last_name,
                            'relationship': request.form.get('guardian2_relationship'),
                            'email': guardian2_email,
                            'phone': request.form.get('guardian2_phone'),
                            'address': request.form.get('guardian2_address'),
                            'city': request.form.get('guardian2_city'),
                            'postal_code': request.form.get('guardian2_postal_code')
                        }
                        
                    guardian2 = Guardian(**guardian2_data)
                    db.session.add(guardian2)
                
                # Mettre à jour les informations de contact d'urgence
                candidate.emergency_contact_first_name = request.form.get('emergency_contact_first_name')
                candidate.emergency_contact_last_name = request.form.get('emergency_contact_last_name')
                candidate.emergency_contact_phone = request.form.get('emergency_contact_phone')
                candidate.emergency_contact_name = f"{request.form.get('emergency_contact_first_name')} {request.form.get('emergency_contact_last_name')}"
                
                # Mettre à jour le statut de candidature
                candidate.application_status = 'step4'
                db.session.commit()
                
                # Envoyer un email de confirmation de passage d'étape
                from utils.email import send_step_completion_email
                send_step_completion_email(candidate, 3, 4)
                print(f"Email de passage d'étape 3->4 envoyé à {candidate.email}")
                
                return redirect(url_for('registration.multi_step_register', step=4, candidate_id=candidate.id))
            
            # Étape 4 - Documents à signer
            elif step == 4:
                print("\n=== ÉTAPE 4 - DÉBUT ===")
                if not candidate:
                    flash('Veuillez compléter les étapes précédentes en premier.', 'danger')
                    return redirect(url_for('registration.multi_step_register', step=1))
                
                print(f"Candidat trouvé avec ID: {candidate.id}")
                
                # Créer une application si elle n'existe pas
                application = Application.query.filter_by(candidate_id=candidate.id).first()
                
                # Récupérer la période d'inscription active pour définir l'année de promotion
                active_period = ApplicationPeriod.query.filter_by(is_active=True).first()
                
                if not application:
                    print(f"Aucune application existante pour le candidat {candidate.id}. Création en cours...")
                    application = Application(
                        candidate_id=candidate.id,
                        promotion_year=active_period.promotion_year if active_period else None
                    )
                    db.session.add(application)
                    db.session.commit()  # Commit immédiatement pour avoir l'ID persisté
                    print(f"Nouvelle application créée avec ID: {application.id}")
                else:
                    print(f"Application existante trouvée avec ID: {application.id}")
                
                # Récupérer les documents existants à signer
                try:
                    documents = Document.query.filter_by(application_id=application.id).all()
                    document_count = len(documents) if documents else 0
                    print(f"Nombre de documents trouvés: {document_count}")
                    
                    if document_count > 0:
                        for i, doc in enumerate(documents):
                            print(f"Document {i+1}: {doc.document_type}, statut: {doc.status}, ID: {doc.id}")
                    
                    # Générer automatiquement les documents s'ils n'existent pas déjà
                    if not documents or document_count == 0:
                        print(f"Aucun document trouvé. Génération pour le candidat {candidate.id}")
                        documents = generate_blank_documents(candidate, application)
                        # Le commit est fait dans generate_blank_documents
                        generated_count = len(documents) if documents else 0
                        print(f"Documents générés: {generated_count}")
                        
                        if generated_count > 0:
                            flash('Les documents ont été générés automatiquement. Vous pouvez maintenant les signer.', 'success')
                        else:
                            print("ERREUR: Aucun document n'a été généré! Vérifiez les logs pour plus de détails.")
                            flash('Une erreur est survenue lors de la génération des documents. Veuillez réessayer.', 'danger')
                    
                    # Rafraîchir la liste des documents depuis la base de données
                    documents = Document.query.filter_by(application_id=application.id).all()
                    print(f"Après rafraîchissement, {len(documents) if documents else 0} documents trouvés")
                    
                    # Vérifier que tous les documents ont un chemin de fichier valide
                    for doc in documents:
                        if not os.path.exists(doc.file_path):
                            print(f"ATTENTION: Le fichier {doc.file_path} n'existe pas sur le disque")
                            
                            # Essayer de retrouver le fichier avec seulement le nom de fichier
                            documents_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
                            corrected_path = os.path.join(documents_dir, doc.filename)
                            
                            if os.path.exists(corrected_path):
                                print(f"Fichier trouvé à {corrected_path}, mise à jour du chemin dans la base de données")
                                doc.file_path = corrected_path
                                db.session.add(doc)
                        else:
                            print(f"Document {doc.id} a un fichier valide: {doc.file_path}")
                    
                    db.session.commit()
                
                except Exception as e:
                    print(f"ERREUR lors de la récupération ou génération des documents: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    flash('Une erreur est survenue. Veuillez contacter l\'administrateur.', 'danger')
                    documents = []
                
                # Afficher le formulaire avec les documents générés
                if request.method == 'GET':
                    print(f"Affichage du formulaire avec {len(documents)} documents")
                    for doc in documents:
                        print(f"Document à afficher: ID={doc.id}, Type={doc.document_type}, Statut={doc.status}, Chemin={doc.file_path}")
                    
                    return render_template(
                        'registration/multi_step_register.html',
                        step=step,
                        candidate=candidate,
                        documents=documents
                    )
                
                # Vérifier si tous les documents requis sont présents
                missing_documents = []
                
                # Vérifier s'il manque des documents d'identité qui n'ont pas été téléversés à l'étape 1
                if not candidate.motivation_letter:
                    if not 'motivation_letter' in request.files or not request.files['motivation_letter'].filename:
                        missing_documents.append("Lettre de motivation")
                
                if not candidate.vital_card_copy:
                    if not 'vital_card_copy' in request.files or not request.files['vital_card_copy'].filename:
                        missing_documents.append("Copie de la carte vitale")
                
                if not candidate.id_card_copy:
                    if not 'id_card_copy' in request.files or not request.files['id_card_copy'].filename:
                        missing_documents.append("Copie de la carte d'identité")
                
                if not candidate.insurance_certificate:
                    if not 'insurance_certificate' in request.files or not request.files['insurance_certificate'].filename:
                        missing_documents.append("Attestation d'assurance")
                
                if not candidate.recent_photo:
                    if not 'recent_photo' in request.files or not request.files['recent_photo'].filename:
                        missing_documents.append("Photo récente")
                
                # Vérifier si les documents signés sont présents et complets
                # Compter les documents où le statut est 'complete'
                parental_auth = Document.query.filter_by(application_id=application.id, document_type='parental_auth', status='complete').first()
                if not parental_auth:
                    missing_documents.append("Autorisation parentale signée")
                
                cadet_declaration = Document.query.filter_by(application_id=application.id, document_type='cadet_declaration', status='complete').first()
                if not cadet_declaration:
                    missing_documents.append("Déclaration du cadet signée")
                
                image_rights = Document.query.filter_by(application_id=application.id, document_type='image_rights', status='complete').first()
                if not image_rights:
                    missing_documents.append("Droit à l'image signé")
                
                medical_certificate = Document.query.filter_by(application_id=application.id, document_type='medical_certificate', status='complete').first()
                if not medical_certificate:
                    missing_documents.append("Certificat médical signé")
                
                rules = Document.query.filter_by(application_id=application.id, document_type='rules', status='complete').first()
                if not rules:
                    missing_documents.append("Règlement ACADEF signé")
                
                # S'il manque des documents, afficher un message et retourner à l'étape 4
                if missing_documents:
                    missing_docs_str = ", ".join(missing_documents)
                    flash(f'Documents manquants: {missing_docs_str}. Veuillez téléverser tous les documents obligatoires pour continuer.', 'danger')
                    
                    context = prepare_multi_step_template_context(
                        step=step, 
                        candidate=candidate,
                        missing_documents=missing_documents
                    )
                    return render_template('registration/multi_step_register.html', **context)
                
                # Traiter les fichiers d'identité manquants
                upload_folder = current_app.config['UPLOAD_FOLDER']
                
                if not candidate.motivation_letter and 'motivation_letter' in request.files and request.files['motivation_letter'].filename:
                    motivation_file = request.files['motivation_letter']
                    motivation_filename = f"motivation_{candidate.id}_{uuid.uuid4().hex}.{motivation_file.filename.rsplit('.', 1)[1].lower()}"
                    motivation_path = os.path.join(upload_folder, motivation_filename)
                    motivation_file.save(motivation_path)
                    candidate.motivation_letter = motivation_filename
                
                if not candidate.vital_card_copy and 'vital_card_copy' in request.files and request.files['vital_card_copy'].filename:
                    vital_card_file = request.files['vital_card_copy']
                    vital_card_filename = f"vital_card_{candidate.id}_{uuid.uuid4().hex}.{vital_card_file.filename.rsplit('.', 1)[1].lower()}"
                    vital_card_path = os.path.join(upload_folder, vital_card_filename)
                    vital_card_file.save(vital_card_path)
                    candidate.vital_card_copy = vital_card_filename
                
                if not candidate.id_card_copy and 'id_card_copy' in request.files and request.files['id_card_copy'].filename:
                    id_card_file = request.files['id_card_copy']
                    id_card_filename = f"id_card_{candidate.id}_{uuid.uuid4().hex}.{id_card_file.filename.rsplit('.', 1)[1].lower()}"
                    id_card_path = os.path.join(upload_folder, id_card_filename)
                    id_card_file.save(id_card_path)
                    candidate.id_card_copy = id_card_filename
                
                if not candidate.insurance_certificate and 'insurance_certificate' in request.files and request.files['insurance_certificate'].filename:
                    insurance_file = request.files['insurance_certificate']
                    insurance_filename = f"insurance_{candidate.id}_{uuid.uuid4().hex}.{insurance_file.filename.rsplit('.', 1)[1].lower()}"
                    insurance_path = os.path.join(upload_folder, insurance_filename)
                    insurance_file.save(insurance_path)
                    candidate.insurance_certificate = insurance_filename
                
                if not candidate.recent_photo and 'recent_photo' in request.files and request.files['recent_photo'].filename:
                    photo_file = request.files['recent_photo']
                    photo_filename = f"photo_{candidate.id}_{uuid.uuid4().hex}.{photo_file.filename.rsplit('.', 1)[1].lower()}"
                    photo_path = os.path.join(upload_folder, photo_filename)
                    photo_file.save(photo_path)
                    candidate.recent_photo = photo_filename
                
                if not candidate.mutual_card_copy and 'mutual_card_copy' in request.files and request.files['mutual_card_copy'].filename:
                    mutual_card_file = request.files['mutual_card_copy']
                    mutual_card_filename = f"mutual_card_{candidate.id}_{uuid.uuid4().hex}.{mutual_card_file.filename.rsplit('.', 1)[1].lower()}"
                    mutual_card_path = os.path.join(upload_folder, mutual_card_filename)
                    mutual_card_file.save(mutual_card_path)
                    candidate.mutual_card_copy = mutual_card_filename
                
                # Les documents signés sont maintenant générés automatiquement à l'étape 4
                # et mis à jour en fonction des signatures électroniques
                
                # Vérifions si les documents de signature existent déjà pour cette application
                documents_by_type = {}
                for doc in documents:
                    documents_by_type[doc.document_type] = doc
                
                # Si les documents n'existent pas encore, ou ont été régénérés, les ajouter à la base de données
                document_types = ['parental_auth', 'cadet_declaration', 'image_rights', 'medical_certificate', 'rules']
                
                # Vérifions les processus de signature pour chaque document
                for doc_type in document_types:
                    doc = documents_by_type.get(doc_type)
                    
                    # Si le document n'existe pas déjà, vérifier s'il a été chargé manuellement
                    if not doc and f'signed_{doc_type}' in request.files and request.files[f'signed_{doc_type}'].filename:
                        file = request.files[f'signed_{doc_type}']
                        filename = f"{doc_type}_{candidate.id}_{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)
                        
                        # Créer un nouveau document dans la base de données
                        doc = Document(
                            application_id=application.id,
                            filename=filename,
                            original_filename=file.filename,
                            file_path=file_path,
                            document_type=doc_type,
                            status='complete'
                        )
                        db.session.add(doc)
                
                # Mettre à jour le statut de candidature
                candidate.application_status = 'step5'
                db.session.commit()
                
                # Envoyer un email de confirmation de passage d'étape
                from utils.email import send_step_completion_email
                send_step_completion_email(candidate, 4, 5)
                print(f"Email de passage d'étape 4->5 envoyé à {candidate.email}")
                
                return redirect(url_for('registration.multi_step_register', step=5, candidate_id=candidate.id))
            
            # Étape 5 - Finalisation
            elif step == 5:
                if not candidate:
                    flash('Veuillez compléter les étapes précédentes en premier.', 'danger')
                    return redirect(url_for('registration.multi_step_register', step=1))
                
                # Vérifier que les conditions sont acceptées
                if request.form.get('terms_agreement') != 'on':
                    flash('Vous devez accepter les conditions pour finaliser votre candidature.', 'danger')
                    context = prepare_multi_step_template_context(step, candidate=candidate)
                    return render_template('registration/multi_step_register.html', **context)
                
                # Finaliser la candidature
                application = Application.query.filter_by(candidate_id=candidate.id).first()
                
                # Récupérer la période d'inscription active pour définir l'année de promotion
                active_period = ApplicationPeriod.query.filter_by(is_active=True).first()
                
                if not application:
                    application = Application(
                        candidate_id=candidate.id,
                        promotion_year=active_period.promotion_year if active_period else None
                    )
                    db.session.add(application)
                
                # Mettre à jour le statut final
                candidate.application_status = 'pending'
                application.status = 'pending'
                db.session.commit()
                
                # Générer le PDF récapitulatif
                pdf_filename = f"registration_{candidate.id}_{uuid.uuid4().hex}.pdf"
                pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_filename)
                
                generate_registration_pdf(
                    pdf_path=pdf_path,
                    candidate=candidate,
                    guardians=candidate.guardians,
                    medical_info=candidate.medical_information,
                    measurements=candidate.measurements
                )
                
                # Sauvegarder le document
                document = Document(
                    application_id=application.id,
                    filename=pdf_filename,
                    original_filename=f"Registration_{candidate.last_name}.pdf",
                    file_path=pdf_path,
                    document_type='registration_summary',
                    status='complete'
                )
                db.session.add(document)
                db.session.commit()
                
                # Notifier l'administrateur et le candidat
                from utils.email import notify_admin_document_upload, notify_all_steps_completed
                
                # Envoyer email à l'admin
                notify_admin_document_upload(application)
                
                # Envoyer email au candidat pour l'informer que toutes les étapes sont complétées
                notify_all_steps_completed(candidate)
                print(f"Email de finalisation envoyé à {candidate.email}")
                
                flash('Votre candidature a été soumise avec succès ! Vous recevrez bientôt des nouvelles concernant l\'avancement de votre dossier.', 'success')
                return redirect(url_for('registration.success'))
                
        except Exception as e:
            db.session.rollback()
            import traceback
            error_traceback = traceback.format_exc()
            print("Erreur lors de l'inscription :", str(e))
            print("Traceback:", error_traceback)
            flash(f'Une erreur est survenue : {str(e)}', 'danger')
    
    # S'assurer que les documents soient toujours disponibles pour l'étape 4
    documents = []
    if step == 4 and candidate:
        application = Application.query.filter_by(candidate_id=candidate.id).first()
        if application:
            try:
                documents = Document.query.filter_by(application_id=application.id).all()
                print(f"GET: Chargement de {len(documents)} documents pour l'application {application.id}")
                
                # Vérifier que tous les documents ont un chemin de fichier valide
                for doc in documents:
                    if not os.path.exists(doc.file_path):
                        print(f"GET: Le fichier {doc.file_path} n'existe pas sur le disque")
                        
                        # Essayer de corriger le chemin
                        documents_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
                        corrected_path = os.path.join(documents_dir, doc.filename)
                        
                        if os.path.exists(corrected_path):
                            print(f"GET: Fichier trouvé à {corrected_path}, mise à jour du chemin")
                            doc.file_path = corrected_path
                            db.session.add(doc)
                            db.session.commit()
                    else:
                        print(f"GET: Document {doc.id} a un fichier valide à {doc.file_path}")
                
                # Si aucun document n'existe, les générer maintenant
                if not documents:
                    print(f"GET: Aucun document trouvé, génération automatique pour l'application {application.id}")
                    documents = generate_blank_documents(candidate, application)
                    if documents:
                        flash('Les documents ont été générés automatiquement. Vous pouvez maintenant les signer.', 'success')
            except Exception as e:
                print(f"ERREUR lors du chargement des documents à l'étape 4: {str(e)}")
                import traceback
                print(traceback.format_exc())
    
    # Préparer le contexte de manière standardisée pour le template
    context = prepare_multi_step_template_context(
        step=step, 
        candidate_id=candidate_id, 
        candidate=candidate,
        documents=documents
    )
    
    return render_template('registration/multi_step_register.html', **context)

@registration_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("Formulaire soumis :", request.form)
        try:
            # Vérifier que les mots de passe correspondent
            candidate_password = request.form.get('candidate_password')
            candidate_password_confirm = request.form.get('candidate_password_confirm')
            
            if candidate_password != candidate_password_confirm:
                flash('Les mots de passe ne correspondent pas.', 'danger')
                return render_template('registration/register.html')
            
            # Get candidate information from the form
            candidate_data = {
                'first_name': request.form.get('candidate_first_name'),
                'last_name': request.form.get('candidate_last_name'),
                'date_of_birth': datetime.strptime(request.form.get('candidate_dob'), '%Y-%m-%d'),
                'birth_place': request.form.get('candidate_birth_place'),
                'address': request.form.get('candidate_address'),
                'city': request.form.get('candidate_city'),
                'postal_code': request.form.get('candidate_postal_code'),
                'phone': request.form.get('candidate_phone'),
                'mobile_phone': request.form.get('candidate_mobile_phone'),
                'email': request.form.get('candidate_email'),
                'school': request.form.get('candidate_school'),
                'grade': request.form.get('candidate_grade'),
                'emergency_contact_name': request.form.get('candidate_emergency_contact_name'),
                'emergency_contact_phone': request.form.get('candidate_emergency_contact_phone'),
                'first_aid_certified': request.form.get('candidate_first_aid_certified') == 'on',
                'additional_info': request.form.get('candidate_additional_info'),
                'image_rights': request.form.get('candidate_image_rights') == 'on'
            }

            # Créer un compte utilisateur pour le candidat
            username = f"{request.form.get('candidate_first_name').lower()}.{request.form.get('candidate_last_name').lower()}"
            # Vérifier si l'email ou le username existent déjà
            existing_email = User.query.filter_by(email=request.form.get('candidate_email')).first()
            existing_username = User.query.filter_by(username=username).first()
            
            if existing_email:
                flash('Cette adresse email est déjà utilisée.', 'danger')
                return render_template('registration/register.html')
                
            if existing_username:
                # Ajouter un suffixe numérique pour éviter les doublons
                import random
                username = f"{username}{random.randint(1, 999)}"
                
            user = User(
                username=username,
                email=request.form.get('candidate_email'),
                password_hash=generate_password_hash(candidate_password),
                is_active=True
            )
            db.session.add(user)
            db.session.flush()  # Pour obtenir l'ID de l'utilisateur
            
            # Create candidate record
            candidate = Candidate(**candidate_data, user_id=user.id)
            db.session.add(candidate)
            db.session.flush()  # Flush to get the candidate ID
            
            # Add medical information if provided
            medical_info = None
            if any(key for key in request.form.keys() if key.startswith('medical_')):
                medical_data = {
                    'candidate_id': candidate.id,
                    'medical_certificate_date': datetime.strptime(request.form.get('medical_certificate_date'), '%Y-%m-%d') if request.form.get('medical_certificate_date') else None,
                    'doctor_name': request.form.get('medical_doctor_name'),
                    'sport_allowed': request.form.get('medical_sport_allowed') == 'on',
                    'sport_competition_allowed': request.form.get('medical_sport_competition_allowed') == 'on',
                    'collective_living_allowed': request.form.get('medical_collective_living_allowed') == 'on',
                    'vaccinations_up_to_date': request.form.get('medical_vaccinations_up_to_date') == 'on',
                    'flight_allowed': request.form.get('medical_flight_allowed') == 'on',
                    'family_cardiac_death': request.form.get('medical_family_cardiac_death') == 'on',
                    'chest_pain': request.form.get('medical_chest_pain') == 'on',
                    'asthma': request.form.get('medical_asthma') == 'on',
                    'fainting': request.form.get('medical_fainting') == 'on',
                    'stopped_sport_for_health': request.form.get('medical_stopped_sport_for_health') == 'on',
                    'long_term_treatment': request.form.get('medical_long_term_treatment') == 'on',
                    'pain_after_injury': request.form.get('medical_pain_after_injury') == 'on',
                    'sport_interrupted_health': request.form.get('medical_sport_interrupted_health') == 'on',
                    'medical_advice_needed': request.form.get('medical_medical_advice_needed') == 'on',
                    'additional_medical_info': request.form.get('medical_additional_info')
                }
                medical_info = MedicalInformation(**medical_data)
                db.session.add(medical_info)
                db.session.flush()
            
            # Add physical measurements if provided
            measurements = None
            if any(key for key in request.form.keys() if key.startswith('measurement_')):
                measurements_data = {
                    'candidate_id': candidate.id,
                    'height': int(request.form.get('measurement_height')) if request.form.get('measurement_height') else None,
                    'weight': int(request.form.get('measurement_weight')) if request.form.get('measurement_weight') else None,
                    'head_size': int(request.form.get('measurement_head_size')) if request.form.get('measurement_head_size') else None,
                    'neck_size': int(request.form.get('measurement_neck_size')) if request.form.get('measurement_neck_size') else None,
                    'chest_size': int(request.form.get('measurement_chest_size')) if request.form.get('measurement_chest_size') else None,
                    'waist_size': int(request.form.get('measurement_waist_size')) if request.form.get('measurement_waist_size') else None,
                    'bust_height': int(request.form.get('measurement_bust_height')) if request.form.get('measurement_bust_height') else None,
                    'inseam': int(request.form.get('measurement_inseam')) if request.form.get('measurement_inseam') else None,
                    'shoe_size': int(request.form.get('measurement_shoe_size')) if request.form.get('measurement_shoe_size') else None
                }
                measurements = PhysicalMeasurements(**measurements_data)
                db.session.add(measurements)
                db.session.flush()
            
            # Get number of guardians
            num_guardians = int(request.form.get('num_guardians', 1))
            
            # Process guardian information
            for i in range(1, num_guardians + 1):
                guardian_data = {
                    'candidate_id': candidate.id,
                    'first_name': request.form.get(f'guardian_{i}_first_name'),
                    'last_name': request.form.get(f'guardian_{i}_last_name'),
                    'relationship': request.form.get(f'guardian_{i}_relationship'),
                    'email': request.form.get(f'guardian_{i}_email'),
                    'phone': request.form.get(f'guardian_{i}_phone'),
                    'address': request.form.get(f'guardian_{i}_address'),
                    'city': request.form.get(f'guardian_{i}_city'),
                    'postal_code': request.form.get(f'guardian_{i}_postal_code')
                }
                
                guardian = Guardian(**guardian_data)
                db.session.add(guardian)
            
            # Create application record with promotion year from active period
            active_period = ApplicationPeriod.query.filter_by(is_active=True).first()
            application = Application(
                candidate_id=candidate.id,
                promotion_year=active_period.promotion_year if active_period else None
            )
            db.session.add(application)
            db.session.flush()  # Flush to get the application ID
            
            # Generate registration PDF
            pdf_filename = f"registration_{candidate.id}_{uuid.uuid4().hex}.pdf"
            pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_filename)
            
            generate_registration_pdf(
                pdf_path=pdf_path,
                candidate=candidate,
                guardians=candidate.guardians,
                medical_info=medical_info,
                measurements=measurements
            )
            
            # Save document record
            document = Document(
                application_id=application.id,
                filename=pdf_filename,
                original_filename=f"Registration_{candidate.last_name}.pdf",
                file_path=pdf_path,
                document_type='registration',
                status='pending'
            )
            db.session.add(document)
            db.session.flush()
            
            # Create signing process
            signing_token = uuid.uuid4().hex
            expiry_date = datetime.utcnow() + timedelta(days=7)
            
            signing_process = SigningProcess(
                document_id=document.id,
                signing_token=signing_token,
                expiry_date=expiry_date
            )
            db.session.add(signing_process)
            
            # Commit all changes
            db.session.commit()
            
            # Send email to candidate
            send_candidate_registration_email(candidate, document, signing_token)
            
            # Redirect to success page
            flash('Inscription réussie ! Veuillez vérifier votre e-mail pour les instructions suivantes.', 'success')
            return redirect(url_for('registration.success'))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            error_traceback = traceback.format_exc()
            print("Erreur lors de l'inscription :", str(e))
            print("Traceback:", error_traceback)
            flash(f'Une erreur est survenue lors de l\'inscription : {str(e)}', 'danger')
    
    return render_template('registration/register.html')

@registration_bp.route('/success')
def success():
    return render_template('registration/success.html')

@registration_bp.route('/document/<token>', methods=['GET', 'POST'])
def view_document(token):
    # Get the signing process by token
    signing_process = SigningProcess.query.filter_by(signing_token=token).first_or_404()
    
    # Check if the token is expired
    if signing_process.expiry_date < datetime.utcnow():
        flash('Ce lien de signature a expiré.', 'danger')
        return redirect(url_for('index'))
    
    document = signing_process.document
    application = document.application
    candidate = application.candidate
    guardians = candidate.guardians
    medical_info = candidate.medical_information if hasattr(candidate, 'medical_information') else None
    measurements = candidate.measurements if hasattr(candidate, 'measurements') else None
    
    if request.method == 'POST':
        signer_type = request.form.get('signer_type')
        
        if signer_type == 'candidate':
            signing_process.candidate_signed = True
            signing_process.candidate_signed_date = datetime.utcnow()
            document.status = 'signed_candidate'
            
            # Send emails to guardians for their signatures
            for guardian in guardians:
                # This function should be implemented in utils/email.py
                from utils.email import send_guardian_signing_email
                send_guardian_signing_email(guardian, document, signing_process.signing_token)
                
            flash('Document signé avec succès. Les tuteurs légaux seront notifiés.', 'success')
            
        elif signer_type == 'guardian':
            signing_process.guardian_signed = True
            signing_process.guardian_signed_date = datetime.utcnow()
            document.status = 'signed_guardian'
            
            # Request additional documents from candidate
            from utils.email import request_additional_documents
            request_additional_documents(candidate)
            
            flash('Document signé avec succès. Des documents supplémentaires ont été demandés au candidat.', 'success')
            
        db.session.commit()
        return redirect(url_for('registration.success'))
    
    # Determine if the document is being viewed by candidate or guardian based on previous signatures
    is_candidate_view = not signing_process.candidate_signed
    is_guardian_view = signing_process.candidate_signed and not signing_process.guardian_signed
    
    return render_template(
        'registration/document_signing.html',
        signing_process=signing_process,
        document=document,
        candidate=candidate,
        guardians=guardians,
        medical_info=medical_info,
        measurements=measurements,
        is_candidate_view=is_candidate_view,
        is_guardian_view=is_guardian_view
    )

@registration_bp.route('/upload-document/<application_id>', methods=['POST'])
def upload_document(application_id):
    application = Application.query.get_or_404(application_id)
    
    if 'document' not in request.files:
        flash('Aucun fichier sélectionné.', 'danger')
        return redirect(request.referrer)
    
    file = request.files['document']
    
    if file.filename == '':
        flash('Aucun fichier sélectionné.', 'danger')
        return redirect(request.referrer)
    
    document_type = request.form.get('document_type')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        document = Document(
            application_id=application.id,
            filename=unique_filename,
            original_filename=filename,
            file_path=file_path,
            document_type=document_type,
            status='complete'
        )
        
        db.session.add(document)
        db.session.commit()
        
        flash('Document téléchargé avec succès.', 'success')
        
        # Notify admin of document upload
        from utils.email import notify_admin_document_upload
        notify_admin_document_upload(application)
        
        return redirect(url_for('registration.success'))
    
    flash('Type de fichier invalide.', 'danger')
    return redirect(request.referrer)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def generate_random_password(length=12):
    import random
    import string
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))

# Fonction utilitaire pour préparer le contexte du template multi_step_register
def prepare_multi_step_template_context(step, candidate_id=None, candidate=None, **kwargs):
    """
    Prépare le contexte standard pour le template multi_step_register.html
    en s'assurant que toutes les variables nécessaires sont présentes.
    
    Args:
        step (int): L'étape actuelle
        candidate_id (int, optional): ID du candidat
        candidate (Candidate, optional): Objet candidat
        **kwargs: Paramètres additionnels à passer au template
        
    Returns:
        dict: Contexte pour le template
    """
    context = {
        'step': step,
        'candidate_id': candidate_id
    }
    
    # S'assurer que l'objet candidate est disponible
    if candidate is None and candidate_id is not None:
        candidate = Candidate.query.get(candidate_id)
    
    if candidate is not None:
        context['candidate'] = candidate
        context['candidate_id'] = candidate.id
        
        # Si on est à l'étape 4, récupérer également les documents
        if step == 4:
            # Trouver l'application associée
            application = Application.query.filter_by(candidate_id=candidate.id).first()
            if application:
                context['application'] = application
                
                # Récupérer les documents
                documents = Document.query.filter_by(application_id=application.id).all()
                context['documents'] = documents
                
                # Vérifier les types de documents qui pourraient manquer
                missing_documents = []
                document_types = ['parental_auth', 'cadet_declaration', 'image_rights', 'medical_certificate', 'rules']
                existing_types = [doc.document_type for doc in documents]
                
                for doc_type in document_types:
                    if doc_type not in existing_types:
                        missing_documents.append(doc_type)
                
                context['missing_documents'] = missing_documents
    
    # Ajouter les paramètres additionnels
    context.update(kwargs)
    
    return context
