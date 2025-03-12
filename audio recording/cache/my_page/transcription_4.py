import streamlit as st
import logging
import tempfile
import os
from typing import Optional, Dict, Any, List, Tuple
import time

from core.transcription import transcribe_or_translate_locally, request_transcription
from core.gpt_processor import summarize_text, extract_keywords, ask_question_about_text
from core.utils import create_chapters_from_segments, export_text_file
from core.error_handling import handle_error, ErrorType, safe_execute
from core.session_manager import get_session_value, set_session_value
from core.api_key_manager import api_key_manager
from core.storage_manager import storage_manager
from core.database import Transcription, get_db
from core.task_queue import celery_app
from celery.result import AsyncResult

# Types personnalisés pour la clarté
SegmentType = Dict[str, Any]
TranscriptionResult = Dict[str, Any]


# Fonctions de transcription avec cache
@st.cache_data(show_spinner=False, ttl=3600)
def cached_transcribe(
        file_path: str,
        whisper_model: str,
        translate: bool
) -> TranscriptionResult:
    """
    Cache le résultat de la transcription pour éviter de refaire le travail.

    Args:
        file_path: Chemin du fichier audio
        whisper_model: Modèle Whisper à utiliser
        translate: Si True, traduit plutôt que transcrire

    Returns:
        Résultat de la transcription
    """
    return transcribe_or_translate_locally(file_path, whisper_model, translate)


def check_transcription_status(task_id):
    """Vérifie le statut d'une tâche de transcription"""
    task = AsyncResult(task_id, app=celery_app)
    return task.status, task.result


def process_transcription_sync(
        audio_data: bytes,
        whisper_model: str,
        translate: bool = False
) -> Tuple[bool, str]:
    """
    Traite la transcription d'un fichier audio avec une barre de progression.
    Version synchrone (pour petits fichiers ou compatibilité)

    Args:
        audio_data: Contenu du fichier audio en bytes
        whisper_model: Modèle Whisper à utiliser
        translate: Si True, traduit plutôt que transcrire

    Returns:
        (succès, message)
    """
    if not audio_data:
        return False, "Aucun fichier audio fourni."

    try:
        # Créer la barre de progression
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Préparation du fichier...")

        # Étape 1: Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(audio_data)

        progress_bar.progress(0.1)
        status_text.text("Fichier prêt. Chargement du modèle Whisper...")

        # Étape 2: Lancer la transcription
        def progress_callback(progress: float, message: str):
            progress_bar.progress(0.1 + progress * 0.8)  # 10% à 90%
            status_text.text(message)

        result = cached_transcribe(tmp_path, whisper_model, translate)

        # Étape 3: Traiter le résultat
        progress_bar.progress(0.9)
        status_text.text("Finalisation...")

        # Nettoyage du fichier temporaire
        try:
            os.remove(tmp_path)
        except:
            logging.warning(f"Impossible de supprimer le fichier temporaire: {tmp_path}")

        # Vérifier les erreurs
        if error := result.get("error"):
            progress_bar.progress(1.0)
            status_text.text("Erreur lors de la transcription.")
            return False, error

        # Sauvegarder dans le stockage et la base de données
        # Sauvegarder l'audio
        filename = f"audio_{int(time.time())}.wav"
        audio_path = storage_manager.save_audio_file(
            st.session_state["user_id"],
            audio_data,
            filename
        )

        # Sauvegarder la transcription
        transcription_filename = f"transcription_{int(time.time())}.txt"
        transcription_path = storage_manager.save_transcription(
            st.session_state["user_id"],
            result["text"],
            transcription_filename
        )

        # Enregistrer dans la base de données
        db = next(get_db())

        new_transcription = Transcription(
            user_id=st.session_state["user_id"],
            filename=filename,
            duration=0,  # À calculer si possible
            model_used=whisper_model,
            text=result["text"]
        )

        db.add(new_transcription)
        db.commit()

        # Stockage des résultats dans la session
        set_session_value("transcribed_text", result["text"])
        set_session_value("segments", result["segments"])
        set_session_value("detected_language", result.get("language", ""))

        # Terminer la barre de progression
        progress_bar.progress(1.0)
        status_text.text("Transcription terminée!")
        time.sleep(0.5)  # Laisser le temps de voir le message
        status_text.empty()

        from core.session_manager import log_user_activity
        log_user_activity(
            st.session_state["user_id"],
            "transcription",
            f"Modèle: {whisper_model}, Durée: {duration_seconds :.1f}s"
        )
        return True, "Transcription terminée avec succès!"

    except Exception as e:
        return False, handle_error(e, ErrorType.PROCESSING_ERROR,
                                   "Erreur lors de la transcription.")


