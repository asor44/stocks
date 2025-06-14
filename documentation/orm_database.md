# Documentation ORM - Schéma de la Base de Données

## Introduction

Cette documentation décrit le schéma de la base de données utilisée par la plateforme de gestion des candidatures ACADEF. L'application utilise SQLAlchemy comme ORM (Object-Relational Mapping) avec Flask-SQLAlchemy pour simplifier l'interaction avec la base de données PostgreSQL.

## Modèles et Relations

Le diagramme suivant représente les principales entités du système et leurs relations :

```
                                 +-------------+
                                 |    User     |
                                 +-------------+
                                 | id          |
                                 | username    |
                                 | email       |
                                 | password    |
                                 | is_admin    |
                                 | is_active   |
                                 +------+------+
                                        |
                               +--------+---------+
                               |                  |
                        +------v------+    +------v------+
                        |  Candidate  |    |   Guardian  |
                        +-------------+    +-------------+
                        | id          |    | id          |
                        | user_id     |    | user_id     |
                        | first_name  |    | candidate_id|
                        | last_name   |    | first_name  |
                        | ...         |    | last_name   |
                        +------+------+    | ...         |
                               |           +-------------+
                               |
              +----------------+----------------+
              |                |                |
      +-------v------+ +-------v------+ +-------v------+
      | Application  | |   Medical    | |   Physical   |
      +-------------+| | Information  | | Measurements |
      | id           | +-------------+| +-------------+|
      | candidate_id | | id           | | id           |
      | status       | | candidate_id | | candidate_id |
      | ...          | | ...          | | ...          |
      +------+-------+ +-------------+ +-------------+
             |
             |
      +------v-------+
      |   Document   |
      +--------------+
      | id           |
      |application_id|
      | filename     |
      | document_type|
      | ...          |
      +------+-------+
             |
             |
      +------v-------+
      |  Signing     |
      |  Process     |
      +--------------+
      | id           |
      | document_id  |
      | ...          |
      +--------------+
```

## Description des Tables

### User

La table `User` stocke les informations d'authentification pour tous les types d'utilisateurs.

```python
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
```

**Relations:**
- `candidate` : Relation one-to-one avec la table Candidate
- `guardian` : Relation one-to-one avec la table Guardian

### Candidate

La table `Candidate` stocke les informations détaillées sur les candidats.

```python
class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    nationality = db.Column(db.String(64), nullable=True)
    birth_place = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(64), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    mobile_phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    school = db.Column(db.String(120), nullable=True)
    grade = db.Column(db.String(64), nullable=True)
    # Informations de contact d'urgence
    emergency_contact_name = db.Column(db.String(120), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    # Documents
    motivation_letter = db.Column(db.String(255), nullable=True)
    vital_card_copy = db.Column(db.String(255), nullable=True)
    id_card_copy = db.Column(db.String(255), nullable=True)
    insurance_certificate = db.Column(db.String(255), nullable=True)
    recent_photo = db.Column(db.String(255), nullable=True)
    mutual_card_copy = db.Column(db.String(255), nullable=True)
    # Statut et métadonnées
    application_status = db.Column(db.String(30), default='step1')
    additional_info = db.Column(db.Text, nullable=True)
    image_rights = db.Column(db.Boolean, default=True)
    promotion_year = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Champs pour le renouvellement d'informations
    info_renewal_requested = db.Column(db.Boolean, default=False)
    info_renewal_message = db.Column(db.Text, nullable=True)
    info_renewal_requested_at = db.Column(db.DateTime, nullable=True)
    info_renewal_requested_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_candidate_renewal_by'), nullable=True)
```

**Relations:**
- `application` : Relation one-to-one avec la table Application
- `guardians` : Relation one-to-many avec la table Guardian
- `medical_information` : Relation one-to-one avec la table MedicalInformation
- `measurements` : Relation one-to-one avec la table PhysicalMeasurements

### Guardian

La table `Guardian` stocke les informations sur les tuteurs légaux des candidats.

```python
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
    # Champs pour le renouvellement d'informations
    info_renewal_requested = db.Column(db.Boolean, default=False)
    info_renewal_message = db.Column(db.Text, nullable=True)
    info_renewal_requested_at = db.Column(db.DateTime, nullable=True)
    info_renewal_requested_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_guardian_renewal_by'), nullable=True)
```

### Application

La table `Application` gère le statut global de la candidature et son traitement administratif.

