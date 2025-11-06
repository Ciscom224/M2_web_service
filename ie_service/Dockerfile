FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y gcc && apt-get clean

# Copier les dépendances Python
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -U pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source du service
COPY . /app

# Exposer le port du service IE
EXPOSE 8001

# Démarrage du service
CMD ["python", "main.py"]