def process_transcription_async(audio_data, whisper_model, translate=False):
    """
    Version asynchrone de la transcription utilisant la file d'attente
    """
    if not audio_data:
        return False, "Aucun fichier audio fourni."

    try:
        # Sauvegarder l'audio
        filename = f"audio_{int(time.time())}.wav"
        audio_path = storage_manager.save_audio_file(
            st.session_state["user_id"],
            audio_data,
            filename
        )

        if audio_path:
            # Demander la transcription asynchrone
            task_id = request_transcription(
                audio_path,
                st.session_state["user_id"],
                filename,
                whisper_model,
                translate
            )

            # Stocker l'ID de la tâche dans la session
            st.session_state["transcription_task_id"] = task_id
            return True, "Transcription lancée en arrière-plan. Vous pouvez suivre l'avancement ici."
        else:
            return False, "Erreur lors de la sauvegarde du fichier audio."

    except Exception as e:
        return False, handle_error(e, ErrorType.PROCESSING_ERROR,
                                   "Erreur lors du lancement de la transcription.")



# [Les fonctions pour les analyses GPT restent inchangées]
def run_gpt_summary(
        api_key: str,
        style: str = "bullet",
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7
) -> bool:
    """
    Exécute l'analyse de résumé GPT sur le texte transcrit.

    Args:
        api_key: Clé API OpenAI
        style: Style de résumé ("bullet", "concise", "detailed")
        model: Modèle GPT à utiliser
        temperature: Température pour la génération

    Returns:
        True si succès, False sinon
    """
    text = get_session_value("transcribed_text", "")
    if not text:
        st.warning("Aucun texte à résumer. Veuillez d'abord faire une transcription.")
        return False

    if not api_key:
        st.warning("Clé API OpenAI requise pour cette fonctionnalité.")
        return False

    try:
        with st.spinner("Génération du résumé en cours..."):
            summary = summarize_text(
                text=text,
                api_key=api_key,
                gpt_model=model,
                temperature=temperature,
                style=style
            )

        set_session_value("summary_result", summary)
        return True

    except Exception as e:
        handle_error(e, ErrorType.API_ERROR,
                     "Erreur lors de la génération du résumé.")
        return False


def run_gpt_keywords(api_key: str, model: str = "gpt-3.5-turbo") -> bool:
    """
    Extrait les mots-clés du texte transcrit via GPT.

    Args:
        api_key: Clé API OpenAI
        model: Modèle GPT à utiliser

    Returns:
        True si succès, False sinon
    """
    text = get_session_value("transcribed_text", "")
    if not text:
        st.warning("Aucun texte pour extraire des mots-clés. Veuillez d'abord faire une transcription.")
        return False

    if not api_key:
        st.warning("Clé API OpenAI requise pour cette fonctionnalité.")
        return False

    try:
        with st.spinner("Extraction des mots-clés en cours..."):
            keywords = extract_keywords(text, api_key, model=model)

        set_session_value("keywords_result", keywords)
        return True

    except Exception as e:
        handle_error(e, ErrorType.API_ERROR,
                     "Erreur lors de l'extraction des mots-clés.")
        return False


