from datetime import datetime, timedelta
import os
import uuid
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    candidate = db.relationship('Candidate', backref='user', uselist=False, foreign_keys='Candidate.user_id')
    guardian = db.relationship('Guardian', backref='user', uselist=False, foreign_keys='Guardian.user_id')

    def __repr__(self):
        return f'<User {self.username}>'


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    nationality = db.Column(db.String(64), nullable=True)
    birth_place = db.Column(db.String(120), nullable=True)
    birth_place_postal_code = db.Column(db.String(20), nullable=True)
    birth_place_city = db.Column(db.String(64), nullable=True)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(64), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    mobile_phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    school = db.Column(db.String(120), nullable=True)
    grade = db.Column(db.String(64), nullable=True)
    emergency_contact_name = db.Column(db.String(120), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    emergency_contact_first_name = db.Column(db.String(64), nullable=True)
    emergency_contact_last_name = db.Column(db.String(64), nullable=True)
    first_aid_certified = db.Column(db.Boolean, default=False)
    motivation_letter = db.Column(db.String(255), nullable=True)  # Chemin vers le fichier
    vital_card_copy = db.Column(db.String(255), nullable=True)  # Chemin vers le fichier
    id_card_copy = db.Column(db.String(255), nullable=True)  # Chemin vers le fichier
    insurance_certificate = db.Column(db.String(255), nullable=True)  # Chemin vers le fichier
    recent_photo = db.Column(db.String(255), nullable=True)  # Chemin vers le fichier
    mutual_card_copy = db.Column(db.String(255), nullable=True)  # Chemin vers le fichier
    application_status = db.Column(db.String(30), default='step1')  # step1, step2, step3, step4, step5, approved, rejected
    additional_info = db.Column(db.Text, nullable=True)
    image_rights = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    promotion_year = db.Column(db.Integer, nullable=True)  # Année de promotion (ex: 2024, 2025)
    
    # Champs pour le renouvellement des informations
    info_renewal_requested = db.Column(db.Boolean, default=False)
    info_renewal_message = db.Column(db.Text, nullable=True)
    info_renewal_requested_at = db.Column(db.DateTime, nullable=True)
    info_renewal_requested_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_candidate_renewal_by'), nullable=True)
    
    # Relationships
    application = db.relationship('Application', backref='candidate', uselist=False)
    guardians = db.relationship('Guardian', backref='candidate')

    def __repr__(self):
        return f'<Candidate {self.first_name} {self.last_name}>'


class Guardian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    relationship = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(64), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Champs pour le renouvellement des informations
    info_renewal_requested = db.Column(db.Boolean, default=False)
    info_renewal_message = db.Column(db.Text, nullable=True)
    info_renewal_requested_at = db.Column(db.DateTime, nullable=True)
    info_renewal_requested_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_guardian_renewal_by'), nullable=True)

    def __repr__(self):
        return f'<Guardian {self.first_name} {self.last_name}>'


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    review_date = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_application_reviewed_by'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    promotion_year = db.Column(db.Integer, nullable=True)  # Année de promotion (ex: 2024, 2025)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = db.relationship('Document', backref='application', lazy=True)
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f'<Application {self.id} - {self.status}>'


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # registration, medical, etc.
    uploaded_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_document_updated_by'), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, signed_candidate, signed_guardian, complete
    
    # Champs pour le renouvellement des documents
    renewal_requested = db.Column(db.Boolean, default=False)
    renewal_message = db.Column(db.Text, nullable=True)
    renewal_requested_at = db.Column(db.DateTime, nullable=True)
    renewal_requested_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_document_renewal_by'), nullable=True)
    
    @property
    def document_type_display(self):
        """Retourne un nom lisible pour le type de document"""
        types = {
            'parental_auth': 'Autorisation Parentale',
            'cadet_declaration': 'Déclaration du Cadet',
            'image_rights': 'Droit à l\'Image',
            'medical_certificate': 'Certificat Médical',
            'rules': 'Règlement ACADEF',
            'registration_summary': 'Dossier d\'inscription'
        }
        return types.get(self.document_type, self.document_type.replace('_', ' ').title())
    
    def __repr__(self):
        return f'<Document {self.document_type} - {self.status}>'


class SigningProcess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    candidate_signed = db.Column(db.Boolean, default=False)
    candidate_signed_date = db.Column(db.DateTime, nullable=True)
    guardian_signed = db.Column(db.Boolean, default=False)
    guardian_signed_date = db.Column(db.DateTime, nullable=True)
    signing_token = db.Column(db.String(64), nullable=False, unique=True)
    expiry_date = db.Column(db.DateTime, nullable=False)
    
    # Relationship
    document = db.relationship('Document', backref='signing_process', uselist=False)
    
    def __repr__(self):
        return f'<SigningProcess {self.id}>'


class MedicalInformation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    
    # Certificat médical
    medical_certificate_date = db.Column(db.Date, nullable=True)
    doctor_name = db.Column(db.String(120), nullable=True)
    sport_allowed = db.Column(db.Boolean, default=False)
    sport_competition_allowed = db.Column(db.Boolean, default=False)
    collective_living_allowed = db.Column(db.Boolean, default=False)
    vaccinations_up_to_date = db.Column(db.Boolean, default=False)
    flight_allowed = db.Column(db.Boolean, default=False)
    
    # Questionnaire de santé
    family_cardiac_death = db.Column(db.Boolean, default=False)
    chest_pain = db.Column(db.Boolean, default=False)
    asthma = db.Column(db.Boolean, default=False)
    fainting = db.Column(db.Boolean, default=False)
    stopped_sport_for_health = db.Column(db.Boolean, default=False)
    long_term_treatment = db.Column(db.Boolean, default=False)
    pain_after_injury = db.Column(db.Boolean, default=False)
    sport_interrupted_health = db.Column(db.Boolean, default=False)
    medical_advice_needed = db.Column(db.Boolean, default=False)
    
    # Informations additionnelles
    additional_medical_info = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<MedicalInformation for candidate {self.candidate_id}>'


class PhysicalMeasurements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    
    # Mensurations
    height = db.Column(db.Integer, nullable=True)  # en cm
    head_size = db.Column(db.Integer, nullable=True)  # tour de tête en cm
    neck_size = db.Column(db.Integer, nullable=True)  # tour de cou en cm
    chest_size = db.Column(db.Integer, nullable=True)  # tour de poitrine en cm
    waist_size = db.Column(db.Integer, nullable=True)  # tour de ceinture en cm
    bust_height = db.Column(db.Integer, nullable=True)  # hauteur du buste en cm
    inseam = db.Column(db.Integer, nullable=True)  # hauteur entre jambes en cm
    shoe_size = db.Column(db.Integer, nullable=True)  # pointure
    weight = db.Column(db.Integer, nullable=True)  # poids en kg
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PhysicalMeasurements for candidate {self.candidate_id}>'


# Créons une classe pour les rendez-vous d'entretien
class AppointmentSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    max_candidates = db.Column(db.Integer, default=1)
    current_candidates = db.Column(db.Integer, default=0)
    additional_info = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationship
    bookings = db.relationship('AppointmentBooking', backref='appointment_slot')
    
    def is_available(self):
        return self.current_candidates < self.max_candidates
    
    def __repr__(self):
        return f'<AppointmentSlot {self.date} {self.start_time}-{self.end_time}>'


class AppointmentBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_slot_id = db.Column(db.Integer, db.ForeignKey('appointment_slot.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    
    def __repr__(self):
        return f'<AppointmentBooking {self.id}>'


# Créons une table pour les périodes d'ouverture/fermeture des candidatures
class ApplicationPeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    promotion_year = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ApplicationPeriod {self.name} - {self.promotion_year}>'


# Ajout des relations de Candidate vers les nouvelles tables
Candidate.medical_information = db.relationship('MedicalInformation', backref='candidate', uselist=False)
Candidate.measurements = db.relationship('PhysicalMeasurements', backref='candidate', uselist=False)
Candidate.appointment_bookings = db.relationship('AppointmentBooking', backref='candidate')
