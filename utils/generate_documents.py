import os
import uuid
from datetime import datetime, timedelta
from flask import current_app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from app import db
from models import Document, SigningProcess

def ensure_documents_directory():
    """Créer le répertoire documents dans le dossier d'upload s'il n'existe pas"""
    try:
        # Récupérer le dossier d'upload depuis la configuration
        upload_folder = current_app.config['UPLOAD_FOLDER']
        print(f"DEBUG: Dossier d'upload configuré: {upload_folder}")
        
        # S'assurer que le dossier d'upload existe
        if not os.path.exists(upload_folder):
            print(f"DEBUG: Le dossier d'upload {upload_folder} n'existe pas, création...")
            os.makedirs(upload_folder, exist_ok=True)
            print(f"DEBUG: Dossier d'upload créé avec succès.")
        
        # Créer le sous-dossier documents
        documents_dir = os.path.join(upload_folder, 'documents')
        print(f"DEBUG: Chemin complet du dossier documents: {documents_dir}")
        
        if not os.path.exists(documents_dir):
            print(f"DEBUG: Le dossier {documents_dir} n'existe pas, création...")
            os.makedirs(documents_dir, exist_ok=True)
            print(f"DEBUG: Dossier créé avec succès.")
        else:
            print(f"DEBUG: Le dossier {documents_dir} existe déjà.")
            
        # Vérifier et corriger les permissions
        try:
            if not os.access(documents_dir, os.W_OK):
                print(f"ERREUR: Pas de permission d'écriture sur {documents_dir}")
                os.chmod(documents_dir, 0o777)  # Essayer de corriger les permissions
                print(f"Tentative de correction des permissions sur {documents_dir}")
        except Exception as perm_error:
            print(f"ERREUR lors de la modification des permissions: {str(perm_error)}")
            
        return documents_dir
    except Exception as e:
        print(f"ERREUR lors de la création du dossier documents: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Utiliser un chemin de secours dans le répertoire courant
        current_dir = os.getcwd()
        fallback_dir = os.path.join(current_dir, 'documents')
        print(f"Utilisation du chemin de secours: {fallback_dir}")
        os.makedirs(fallback_dir, exist_ok=True)
        try:
            os.chmod(fallback_dir, 0o777)
        except:
            pass
        return fallback_dir

def create_blank_pdf(document_type, candidate):
    """
    Créer un PDF vierge avec des informations de base
    
    Args:
        document_type (str): Type de document (parental_auth, cadet_declaration, etc.)
        candidate: Instance du modèle Candidate
    
    Returns:
        str: Chemin du fichier créé
    """
    try:
        documents_dir = ensure_documents_directory()
        print(f"DEBUG: Génération du document {document_type} dans {documents_dir}")
        
        # Générer un nom de fichier unique
        filename = f"{document_type}_{uuid.uuid4().hex}.pdf"
        file_path = os.path.join(documents_dir, filename)
        print(f"DEBUG: Chemin complet du fichier à créer: {file_path}")
        
        # Créer le PDF
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        print(f"DEBUG: Canvas PDF créé avec dimensions {width}x{height}")
    except Exception as e:
        print(f"ERREUR lors de la création du PDF {document_type}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise
    
    # Ajouter un titre
    if document_type == 'parental_auth':
        title = "Autorisation Parentale"
    elif document_type == 'cadet_declaration':
        title = "Déclaration du Cadet"
    elif document_type == 'image_rights':
        title = "Droit à l'Image"
    elif document_type == 'medical_certificate':
        title = "Certificat Médical"
    elif document_type == 'rules':
        title = "Règlement ACADEF"
    else:
        title = "Document"
    
    # Ajouter un en-tête
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2.0, height - 2*cm, title)
    
    # Informations du candidat
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 4*cm, f"Nom: {candidate.last_name}")
    c.drawString(2*cm, height - 4.5*cm, f"Prénom: {candidate.first_name}")
    c.drawString(2*cm, height - 5*cm, f"Date de naissance: {candidate.date_of_birth}")
    
    # Contenu du document selon le type
    c.setFont("Helvetica", 11)
    if document_type == 'parental_auth':
        c.drawString(2*cm, height - 7*cm, "Je, soussigné(e), ________________________, tuteur légal de l'enfant nommé ci-dessus,")
        c.drawString(2*cm, height - 7.5*cm, "autorise sa participation aux activités de l'Académie des Cadets de la Défense.")
    elif document_type == 'cadet_declaration':
        c.drawString(2*cm, height - 7*cm, "Je, soussigné(e), ________________________, m'engage à respecter les règles")
        c.drawString(2*cm, height - 7.5*cm, "et à participer activement aux activités de l'Académie des Cadets de la Défense.")
    elif document_type == 'image_rights':
        c.drawString(2*cm, height - 7*cm, "J'autorise l'Académie des Cadets de la Défense à utiliser des images ou vidéos")
        c.drawString(2*cm, height - 7.5*cm, "sur lesquelles figure le cadet pour la communication de l'académie.")
    elif document_type == 'medical_certificate':
        c.drawString(2*cm, height - 7*cm, "Ce document atteste que le cadet est apte à participer aux activités sportives")
        c.drawString(2*cm, height - 7.5*cm, "et aux activités collectives de l'Académie des Cadets de la Défense.")
    elif document_type == 'rules':
        c.drawString(2*cm, height - 7*cm, "J'ai pris connaissance du règlement intérieur de l'Académie des Cadets de la Défense")
        c.drawString(2*cm, height - 7.5*cm, "et m'engage à le respecter en tous points.")
    
    # Zones de signature
    c.drawString(2*cm, height - 10*cm, "Signature du candidat:")
    c.drawString(2*cm, height - 14*cm, "Signature du tuteur légal:")
    
    # Date de création
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(width - 6*cm, 1*cm, f"Document généré le {datetime.now().strftime('%d/%m/%Y')}")
    
    c.save()
    return file_path

