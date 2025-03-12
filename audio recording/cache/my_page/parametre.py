import streamlit as st
import logging
import os
from typing import Dict, List, Any

from core.session_manager import get_session_value, set_session_value
from core.api_key_manager import api_key_manager
from core.error_handling import handle_error, ErrorType

# Configuration des options de l'application
APP_OPTIONS = {
    "languages": ["français", "anglais"],
    "themes": ["sombre", "clair"],
    "retention_periods": [7, 30, 60, 90, 180, 365],
    "whisper_models": ["tiny", "base", "small", "medium", "large"],
    "gpt_models": ["gpt-3.5-turbo", "gpt-4"]
}


def toggle_mode():
    """Bascule entre le mode clair et sombre."""
    st.session_state.dark_mode = not st.session_state.dark_mode


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Sauvegarde les paramètres dans la session et dans un fichier de configuration.

    Args:
        settings: Dictionnaire des paramètres à sauvegarder

    Returns:
        True si succès, False sinon
    """
    try:
        # Sauvegarder dans session_state
        for key, value in settings.items():
            set_session_value(key, value)

        # Journalisation
        logging.info(f"Paramètres sauvegardés: {', '.join(settings.keys())}")

        return True

    except Exception as e:
        handle_error(e, ErrorType.PROCESSING_ERROR,
                     "Erreur lors de la sauvegarde des paramètres.")
        return False


def get_current_settings() -> Dict[str, Any]:
    """
    Récupère les paramètres actuels depuis la session.

    Returns:
        Dictionnaire des paramètres actuels
    """
    return {
        "default_language": get_session_value("default_language", "français"),
        "dark_mode": get_session_value("dark_mode", True),
        "enable_notifications": get_session_value("enable_notifications", False),
        "email_notifications": get_session_value("email_notifications", False),
        "push_notifications": get_session_value("push_notifications", False),
        "enable_history": get_session_value("enable_history", True),
        "history_retention": get_session_value("history_retention", 30),
        "enable_analytics": get_session_value("enable_analytics", True),
        "allow_user_creation": get_session_value("allow_user_creation", True),
        "default_whisper_model": get_session_value("default_whisper_model", "base"),
        "default_gpt_model": get_session_value("default_gpt_model", "gpt-3.5-turbo"),
        "google_drive_integration": get_session_value("google_drive_integration", False),
        "dropbox_integration": get_session_value("dropbox_integration", False),
    }


def afficher_page_7():
    st.title("⚙️ Paramètres avancés")

    # Détection mobile
    is_mobile = st.session_state.get("is_mobile", False)

    # Récupération des paramètres actuels
    settings = get_current_settings()

    # Onglets pour organiser les paramètres (simplifiés sur mobile)
    if is_mobile:
        tabs = st.tabs(["Général", "Trans.", "Notif.", "Stock.", "Intég.", "Avancé"])
    else:
        tabs = st.tabs([
            "Général", "Transcription", "Notifications",
            "Stockage", "Intégrations", "Avancé"
        ])

    # Bouton de sauvegarde flottant (sticky)
    st.markdown("""
    <style>
    .sticky-save {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

    # Container pour les paramètres modifiés
    modified_settings = {}

    # Tab 1: Général
    with tabs[0]:
        st.subheader("🌐 Paramètres généraux")

        if is_mobile:
            # Version mobile: empilée
            # Langue
            new_lang = st.selectbox(
                "Langue par défaut",
                options=APP_OPTIONS["languages"],
                index=APP_OPTIONS["languages"].index(settings["default_language"])
            )

            if new_lang != settings["default_language"]:
                modified_settings["default_language"] = new_lang

            # Thème
            st.write("Thème de l'interface")
            if st.button("Basculer mode clair/sombre", use_container_width=True):
                toggle_mode()
                modified_settings["dark_mode"] = not settings["dark_mode"]

            # Paramètres d'analyse
            st.divider()
            analytics = st.checkbox(
                "Activer les analytics",
                value=settings["enable_analytics"]
            )

            if analytics != settings["enable_analytics"]:
                modified_settings["enable_analytics"] = analytics
        else:
            # Version desktop: colonnes
            col1, col2 = st.columns(2)

            with col1:
                # Langue
                new_lang = st.selectbox(
                    "Langue par défaut",
                    options=APP_OPTIONS["languages"],
                    index=APP_OPTIONS["languages"].index(settings["default_language"]),
                    help="Langue utilisée dans l'interface"
                )

                if new_lang != settings["default_language"]:
                    modified_settings["default_language"] = new_lang

            with col2:
                # Thème
                st.write("Thème de l'interface")
                if st.button(
                        "Basculer mode clair/sombre",
                        help="Change l'apparence de l'interface"
                ):
                    toggle_mode()
                    modified_settings["dark_mode"] = not settings["dark_mode"]

            # Paramètres d'analyse
            st.divider()
            analytics = st.checkbox(
                "Activer les analytics",
                value=settings["enable_analytics"],
                help="Collecte anonyme de statistiques d'utilisation pour améliorer l'application"
            )

            if analytics != settings["enable_analytics"]:
                modified_settings["enable_analytics"] = analytics

    # Tab 2: Transcription
    with tabs[1]:
        st.subheader("🎤 Transcription")

        # Modèle Whisper par défaut
        default_whisper = st.selectbox(
            "Modèle Whisper",
            options=APP_OPTIONS["whisper_models"],
            index=APP_OPTIONS["whisper_models"].index(
                settings.get("default_whisper_model", "base")
            ),
            help="Modèle par défaut pour les transcriptions"
        )

        if default_whisper != settings.get("default_whisper_model", "base"):
            modified_settings["default_whisper_model"] = default_whisper

        # Modèle GPT par défaut
        default_gpt = st.selectbox(
            "Modèle GPT",
            options=APP_OPTIONS["gpt_models"],
            index=APP_OPTIONS["gpt_models"].index(
                settings.get("default_gpt_model", "gpt-3.5-turbo")
            ),
            help="Modèle par défaut pour les analyses"
        )

        if default_gpt != settings.get("default_gpt_model", "gpt-3.5-turbo"):
            modified_settings["default_gpt_model"] = default_gpt

        # Clé API OpenAI
        st.subheader("🔑 Clé API")
        api_key_manager.render_api_key_input("openai", "Clé API OpenAI")

    # ... [Continuer avec les autres onglets de la même façon]

    # Bouton de sauvegarde (affiché si des modifications ont été faites)
    if modified_settings:
        st.markdown('<div class="sticky-save">', unsafe_allow_html=True)
        save_button = st.button(
            f"💾 Sauvegarder ({len(modified_settings)})" if is_mobile else
            f"💾 Sauvegarder les {len(modified_settings)} modifications",
            type="primary",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if save_button:
            if save_settings(modified_settings):
                st.success("Paramètres sauvegardés avec succès !")
                # Forcer un rechargement pour appliquer les changements
                st.rerun()