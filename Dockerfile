# Utilise une image de base Python légère (Alpine est souvent un bon choix pour les conteneurs)
FROM python:3.9-alpine

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Copie le fichier requirements.txt et installe les dépendances
# Cela permet de mettre en cache les dépendances si le code source ne change pas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le reste du code de l'application
COPY . .

# Expose le port sur lequel Gunicorn écoutera
EXPOSE 5000

# Commande pour démarrer l'application avec Gunicorn
# Les variables d'environnement seront injectées par Docker Compose
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "main:app"]
