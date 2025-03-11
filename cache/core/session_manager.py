# core/session_manager.py
import streamlit as st
from typing import Any, Dict, Optional
import os


def initialize_session_state():
    """
    Initialise toutes les variables de session en un seul endroit.
    À appeler au début de l'application.
    """
    # Variables d'authentification
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Variables d'UI
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

    if "selected_page" not in st.session_state:
        st.session_state.selected_page = "Dashboard"

    # Variables de transcription
    if "transcribed_text" not in st.session_state:
        st.session_state.transcribed_text = ""

    if "segments" not in st.session_state:
        st.session_state.segments = []

    # Variables de chemins de fichiers
    if "downloaded_audio_path" not in st.session_state:
        st.session_state.downloaded_audio_path = ""

    if "mp4_audio_path" not in st.session_state:
        st.session_state.mp4_audio_path = ""

    # Variables API
    if "openai_api_key" not in st.session_state:
        # Récupérer depuis les variables d'environnement si disponible
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")

    # Variables de résultats
    if "summary_result" not in st.session_state:
        st.session_state.summary_result = ""

    if "keywords_result" not in st.session_state:
        st.session_state.keywords_result = ""

    if "answer_result" not in st.session_state:
        st.session_state.answer_result = ""

    if "chapters_result" not in st.session_state:
        st.session_state.chapters_result = ""

    if "tts_audio_data" not in st.session_state:
        st.session_state.tts_audio_data = None

    # Variables pour l'upload de fichier
    if "uploaded_mp4" not in st.session_state:
        st.session_state.uploaded_mp4 = None


def get_session_value(key: str, default: Any = None) -> Any:
    """
    Récupère une valeur de session de manière sécurisée.

    Args:
        key: Clé de la variable de session
        default: Valeur par défaut si la clé n'existe pas

    Returns:
        Valeur stockée ou valeur par défaut
    """
    return st.session_state.get(key, default)


def set_session_value(key: str, value: Any) -> None:
    """
    Définit une valeur de session.

    Args:
        key: Clé de la variable de session
        value: Valeur à stocker
    """
    st.session_state[key] = value


def clear_session_values(keys: Optional[list] = None) -> None:
    """
    Efface des valeurs de session.

    Args:
        keys: Liste des clés à effacer, ou None pour utiliser les valeurs par défaut
    """
    if keys is None:
        # Valeurs à réinitialiser par défaut
        keys = ["transcribed_text", "segments", "summary_result",
                "keywords_result", "answer_result", "chapters_result"]

    for key in keys:
        if key in st.session_state:
            if isinstance(st.session_state[key], str):
                st.session_state[key] = ""
            elif isinstance(st.session_state[key], list):
                st.session_state[key] = []
            elif isinstance(st.session_state[key], dict):
                st.session_state[key] = {}
            else:
                st.session_state[key] = None