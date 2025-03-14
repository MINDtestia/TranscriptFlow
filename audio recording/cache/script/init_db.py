from core.database import Base, engine, User, APIKey, Transcription, Subscription, get_db
from core.auth_manager import get_password_hash
import argparse


def init_database():
    """Initialise la base de données et crée les tables"""
    Base.metadata.create_all(bind=engine)
    print("Base de données initialisée avec succès!")


def create_admin_user(username, password, email):
    """Crée un utilisateur admin"""
    db = next(get_db())

    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print(f"L'utilisateur {username} existe déjà.")
        return

    # Créer le nouvel utilisateur admin
    hashed_password = get_password_hash(password)
    admin_user = User(
        username=username,
        email=email,
        first_name="Admin",
        last_name="User",
        hashed_password=hashed_password,
        is_admin=True
    )

    db.add(admin_user)
    db.commit()
    print(f"Utilisateur admin '{username}' créé avec succès!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialisation de la base de données")
    parser.add_argument("--create-admin", action="store_true", help="Créer un utilisateur admin")
    parser.add_argument("--username", help="Nom d'utilisateur admin")
    parser.add_argument("--password", help="Mot de passe admin")
    parser.add_argument("--email", help="Email admin")

    args = parser.parse_args()

    # Initialiser la base de données
    init_database()

    # Créer un administrateur si demandé
    if args.create_admin:
        if not all([args.username, args.password, args.email]):
            print("Erreur: --username, --password et --email sont requis pour créer un admin")
        else:
            create_admin_user(args.username, args.password, args.email)