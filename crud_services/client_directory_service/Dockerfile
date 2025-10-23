# Image de base
FROM python:3.10-slimls


# Répertoire de travail
WORKDIR /app

# Étape 3 : Copier le code source du service
COPY . /app

# Installation  des dépendances
RUN pip install --no-cache-dir spyne==2.14.0 lxml

# Port
EXPOSE 8001

# lancement du service
CMD ["python", "main.py"]
