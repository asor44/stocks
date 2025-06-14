import os
import requests
import json
import logging
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

# Configuration des API
OTHER_APP_API_URL = os.environ.get('OTHER_APP_API_URL')
OTHER_APP_API_KEY = os.environ.get('OTHER_APP_API_KEY')

WP_API_URL = os.environ.get('WP_API_URL')
WP_API_USERNAME = os.environ.get('WP_API_USERNAME')
WP_API_PASSWORD = os.environ.get('WP_API_PASSWORD')

# Configuration pour les tests si les variables d'environnement ne sont pas définies
if not OTHER_APP_API_URL:
    logger.warning("OTHER_APP_API_URL n'est pas défini, utilisation d'une valeur par défaut pour les tests")
    OTHER_APP_API_URL = "https://api.example.com"

if not WP_API_URL:
    logger.warning("WP_API_URL n'est pas défini, utilisation d'une valeur par défaut pour les tests")
    WP_API_URL = "https://wordpress.example.com"

def create_account_in_other_app(user_data):
    """
    Crée un compte utilisateur dans l'autre application via son API.
    
    Args:
        user_data (dict): Données de l'utilisateur à créer
            {
                'username': 'nom_utilisateur',
                'email': 'email@example.com',
                'password': 'mot_de_passe',
                'first_name': 'Prénom',
                'last_name': 'Nom',
                'role': 'role' # 'candidate' ou 'guardian'
            }
    
    Returns:
        dict: Réponse de l'API ou message d'erreur
    """
    if not OTHER_APP_API_URL or not OTHER_APP_API_KEY:
        logger.error("Configuration de l'API de l'autre application manquante")
        return {
            'success': False,
            'message': "Configuration de l'API manquante"
        }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {OTHER_APP_API_KEY}'
        }
        
        response = requests.post(
            f"{OTHER_APP_API_URL}/users/create",
            headers=headers,
            data=json.dumps(user_data)
        )
        
        if response.status_code == 201:
            logger.info(f"Compte créé avec succès dans l'autre application pour {user_data['email']}")
            return {
                'success': True,
                'data': response.json()
            }
        else:
            logger.error(f"Erreur lors de la création du compte dans l'autre application: {response.text}")
            return {
                'success': False,
                'message': f"Erreur {response.status_code}: {response.text}"
            }
    
    except Exception as e:
        logger.exception(f"Exception lors de la création du compte dans l'autre application")
        return {
            'success': False,
            'message': str(e)
        }

