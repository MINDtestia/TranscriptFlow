#!/bin/bash
set -e

echo "Déploiement de TranscriptFlow sur VPS Hostinger..."

# Vérifier que Docker et Docker Compose sont installés
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Installation de Docker et Docker Compose..."
    apt update
    apt install -y docker.io docker-compose
fi

# Vérifier si le fichier .env existe, sinon le créer
if [ ! -f .env ]; then
    echo "Génération du fichier .env..."
    # Générer des mots de passe aléatoires sécurisés
    POSTGRES_PASSWORD=$(openssl rand -base64 16)
    MINIO_SECRET_KEY=$(openssl rand -base64 16)
    JWT_SECRET_KEY=$(openssl rand -base64 32)

    # Créer le fichier .env
    cat > .env << EOF
# Base de données
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# MinIO
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=$MINIO_SECRET_KEY

# JWT
JWT_SECRET_KEY=$JWT_SECRET_KEY

# OpenAI - À REMPLIR
OPENAI_API_KEY=votre_clé_api_openai

# Traefik
TRAEFIK_USER=admin
TRAEFIK_PASSWORD=admin:$(openssl passwd -apr1 $(openssl rand -base64 12))
EOF

    echo "Fichier .env généré. IMPORTANT: Éditez-le pour configurer votre clé API OpenAI."
fi

# Créer les répertoires nécessaires
mkdir -p data
mkdir -p local_storage
mkdir -p traefik

# Configuration de base pour Traefik (si elle n'existe pas)
if [ ! -f traefik/traefik.yml ]; then
    echo "Création de la configuration Traefik..."
    mkdir -p traefik

    # Fichier de configuration de base
    cat > traefik/traefik.yml << EOF
api:
  dashboard: true

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false

certificatesResolvers:
  letsencrypt:
    acme:
      email: votre@email.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web
EOF

    echo "Configuration Traefik créée. Veuillez éditer traefik/traefik.yml pour configurer votre email."
fi

# Démarrer les services
echo "Démarrage des services..."
docker-compose up -d

# Attendre que les services démarrent
echo "Attente du démarrage des services (30 secondes)..."
sleep 30

# Initialiser la base de données et créer un admin
echo "Initialisation de la base de données..."
docker-compose exec webapp python -m script.init_db --create-admin --username admin --password admin123 --email admin@example.com

echo "Déploiement terminé avec succès!"
echo "Vous pouvez accéder à TranscriptFlow à l'adresse: http://$(curl -s ifconfig.me):8501"
echo "IMPORTANT: Changez le mot de passe admin par défaut après la première connexion!"