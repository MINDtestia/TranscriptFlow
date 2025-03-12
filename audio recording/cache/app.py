# lancer // streamlit run '/Users/alexis/Desktop/Python/audio recording/cache/app.py'

import os
import logging
import streamlit as st

from core.session_manager import initialize_session_state
from core.database import Base, engine
from core.auth_manager import login_user, register_user, logout_user
from core.plan_manager import PlanManager
from my_page.setting.account_settings import afficher_page_compte
# Définir le chemin de base du projet
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="TranscriptFlow",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'app.log')),
        logging.StreamHandler()
    ]
)

# Assurez-vous que la base de données est initialisée
Base.metadata.create_all(bind=engine)

# Initialiser toutes les variables de session
initialize_session_state()

if not st.session_state.get("authenticated", False):
    # Interface d'authentification avec onglets
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])

    with tab1:
        if login_user():
            st.rerun()

    with tab2:
        if register_user():
            st.success("Veuillez vous connecter avec votre nouveau compte.")

    # Arrêter l'exécution si non authentifié
    st.stop()

# Si on arrive ici, l'utilisateur est authentifié
logout_user()  # Afficher le bouton de déconnexion
# Afficher les informations d'utilisation
if st.session_state.get("user_id"):
    PlanManager.display_user_usage(st.session_state["user_id"])

from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Chemin relatif pour le logo
logo = os.path.join(BASE_DIR, "image", "logo.jpg")
if not os.path.exists(logo):
    logging.warning(f"Logo non trouvé: {logo}")
    # Utiliser un logo par défaut ou une icône
    logo = "🎙️"

# On importe vos fonctions depuis pages_my/
from my_page.dashboard_1 import afficher_page_1
from my_page.extraction_youtube_2 import afficher_page_2
from my_page.extract_video_3 import afficher_page_3
from my_page.transcription_4 import afficher_page_4
from my_page.text_to_audio import afficher_page_5

# Renommé de "Parametre" à "parametres" pour consistance
from my_page.parametre import afficher_page_7

# ---------------------
# Gestion mode clair/sombre + CSS
# ---------------------
def toggle_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode


mode_color = "#0E1117" if st.session_state.dark_mode else "white"
text_color = "white" if st.session_state.dark_mode else "black"

st.markdown(f"""
<style>
[data-testid="stSidebar"] {{
    background-color:  #00a2ff;
    padding-top: -100px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 94vh;
}}

.sidebar-title {{
    margin-top: 0px;
    font-size: 30px;
    font-weight: bold;
    color: #111;
    padding-left: 16px;
    margin-bottom: 50px;

}}

.bottom-menu {{
    margin-top: 300px;
    padding-bottom: 1px;
}}

.stApp {{
    background-color: {mode_color};
    color: {text_color};
}}
</style>
""", unsafe_allow_html=True)

# ---------------------
# Barre latérale + navigation
# ---------------------
with st.sidebar:
    # Vérification si le logo est une chaîne (emoji) ou un chemin de fichier
    if isinstance(logo, str) and logo.startswith("🎙️"):
        st.write(logo, unsafe_allow_html=True)
    else:
        st.image(logo, width=50)

    st.markdown("<div class='sidebar-title'>TranscriptFlow</div>", unsafe_allow_html=True)

    # Affichage du nom d'utilisateur
    if "username" in st.session_state:
        st.write(f"👤 Connecté: **{st.session_state['username']}**")

    menu_top = [
        "Dashboard",
        "Extraction d'une vidéo youtube",
        "Extraction d'un fichier vidéo",
        "Transcription",
        "Text to Audio"
    ]

    menu_bottom = ["API Clés", "Paramètres","Mon Compte"]

    # Boutons du haut
    for item in menu_top:
        if st.button(item, key=f"menu_{item}", use_container_width=True):
            st.session_state.selected_page = item

    # Espacement vers le bas (bien propre)
    st.markdown("<div style='margin-top: 200px;'></div>", unsafe_allow_html=True)

    # Boutons du bas
    for item in menu_bottom:
        if st.button(item, key=f"menu_{item}", use_container_width=True):
            st.session_state.selected_page = item
# ---------------------
# Routes / Pages principales
# ---------------------
page = st.session_state.selected_page

if page == "Dashboard":
    afficher_page_1()

elif page == "Extraction d'une vidéo youtube":
    afficher_page_2()

elif page == "Extraction d'un fichier vidéo":
    afficher_page_3()

elif page == "Transcription":
    afficher_page_4()

elif page == "Text to Audio":
    afficher_page_5()

elif page == "API Clés":
    st.title("API Clés")
    st.session_state.openai_api_key = st.text_input(
        "Clé API OpenAI",
        type="password",
        value=st.session_state.openai_api_key
    )

elif page == "Paramètres":
    afficher_page_7()

elif page == "Mon Compte":
    afficher_page_compte()