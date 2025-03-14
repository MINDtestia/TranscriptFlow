import os
import tempfile
import streamlit as st
from typing import Union, Optional
import logging

from core.audio_extractor import extract_audio_from_mp4
from core.error_handling import handle_error, ErrorType
from core.session_manager import get_session_value, set_session_value


@st.cache_data(show_spinner=False, ttl=3600)
def cached_extract_audio_from_mp4(file_path: str) -> str:
    """
    Extrait et met en cache l'audio d'un fichier MP4.

    Args:
        file_path: Chemin du fichier vidéo

    Returns:
        Chemin du fichier audio extrait ou message d'erreur
    """
    return extract_audio_from_mp4(file_path)


def validate_video_file(file) -> bool:
    """
    Valide un fichier vidéo téléchargé.

    Args:
        file: Objet fichier Streamlit

    Returns:
        True si le fichier est valide, False sinon
    """
    if file is None:
        return False

    # Vérifier l'extension
    allowed_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv']
    file_ext = os.path.splitext(file.name)[1].lower()
    # Vérifier la taille (max 500 MB) - AUGMENTER À 4000 MB
    max_size_mb = 4000  # Modifié de 500 à 4000
    file_size_mb = file.size / (1024 * 1024)

    if file_size_mb > max_size_mb:
        st.warning(f"Le fichier est trop volumineux ({file_size_mb:.1f} MB). Maximum: {max_size_mb} MB")
        return False

    if file_ext not in allowed_extensions:
        st.warning(f"Format de fichier non supporté. Formats acceptés: {', '.join(allowed_extensions)}")
        return False

    # Vérifier la taille (max 500 MB)
    max_size_mb = 500
    file_size_mb = file.size / (1024 * 1024)

    if file_size_mb > max_size_mb:
        st.warning(f"Le fichier est trop volumineux ({file_size_mb:.1f} MB). Maximum: {max_size_mb} MB")
        return False

    return True


