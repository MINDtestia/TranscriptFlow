#!/usr/bin/env python3
"""
Script d'installation automatisée pour TranscriptFlow.
Ce script va:
1. Vérifier les prérequis
2. Créer un environnement virtuel
3. Installer les dépendances
4. Configurer les fichiers de base
"""

import os
import sys
import subprocess
import platform
import shutil
import getpass
import random
import string
import tempfile
from pathlib import Path
import argparse

# Constantes
MIN_PYTHON_VERSION = (3, 9)
REQUIRED_COMMANDS = ["ffmpeg", "git"]
DEFAULT_VENV_DIR = ".venv"
GITHUB_REPO = "https://github.com/username/transcriptflow.git"


# Couleurs pour les messages de terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(message, color, bold=False):
    """Affiche un message coloré dans le terminal."""
    if bold:
        print(f"{color}{Colors.BOLD}{message}{Colors.ENDC}")
    else:
        print(f"{color}{message}{Colors.ENDC}")


def print_header(message):
    """Affiche un en-tête."""
    print()
    print_colored(f"=== {message} ===", Colors.HEADER, bold=True)


def print_step(message):
    """Affiche une étape."""
    print_colored(f"→ {message}", Colors.BLUE)


def print_success(message):
    """Affiche un message de succès."""
    print_colored(f"✓ {message}", Colors.GREEN)


def print_warning(message):
    """Affiche un avertissement."""
    print_colored(f"⚠ {message}", Colors.WARNING)


def print_error(message):
    """Affiche une erreur."""
    print_colored(f"✗ {message}", Colors.FAIL)


def check_python_version():
    """Vérifie si la version de Python est suffisante."""
    print_step("Vérification de la version de Python...")
    current_version = sys.version_info[:2]
    if current_version < MIN_PYTHON_VERSION:
        print_error(f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} ou supérieur est requis.")
        print_error(f"Version actuelle: {current_version[0]}.{current_version[1]}")
        return False
    print_success(f"Python {current_version[0]}.{current_version[1]} détecté.")
    return True


def check_commands():
    """Vérifie si les commandes requises sont disponibles."""
    print_step("Vérification des dépendances système...")
    missing_commands = []

    for cmd in REQUIRED_COMMANDS:
        try:
            subprocess.run(["which", cmd], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            missing_commands.append(cmd)

    if missing_commands:
        print_error(f"Les commandes suivantes ne sont pas installées: {', '.join(missing_commands)}")

        if "ffmpeg" in missing_commands:
            if platform.system() == "Darwin":  # macOS
                print_warning("Pour installer FFmpeg sur macOS:")
                print("  brew install ffmpeg")
            elif platform.system() == "Linux":
                print_warning("Pour installer FFmpeg sur Linux (Ubuntu/Debian):")
                print("  sudo apt-get update && sudo apt-get install -y ffmpeg")
            elif platform.system() == "Windows":
                print_warning("Pour installer FFmpeg sur Windows:")
                print("  1. Téléchargez FFmpeg depuis https://ffmpeg.org/download.html")
                print("  2. Extrayez l'archive et ajoutez le dossier bin aux variables d'environnement PATH")

        return False

    print_success("Toutes les dépendances système sont installées.")
    return True


def create_virtual_env(venv_dir):
    """Crée un environnement virtuel Python."""
    print_step(f"Création de l'environnement virtuel dans {venv_dir}...")

    if os.path.exists(venv_dir):
        print_warning(f"Le dossier {venv_dir} existe déjà.")
        overwrite = input("Voulez-vous le remplacer ? [o/N] ").lower()
        if overwrite != 'o':
            print_warning("Installation annulée.")
            return False
        shutil.rmtree(venv_dir)

    try:
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        print_success(f"Environnement virtuel créé dans {venv_dir}.")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erreur lors de la création de l'environnement virtuel: {e}")
        return False


def install_dependencies(venv_dir):
    """Installe les dépendances Python dans l'environnement virtuel."""
    print_step("Installation des dépendances Python...")

    # Déterminer le chemin de pip dans l'environnement virtuel
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_dir, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")

    try:
        # Mettre à jour pip
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)

        # Installer les dépendances
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)

        print_success("Dépendances installées avec succès.")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erreur lors de l'installation des dépendances: {e}")
        return False


def create_env_file():
    """Crée un fichier .env avec la configuration de base."""
    print_step("Création du fichier .env...")

    if os.path.exists(".env"):
        print_warning("Le fichier .env existe déjà.")
        overwrite = input("Voulez-vous le remplacer ? [o/N] ").lower()
        if overwrite != 'o':
            print_warning("Configuration du fichier .env ignorée.")
            return False

    # Demander la clé API OpenAI
    openai_key = getpass.getpass("Entrez votre clé API OpenAI (laissez vide pour configurer plus tard): ")

    with open(".env", "w") as f:
        f.write(f"OPENAI_API_KEY={openai_key}\n")
        f.write("# Autres variables d'environnement peuvent être ajoutées ici\n")

    print_success("Fichier .env créé avec succès.")
    return True


