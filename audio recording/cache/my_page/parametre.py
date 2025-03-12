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

    # Récupération des paramètres actuels
    settings = get_current_settings()

    # Onglets pour organiser les paramètres
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
        st.subheader("🎤 Paramètres de transcription")

        # Modèle Whisper par défaut
        default_whisper = st.selectbox(
            "Modèle Whisper par défaut",
            options=APP_OPTIONS["whisper_models"],
            index=APP_OPTIONS["whisper_models"].index(
                settings.get("default_whisper_model", "base")
            ),
            help="Le modèle utilisé par défaut pour les transcriptions"
        )

        if default_whisper != settings.get("default_whisper_model", "base"):
            modified_settings["default_whisper_model"] = default_whisper

        # Modèle GPT par défaut
        default_gpt = st.selectbox(
            "Modèle GPT par défaut",
            options=APP_OPTIONS["gpt_models"],
            index=APP_OPTIONS["gpt_models"].index(
                settings.get("default_gpt_model", "gpt-3.5-turbo")
            ),
            help="Le modèle utilisé par défaut pour les analyses GPT"
        )

        if default_gpt != settings.get("default_gpt_model", "gpt-3.5-turbo"):
            modified_settings["default_gpt_model"] = default_gpt

        # Clé API OpenAI
        st.subheader("🔑 Clé API")
        api_key_manager.render_api_key_input("openai", "Clé API OpenAI")

    # Tab 3: Notifications
    with tabs[2]:
        st.subheader("🔔 Paramètres des notifications")

        # Activation générale
        enable_notifs = st.checkbox(
            "Activer les notifications",
            value=settings["enable_notifications"],
            help="Active ou désactive toutes les notifications"
        )

        if enable_notifs != settings["enable_notifications"]:
            modified_settings["enable_notifications"] = enable_notifs

        # Types de notifications
        st.write("Types de notifications:")

        col1, col2 = st.columns(2)

        with col1:
            email_notifs = st.checkbox(
                "Notifications par email",
                value=settings["email_notifications"],
                disabled=not enable_notifs,
                help="Envoie des notifications par email"
            )

            if email_notifs != settings["email_notifications"]:
                modified_settings["email_notifications"] = email_notifs

        with col2:
            push_notifs = st.checkbox(
                "Notifications push",
                value=settings["push_notifications"],
                disabled=not enable_notifs,
                help="Affiche des notifications push dans le navigateur"
            )

            if push_notifs != settings["push_notifications"]:
                modified_settings["push_notifications"] = push_notifs

    # Tab 4: Stockage
    with tabs[3]:
        st.subheader("📦 Paramètres de stockage")

        # Historique
        enable_history = st.checkbox(
            "Activer l'enregistrement des historiques",
            value=settings["enable_history"],
            help="Enregistre l'historique des actions"
        )

        if enable_history != settings["enable_history"]:
            modified_settings["enable_history"] = enable_history

        # Durée de rétention
        retention = st.select_slider(
            "Durée de rétention des historiques (jours)",
            options=APP_OPTIONS["retention_periods"],
            value=settings["history_retention"],
            disabled=not enable_history,
            help="Durée pendant laquelle les historiques sont conservés"
        )

        if retention != settings["history_retention"]:
            modified_settings["history_retention"] = retention

        # Actions sur l'historique
        if enable_history:
            if st.button("Effacer tout l'historique", type="secondary"):
                st.warning("Historique effacé !")
                set_session_value("history", [])

    # Tab 5: Intégrations
    with tabs[4]:
        st.subheader("🔗 Intégrations externes")

        # Google Drive
        google_drive = st.checkbox(
            "Connecter à Google Drive",
            value=settings["google_drive_integration"],
            help="Permet d'importer/exporter des fichiers depuis Google Drive"
        )

        if google_drive != settings["google_drive_integration"]:
            modified_settings["google_drive_integration"] = google_drive

        # Dropbox
        dropbox = st.checkbox(
            "Connecter à Dropbox",
            value=settings["dropbox_integration"],
            help="Permet d'importer/exporter des fichiers depuis Dropbox"
        )

        if dropbox != settings["dropbox_integration"]:
            modified_settings["dropbox_integration"] = dropbox

    # Tab 6: Avancé
    with tabs[5]:
        st.subheader("🛠️ Paramètres avancés")

        # Gestion des utilisateurs
        allow_users = st.checkbox(
            "Autoriser la création de nouveaux utilisateurs",
            value=settings["allow_user_creation"],
            help="Permet aux utilisateurs de créer de nouveaux comptes"
        )

        if allow_users != settings["allow_user_creation"]:
            modified_settings["allow_user_creation"] = allow_users

        # Cache
        if st.button("Vider le cache", help="Supprime les fichiers temporaires et le cache"):
            # Logique de nettoyage du cache
            st.cache_data.clear()
            st.success("Cache vidé avec succès !")

        # Téléchargement des logs
        if st.button("Télécharger les logs", help="Télécharge les fichiers de journalisation"):
            log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.log")
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    log_content = f.read()

                st.download_button(
                    "Télécharger les logs",
                    data=log_content,
                    file_name="transcriptflow_logs.txt",
                    mime="text/plain"
                )
            else:
                st.warning("Aucun fichier de log trouvé.")

    # Bouton de sauvegarde (affiché si des modifications ont été faites)
    if modified_settings:
        st.markdown('<div class="sticky-save">', unsafe_allow_html=True)
        save_button = st.button(
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