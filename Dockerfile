# Utilisation d'une image Python légère
FROM python:3.12-slim

# Définition des variables d'environnement pour optimiser Python
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Définition du répertoire de travail
WORKDIR /app/API_Domino

# Installation des dépendances système nécessaires
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier uniquement requirements.txt pour optimiser le cache Docker
COPY API_Domino/requirements.txt /app/API_Domino/requirements.txt

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY API_Domino/ /app/API_Domino/

# Exposer le port pour Northflank
EXPOSE 8000

# Commande pour démarrer l'API avec Daphne (ASGI)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "API_Domino.asgi:application"]