def generate_blank_documents(candidate, application):
    """
    Générer tous les documents pour la signature électronique
    
    Args:
        candidate: Instance du modèle Candidate
        application: Instance du modèle Application
    
    Returns:
        list: Liste des documents créés
    """
    print(f"DEBUG: Début de la génération de documents pour le candidat {candidate.id} et l'application {application.id}")
    
    document_types = [
        'parental_auth', 
        'cadet_declaration', 
        'image_rights', 
        'medical_certificate', 
        'rules'
    ]
    
    created_documents = []
    
    for doc_type in document_types:
        try:
            print(f"DEBUG: Traitement du document de type {doc_type}")
            # Vérifier si le document existe déjà pour cette application
            existing_doc = Document.query.filter_by(
                application_id=application.id,
                document_type=doc_type
            ).first()
            
            if existing_doc:
                print(f"DEBUG: Document existant trouvé pour {doc_type}: {existing_doc.id}")
                created_documents.append(existing_doc)
                continue
                
            # Créer le document s'il n'existe pas
            file_path = create_blank_pdf(doc_type, candidate)
            print(f"DEBUG: PDF créé à {file_path}")
            
            # Récupérer uniquement le nom du fichier depuis le chemin complet
            filename = os.path.basename(file_path)
            
            # Créer une entrée dans la base de données
            document = Document(
                application_id=application.id,
                filename=filename,
                original_filename=f"{doc_type}.pdf",
                file_path=file_path,  # Chemin complet pour le stockage
                document_type=doc_type,
                status='pending'
            )
            
            db.session.add(document)
            db.session.flush()  # Pour obtenir l'ID du document avant le commit final
            print(f"DEBUG: Document ajouté à la DB avec ID {document.id}")
            
            # Créer le processus de signature
            signing_token = str(uuid.uuid4())
            signing_process = SigningProcess(
                document_id=document.id,
                signing_token=signing_token,
                expiry_date=datetime.now() + timedelta(days=30)
            )
            
            db.session.add(signing_process)
            print(f"DEBUG: Processus de signature créé avec token {signing_token}")
            created_documents.append(document)
        except Exception as e:
            print(f"ERREUR lors de la génération du document {doc_type}: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    db.session.commit()
    return created_documents