def extract_audio_with_progress(file) -> Optional[bytes]:
    """
    Extrait l'audio d'un fichier vidéo avec barre de progression.

    Args:
        file: Objet fichier Streamlit

    Returns:
        Contenu audio en bytes ou None en cas d'erreur
    """
    if not validate_video_file(file):
        return None

    try:
        progress_bar = st.progress(0, "Préparation de l'extraction...")

        # Étape 1: Écrire le fichier temporaire (25%)
        progress_bar.progress(0.05, "Préparation du fichier vidéo...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmpfile:
            temp_file_path = tmpfile.name
            tmpfile.write(file.getbuffer())

        progress_bar.progress(0.25, "Fichier prêt, extraction audio en cours...")

        # Étape 2: Extraire l'audio (75%)
        audio_path = cached_extract_audio_from_mp4(temp_file_path)

        if isinstance(audio_path, str) and audio_path.startswith("ERROR"):
            handle_error(Exception(audio_path), ErrorType.PROCESSING_ERROR,
                         "L'extraction audio a échoué. Vérifiez le format du fichier.")
            return None

        progress_bar.progress(0.75, "Audio extrait, finalisation...")

        # Étape 3: Lire le contenu audio (100%)
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        progress_bar.progress(1.0, "Extraction terminée!")

        # Nettoyage des fichiers temporaires
        try:
            os.remove(temp_file_path)
            os.remove(audio_path)
        except Exception as e:
            logging.warning(f"Erreur lors du nettoyage des fichiers temporaires: {e}")

        return audio_bytes

    except Exception as e:
        handle_error(e, ErrorType.PROCESSING_ERROR,
                     "Une erreur est survenue pendant l'extraction audio.")

        # Nettoyage de sécurité
        try:
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if 'audio_path' in locals() and os.path.exists(audio_path):
                os.remove(audio_path)
        except:
            pass

        return None

def extract_audio_with_progress_from_path(file_path: str) -> Optional[bytes]:
    """
    Extrait l'audio d'un fichier vidéo avec barre de progression à partir d'un chemin de fichier.

    Args:
        file_path: Chemin du fichier sur le serveur

    Returns:
        Contenu audio en bytes ou None en cas d'erreur
    """
    if not os.path.exists(file_path):
        st.error(f"Fichier non trouvé: {file_path}")
        return None

    try:
        progress_bar = st.progress(0, "Préparation de l'extraction...")
        progress_bar.progress(0.25, "Extraction audio en cours...")

        # Extraire l'audio
        audio_path = cached_extract_audio_from_mp4(file_path)

        if isinstance(audio_path, str) and audio_path.startswith("ERROR"):
            handle_error(Exception(audio_path), ErrorType.PROCESSING_ERROR,
                        "L'extraction audio a échoué. Vérifiez le format du fichier.")
            return None

        progress_bar.progress(0.75, "Audio extrait, finalisation...")

        # Lire le contenu audio
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        progress_bar.progress(1.0, "Extraction terminée!")

        # Nettoyage du fichier audio temporaire
        try:
            os.remove(audio_path)
        except Exception as e:
            logging.warning(f"Erreur lors du nettoyage des fichiers temporaires: {e}")

        return audio_bytes

    except Exception as e:
        handle_error(e, ErrorType.PROCESSING_ERROR,
                    "Une erreur est survenue pendant l'extraction audio.")
        return None

def afficher_page_3():
    st.title("Extraction d'un fichier vidéo")

    # Détection mobile
    is_mobile = st.session_state.get("is_mobile", False)

    # Style personnalisé pour la zone de dépôt
    st.markdown(
        """
        <style>
        /* Sélection du dropzone via data-testid */
        div[data-testid="stFileUploadDropzone"] label {
            /* On masque le texte d'origine */
            visibility: hidden;
        }
        div[data-testid="stFileUploadDropzone"] label:after {
            /* On insère notre propre texte */
            content: "Glissez et déposez votre fichier vidéo ici ou cliquez pour parcourir";
            visibility: visible;
            display: block;
            margin-top: 1rem;
            font-size: 1rem;
            color: #999;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Interface utilisateur améliorée - adaptée pour mobile
    uploaded_file = st.file_uploader(
        "Choisissez un fichier vidéo à extraire" if not is_mobile else "Charger un fichier vidéo",
        type=["mp4", 'mov', 'avi', 'mkv', 'wmv'],
        key="video_uploader",
        help="Formats supportés: MP4, MOV, AVI, MKV, WMV. Taille maximale: 500 MB."
    )
    # Après le file_uploader actuel, ajoutez ceci:
    st.divider()
    st.markdown("### Alternative pour fichiers volumineux (+200MB)")

    server_file_path = st.text_input(
        "Chemin du fichier sur le serveur:",
        placeholder="/chemin/vers/votre/fichier.mp4",
        help="Si le fichier est déjà présent sur le serveur, entrez son chemin absolu ici."
    )

    # Vérification et prévisualisation du fichier spécifié
    if server_file_path:
        if os.path.exists(server_file_path):
            file_size_mb = os.path.getsize(server_file_path) / (1024 * 1024)
            st.success(f"✅ Fichier trouvé: {os.path.basename(server_file_path)} ({file_size_mb:.2f} MB)")

            # Prévisualisation avec ffmpeg si c'est une vidéo
            if server_file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                # Créer une miniature si possible
                try:
                    import subprocess
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                        thumbnail_path = tmp.name
                    subprocess.run([
                        'ffmpeg', '-y', '-i', server_file_path,
                        '-ss', '00:00:01.000', '-vframes', '1',
                        thumbnail_path
                    ], check=True, capture_output=True)

                    if os.path.exists(thumbnail_path):
                        st.image(thumbnail_path, caption="Aperçu du fichier vidéo")
                        os.unlink(thumbnail_path)
                except:
                    st.info("Aperçu non disponible")

            # Bouton d'extraction
            if st.button("Extraire l'audio depuis ce fichier", key="server_extract_btn", use_container_width=True):
                audio_bytes = extract_audio_with_progress_from_path(server_file_path)

                if audio_bytes:
                    st.success("Extraction terminée avec succès ✅")
                    st.audio(audio_bytes, format="audio/wav")

                    # Options après extraction
                    download_col, transcribe_col = st.columns([1, 1]) if not is_mobile else ([1])

                    with download_col:
                        st.download_button(
                            label="Télécharger l'audio extrait",
                            data=audio_bytes,
                            file_name=f"{os.path.splitext(os.path.basename(server_file_path))[0]}.wav",
                            mime="audio/wav",
                            use_container_width=True
                        )

                    if is_mobile:
                        if st.button("Passer à la transcription", use_container_width=True):
                            set_session_value("audio_bytes_for_transcription", audio_bytes)
                            set_session_value("selected_page", "Transcription")
                            st.rerun()
                    else:
                        with transcribe_col:
                            if st.button("Passer à la transcription", key="to_transcription_path_btn"):
                                set_session_value("audio_bytes_for_transcription", audio_bytes)
                                set_session_value("selected_page", "Transcription")
                                st.rerun()
        else:
            st.error(f"❌ Fichier non trouvé: {server_file_path}")
            st.info("Assurez-vous que le chemin est correct et que le fichier est accessible par l'application.")
    # Mettre à jour session_state
    set_session_value("uploaded_mp4", uploaded_file)

    # Afficher des statistiques sur le fichier
    if uploaded_file:
        if is_mobile:
            # Version mobile: empilée
            st.info(f"Fichier: {uploaded_file.name}")
            size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"Taille: {size_mb:.2f} MB")
        else:
            # Version desktop: colonnes
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"Fichier: {uploaded_file.name}")
            with col2:
                size_mb = uploaded_file.size / (1024 * 1024)
                st.info(f"Taille: {size_mb:.2f} MB")

    # Bouton d'extraction
    extract_button = st.button(
        "Extraire l'audio du fichier vidéo",
        disabled=uploaded_file is None,
        use_container_width=True
    )

    if extract_button:
        audio_bytes = extract_audio_with_progress(get_session_value("uploaded_mp4"))

        if audio_bytes:
            st.success("Extraction terminée avec succès ✅")

            # Écouter l'audio
            st.audio(audio_bytes, format="audio/wav")

            # Télécharger l'audio
            download_col, transcribe_col = st.columns([1, 1]) if not is_mobile else ([1])

            with download_col:
                st.download_button(
                    label="Télécharger l'audio extrait",
                    data=audio_bytes,
                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}.wav",
                    mime="audio/wav",
                    use_container_width=True
                )

                # Bouton d'explication pour guider l'utilisateur
                if st.button("💡 Comment transcrire cette audio?", use_container_width=True):
                    # Créer un conteneur pour le guide
                    guide_container = st.container()

                    with guide_container:
                        st.markdown("## 🎯 Guide de transcription en 3 étapes")

                        # Étape 1
                        st.markdown("### ÉTAPE 1: Extraire l'audio")
                        st.markdown("• Récupérer votre fichier vidéo et cliquez sur \"Télécharger\"")
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