# Cahier des Charges - Plateforme de Gestion des Candidatures ACADEF

## 1. Présentation du Projet

### 1.1 Contexte
L'Académie des Cadets de la Défense (ACADEF) de Nantes nécessite une plateforme moderne pour gérer efficacement le processus d'inscription des candidats. Cette application remplacera le système actuel basé sur des documents papier et des processus manuels.

### 1.2 Objectifs
- Dématérialiser le processus de candidature
- Faciliter la gestion administrative des candidatures
- Améliorer l'expérience utilisateur pour les candidats et leurs tuteurs légaux
- Sécuriser les données personnelles conformément au RGPD
- Permettre un suivi en temps réel de l'état des candidatures
- Intégrer un système de signature électronique des documents officiels

## 2. Spécifications Fonctionnelles

### 2.1 Processus d'Inscription en 5 Étapes
1. **Étape 1** : Saisie des informations personnelles du candidat et téléchargement des documents d'identité
2. **Étape 2** : Saisie des mensurations physiques pour l'uniforme et l'équipement
3. **Étape 3** : Enregistrement des informations des tuteurs légaux
4. **Étape 4** : Signature électronique des documents obligatoires
5. **Étape 5** : Finalisation de la candidature

### 2.2 Gestion des Utilisateurs
- **Candidats** : Création de compte lors de l'étape 1, accès à leur dossier
- **Tuteurs légaux** : Création de compte lors de l'étape 3, accès aux documents à signer
- **Administrateurs** : Gestion complète des candidatures et des périodes d'inscription

### 2.3 Gestion des Documents
- Génération automatique de PDFs personnalisés pour chaque candidat
- Circuit de signature électronique (candidat → tuteurs légaux)
- Stockage sécurisé des documents officiels
- Possibilité de télécharger les documents signés

### 2.4 Processus de Validation
- Validation automatique des étapes lors de la progression
- Validation administrative des dossiers complets
- Génération de notifications aux différentes étapes
- Possibilité de demander des compléments d'information

### 2.5 Intégration Externe
- API pour synchronisation avec les applications externes de l'ACADEF
- Intégration WordPress pour la communication publique

## 3. Spécifications Techniques

### 3.1 Architecture
- Application web Flask (Python)
- Base de données PostgreSQL
- Architecture MVC

### 3.2 Sécurité
- Authentification sécurisée
- Chiffrement des données sensibles
- Sessions sécurisées avec cookies HTTP-only
- Protection CSRF sur tous les formulaires
- Validation des entrées côté serveur et client

### 3.3 Interface Utilisateur
- Design responsive compatible mobile et desktop
- Interface intuitive adaptée aux différents profils d'utilisateurs
- Formulaires interactifs avec validation en temps réel

### 3.4 Performance
- Optimisation des requêtes de base de données
- Mise en cache des données statiques
- Chargement asynchrone des ressources

## 4. Contraintes et Exigences

### 4.1 Légales
- Conformité RGPD pour la collecte et le traitement des données personnelles
- Validité juridique des signatures électroniques
- Conservation des données selon les durées légales

### 4.2 Techniques
- Compatibilité avec les navigateurs modernes (Chrome, Firefox, Safari, Edge)
- Temps de réponse inférieur à 3 secondes pour les opérations courantes
- Disponibilité 24/7 avec maintenance planifiée

### 4.3 Organisationnelles
- Respect des périodes d'inscription définies par l'ACADEF
- Adaptation aux processus administratifs existants
- Prise en compte des différentes promotions et années scolaires

## 5. Livrables

### 5.1 Application
- Code source complet de l'application
- Base de données initialisée
- Documentation technique et utilisateur

### 5.2 Documentation
- Manuel d'utilisation pour les différents profils d'utilisateurs
- Documentation technique pour la maintenance
- Schéma de la base de données
- Guide de déploiement

## 6. Planning et Jalons

### 6.1 Phases de Développement
1. **Phase d'analyse et conception** : Définition détaillée des besoins et maquettage
2. **Phase de développement** : Implémentation des fonctionnalités
3. **Phase de test** : Tests unitaires, fonctionnels et d'intégration
4. **Phase de déploiement** : Mise en production et formation des utilisateurs
5. **Phase de maintenance** : Corrections de bugs et évolutions

### 6.2 Jalons Clés
- Validation de la conception
- Livraison du prototype fonctionnel
- Recette utilisateur
- Mise en production
- Formation des administrateurs

## 7. Modalités de Validation

- Tests de recette avec des scénarios utilisateurs réels
- Validation des performances sous charge
- Audit de sécurité
- Validation juridique des processus de signature électronique