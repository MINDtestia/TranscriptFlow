#!/bin/bash
set -e

echo "Déploiement de TranscriptFlow..."

# Générer un fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo "Génération du fichier .env..."
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    MINIO_SECRET_KEY=$(openssl rand -base64 32)
    JWT_SECRET_KEY=$(openssl rand -base64 64)
    TRAEFIK_PASSWORD=$(htpasswd -nb admin $(openssl rand -base64 12) | sed -e s/\\$/\\$\\$/g)

    cat > .env << EOF
# Base de données
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# MinIO
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=$MINIO_SECRET_KEY

# JWT
JWT_SECRET_KEY=$JWT_SECRET_KEY

# Traefik
TRAEFIK_USER=admin
TRAEFIK_PASSWORD=$TRAEFIK_PASSWORD

# OpenAI - À REMPLIR
OPENAI_API_KEY=votre_clé_api_openai
EOF

    echo "Fichier .env généré. Veuillez éditer pour configurer votre clé API OpenAI."
fi

# Vérifier si la configuration Traefik existe
if [ ! -d traefik ]; then
    echo "Création de la configuration Traefik..."
    mkdir -p traefik

    # Traefik configuration
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

    echo "Configuration Traefik créée. Veuillez éditer le fichier traefik/traefik.yml pour configurer votre email."
fi

# Démarrer les services
echo "Démarrage des services..."
docker-compose up -d

# Initialiser la base de données et créer un admin
echo "Initialisation de la base de données..."
echo "Veuillez attendre 10 secondes pour que la base de données démarre..."
sleep 10
docker-compose exec webapp python scripts/init_db.py --create-admin --username admin --password admin123 --email admin@example.com

echo "Déploiement terminé avec succès!"
echo "Vous pouvez accéder à TranscriptFlow à l'adresse: http://localhost:8501"
echo "Identifiants par défaut: admin / admin123"
echo "N'oubliez pas de changer ce mot de passe!"