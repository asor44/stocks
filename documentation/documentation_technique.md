# Documentation Technique - Plateforme de Gestion des Candidatures ACADEF

## 1. Architecture Globale

### 1.1 Structure du Projet

L'application est structurée selon les principes MVC (Modèle-Vue-Contrôleur) adaptés à Flask :

```
/
├── app.py                  # Point d'entrée principal, configuration de l'application
├── main.py                 # Script de démarrage
├── config.py               # Configuration de l'application
├── models.py               # Modèles ORM (SQLAlchemy)
├── routes/                 # Contrôleurs (blueprints Flask)
│   ├── __init__.py
│   ├── admin.py            # Routes d'administration
│   ├── admin_settings.py   # Routes de configuration admin
│   ├── auth.py             # Routes d'authentification
│   └── registration.py     # Routes d'inscription
├── static/                 # Ressources statiques
│   ├── css/
│   ├── js/
│   └── images/
├── templates/              # Vues (templates Jinja2)
│   ├── admin/
│   ├── auth/
│   ├── email/
│   └── registration/
├── uploads/                # Stockage des fichiers téléversés
├── utils/                  # Utilitaires et fonctions partagées
│   ├── email.py            # Fonctions d'envoi d'emails
│   ├── generate_documents.py # Génération de documents
│   ├── integration.py      # Intégration avec systèmes externes
│   └── pdf.py              # Génération de PDF
└── documentation/          # Documentation du projet
```

### 1.2 Pile Technologique

- **Backend** : Python 3.x, Flask 2.x
- **ORM** : SQLAlchemy avec Flask-SQLAlchemy
- **Base de données** : PostgreSQL
- **Authentification** : Flask-Login
- **Formulaires** : Flask-WTF
- **Email** : Flask-Mail
- **Génération PDF** : ReportLab
- **Frontend** : HTML5, CSS3 (Bootstrap), JavaScript

## 2. Composants Principaux

### 2.1 Configuration (config.py)

La classe `Config` centralise tous les paramètres de l'application :
- Configuration de la base de données
- Paramètres SMTP pour l'envoi d'emails
- Gestion des uploads de fichiers
- Clés de sécurité et paramètres de session

### 2.2 Authentification (routes/auth.py)

Le système d'authentification gère :
- Inscription et connexion des utilisateurs
- Gestion des sessions avec Flask-Login
- Réinitialisation de mot de passe
- Contrôle d'accès selon les rôles (admin, candidat, tuteur)

### 2.3 Processus d'Inscription (routes/registration.py)

Le cœur du système est un processus d'inscription en 5 étapes :
1. **Informations personnelles du candidat**
   - Création du compte utilisateur
   - Saisie des données personnelles
   - Upload des documents d'identité

2. **Mensurations physiques**
   - Saisie des mensurations pour l'équipement
   - Stockage des données dans PhysicalMeasurements

3. **Informations des tuteurs légaux**
   - Ajout des tuteurs légaux
   - Création de comptes pour les tuteurs
   - Envoi d'emails d'invitation

4. **Signature des documents**
   - Génération automatique des PDF à signer
   - Signature électronique par le candidat
   - Invitation des tuteurs à signer
   - Traçabilité du processus de signature

5. **Finalisation et soumission**
   - Vérification de l'ensemble des éléments
   - Soumission de la candidature
   - Notification à l'administration

### 2.4 Génération de Documents (utils/generate_documents.py et utils/pdf.py)

Le système génère automatiquement plusieurs types de documents PDF :
- **Autorisation parentale** : Consentement des tuteurs légaux
- **Certificat médical** : Formulaire à faire remplir par un médecin
- **Déclaration du cadet** : Engagement du candidat
- **Droit à l'image** : Autorisation d'utilisation des photos/vidéos
- **Règlement ACADEF** : Règles de conduite signées

Les documents sont générés avec ReportLab, personnalisés avec les informations du candidat et stockés dans le système de fichiers.

### 2.5 Système de Signature Électronique

Le processus de signature comprend :
1. **Génération de token unique** pour chaque document à signer
2. **Envoi d'emails avec liens sécurisés** vers l'interface de signature
3. **Interface de visualisation et signature** des documents
4. **Traçabilité des signatures** (date, utilisateur, etc.)
5. **Vérification de validité** des tokens de signature

### 2.6 Administration (routes/admin.py et routes/admin_settings.py)

L'interface d'administration permet :
- Gestion des candidatures (consultation, approbation, rejet)
- Configuration des périodes d'inscription
- Gestion des créneaux d'entretien
- Suivi des statistiques et reporting
- Paramétrage du système

## 3. Flux de Données et Processus

### 3.1 Création de Compte et Authentification