def delete_account_in_other_app(username_or_email):
    """
    Supprime un compte utilisateur dans l'autre application via son API.
    
    Args:
        username_or_email (str): Nom d'utilisateur ou email de l'utilisateur à supprimer
    
    Returns:
        dict: Réponse de l'API ou message d'erreur
    """
    if not OTHER_APP_API_URL or not OTHER_APP_API_KEY:
        logger.error("Configuration de l'API de l'autre application manquante")
        return {
            'success': False,
            'message': "Configuration de l'API manquante"
        }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {OTHER_APP_API_KEY}'
        }
        
        # Données pour identifier l'utilisateur à supprimer
        data = {
            'identifier': username_or_email  # peut être username ou email selon l'API
        }
        
        response = requests.delete(
            f"{OTHER_APP_API_URL}/users/delete",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code in (200, 204):
            logger.info(f"Compte supprimé avec succès dans l'autre application pour {username_or_email}")
            return {
                'success': True,
                'message': f"Compte supprimé avec succès pour {username_or_email}"
            }
        else:
            logger.error(f"Erreur lors de la suppression du compte dans l'autre application: {response.text}")
            return {
                'success': False,
                'message': f"Erreur {response.status_code}: {response.text}"
            }
    
    except Exception as e:
        logger.exception(f"Exception lors de la suppression du compte dans l'autre application")
        return {
            'success': False,
            'message': str(e)
        }

def delete_account_in_wordpress(username_or_id):
    """
    Supprime un compte utilisateur dans WordPress via l'API REST.
    
    Args:
        username_or_id (str/int): Nom d'utilisateur ou ID de l'utilisateur à supprimer
    
    Returns:
        dict: Réponse de l'API ou message d'erreur
    """
    if not WP_API_URL or not WP_API_USERNAME or not WP_API_PASSWORD:
        logger.error("Configuration de l'API WordPress manquante")
        return {
            'success': False,
            'message': "Configuration de l'API WordPress manquante"
        }
    
    try:
        # Authentification WordPress par Basic Auth
        auth = (WP_API_USERNAME, WP_API_PASSWORD)
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Déterminer si c'est un ID ou un nom d'utilisateur
        user_id = None
        if isinstance(username_or_id, int) or (isinstance(username_or_id, str) and username_or_id.isdigit()):
            user_id = username_or_id
        else:
            # Si c'est un nom d'utilisateur, on doit d'abord trouver l'ID
            try:
                response = requests.get(
                    f"{WP_API_URL}/wp-json/wp/v2/users?search={username_or_id}",
                    auth=auth,
                    headers=headers
                )
                if response.status_code == 200:
                    users = response.json()
                    if users and len(users) > 0:
                        user_id = users[0]['id']
            except Exception as e:
                logger.exception(f"Erreur lors de la recherche de l'utilisateur WordPress: {str(e)}")
        
        if not user_id:
            return {
                'success': False,
                'message': f"Impossible de trouver l'utilisateur WordPress: {username_or_id}"
            }
        
        # Supprimer l'utilisateur (force=true pour assigner son contenu à un autre utilisateur)
        response = requests.delete(
            f"{WP_API_URL}/wp-json/wp/v2/users/{user_id}?force=true&reassign=1",
            auth=auth,
            headers=headers
        )
        
        if response.status_code in (200, 204):
            logger.info(f"Compte WordPress supprimé avec succès pour ID {user_id}")
            return {
                'success': True,
                'message': f"Compte WordPress supprimé avec succès"
            }
        else:
            logger.error(f"Erreur lors de la suppression du compte WordPress: {response.text}")
            return {
                'success': False,
                'message': f"Erreur {response.status_code}: {response.text}"
            }
    
    except Exception as e:
        logger.exception(f"Exception lors de la suppression du compte WordPress")
        return {
            'success': False,
            'message': str(e)
        }

def create_account_in_wordpress(user_data):
    """
    Crée un compte utilisateur dans WordPress via l'API REST.
    
    Args:
        user_data (dict): Données de l'utilisateur à créer
            {
                'username': 'nom_utilisateur',
                'email': 'email@example.com',
                'password': 'mot_de_passe',
                'first_name': 'Prénom',
                'last_name': 'Nom',
                'roles': ['subscriber'] # rôle WordPress
            }
    
    Returns:
        dict: Réponse de l'API ou message d'erreur
    """
    if not WP_API_URL or not WP_API_USERNAME or not WP_API_PASSWORD:
        logger.error("Configuration de l'API WordPress manquante")
        return {
            'success': False,
            'message': "Configuration de l'API WordPress manquante"
        }
    
    try:
        # Authentification WordPress par Basic Auth
        auth = (WP_API_USERNAME, WP_API_PASSWORD)
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # WordPress API endpoint pour créer un utilisateur
        response = requests.post(
            f"{WP_API_URL}/wp-json/wp/v2/users",
            auth=auth,
            headers=headers,
            data=json.dumps(user_data)
        )
        
        if response.status_code in (201, 200):
            logger.info(f"Compte WordPress créé avec succès pour {user_data['email']}")
            return {
                'success': True,
                'data': response.json()
            }
        else:
            logger.error(f"Erreur lors de la création du compte WordPress: {response.text}")
            return {
                'success': False,
                'message': f"Erreur {response.status_code}: {response.text}"
            }
    
    except Exception as e:
        logger.exception(f"Exception lors de la création du compte WordPress")
        return {
            'success': False,
            'message': str(e)
        }