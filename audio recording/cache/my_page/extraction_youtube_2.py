import streamlit as st
import logging
from typing import Union

# On importe désormais la nouvelle fonction qui renvoie des bytes
from core.audio_extractor import download_youtube_audio
from core.error_handling import handle_error, ErrorType, safe_execute
from core.session_manager import get_session_value, set_session_value


def validate_youtube_url(url: str) -> bool:
    """
    Valide une URL YouTube de manière basique.

    Args:
        url: L'URL à valider

    Returns:
        True si l'URL semble valide, False sinon
    """
    url = url.strip()
    if not url:
        return False

    valid_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
    return any(domain in url for domain in valid_domains)


@st.cache_data(show_spinner=False)
def cached_download_youtube_audio(url: str) -> Union[bytes, str]:
    """
    Télécharge et met en cache l'audio d'une vidéo YouTube.

    Args:
        url: L'URL YouTube à télécharger

    Returns:
        Le contenu audio en bytes ou un message d'erreur
    """
    return download_youtube_audio(url)


def do_download_youtube(url: str) -> None:
    """
    Fonction principale pour télécharger l'audio depuis YouTube.

    Args:
        url: L'URL YouTube à télécharger
    """
    if not validate_youtube_url(url):
        st.warning("Veuillez fournir une URL YouTube valide.")
        return

    try:
        with st.spinner("Téléchargement et extraction audio en cours..."):
            audio_bytes = cached_download_youtube_audio(url)

        if isinstance(audio_bytes, str) and audio_bytes.startswith("ERROR"):
            # Si c'est un message d'erreur
            st.error(audio_bytes)
            logging.error(audio_bytes)
        else:
            # Sinon, on a bien reçu le contenu audio
            st.success("Audio extrait avec succès !")
            from core.session_manager import log_user_activity
            log_user_activity(
                st.session_state["user_id"],
                "youtube_extraction",
                f"URL: {url}"
            )
            # Informations sur le fichier
            size_mb = len(audio_bytes) / (1024 * 1024)
            st.info(f"Taille du fichier audio: {size_mb:.2f} Mo")

            # On propose le téléchargement direct via un bouton
            st.download_button(
                label="Télécharger l'audio extrait",
                data=audio_bytes,
                file_name="extrait.wav",
                mime="audio/wav"
            )

            # Option pour passer à la transcription
            if st.button("Passer à la transcription"):
                set_session_value("downloaded_audio_data", audio_bytes)
                set_session_value("selected_page", "Transcription")
                st.rerun()

    except Exception as e:
        handle_error(e, ErrorType.PROCESSING_ERROR,
                     "Erreur lors du téléchargement. Vérifiez l'URL et votre connexion internet.")


def afficher_page_2():
    st.title("Extraction depuis YouTube")

    # Interface utilisateur améliorée
    col1, col2 = st.columns([3, 1])

    with col1:
        url_youtube = st.text_input(
            "URL YouTube",
            placeholder="Collez l'URL YouTube ici (ex: https://www.youtube.com/watch?v=...)"
        )

    with col2:
        st.write("")  # Espace pour aligner avec le champ texte
        st.write("")  # Espace pour aligner avec le champ texte
        download_button = st.button("Télécharger", use_container_width=True)

    # Infobulles explicatives
    st.markdown("""
    <small>
    ℹ️ Formats supportés: Vidéos YouTube standard, shorts, et playlists (1ère vidéo seulement).
    </small>
    """, unsafe_allow_html=True)

    # Téléchargement
    if download_button:
        do_download_youtube(url_youtube)

    # Historique des téléchargements récents (exemple)
    with st.expander("Historique récent"):
        st.info("Fonctionnalité en développement - L'historique des téléchargements sera disponible prochainement.")