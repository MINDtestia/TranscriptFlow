import os
import tempfile
import streamlit as st

from core.audio_extractor import extract_audio_from_mp4


@st.cache_data(show_spinner=False)
def cached_extract_audio_from_mp4(file_path: str) -> str:
    return extract_audio_from_mp4(file_path)

# ---------------------
# Fonctions de callback
# ---------------------

def do_extract_mp4(file):
    if not file:
        st.warning("Veuillez charger un fichier vidéo.")
        return

    with st.spinner("Extraction de l'audio en cours..."):
        # Création d'un fichier temporaire pour stocker la vidéo uploadée
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmpfile:
            temp_file_path = tmpfile.name
            tmpfile.write(file.getbuffer())

        try:
            audio_path = extract_audio_from_mp4(temp_file_path)

            with open(audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()

            st.success("Extraction terminée avec succès ✅")
            st.download_button(
                label="Télécharger l'audio extrait",
                data=audio_bytes,
                file_name="extrait.wav",
                mime="audio/wav"
            )
        finally:
            # Nettoyage des fichiers temporaires
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)



def afficher_page_3():
    st.markdown(
        """
        <style>
        /* Sélection du dropzone via data-testid (peut changer selon versions Streamlit) */
        div[data-testid="stFileUploadDropzone"] label {
            /* On masque le texte d'origine */
            visibility: hidden;
        }
        div[data-testid="stFileUploadDropzone"] label:after {
            /* On insère notre propre texte */
            content: "Glissez et déposez votre fichier ici";
            visibility: visible;
            display: block;
            margin-top: 1rem;
            font-size: 1rem;
            color: #999; /* Couleur personnalisable */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.title("Extraction d'un fichier vidéo")

    if 'uploaded_mp4' not in st.session_state:
        st.session_state.uploaded_mp4 = None

    uploaded_mp4 = st.file_uploader(
        "Choisissez un fichier vidéo à extraire",
        type=["mp4", 'mov', 'avi'],
        key="video_uploader"
    )

    st.session_state.uploaded_mp4 = uploaded_mp4

    st.text_input(
        "Chemin de l'audio extrait (MP4)",
        value=st.session_state.get("mp4_audio_path", ""),
        disabled=True
    )

    if st.button("Extraire l'audio (MP4)"):
        do_extract_mp4(st.session_state.uploaded_mp4)