```python
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    review_date = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_application_reviewed_by'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    promotion_year = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Relations:**
- `documents` : Relation one-to-many avec la table Document
- `reviewer` : Relation many-to-one avec la table User (administrateur qui a examiné la candidature)

### Document

La table `Document` stocke les informations sur tous les documents liés à une candidature.

```python
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    uploaded_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_document_updated_by'), nullable=True)
    status = db.Column(db.String(20), default='pending')
    # Champs pour le renouvellement des documents
    renewal_requested = db.Column(db.Boolean, default=False)
    renewal_message = db.Column(db.Text, nullable=True)
    renewal_requested_at = db.Column(db.DateTime, nullable=True)
    renewal_requested_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_document_renewal_by'), nullable=True)
```

**Relations:**
- `signing_process` : Relation one-to-one avec la table SigningProcess

### SigningProcess

La table `SigningProcess` gère le workflow de signature électronique des documents.

```python
class SigningProcess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    candidate_signed = db.Column(db.Boolean, default=False)
    candidate_signed_date = db.Column(db.DateTime, nullable=True)
    guardian_signed = db.Column(db.Boolean, default=False)
    guardian_signed_date = db.Column(db.DateTime, nullable=True)
    signing_token = db.Column(db.String(64), nullable=False, unique=True)
    expiry_date = db.Column(db.DateTime, nullable=False)
```

### MedicalInformation

La table `MedicalInformation` stocke les informations médicales du candidat.

```python
class MedicalInformation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    # Informations certificat médical
    medical_certificate_date = db.Column(db.Date, nullable=True)
    doctor_name = db.Column(db.String(120), nullable=True)
    sport_allowed = db.Column(db.Boolean, default=False)
    sport_competition_allowed = db.Column(db.Boolean, default=False)
    collective_living_allowed = db.Column(db.Boolean, default=False)
    vaccinations_up_to_date = db.Column(db.Boolean, default=False)
    flight_allowed = db.Column(db.Boolean, default=False)
    # Questionnaire médical
    family_cardiac_death = db.Column(db.Boolean, default=False)
    chest_pain = db.Column(db.Boolean, default=False)
    asthma = db.Column(db.Boolean, default=False)
    fainting = db.Column(db.Boolean, default=False)
    stopped_sport_for_health = db.Column(db.Boolean, default=False)
    long_term_treatment = db.Column(db.Boolean, default=False)
    pain_after_injury = db.Column(db.Boolean, default=False)
    sport_interrupted_health = db.Column(db.Boolean, default=False)
    medical_advice_needed = db.Column(db.Boolean, default=False)
    # Autres
    additional_medical_info = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### PhysicalMeasurements

La table `PhysicalMeasurements` stocke les mensurations physiques du candidat pour la tenue.

```python
class PhysicalMeasurements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
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
```

### AppointmentSlot

La table `AppointmentSlot` gère les créneaux disponibles pour les entretiens.

```python
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
```

**Relations:**
- `bookings` : Relation one-to-many avec la table AppointmentBooking

### AppointmentBooking

La table `AppointmentBooking` gère les réservations des créneaux d'entretien.

```python
class AppointmentBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_slot_id = db.Column(db.Integer, db.ForeignKey('appointment_slot.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
```

### ApplicationPeriod

La table `ApplicationPeriod` gère les périodes pendant lesquelles les candidatures sont ouvertes.

```python
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
```

## Indexation et Performance

Les clés primaires sont automatiquement indexées par PostgreSQL. Les colonnes suivantes bénéficient également d'index pour optimiser les requêtes fréquentes :
- `User.email` et `User.username` (index unique)
- `Candidate.user_id` et `Candidate.application_status`
- `Guardian.candidate_id` et `Guardian.user_id`
- `Application.candidate_id` et `Application.status`
- `Document.application_id` et `Document.document_type`
- `SigningProcess.document_id` et `SigningProcess.signing_token` (index unique)

## Contraintes et Intégrité Référentielle

- Les contraintes de clé étrangère garantissent l'intégrité référentielle entre les tables
- Des contraintes d'unicité empêchent les doublons pour les emails, noms d'utilisateur et tokens
- Les horodatages automatiques (`created_at`, `updated_at`) tracent les modifications

## Migrations et Évolutions

Les migrations de schéma sont gérées via des scripts dédiés qui permettent d'ajouter de nouvelles colonnes ou contraintes sans perte de données. Le fichier `migrate_db.py` contient les fonctions essentielles pour :
- Vérifier l'existence des colonnes
- Ajouter des colonnes si nécessaire
- Exécuter des migrations spécifiques

## Bonnes Pratiques

1. **Utiliser les relations SQLAlchemy** plutôt que de manipuler directement les clés étrangères
2. **Toujours verrouiller les transactions** avec try/except/rollback lors des opérations complexes
3. **Valider les données** avant insertion ou mise à jour
4. **Utiliser les requêtes optimisées** avec jointures appropriées pour limiter le nombre d'accès à la base