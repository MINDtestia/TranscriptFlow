import streamlit as st
import logging

# On importe désormais la nouvelle fonction qui renvoie des bytes
from core.audio_extractor import download_youtube_audio

@st.cache_data(show_spinner=False)
def cached_download_youtube_audio(url):
    """On met en cache le résultat (les bytes) si l'URL est la même."""
    return download_youtube_audio(url)

def do_download_youtube(url: str):
    if not url.strip():
        st.warning("Veuillez fournir une URL YouTube.")
        return
    try:
        with st.spinner("Téléchargement en cours..."):
            audio_bytes = cached_download_youtube_audio(url)

        if isinstance(audio_bytes, str) and audio_bytes.startswith("ERROR"):
            # Si c'est un message d'erreur
            st.error(audio_bytes)
            logging.error(audio_bytes)
        else:
            # Sinon, on a bien reçu le contenu audio
            st.success("Audio extrait avec succès !")

            # On propose le téléchargement direct via un bouton
            st.download_button(
                label="Télécharger l'audio extrait",
                data=audio_bytes,
                file_name="extrait.wav",
                mime="audio/wav"
            )

    except Exception as e:
        logging.error(f"Erreur lors du téléchargement : {e}")
        st.error(f"Erreur : {e}")

def afficher_page_2():
    st.title("Extraction depuis YouTube")
    url_youtube = st.text_input("URL YouTube", placeholder="Collez l'URL YouTube ici")

    if st.button("Télécharger + Extraire (YouTube)"):
        do_download_youtube(url_youtube)
