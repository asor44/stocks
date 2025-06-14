
# Portail d'Inscription Académie des Cadets

Plateforme de gestion des candidatures pour l'Académie des Cadets avec processus d'inscription en plusieurs étapes, signature électronique de documents et approbation administrative.

## Fonctionnalités

- Processus d'inscription en 5 étapes
- Téléchargement et signature de documents
- Gestion des tuteurs légaux
- Interface d'administration pour l'approbation/rejet des candidatures
- Création automatique de comptes dans d'autres applications lors de l'approbation
- Envoi d'emails automatiques

## Configuration

### Configuration de la base de données

L'application peut utiliser PostgreSQL (par défaut) ou MySQL. Pour utiliser MySQL, définissez les variables d'environnement suivantes :

```
DB_TYPE=mysql
MYSQL_HOST=adresse_du_serveur_mysql
MYSQL_USER=nom_utilisateur_mysql
MYSQL_PASSWORD=mot_de_passe_mysql
MYSQL_DATABASE=nom_de_la_base_mysql
MYSQL_PORT=3306
```

Pour PostgreSQL (par défaut), utilisez :

```
DB_TYPE=postgresql
DATABASE_URL=postgresql://user:password@host:port/database
```

### Configuration des emails

Pour l'envoi d'emails via Azure SMTP :

```
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USERNAME=votre_email@votredomaine.com
MAIL_PASSWORD=votre_mot_de_passe
MAIL_DEFAULT_SENDER=votre_email@votredomaine.com
```


### Intégration avec d'autres applications

Pour activer la création automatique de comptes dans d'autres applications lors de l'approbation d'une candidature, configurez les variables d'environnement suivantes :

#### Autre application

```
OTHER_APP_API_URL=https://autre-application-api.com
OTHER_APP_API_KEY=votre_cle_api
```

#### WordPress

```
WP_API_URL=https://votre-site-wordpress.com
WP_API_USERNAME=admin_wordpress
WP_API_PASSWORD=mot_de_passe_wordpress
```

## Déploiement

L'application utilise Gunicorn pour le serveur de production. Pour démarrer :

```
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

