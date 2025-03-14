import streamlit as st
import logging
from typing import Union

# On importe désormais la nouvelle fonction qui renvoie des bytes
from core.audio_extractor import download_youtube_audio
from core.error_handling import handle_error, ErrorType, safe_execute
from core.session_manager import get_session_value, set_session_value
from my_page.transcription_4 import afficher_page_4


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


    except Exception as e:
        handle_error(e, ErrorType.PROCESSING_ERROR,
                     "Erreur lors du téléchargement. Vérifiez l'URL et votre connexion internet.")


def afficher_page_2():
    st.title("Extraction depuis YouTube")

    # Détection mobile
    is_mobile = st.session_state.get("is_mobile", False)

    if is_mobile:
        # Version mobile: empilée verticalement
        url_youtube = st.text_input(
            "URL YouTube",
            placeholder="Collez l'URL YouTube ici"
        )

        download_button = st.button("Télécharger", use_container_width=True)

        # Infobulles explicatives
        st.markdown("""
        <small>
        ℹ️ Formats supportés: Vidéos YouTube standard, shorts et playlists.
        </small>
        """, unsafe_allow_html=True)
    else:
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



    # Bouton d'explication pour guider l'utilisateur
    if st.button("💡 Comment transcrire cette audio?", use_container_width=True):
        # Créer un conteneur pour le guide
        guide_container = st.container()

        with guide_container:
            st.markdown("## 🎯 Guide de transcription en 3 étapes")

            # Étape 1
            st.markdown("### ÉTAPE 1: Extraire l'audio")
            st.markdown("• Collez l'URL YouTube et cliquez sur \"Télécharger\"")
            st.markdown("• Attendez que l'extraction soit terminée")

            # Étape 2
            st.markdown("### ÉTAPE 2: Télécharger l'audio (optionnel)")
            st.markdown("• Utilisez le bouton \"Télécharger l'audio extrait\" pour sauvegarder le fichier")

            # Étape 3
            st.markdown("### ÉTAPE 3: Accéder à la transcription")
            st.markdown("• Cliquez sur \"Transcription\" dans le menu à gauche")
            st.markdown("• Chargez le fichier audio téléchargé dans la section \"Source audio\"")
            st.markdown("• Sélectionnez les options souhaitées et lancez la transcription")

            # Astuce
            st.info(
                "⚠️ **Astuce**: Si vous avez extrait l'audio mais qu'il n'apparaît pas automatiquement dans la page Transcription, téléchargez-le puis importez-le manuellement.")

        # Ajouter un séparateur pour plus de clarté
        st.divider()