def run_gpt_question(question: str, api_key: str, model: str = "gpt-3.5-turbo") -> bool:
    """
    Pose une question au texte transcrit via GPT.

    Args:
        question: Question à poser
        api_key: Clé API OpenAI
        model: Modèle GPT à utiliser

    Returns:
        True si succès, False sinon
    """
    text = get_session_value("transcribed_text", "")
    if not text:
        st.warning("Aucun texte pour poser une question. Veuillez d'abord faire une transcription.")
        return False

    if not question.strip():
        st.warning("Veuillez saisir une question.")
        return False

    if not api_key:
        st.warning("Clé API OpenAI requise pour cette fonctionnalité.")
        return False

    try:
        with st.spinner("Traitement de la question en cours..."):
            answer = ask_question_about_text(text, question, api_key, model=model)

        set_session_value("answer_result", answer)
        return True

    except Exception as e:
        handle_error(e, ErrorType.API_ERROR,
                     "Erreur lors du traitement de la question.")
        return False


def create_text_chapters(chunk_duration: float = 60.0) -> bool:
    """
    Crée des chapitres à partir des segments de transcription.

    Args:
        chunk_duration: Durée en secondes pour chaque chapitre

    Returns:
        True si succès, False sinon
    """
    segments = get_session_value("segments", [])
    if not segments:
        st.warning("Aucun segment disponible. Veuillez faire une transcription avant.")
        return False

    try:
        with st.spinner("Création des chapitres en cours..."):
            chapters = create_chapters_from_segments(segments, chunk_duration=chunk_duration)
            chapter_text = "\n".join(chapters)

        set_session_value("chapters_result", chapter_text)
        return True

    except Exception as e:
        handle_error(e, ErrorType.PROCESSING_ERROR,
                     "Erreur lors de la création des chapitres.")
        return False


def export_text_to_file(text: str, filename: str) -> bool:
    """
    Exporte du texte vers un fichier et propose le téléchargement.

    Args:
        text: Texte à exporter
        filename: Nom du fichier

    Returns:
        True si succès, False sinon
    """
    if not text.strip():
        st.warning("Aucun texte à exporter.")
        return False

    try:
        export_folder = get_session_value("export_folder", "")
        path = export_text_file(text, export_folder, filename)

        # Propose le téléchargement direct
        st.download_button(
            label="Télécharger le fichier",
            data=text.encode("utf-8"),
            file_name=filename,
            mime="text/plain"
        )

        return True

    except Exception as e:
        handle_error(e, ErrorType.FILE_ERROR,
                     "Erreur lors de l'export du fichier.")
        return False


