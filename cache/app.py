# lancer // streamlit run '/Users/alexis/Desktop/Python/audio recording/cache/app.py'

import os
import logging
import streamlit as st
from core.authentication import authenticate, logout

st.set_page_config(
    page_title="TranscriptFlow",
    page_icon= "🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Initialiser la session si elle n'existe pas
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False


# Vérifier l'authentification AVANT de charger l'application
if not st.session_state["authenticated"]:
    if authenticate():
        st.session_state["authenticated"] = True
        st.rerun()
    else:
        st.stop()

# Si authentifié, affiche le reste de ton application
st.write("Vous êtes connecté !")
logout()  # Afficher le bouton de déconnexion
from dotenv import load_dotenv

#Import image

logo = "/Users/alexis/Desktop/Python/audio recording/cache/image/logo.jpg"

# Chargement des variables d'environnement
load_dotenv()



OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

logging.basicConfig(level=logging.INFO)


# On importe vos fonctions depuis pages_my/
from my_page.dashboard_1 import afficher_page_1
from my_page.extraction_youtube_2 import afficher_page_2
from my_page.extract_video_3 import afficher_page_3
from my_page.transcription_4 import afficher_page_4
from my_page.text_to_audio import afficher_page_5
from my_page.Parametre import  afficher_page_7
# ---------------------
# Config de la page
# ---------------------

# Augmentation de la taille maximale d'upload (ici 5000 MB = 5 Go)
#st.set_option('server.maxUploadSize', 5000)

# ---------------------
# Gestion mode clair/sombre + CSS
# ---------------------
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

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
# Initialisation session_state
# ---------------------
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""

if "segments" not in st.session_state:
    st.session_state.segments = []

if "downloaded_audio_path" not in st.session_state:
    st.session_state.downloaded_audio_path = ""

if "mp4_audio_path" not in st.session_state:
    st.session_state.mp4_audio_path = ""

if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = OPENAI_API_KEY

if "summary_result" not in st.session_state:
    st.session_state.summary_result = ""

if "keywords_result" not in st.session_state:
    st.session_state.keywords_result = ""

if "answer_result" not in st.session_state:
    st.session_state.answer_result = ""

if "chapters_result" not in st.session_state:
    st.session_state.chapters_result = ""


# ---------------------
# Barre latérale + navigation
# ---------------------
with st.sidebar:
    st.image(logo, width=50)
    st.markdown("<div class='sidebar-title'>TranscriptFlow</div>", unsafe_allow_html=True)

    menu_top = [
        "Dashboard",
        "Extraction d'une vidéo youtube",
        "Extraction d'un fichier vidéo",
        "Transcription",
        "Text to Audio"
    ]

    menu_bottom = ["API Clés", "Paramètres"]

    if "selected_page" not in st.session_state:
        st.session_state.selected_page = "Dashboard"

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
    afficher_page_7 ()


