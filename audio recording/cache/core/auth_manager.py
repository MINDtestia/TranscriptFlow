import bcrypt
import jwt
from datetime import datetime, timedelta
import streamlit as st
from sqlalchemy.orm import Session
from .database import User, get_db
import os

# Clé secrète pour JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "votre_cle_secrete_par_defaut")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 semaine


def get_password_hash(password):
    """Génère un hash de mot de passe avec bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain_password, hashed_password):
    """Vérifie si le mot de passe correspond au hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def authenticate_user(db: Session, username: str, password: str):
    """Authentifie un utilisateur et retourne l'utilisateur si valide"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict):
    """Crée un token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user_from_token(token: str, db: Session):
    """Récupère l'utilisateur à partir du token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
    except jwt.PyJWTError:
        return None

    user = db.query(User).filter(User.username == username).first()
    return user


def login_user():
    """Interface de connexion pour Streamlit"""
    st.title("Connexion")

    username = st.text_input("Nom d'utilisateur", key="login_username")
    password = st.text_input("Mot de passe", type="password", key="login_password")

    if st.button("Se connecter", key="login_button"):
        if not username or not password:
            st.error("Veuillez entrer un nom d'utilisateur et un mot de passe")
            return False

        # Vérifier l'authentification
        db = next(get_db())
        user = authenticate_user(db, username, password)

        if not user:
            st.error("Nom d'utilisateur ou mot de passe incorrect")
            return False

        # Mise à jour du dernier login
        user.last_login = datetime.utcnow()
        db.commit()

        # Création du token
        token = create_access_token({"sub": user.username})

        # Stockage dans la session
        st.session_state["token"] = token
        st.session_state["user_id"] = user.id
        st.session_state["username"] = user.username
        st.session_state["is_admin"] = user.is_admin
        st.session_state["authenticated"] = True

        st.success(f"Bienvenue {user.first_name}!")
        return True

    return False


def register_user():
    """Interface d'inscription pour Streamlit"""
    st.title("Inscription")

    email = st.text_input("Email", key="register_email")
    username = st.text_input("Nom d'utilisateur", key="register_username")
    first_name = st.text_input("Prénom", key="register_first_name")
    last_name = st.text_input("Nom", key="register_last_name")
    password = st.text_input("Mot de passe", type="password", key="register_password")
    password_confirm = st.text_input("Confirmer le mot de passe", type="password", key="register_password_confirm")

    if st.button("S'inscrire", key="register_button"):
        if not all([email, username, first_name, password, password_confirm]):
            st.error("Veuillez remplir tous les champs obligatoires")
            return False

        if password != password_confirm:
            st.error("Les mots de passe ne correspondent pas")
            return False

        # Vérifier si l'utilisateur existe déjà
        db = next(get_db())
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            st.error("Cet utilisateur ou cet email existe déjà")
            return False

        # Création du nouvel utilisateur
        hashed_password = get_password_hash(password)
        new_user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hashed_password
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        st.success("Inscription réussie! Vous pouvez maintenant vous connecter.")
        return True

    return False


def logout_user():
    """Déconnexion de l'utilisateur"""
    if st.button("Déconnexion", key="logout_button"):
        for key in ["token", "user_id", "username", "is_admin", "authenticated"]:
            if key in st.session_state:
                del st.session_state[key]
        st.success("Vous avez été déconnecté avec succès!")
        st.rerun()


def change_password(user_id: int, current_password: str, new_password: str) -> bool:
    """Change le mot de passe d'un utilisateur"""
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return False

    # Vérifier l'ancien mot de passe
    if not verify_password(current_password, user.hashed_password):
        return False

    # Mettre à jour avec le nouveau mot de passe
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True


def reset_password_request(email: str) -> bool:
    """Génère un token de réinitialisation pour un utilisateur"""
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return False

    # Générer un token valide pendant 1 heure
    token = create_access_token(
        {"sub": user.username, "type": "reset_password"},
        expires_minutes=60
    )

    # Ici, vous ajouteriez la logique pour envoyer un email avec le token

    return True


def reset_password_confirm(token: str, new_password: str) -> bool:
    """Réinitialise le mot de passe avec un token valide"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("type")

        if not username or token_type != "reset_password":
            return False

        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return False

        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return True

    except jwt.PyJWTError:
        return False