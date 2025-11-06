# Image de base
FROM python:3.10-slim

# Répertoire de travail
WORKDIR /app

# Copier le code source
COPY . /app

# Installer les dépendances nécessaires
RUN pip install --no-cache-dir spyne==2.14.0 lxml requests

# Exposer le port du service SOAP
EXPOSE 8000

# Lancer le service
CMD ["python", "main.py"]
