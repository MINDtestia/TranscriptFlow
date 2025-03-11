import streamlit as st
import streamlit_authenticator as stauth
import yaml
import os
from yaml.loader import SafeLoader

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if not os.path.exists(config_path):
        st.error(f"Fichier introuvable : {config_path}")
        return None

    with open(config_path, "r") as file:
        return yaml.load(file, Loader=SafeLoader)

def authenticate():
    config = load_config()
    if not config:
        return False

    authenticator = stauth.Authenticate(
        credentials=config["credentials"],
        cookie_name=config["cookie"]["name"],
        key=config["cookie"]["key"],
        cookie_expiry_days=config["cookie"]["expiry_days"]
    )

    authenticator.login(location="main")

    # Récupère les valeurs directement depuis st.session_state
    authentication_status = st.session_state.get("authentication_status")
    name = st.session_state.get("name")
    username = st.session_state.get("username")

    if authentication_status:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.success(f"Bienvenue {name} !")
        return True
    elif authentication_status is False:
        st.error("Identifiant ou mot de passe incorrect.")
        return False
    elif authentication_status is None:
        st.warning("Veuillez entrer votre nom d'utilisateur et mot de passe.")
        return False


def logout():
    config = load_config()
    if config:
        authenticator = stauth.Authenticate(
            credentials=config["credentials"],
            cookie_name=config["cookie"]["name"],
            key=config["cookie"]["key"],
            cookie_expiry_days=config["cookie"]["expiry_days"]
        )
        authenticator.logout("Déconnexion", "sidebar")
