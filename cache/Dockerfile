FROM python:3.10-slim

LABEL maintainer="votre-email@example.com"
LABEL description="TranscriptFlow - Application d'extraction, transcription et analyse audio"
LABEL version="1.0.0"

# Définir le répertoire de travail
WORKDIR /app

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true

# Installer les dépendances système (ffmpeg, etc.)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier l'application
COPY . .

# Créer un répertoire pour le cache et les données persistantes
RUN mkdir -p /data/cache /data/uploads

# Volume pour stocker les données persistantes
VOLUME ["/data"]

# Exposer le port Streamlit
EXPOSE 8501

# Commande de démarrage
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Vérification de santé
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/ || exit 1