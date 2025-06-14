# Documentation - Plateforme de Gestion des Candidatures ACADEF

## Présentation

Cette documentation regroupe l'ensemble des informations relatives à la plateforme de gestion des candidatures pour l'Académie des Cadets de la Défense (ACADEF) de Nantes. La plateforme permet aux candidats de s'inscrire, soumettre leurs documents, signer électroniquement les formulaires requis, et aux administrateurs de gérer l'ensemble du processus de candidature.

## Index des Documents

### 1. Cahier des Charges
[Cahier des Charges](cahier_des_charges.md)

Ce document présente les spécifications fonctionnelles et techniques du projet, les objectifs, les contraintes et les livrables attendus.

### 2. User Stories
[User Stories](user_stories.md)

Les user stories détaillent les besoins des différents utilisateurs (candidats, tuteurs légaux, administrateurs) sous forme de scénarios d'utilisation.

### 3. Documentation ORM / Base de Données
[ORM Database](orm_database.md)

Description détaillée du schéma de la base de données, des modèles ORM, des relations entre entités et des contraintes d'intégrité.

### 4. Documentation Technique
[Documentation Technique](documentation_technique.md)

Documentation technique complète pour les développeurs, incluant l'architecture du système, les composants principaux, les flux de données, les aspects de sécurité et les procédures de déploiement.

### 5. Documentation Utilisateur
[Documentation Utilisateur](documentation_utilisateur.md)

Guide complet pour les utilisateurs finaux, expliquant comment utiliser la plateforme selon leur rôle (candidat, tuteur légal, administrateur).

## Informations Techniques

- **Langage de programmation** : Python
- **Framework** : Flask
- **Base de données** : PostgreSQL
- **ORM** : SQLAlchemy
- **Génération PDF** : ReportLab
- **Frontend** : HTML, CSS (Bootstrap), JavaScript

## Structure du Projet

```
/
├── app.py                  # Point d'entrée principal
├── main.py                 # Script de démarrage
├── config.py               # Configuration
├── models.py               # Modèles ORM
├── routes/                 # Contrôleurs
├── static/                 # Ressources statiques
├── templates/              # Vues
├── uploads/                # Fichiers téléversés
├── utils/                  # Utilitaires
└── documentation/          # Documentation
```

## Maintenance et Contact

Pour toute question concernant la documentation ou le projet :

- **Responsable technique** : [Nom du responsable technique]
- **Email** : [Email du support technique]

---

© 2025 Académie des Cadets de la Défense - Nantes