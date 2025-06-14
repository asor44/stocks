from flask import current_app, url_for
from flask_mail import Message
from app import mail
import logging

def send_email(subject, recipient, html_body, attachments=None):
    """
    Send an email with the given subject and body to the recipient.
    
    Args:
        subject (str): Email subject
        recipient (str): Email recipient
        html_body (str): HTML content of the email
        attachments (list, optional): List of attachment tuples (filename, content_type, data)
    """
    try:
        msg = Message(
            subject,
            recipients=[recipient],
            html=html_body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        if attachments:
            for attachment in attachments:
                msg.attach(*attachment)
        
        mail.send(msg)
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {recipient}: {str(e)}")
        return False

def send_candidate_registration_email(candidate, document, signing_token):
    """
    Send registration confirmation email to the candidate with the signing link.
    
    Args:
        candidate: Candidate model instance
        document: Document model instance
        signing_token: Unique token for the signing process
    """
    subject = "Inscription Académie des Cadets de la Défense - Documents à signer"
    
    # URL pour la signature du document
    signing_url = url_for(
        'registration.sign_document_with_token',
        token=signing_token,
        _external=True
    )
    
    html_body = f"""
    <h2>Bienvenue à l'Académie des Cadets de la Défense</h2>
    <p>Cher(e) {candidate.first_name} {candidate.last_name},</p>
    <p>Nous vous remercions de votre inscription. Pour finaliser votre candidature, 
    veuillez signer électroniquement les documents nécessaires.</p>
    
    <p><strong>Document à signer:</strong> {document.document_type_display}</p>
    
    <p>Pour signer ce document, veuillez cliquer sur le lien ci-dessous:</p>
    <p><a href="{signing_url}" style="display: inline-block; padding: 10px 20px; 
    background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
    Signer le Document</a></p>
    
    <p>Ce lien est valable pendant 30 jours.</p>
    
    <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
    
    <p>Cordialement,<br>
    L'équipe de l'Académie des Cadets de la Défense</p>
    """
    
    return send_email(subject, candidate.email, html_body)

def send_guardian_signing_email(guardian, document, signing_token):
    """
    Send email to guardian requesting them to sign the document.
    
    Args:
        guardian: Guardian model instance
        document: Document model instance
        signing_token: Unique token for the signing process
    """
    subject = "Académie des Cadets de la Défense - Document à signer"
    
    # URL pour la signature du document
    signing_url = url_for(
        'registration.sign_document_with_token',
        token=signing_token,
        _external=True
    )
    
    candidate = document.application.candidate
    
    html_body = f"""
    <h2>Demande de Signature de Document</h2>
    <p>Cher(e) {guardian.first_name} {guardian.last_name},</p>
    
    <p>Vous recevez cet email car {candidate.first_name} {candidate.last_name} 
    est en cours d'inscription à l'Académie des Cadets de la Défense et a besoin de votre
    signature en tant que tuteur(trice) légal(e).</p>
    
    <p><strong>Document à signer:</strong> {document.document_type_display}</p>
    
    <p>Pour signer ce document, veuillez cliquer sur le lien ci-dessous:</p>
    <p><a href="{signing_url}" style="display: inline-block; padding: 10px 20px; 
    background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
    Signer le Document</a></p>
    
    <p>Ce lien est valable pendant 30 jours.</p>
    
    <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
    
    <p>Cordialement,<br>
    L'équipe de l'Académie des Cadets de la Défense</p>
    """
    
    return send_email(subject, guardian.email, html_body)

def request_additional_documents(candidate):
    """
    Send email to candidate requesting additional documents.
    
    Args:
        candidate: Candidate model instance
    """
    subject = "Académie des Cadets de la Défense - Documents supplémentaires requis"
    
    login_url = url_for('auth.login', _external=True)
    
    html_body = f"""
    <h2>Documents supplémentaires requis</h2>
    <p>Cher(e) {candidate.first_name} {candidate.last_name},</p>
    
    <p>Nous avons bien reçu votre inscription à l'Académie des Cadets de la Défense. 
    Cependant, nous avons besoin de documents supplémentaires pour compléter votre dossier.</p>
    
    <p>Veuillez vous connecter à votre compte pour voir quels documents sont manquants:</p>
    <p><a href="{login_url}" style="display: inline-block; padding: 10px 20px; 
    background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
    Se connecter</a></p>
    
    <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
    
    <p>Cordialement,<br>
    L'équipe de l'Académie des Cadets de la Défense</p>
    """
    
    return send_email(subject, candidate.email, html_body)

def notify_admin_document_upload(application):
    """
    Notify administrators about document uploads.
    
    Args:
        application: Application model instance
    """
    # Trouver tous les administrateurs
    from models import User
    admins = User.query.filter_by(is_admin=True).all()
    
    if not admins:
        return False
    
    candidate = application.candidate
    subject = f"Nouveau document téléversé - {candidate.first_name} {candidate.last_name}"
    
    admin_url = url_for('admin.application_detail', application_id=application.id, _external=True)
    
    html_body = f"""
    <h2>Nouveau document téléversé</h2>
    <p>Le candidat {candidate.first_name} {candidate.last_name} a téléversé un nouveau document.</p>
    
    <p>Pour examiner ce document, cliquez sur le lien ci-dessous:</p>
    <p><a href="{admin_url}" style="display: inline-block; padding: 10px 20px; 
    background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
    Voir le Dossier</a></p>
    
    <p>Cordialement,<br>
    Le système de l'Académie des Cadets de la Défense</p>
    """
    
    # Envoyer à tous les administrateurs
    success = True
    for admin in admins:
        if not send_email(subject, admin.email, html_body):
            success = False
    
    return success

def send_approval_email(candidate, candidate_password, guardian_accounts):
    """
    Send approval email to candidate with account credentials.
    
    Args:
        candidate: Candidate model instance
        candidate_password: Generated password for candidate
        guardian_accounts: List of dictionaries with guardian and password
    """
    subject = "Félicitations - Votre candidature a été approuvée"
    
    login_url = url_for('auth.login', _external=True)
    
    guardian_html = ""
    for account in guardian_accounts:
        guardian = account['guardian']
        password = account['password']
        guardian_html += f"""
        <h3>Compte Tuteur: {guardian.first_name} {guardian.last_name}</h3>
        <p><strong>Identifiant:</strong> {guardian.email}<br>
        <strong>Mot de passe:</strong> {password}</p>
        """
    
    html_body = f"""
    <h2>Félicitations - Votre candidature a été approuvée!</h2>
    <p>Cher(e) {candidate.first_name} {candidate.last_name},</p>
    
    <p>Nous sommes heureux de vous informer que votre candidature à l'Académie des Cadets de la Défense a été approuvée.</p>
    
    <p>Vos identifiants pour accéder à la plateforme sont:</p>
    <p><strong>Identifiant:</strong> {candidate.email}<br>
    <strong>Mot de passe:</strong> {candidate_password}</p>
    
    <p>Des comptes ont également été créés pour vos tuteurs légaux:</p>
    {guardian_html}
    
    <p>Pour vous connecter, cliquez sur le lien suivant:</p>
    <p><a href="{login_url}" style="display: inline-block; padding: 10px 20px; 
    background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
    Se connecter</a></p>
    
    <p>Bienvenue à l'Académie des Cadets de la Défense!</p>
    
    <p>Cordialement,<br>
    L'équipe de l'Académie des Cadets de la Défense</p>
    """
    
    return send_email(subject, candidate.email, html_body)

def send_rejection_email(candidate, rejection_reason):
    """
    Send rejection email to candidate.
    
    Args:
        candidate: Candidate model instance
        rejection_reason: Reason for rejection
    """
    subject = "Réponse à votre candidature - Académie des Cadets de la Défense"
    
    html_body = f"""
    <h2>Réponse à votre candidature</h2>
    <p>Cher(e) {candidate.first_name} {candidate.last_name},</p>
    
    <p>Nous vous remercions d'avoir postulé à l'Académie des Cadets de la Défense.</p>
    
    <p>Après examen attentif de votre dossier, nous sommes au regret de vous informer que votre candidature n'a pas été retenue.</p>
    
    <p><strong>Motif:</strong> {rejection_reason}</p>
    
    <p>Nous vous encourageons à postuler à nouveau lors d'une prochaine session si vous le souhaitez.</p>
    
    <p>Cordialement,<br>
    L'équipe de l'Académie des Cadets de la Défense</p>
    """
    
    return send_email(subject, candidate.email, html_body)

def send_document_signing_request(user, document, signing_process):
    """
    Send email to a user requesting them to sign a document.
    
    Args:
        user: User model instance (can be candidate or guardian)
        document: Document model instance to be signed
        signing_process: SigningProcess model instance
    """
    subject = "Document à signer - Académie des Cadets de la Défense"
    
    # Déterminer s'il s'agit d'un candidat ou d'un tuteur
    from models import Candidate, Guardian
    
    candidate = Candidate.query.filter_by(user_id=user.id).first()
    guardian = Guardian.query.filter_by(user_id=user.id).first()
    
    if candidate:
        # C'est un candidat
        return send_candidate_registration_email(candidate, document, signing_process.signing_token)
    elif guardian:
        # C'est un tuteur
        return send_guardian_signing_email(guardian, document, signing_process.signing_token)
    else:
        # Ni l'un ni l'autre, envoyer un email générique
        signing_url = url_for('registration.sign_document_with_token', token=signing_process.signing_token, _external=True)
        
        html_body = f"""
        <h2>Document à signer</h2>
        <p>Bonjour {user.username},</p>
        
        <p>Un document requiert votre signature électronique pour l'Académie des Cadets de la Défense.</p>
        
        <p><strong>Document:</strong> {document.document_type_display}</p>
        
        <p>Pour signer ce document, veuillez cliquer sur le lien ci-dessous:</p>
        <p><a href="{signing_url}" style="display: inline-block; padding: 10px 20px; 
        background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
        Signer le Document</a></p>
        
        <p>Ce lien est valable pendant 30 jours.</p>
        
        <p>Cordialement,<br>
        L'équipe de l'Académie des Cadets de la Défense</p>
        """
        
        return send_email(subject, user.email, html_body)

def send_step_completion_email(candidate, step_completed, next_step):
    """
    Envoie un email au candidat pour l'informer qu'il a complété une étape de l'inscription
    et lui indiquer l'étape suivante.
    
    Args:
        candidate: Instance du modèle Candidate
        step_completed (int): Numéro de l'étape complétée (1-5)
        next_step (int): Numéro de l'étape suivante (1-5)
    """
    # Descriptions des étapes
    step_descriptions = {
        1: "Informations personnelles",
        2: "Mesures physiques",
        3: "Informations des tuteurs légaux",
        4: "Signature des documents",
        5: "Finalisation de la candidature"
    }
    
    subject = f"Étape {step_completed} complétée - Académie des Cadets de la Défense"
    
    # URL pour l'étape suivante
    next_step_url = url_for(
        'registration.multi_step_register',
        step=next_step,
        candidate_id=candidate.id,
        _external=True
    )
    
    html_body = f"""
    <h2>Félicitations pour votre progression !</h2>
    <p>Cher(e) {candidate.first_name} {candidate.last_name},</p>
    
    <p>Nous sommes heureux de vous informer que vous avez complété avec succès 
    l'étape {step_completed} de votre candidature : <strong>{step_descriptions.get(step_completed)}</strong>.</p>
    
    <p>Votre candidature avance bien. La prochaine étape concerne : <strong>{step_descriptions.get(next_step)}</strong>.</p>
    
    <p>Pour continuer votre candidature, cliquez sur le lien ci-dessous :</p>
    <p><a href="{next_step_url}" style="display: inline-block; padding: 10px 20px; 
    background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
    Continuer à l'étape {next_step}</a></p>
    
    <p>Vous pouvez également vous reconnecter ultérieurement pour reprendre votre candidature 
    là où vous l'avez laissée.</p>
    
    <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
    
    <p>Cordialement,<br>
    L'équipe de l'Académie des Cadets de la Défense</p>
    """
    
    return send_email(subject, candidate.email, html_body)

def notify_all_steps_completed(candidate):
    """
    Envoie un email au candidat pour l'informer qu'il a complété toutes les étapes de l'inscription
    et que sa candidature est en attente d'examen.
    
    Args:
        candidate: Instance du modèle Candidate
    """
    subject = "Candidature complétée - Académie des Cadets de la Défense"
    
    # URL pour se connecter et voir le statut
    login_url = url_for('auth.login', _external=True)
    
    html_body = f"""
    <h2>Candidature complétée avec succès !</h2>
    <p>Cher(e) {candidate.first_name} {candidate.last_name},</p>
    
    <p>Toutes nos félicitations ! Vous avez complété avec succès toutes les étapes de votre candidature
    pour l'Académie des Cadets de la Défense.</p>
    
    <p>Votre dossier est maintenant <strong>en attente d'examen</strong> par notre équipe. Nous examinerons
    attentivement votre candidature et vous informerons de notre décision dans les meilleurs délais.</p>
    
    <p>Vous pouvez consulter le statut de votre candidature à tout moment en vous connectant à votre compte :</p>
    <p><a href="{login_url}" style="display: inline-block; padding: 10px 20px; 
    background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
    Se connecter</a></p>
    
    <p>Nous vous remercions pour l'intérêt que vous portez à l'Académie des Cadets de la Défense.</p>
    
    <p>Cordialement,<br>
    L'équipe de l'Académie des Cadets de la Défense</p>
    """
    
    # Notifier également les administrateurs
    notify_admin_new_complete_application(candidate)
    
    return send_email(subject, candidate.email, html_body)

def notify_admin_new_complete_application(candidate):
    """
    Notifie les administrateurs qu'une nouvelle candidature complète est disponible pour examen.
    
    Args:
        candidate: Instance du modèle Candidate
    """
    from models import User, Application
    
    # Trouver tous les administrateurs
    admins = User.query.filter_by(is_admin=True).all()
    
    if not admins:
        return False
        
    application = Application.query.filter_by(candidate_id=candidate.id).first()
    if not application:
        return False
    
    subject = f"Nouvelle candidature complète - {candidate.first_name} {candidate.last_name}"
    
    # URL pour examiner la candidature
    admin_url = url_for('admin.application_detail', application_id=application.id, _external=True)
    
    html_body = f"""
    <h2>Nouvelle candidature complète à examiner</h2>
    <p>Bonjour,</p>
    
    <p>Une nouvelle candidature a été complétée et est prête à être examinée.</p>
    
    <p><strong>Candidat :</strong> {candidate.first_name} {candidate.last_name}<br>
    <strong>Email :</strong> {candidate.email}<br>
    <strong>Date de naissance :</strong> {candidate.date_of_birth.strftime('%d/%m/%Y')}</p>
    
    <p>Pour examiner cette candidature, cliquez sur le lien ci-dessous :</p>
    <p><a href="{admin_url}" style="display: inline-block; padding: 10px 20px; 
    background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">
    Examiner la candidature</a></p>
    
    <p>Cordialement,<br>
    Le système de l'Académie des Cadets de la Défense</p>
    """
    
    # Envoyer à tous les administrateurs
    success = True
    for admin in admins:
        if not send_email(subject, admin.email, html_body):
            success = False
    
    return success