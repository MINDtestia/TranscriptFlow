# lancer // streamlit run '/Users/alexis/Desktop/Python/audio recording/cache/app.py'
import os
import logging
import streamlit as st

# Définir le chemin de base du projet
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Définition de la fonction is_mobile() AVANT son utilisation
def is_mobile():
    """Détecte si l'utilisateur est sur un appareil mobile"""
    if "is_mobile" not in st.session_state:
        # Initialisation par défaut
        st.session_state.is_mobile = False

        # On utilise la largeur de l'écran comme heuristique
        # Utilisation de st.query_params au lieu de st.experimental_get_query_params
        if st.query_params.get("view") == "mobile":
            st.session_state.is_mobile = True

    return st.session_state.is_mobile


# PREMIÈRE commande Streamlit: configuration de la page
st.set_page_config(
    page_title="TranscriptFlow",
    page_icon="🎙️",
    layout="wide" if not is_mobile() else "centered",
    initial_sidebar_state="expanded" if not is_mobile() else "collapsed"
)

# Après st.set_page_config(), on peut procéder aux autres imports et opérations
from core.session_manager import initialize_session_state
from core.database import Base, engine
from core.auth_manager import login_user, register_user, logout_user
from core.plan_manager import PlanManager
from my_page.setting.account_settings import afficher_page_compte

# Script de détection mobile côté client - après set_page_config
device_detector = st.empty()
device_detector.markdown("""
<script>
if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
   (window.innerWidth <= 767)) {
    // Ajouter le paramètre view=mobile à l'URL
    const url = new URL(window.location);
    url.searchParams.set('view', 'mobile');
    window.history.replaceState({}, '', url);
    // Forcer le rechargement si c'est la première détection
    if (!window.location.href.includes('view=mobile')) {
        window.location.href = url.toString();
    }
}
</script>
""", unsafe_allow_html=True)

# CSS pour l'adaptation mobile
mobile_css = """
<style>
@media (max-width: 768px) {
    /* Réduire les marges et padding */
    .block-container {
        padding: 1rem 0.5rem !important;
    }

    /* Textes plus lisibles sur petit écran */
    h1 {
        font-size: 1.5rem !important;
    }

    h2, h3 {
        font-size: 1.2rem !important;
    }

    /* Boutons plus grands pour le tactile */
    button, .stButton>button {
        min-height: 2.5rem !important;
        width: 100% !important;
    }

    /* Formulaires plus accessibles */
    input, textarea, select {
        font-size: 16px !important; /* Empêche le zoom iOS sur focus */
    }

    /* Colonnes sur toute la largeur */
    .row-widget.stHorizontal > div {
        flex: 1 1 100% !important;
        width: 100% !important;
    }

    /* Tableaux plus lisibles */
    .dataframe {
        font-size: 0.7rem !important;
    }

    /* Améliorer la sidebar */
    [data-testid="stSidebar"] {
        width: 100% !important;
    }
}
</style>
"""
st.markdown(mobile_css, unsafe_allow_html=True)

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


# Définir fonction toggle_mode() pour le thème clair/sombre
def toggle_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode


# Assurer que is_mobile est défini dans session_state
st.session_state.is_mobile = is_mobile()

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

# On importe les fonctions des pages
from my_page.dashboard_1 import afficher_page_1
from my_page.extraction_youtube_2 import afficher_page_2
from my_page.extract_video_3 import afficher_page_3
from my_page.transcription_4 import afficher_page_4
from my_page.text_to_audio import afficher_page_5
from my_page.parametre import afficher_page_7

# Configuration du mode clair/sombre
mode_color = "#0E1117" if st.session_state.dark_mode else "white"
text_color = "white" if st.session_state.dark_mode else "black"

st.markdown(f"""
<style>
[data-testid="stSidebar"] {{
    background-color: #00a2ff;
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

    menu_bottom = ["API Clés", "Paramètres", "Mon Compte"]

    # Navigation adaptative selon le type d'appareil
    if st.session_state.is_mobile:
        # Version mobile: menu déroulant
        st.markdown("### Menu")
        selected_page = st.selectbox(
            "Navigation",
            options=menu_top + menu_bottom,
            index=menu_top.index(st.session_state.selected_page) if st.session_state.selected_page in menu_top
            else (len(menu_top) + menu_bottom.index(
                st.session_state.selected_page) if st.session_state.selected_page in menu_bottom else 0)
        )

        if selected_page != st.session_state.selected_page:
            st.session_state.selected_page = selected_page
            st.rerun()
    else:
        # Version desktop: boutons
        for item in menu_top:
            if st.button(item, key=f"menu_{item}", use_container_width=True):
                st.session_state.selected_page = item

        # Espacement vers le bas
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