```
+----------------+     +----------------+     +----------------+
| Formulaire     | --> | Validation     | --> | Création       |
| d'inscription  |     | des données    |     | utilisateur    |
+----------------+     +----------------+     +----------------+
                                                      |
                                                      v
                       +----------------+     +----------------+
                       | Envoi email    | <-- | Génération     |
                       | confirmation   |     | mot de passe   |
                       +----------------+     +----------------+
```

### 3.2 Processus de Candidature

```
+----------------+     +----------------+     +----------------+
| Étape 1        | --> | Étape 2        | --> | Étape 3        |
| Infos candidat |     | Mensurations   |     | Infos tuteurs  |
+----------------+     +----------------+     +----------------+
                                                      |
                                                      v
                       +----------------+     +----------------+
                       | Étape 5        | <-- | Étape 4        |
                       | Finalisation   |     | Signatures     |
                       +----------------+     +----------------+
                              |
                              v
                       +----------------+
                       | Soumission à   |
                       | l'administration|
                       +----------------+
```

### 3.3 Processus de Signature

```
+----------------+     +----------------+     +----------------+
| Génération     | --> | Signature      | --> | Invitation     |
| documents PDF  |     | candidat       |     | tuteurs        |
+----------------+     +----------------+     +----------------+
                                                      |
                                                      v
                       +----------------+     +----------------+
                       | Finalisation   | <-- | Signature      |
                       | documents      |     | tuteurs        |
                       +----------------+     +----------------+
```

## 4. Sécurité

### 4.1 Authentification et Autorisation

- **Hachage des mots de passe** avec Werkzeug
- **Sessions sécurisées** avec cookies HTTP-only
- **CSRF protection** sur tous les formulaires
- **Contrôle d'accès** basé sur les rôles et permissions

### 4.2 Sécurité des Données

- **Validation des entrées** côté serveur et client
- **Protection contre les injections SQL** avec SQLAlchemy
- **Limitation des uploads** aux types de fichiers autorisés
- **Noms de fichiers sécurisés** pour éviter les attaques par traversée de chemin

### 4.3 Confidentialité

- **Chiffrement des communications** avec HTTPS
- **Accès restreint** aux informations sensibles
- **Tokens à durée limitée** pour les opérations sensibles

## 5. Gestion des Emails

### 5.1 Types d'Emails Envoyés

- **Confirmation d'inscription** aux candidats
- **Invitation des tuteurs** à créer leur compte
- **Demandes de signature** pour les documents
- **Notifications d'étape** lors de la progression dans le formulaire
- **Confirmation de candidature** complète
- **Notifications administratives** pour nouvelles candidatures

### 5.2 Configuration SMTP

Les paramètres de connexion au serveur SMTP sont configurés via des variables d'environnement :
- `MAIL_SERVER` : serveur SMTP (ex: smtp.office365.com)
- `MAIL_PORT` : port SMTP (généralement 587 pour TLS)
- `MAIL_USERNAME` : adresse email d'envoi
- `MAIL_PASSWORD` : mot de passe de l'email d'envoi

## 6. Intégration Externe

### 6.1 API pour Applications Externes

L'application peut se synchroniser avec d'autres systèmes de l'ACADEF via des intégrations API :
- Création de comptes utilisateurs sur la plateforme principale
- Synchronisation des données de candidature
- Importation des résultats d'entretien

### 6.2 Intégration WordPress

L'application peut se connecter à un site WordPress pour :
- Publier les périodes d'inscription actives
- Mettre à jour les informations de contact
- Gérer les actualités liées aux candidatures

## 7. Déploiement

### 7.1 Prérequis Serveur

- Python 3.x
- PostgreSQL
- Serveur SMTP pour l'envoi d'emails
- Stockage fichiers (minimum 5 Go recommandé)

### 7.2 Variables d'Environnement

Les configurations sensibles sont gérées via des variables d'environnement :
- `DATABASE_URL` : URL de connexion à la base de données
- `SECRET_KEY` : Clé secrète pour les sessions et CSRF
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` : Configuration email
- `WP_API_URL`, `WP_API_KEY` : Connexion WordPress (si utilisée)
- `OTHER_APP_API_URL`, `OTHER_APP_API_KEY` : Connexion API externe (si utilisée)

## 8. Maintenance et Évolution

### 8.1 Migrations de Base de Données

Le fichier `migrate_db.py` contient les outils nécessaires pour faire évoluer le schéma de la base de données sans perte de données :
- Ajout de colonnes
- Modification de types de données
- Création de nouvelles tables

### 8.2 Logs et Monitoring

L'application journalise :
- Les connexions et tentatives d'authentification
- Les modifications importantes sur les candidatures
- Les erreurs système et techniques
- Les emails envoyés