def setup_auth_config():
    """Configure le fichier d'authentification."""
    print_step("Configuration de l'authentification...")

    auth_dir = os.path.join("core")
    os.makedirs(auth_dir, exist_ok=True)

    config_path = os.path.join(auth_dir, "config.yaml")

    if os.path.exists(config_path):
        print_warning("Le fichier de configuration d'authentification existe déjà.")
        overwrite = input("Voulez-vous le remplacer ? [o/N] ").lower()
        if overwrite != 'o':
            print_warning("Configuration de l'authentification ignorée.")
            return False

    # Générer un mot de passe admin aléatoire
    def generate_password():
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(chars) for _ in range(12))

    admin_password = generate_password()
    user_password = generate_password()

    # Dans une application réelle, on devrait hasher les mots de passe
    # Ici, on simule des hash pour l'exemple
    admin_hash = f"$2b$12${admin_password}"
    user_hash = f"$2b$12${user_password}"

    config_content = f"""credentials:
  usernames:
    admin:
      email: admin@example.com
      failed_login_attempts: 0
      first_name: Admin
      last_name: User
      logged_in: false
      password: "{admin_hash}"
      roles:
        - admin
    user1:
      email: user1@example.com
      failed_login_attempts: 0
      first_name: User
      last_name: One
      logged_in: false
      password: "{user_hash}"
      roles:
        - viewer

cookie:
  expiry_days: 30
  key: "{"".join(random.choice(string.digits) for _ in range(6))}"
  name: "streamlit_auth"
"""

    with open(config_path, "w") as f:
        f.write(config_content)

    print_success("Configuration d'authentification créée avec succès.")
    print_warning(f"Identifiants par défaut:")
    print(f"  Admin: admin / {admin_password}")
    print(f"  User: user1 / {user_password}")
    print_warning("IMPORTANT: Changez ces mots de passe après la première connexion!")

    return True


def create_directory_structure():
    """Crée la structure de répertoires du projet."""
    print_step("Création de la structure de répertoires...")

    directories = [
        "core",
        "my_page",
        "image",
        "tests",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    print_success("Structure de répertoires créée avec succès.")
    return True


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Installation automatisée de TranscriptFlow")
    parser.add_argument("--venv", default=DEFAULT_VENV_DIR, help="Nom du dossier pour l'environnement virtuel")
    parser.add_argument("--skip-checks", action="store_true", help="Ignorer les vérifications de prérequis")
    parser.add_argument("--clone", action="store_true", help="Cloner le dépôt depuis GitHub")

    args = parser.parse_args()

    print_header("Installation de TranscriptFlow")

    if args.clone:
        print_step(f"Clonage du dépôt depuis {GITHUB_REPO}...")
        try:
            subprocess.run(["git", "clone", GITHUB_REPO, "."], check=True)
            print_success("Dépôt cloné avec succès.")
        except subprocess.CalledProcessError as e:
            print_error(f"Erreur lors du clonage du dépôt: {e}")
            return 1

    if not args.skip_checks:
        if not check_python_version() or not check_commands():
            print_error("Veuillez installer les prérequis manquants et réessayer.")
            return 1

    if not create_virtual_env(args.venv):
        return 1

    if not args.clone:
        if not create_directory_structure():
            return 1

    if not os.path.exists("requirements.txt"):
        print_warning("Création d'un fichier requirements.txt de base...")
        with open("requirements.txt", "w") as f:
            f.write("streamlit==1.20.0\n")
            f.write("python-dotenv==1.0.0\n")
            f.write("openai==1.0.0\n")
            f.write("whisper==1.0\n")
            f.write("pytube==15.0.0\n")
            f.write("ffmpeg-python==0.2.0\n")
            f.write("streamlit-authenticator==0.2.2\n")
            f.write("yt-dlp==2023.3.4\n")
            f.write("certifi==2023.5.7\n")

    if not install_dependencies(args.venv):
        return 1

    if not create_env_file():
        return 1

    if not setup_auth_config():
        return 1

    print_header("Installation terminée avec succès!")

    # Afficher les instructions finales
    if platform.system() == "Windows":
        activate_cmd = f"{args.venv}\\Scripts\\activate"
    else:
        activate_cmd = f"source {args.venv}/bin/activate"

    print_colored("Pour démarrer TranscriptFlow:", Colors.CYAN)
    print(f"  1. Activez l'environnement virtuel: {activate_cmd}")
    print("  2. Lancez l'application: streamlit run app.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())