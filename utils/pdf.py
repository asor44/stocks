import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

def generate_registration_pdf(pdf_path, candidate, guardians, medical_info, measurements):
    """
    Génère un PDF récapitulatif des informations d'inscription
    
    Args:
        pdf_path (str): Chemin complet pour sauvegarder le PDF
        candidate: Instance du modèle Candidate
        guardians: Liste des tuteurs légaux
        medical_info: Informations médicales du candidat
        measurements: Mensurations du candidat
    """
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    # ------ Page 1: Informations personnelles ------
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2.0, height - 2*cm, "Dossier d'inscription")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2.0, height - 3*cm, f"{candidate.first_name} {candidate.last_name}")
    
    # Informations personnelles
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height - 4.5*cm, "Informations personnelles")
    c.line(2*cm, height - 4.7*cm, width - 2*cm, height - 4.7*cm)
    
    c.setFont("Helvetica", 10)
    y_position = height - 5.5*cm
    
    c.drawString(2*cm, y_position, f"Prénom: {candidate.first_name}")
    c.drawString(11*cm, y_position, f"Nom: {candidate.last_name}")
    y_position -= 0.7*cm
    
    birth_date = candidate.date_of_birth.strftime("%d/%m/%Y") if candidate.date_of_birth else "N/A"
    c.drawString(2*cm, y_position, f"Date de naissance: {birth_date}")
    c.drawString(11*cm, y_position, f"Nationalité: {candidate.nationality or 'N/A'}")
    y_position -= 0.7*cm
    
    c.drawString(2*cm, y_position, f"Lieu de naissance: {candidate.birth_place or 'N/A'}")
    c.drawString(11*cm, y_position, f"Code postal: {candidate.birth_place_postal_code or 'N/A'}")
    y_position -= 0.7*cm
    
    # Coordonnées
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_position - 0.5*cm, "Coordonnées")
    c.line(2*cm, y_position - 0.7*cm, width - 2*cm, y_position - 0.7*cm)
    y_position -= 1.5*cm
    
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y_position, f"Adresse: {candidate.address or 'N/A'}")
    y_position -= 0.7*cm
    
    c.drawString(2*cm, y_position, f"Code postal: {candidate.postal_code or 'N/A'}")
    c.drawString(11*cm, y_position, f"Ville: {candidate.city or 'N/A'}")
    y_position -= 0.7*cm
    
    c.drawString(2*cm, y_position, f"Téléphone: {candidate.phone or 'N/A'}")
    c.drawString(11*cm, y_position, f"Email: {candidate.email or 'N/A'}")
    y_position -= 0.7*cm
    
    # Information scolaire
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_position - 0.5*cm, "Informations scolaires")
    c.line(2*cm, y_position - 0.7*cm, width - 2*cm, y_position - 0.7*cm)
    y_position -= 1.5*cm
    
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y_position, f"Établissement: {candidate.school or 'N/A'}")
    c.drawString(11*cm, y_position, f"Classe: {candidate.grade or 'N/A'}")
    y_position -= 0.7*cm
    
    c.drawString(2*cm, y_position, f"Premier secours: {'Oui' if candidate.first_aid_certified else 'Non'}")
    
    # ------ Page 2: Tuteurs légaux ------
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2.0, height - 2*cm, "Tuteurs légaux")
    
    y_position = height - 3.5*cm
    
    # Afficher les informations pour chaque tuteur
    if guardians:
        for i, guardian in enumerate(guardians):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2*cm, y_position, f"Tuteur {i+1}: {guardian.first_name} {guardian.last_name}")
            c.line(2*cm, y_position - 0.2*cm, width - 2*cm, y_position - 0.2*cm)
            y_position -= 1*cm
            
            c.setFont("Helvetica", 10)
            c.drawString(2*cm, y_position, f"Lien de parenté: {guardian.relationship or 'N/A'}")
            y_position -= 0.6*cm
            
            c.drawString(2*cm, y_position, f"Email: {guardian.email or 'N/A'}")
            c.drawString(11*cm, y_position, f"Téléphone: {guardian.phone or 'N/A'}")
            y_position -= 0.6*cm
            
            c.drawString(2*cm, y_position, f"Adresse: {guardian.address or 'N/A'}")
            y_position -= 0.6*cm
            
            c.drawString(2*cm, y_position, f"Code postal: {guardian.postal_code or 'N/A'}")
            c.drawString(11*cm, y_position, f"Ville: {guardian.city or 'N/A'}")
            y_position -= 1.5*cm  # Espace entre les tuteurs
    else:
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y_position, "Aucun tuteur légal renseigné")
        y_position -= 1*cm
    
    # ------ Page 3: Informations médicales et mensurations ------
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2.0, height - 2*cm, "Informations médicales")
    
    y_position = height - 3.5*cm
    
    if medical_info:
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y_position, f"Certificat médical daté du: {medical_info.medical_certificate_date.strftime('%d/%m/%Y') if medical_info.medical_certificate_date else 'Non fourni'}")
        c.drawString(11*cm, y_position, f"Médecin: {medical_info.doctor_name or 'N/A'}")
        y_position -= 0.7*cm
        
        c.drawString(2*cm, y_position, f"Pratique sportive autorisée: {'Oui' if medical_info.sport_allowed else 'Non'}")
        c.drawString(11*cm, y_position, f"Compétition autorisée: {'Oui' if medical_info.sport_competition_allowed else 'Non'}")
        y_position -= 0.7*cm
        
        c.drawString(2*cm, y_position, f"Vie collective autorisée: {'Oui' if medical_info.collective_living_allowed else 'Non'}")
        c.drawString(11*cm, y_position, f"Vol autorisé: {'Oui' if medical_info.flight_allowed else 'Non'}")
        y_position -= 0.7*cm
        
        c.drawString(2*cm, y_position, f"Vaccinations à jour: {'Oui' if medical_info.vaccinations_up_to_date else 'Non'}")
        y_position -= 1.5*cm
        
        # Questionnaire de santé
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y_position, "Questionnaire de santé")
        c.line(2*cm, y_position - 0.2*cm, width - 2*cm, y_position - 0.2*cm)
        y_position -= 1*cm
        
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y_position, f"Antécédents cardiaques familiaux: {'Oui' if medical_info.family_cardiac_death else 'Non'}")
        y_position -= 0.5*cm
        c.drawString(2*cm, y_position, f"Douleurs thoraciques: {'Oui' if medical_info.chest_pain else 'Non'}")
        y_position -= 0.5*cm
        c.drawString(2*cm, y_position, f"Asthme: {'Oui' if medical_info.asthma else 'Non'}")
        y_position -= 0.5*cm
        c.drawString(2*cm, y_position, f"Évanouissements: {'Oui' if medical_info.fainting else 'Non'}")
        y_position -= 0.5*cm
        c.drawString(2*cm, y_position, f"Arrêt du sport pour raison de santé: {'Oui' if medical_info.stopped_sport_for_health else 'Non'}")
        y_position -= 0.5*cm
        c.drawString(2*cm, y_position, f"Traitement médical de longue durée: {'Oui' if medical_info.long_term_treatment else 'Non'}")
        y_position -= 1*cm
        
        if medical_info.additional_medical_info:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2*cm, y_position, "Informations médicales supplémentaires:")
            y_position -= 0.5*cm
            c.setFont("Helvetica", 10)
            
            # Wrap text if needed
            max_width = width - 4*cm
            text = medical_info.additional_medical_info
            lines = []
            
            # Simple text wrapping
            while len(text) > 0:
                if len(text) * 5 < max_width:  # Estimation grossière
                    lines.append(text)
                    text = ""
                else:
                    # Find a good point to break the line
                    break_point = min(int(max_width / 5), len(text))
                    while break_point > 0 and text[break_point] != ' ':
                        break_point -= 1
                    
                    if break_point == 0:
                        break_point = min(int(max_width / 5), len(text))
                    
                    lines.append(text[:break_point])
                    text = text[break_point:].strip()
            
            for line in lines:
                if y_position < 2*cm:  # Si on arrive en bas de page, créer une nouvelle page
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y_position = height - 3*cm
                
                c.drawString(2*cm, y_position, line)
                y_position -= 0.5*cm
    else:
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y_position, "Aucune information médicale renseignée")
        y_position -= 1*cm
    
    # Mensurations sur une nouvelle page
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2.0, height - 2*cm, "Mensurations")
    
    y_position = height - 3.5*cm
    
    if measurements:
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y_position, f"Taille: {measurements.height or 'N/A'} cm")
        c.drawString(8*cm, y_position, f"Poids: {measurements.weight or 'N/A'} kg")
        c.drawString(14*cm, y_position, f"Pointure: {measurements.shoe_size or 'N/A'}")
        y_position -= 0.7*cm
        
        c.drawString(2*cm, y_position, f"Tour de tête: {measurements.head_size or 'N/A'} cm")
        c.drawString(8*cm, y_position, f"Tour de cou: {measurements.neck_size or 'N/A'} cm")
        y_position -= 0.7*cm
        
        c.drawString(2*cm, y_position, f"Tour de poitrine: {measurements.chest_size or 'N/A'} cm")
        c.drawString(8*cm, y_position, f"Tour de taille: {measurements.waist_size or 'N/A'} cm")
        y_position -= 0.7*cm
        
        c.drawString(2*cm, y_position, f"Hauteur du buste: {measurements.bust_height or 'N/A'} cm")
        c.drawString(8*cm, y_position, f"Hauteur entrejambe: {measurements.inseam or 'N/A'} cm")
    else:
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y_position, "Aucune mensuration renseignée")
    
    # Pied de page sur chaque page
    c.showPage()
    c.save()
    
    return pdf_path