def afficher_page_4():
    st.title("Transcription / Traduction")

    # Importer les vérifications des quotas du plan
    from core.plan_manager import PlanManager

    # Récupérer la clé API OpenAI
    openai_api_key = api_key_manager.get_key("openai")

    # Interface principale
    tabs = st.tabs(["Transcription", "Résumé", "Mots-clés", "Questions/Réponses", "Chapitres"])

    # Tab 1: Transcription
    with tabs[0]:
        col1, col2 = st.columns([1, 1])

        with col1:
            # Options de transcription
            st.subheader("Options")

            whisper_model = st.selectbox(
                "Modèle Whisper",
                ["tiny", "base", "small", "medium", "large"],
                help="Plus le modèle est grand, plus la transcription est précise mais lente."
            )

            # Vérification de l'accès au modèle
            if whisper_model not in ["tiny", "base"] and "user_id" in st.session_state:
                if not PlanManager.check_model_access(st.session_state["user_id"], whisper_model):
                    st.warning(
                        f"Note: Le modèle {whisper_model} nécessite un forfait supérieur. La transcription peut échouer.")

            translate_checkbox = st.checkbox(
                "Traduire en anglais (au lieu de transcrire)",
                value=False,
                help="Traduit l'audio en anglais quelle que soit la langue d'origine."
            )

            use_async = st.checkbox(
                "Utiliser le traitement asynchrone",
                value=True,
                help="Recommandé pour les fichiers longs. La transcription s'exécutera en arrière-plan."
            )

            # Source audio
            st.subheader("Source audio")

            # Option 1: Fichier depuis session (précédemment téléchargé)
            audio_data = get_session_value("audio_bytes_for_transcription")
            if audio_data:
                st.success("Fichier audio chargé depuis l'extraction précédente.")
                st.audio(audio_data, format="audio/wav")

            # Option 2: Upload direct
            audio_file = st.file_uploader(
                "Ou chargez un fichier audio",
                type=["wav", "mp3", "m4a", "ogg"],
                help="Formats supportés: WAV, MP3, M4A, OGG"
            )

            if audio_file:
                file_size_mb = audio_file.size / (1024 * 1024)

                # Vérifier la taille du fichier
                if "user_id" in st.session_state:
                    if not PlanManager.check_file_size_limit(st.session_state["user_id"], file_size_mb):
                        st.warning(
                            f"Ce fichier ({file_size_mb:.1f} MB) dépasse la limite de votre forfait. Veuillez passer à un forfait supérieur.")

                audio_data = audio_file.read()
                st.audio(audio_data, format=f"audio/{audio_file.type.split('/')[1]}")
                st.info(f"Taille du fichier: {file_size_mb:.1f} MB")

            # Bouton de transcription
            transcribe_button = st.button(
                "Lancer la transcription",
                disabled=audio_data is None and audio_file is None,
                use_container_width=True
            )

            if transcribe_button:
                # Vérifier les quotas
                if "user_id" in st.session_state:
                    if not PlanManager.check_transcription_quota(st.session_state["user_id"]):
                        st.error(
                            "Vous avez atteint votre quota de transcription pour ce mois. Veuillez passer à un forfait supérieur.")
                    else:
                        data_to_transcribe = audio_data if audio_data else audio_file.read()

                        if use_async:
                            success, message = process_transcription_async(
                                data_to_transcribe,
                                whisper_model,
                                translate_checkbox
                            )
                        else:
                            success, message = process_transcription_sync(
                                data_to_transcribe,
                                whisper_model,
                                translate_checkbox
                            )

                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.error("Erreur de session. Veuillez vous reconnecter.")

            # Vérifier le statut des tâches en cours
            if "transcription_task_id" in st.session_state:
                task_id = st.session_state["transcription_task_id"]
                status, result = check_transcription_status(task_id)

                status_container = st.container()

                if status == "PENDING":
                    status_container.warning("Transcription en attente de traitement...")
                elif status == "STARTED":
                    status_container.info("Transcription en cours...")
                elif status == "SUCCESS":
                    status_container.success("Transcription terminée avec succès!")
                    # Mettre à jour la session avec le résultat
                    set_session_value("transcribed_text", result["text"])
                    set_session_value("detected_language", result.get("language", ""))
                    # Supprimer l'ID de tâche de la session
                    del st.session_state["transcription_task_id"]
                    # Forcer le rafraîchissement
                    st.rerun()
                elif status == "FAILURE":
                    status_container.error("La transcription a échoué. Veuillez réessayer.")
                    if st.button("Effacer la tâche"):
                        del st.session_state["transcription_task_id"]
                        st.rerun()

        with col2:
            # Affichage des résultats
            st.subheader("Texte transcrit")

            transcribed_text = get_session_value("transcribed_text", "")
            detected_language = get_session_value("detected_language", "")

            if detected_language:
                st.info(f"Langue détectée: {detected_language}")

            text_area = st.text_area(
                "Transcription",
                value=transcribed_text,
                height=350,
                key="transcription_textarea"
            )

            # Si modifié, mettre à jour
            if text_area != transcribed_text:
                set_session_value("transcribed_text", text_area)

            # Options d'export
            if transcribed_text:
                st.subheader("Exporter")
                export_folder = st.text_input(
                    "Dossier d'export (optionnel)",
                    placeholder="Ex: /home/user/documents"
                )
                set_session_value("export_folder", export_folder)

                if st.button("Exporter la transcription (.txt)"):
                    if export_text_to_file(transcribed_text, "transcription.txt"):
                        st.success("Transcription exportée avec succès!")

    # [Le code pour les autres onglets reste inchangé]
    # Tab 2: Résumé, Tab 3: Mots-clés, Tab 4: Questions/Réponses, Tab 5: Chapitres