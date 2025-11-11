FROM python:3.10-slim


# Répertoire de travail
WORKDIR /app

# Étape 3 : Copier le code source du service
COPY . /app

# Installation  des dépendances
RUN pip install --no-cache-dir spyne==2.14.0 lxml 

# Port
EXPOSE 8005

# lancement du service
CMD ["python", "main.py"]