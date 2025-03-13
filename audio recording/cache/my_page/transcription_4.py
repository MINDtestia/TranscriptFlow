import streamlit as st
import logging
import tempfile
import os
from typing import Optional, Dict, Any, List, Tuple
import time
import psutil

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

# Liste complète des modèles disponibles
GPT_MODELS = {
    "gpt-3.5-turbo": {"name": "GPT-3.5", "cost": "$0.01-0.05", "speed": "Rapide"},
    "gpt-4o": {"name": "GPT-4o", "cost": "$0.05-0.20", "speed": "Modéré"},
    "gpt-4o-mini": {"name": "GPT-4o Mini", "cost": "$0.02-0.10", "speed": "Modéré"},
    "gpt-4": {"name": "GPT-4", "cost": "$0.10-0.50", "speed": "Lent"}
}

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
    """
    start_time = time.time()
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

        # Vérifier que le fichier existe et a la bonne taille
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            return False, "Erreur lors de la création du fichier temporaire."

        logging.info(f"Fichier temporaire créé: {tmp_path} ({os.path.getsize(tmp_path)} bytes)")

        progress_bar.progress(0.1)
        status_text.text("Fichier prêt. Chargement du modèle Whisper...")

        # Étape 2: Lancer la transcription
        def progress_callback(progress, message):
            progress_bar.progress(0.1 + progress * 0.8)
            status_text.text(message)

        # Utiliser la version non-cachée pour les modèles lourds
        if whisper_model in ["medium", "large"]:
            result = transcribe_or_translate_locally(tmp_path, whisper_model, translate, progress_callback)
        else:
            # Utiliser la version cachée pour les modèles légers (tiny, base, small)
            result = cached_transcribe(tmp_path, whisper_model, translate)

        # Étape 3: Traiter le résultat
        progress_bar.progress(0.9)
        status_text.text("Finalisation...")

        # Nettoyage du fichier temporaire
        try:
            os.remove(tmp_path)
        except Exception as e:
            logging.warning(f"Impossible de supprimer le fichier temporaire: {tmp_path}, Erreur: {str(e)}")

        # Vérifier les erreurs
        if result.get("error"):
            progress_bar.progress(1.0)
            status_text.text(f"Erreur: {result.get('error')}")
            return False, result.get("error")

        # Sauvegarder dans le stockage et la base de données
        # Sauvegarder l'audio (uniquement si nous voulons le conserver)
        filename = f"audio_{int(time.time())}.wav"
        audio_path = storage_manager.save_audio_file(
            st.session_state["user_id"],
            audio_data,
            filename
        )

        if not audio_path:
            logging.warning("Impossible de sauvegarder l'audio, mais la transcription continue")
            # On continue même si l'audio n'est pas sauvegardé

        # Sauvegarder la transcription
        transcription_filename = f"transcription_{int(time.time())}.txt"
        transcription_path = storage_manager.save_transcription(
            st.session_state["user_id"],
            result["text"],
            transcription_filename
        )

        if not transcription_path:
            logging.warning("Impossible de sauvegarder la transcription dans le stockage, mais on continue")
            # On continue même si la transcription n'est pas sauvegardée dans le stockage

        # Enregistrer dans la base de données
        try:
            db = next(get_db())

            new_transcription = Transcription(
                user_id=st.session_state["user_id"],
                filename=filename,
                duration=time.time() - start_time,  # Durée réelle du traitement
                model_used=whisper_model,
                text=result["text"]
            )

            db.add(new_transcription)
            db.commit()
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement en base de données: {str(e)}")
            # On continue quand même car on a la transcription

        # Stockage des résultats dans la session
        st.session_state["transcribed_text"] = result["text"]
        st.session_state["segments"] = result["segments"]
        st.session_state["detected_language"] = result.get("language", "")
        st.session_state["transcription_completed"] = True
        st.session_state["last_transcription_time"] = int(time.time())

        # Terminer la barre de progression
        progress_bar.progress(1.0)
        status_text.text("Transcription terminée!")
        time.sleep(0.5)  # Laisser le temps de voir le message

        # Forcer le rafraîchissement pour afficher la transcription
        st.markdown(
            """
            <script>
            setTimeout(function() {
                window.location.reload();
            }, 1000);
            </script>
            """,
            unsafe_allow_html=True
        )

        from core.session_manager import log_user_activity

        duration_seconds = time.time() - start_time
        log_user_activity(
            st.session_state["user_id"],
            "transcription",
            f"Modèle: {whisper_model}, Durée: {duration_seconds :.1f}s"
        )

        # Essayer de forcer le rerun de Streamlit
        st.rerun()

        return True, "Transcription terminée avec succès!"

    except Exception as e:
        logging.error(f"Exception dans process_transcription_sync: {str(e)}")
        return False, f"Erreur lors de la transcription: {str(e)}"



def process_transcription_async(audio_data, whisper_model, translate=False):
    """
    Version asynchrone de la transcription utilisant la file d'attente
    """
    if not audio_data:
        return False, "Aucun fichier audio fourni."

    try:
        # Créer un fichier temporaire pour sauvegarder l'audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(audio_data)

        # Vérifier que le fichier existe
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            return False, "Erreur lors de la création du fichier temporaire."

        logging.info(
            f"Fichier temporaire pour traitement asynchrone créé: {tmp_path} ({os.path.getsize(tmp_path)} bytes)")

        # Sauvegarder l'audio
        filename = f"audio_{int(time.time())}.wav"
        audio_path = storage_manager.save_audio_file(
            st.session_state["user_id"],
            audio_data,
            filename
        )

        if not audio_path:
            return False, "Erreur lors de la sauvegarde du fichier audio."

        logging.info(f"Audio sauvegardé avec succès: {audio_path}")

        # Si nous sommes ici, c'est que le stockage a fonctionné. On peut lancer la transcription
        try:
            # Demander la transcription asynchrone
            task_id = request_transcription(
                audio_path,
                st.session_state["user_id"],
                filename,
                whisper_model,
                translate
            )

            if not task_id:
                return False, "Erreur lors du lancement de la tâche de transcription."

            # Stocker l'ID de la tâche dans la session
            st.session_state["transcription_task_id"] = task_id
            logging.info(f"Tâche de transcription lancée avec ID: {task_id}")

            return True, "Transcription lancée en arrière-plan. Vous pouvez suivre l'avancement ici."
        except Exception as e:
            logging.error(f"Erreur lors du lancement de la transcription: {str(e)}")
            return False, f"Erreur lors du lancement de la transcription: {str(e)}"

    except Exception as e:
        logging.error(f"Exception dans process_transcription_async: {str(e)}")
        return False, f"Erreur lors du traitement de la transcription: {str(e)}"


# [Les fonctions pour les analyses GPT restent inchangées]
def run_gpt_summary(api_key, style: str = "bullet", model="gpt-3.5-turbo", temperature=0.7):
    """Génère un résumé du texte transcrit"""
    text = get_session_value("transcribed_text", "")

    if not text:
        st.warning("Aucun texte à résumer. Veuillez d'abord faire une transcription.")
        return False

    if not api_key:
        st.error("Clé API OpenAI requise pour cette fonctionnalité.")
        return False

    try:
        # Nettoyer le texte des caractères problématiques
        text = text.encode('utf-8', errors='replace').decode('utf-8')

        with st.spinner("Génération du résumé en cours..."):
            summary = summarize_text(
                text=text,
                api_key=api_key,
                gpt_model=model,
                temperature=temperature,
                style=style
            )

        # Vérifier si le résumé contient une erreur
        if summary.startswith("Erreur"):
            st.error(summary)
            return False

        set_session_value("summary_result", summary)
        return True
    except Exception as e:
        st.error(f"Erreur lors de la génération du résumé: {str(e)}")
        logging.error(f"Exception dans run_gpt_summary: {str(e)}")
        return False

def optimize_whisper_for_limited_ram(model_name="base"):
    """Configure Whisper pour fonctionner avec une RAM limitée"""
    # Limiter l'utilisation de la mémoire pour les modèles whisper
    os.environ["WHISPER_FORCE_CPU"] = "1"  # Force CPU pour une meilleure compatibilité
    os.environ["OMP_NUM_THREADS"] = "2"  # Limite les threads OpenMP

    # Recommandation basée sur la taille du modèle
    recommended_model = model_name
    if model_name == "large" and psutil.virtual_memory().available < 8 * 1024 * 1024 * 1024:  # 8GB
        logging.warning("RAM insuffisante pour le modèle large, passage automatique à medium")
        recommended_model = "medium"
    elif model_name == "medium" and psutil.virtual_memory().available < 4 * 1024 * 1024 * 1024:  # 4GB
        logging.warning("RAM insuffisante pour le modèle medium, passage automatique à small")
        recommended_model = "small"

    return recommended_model

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
    if not api_key:
        st.error("Clé API OpenAI manquante. Veuillez configurer votre clé API dans le menu 'API Clés'.")
        st.warning("Vous pouvez obtenir une clé API sur openai.com/api")
        return False

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

def model_format_func(model_id):
    """Formate l'affichage des modèles dans le selectbox"""
    model_info = GPT_MODELS.get(model_id, {})
    return f"{model_info.get('name', model_id)} - {model_info.get('speed', '')}"


def afficher_page_4():
    st.title("Transcription / Traduction")

    # Détection mobile
    is_mobile = st.session_state.get("is_mobile", False)

    # Vérifier si l'audio a été passé depuis l'extraction YouTube
    audio_data = get_session_value("audio_bytes_for_transcription")
    if audio_data:
        logging.info(f"Audio trouvé dans la session: {len(audio_data)} bytes")
        st.success("Audio chargé depuis l'extraction précédente!")
        st.audio(audio_data, format="audio/wav")
    else:
        logging.warning("Aucun audio trouvé dans la session")

    # Importer les vérifications des quotas du plan
    from core.plan_manager import PlanManager

    # Récupérer la clé API OpenAI
    openai_api_key = api_key_manager.get_key("openai")

    # Interface principale - tabs adaptés pour mobile/desktop
    tabs = st.tabs(["Transcription", "Résumé", "Mots-clés", "Q/R", "Chapitres"] if is_mobile else
                   ["Transcription", "Résumé", "Mots-clés", "Questions/Réponses", "Chapitres"])

    # Tab 1: Transcription
    with tabs[0]:
        if is_mobile:
            # Version mobile: empilée verticalement
            # Options de transcription
            st.subheader("Options")

            whisper_model = st.selectbox(
                "Modèle Whisper",
                ["tiny", "base", "small", "medium"],
                help="Plus le modèle est grand, plus la transcription est précise mais lente."
            )

            # Vérification de l'accès au modèle
            if whisper_model in ["medium"]:
                st.warning(
                    f"⚠️ Le modèle {whisper_model} est très gourmand en ressources. Sur votre matériel, la transcription pourrait prendre 10-15 minutes ou plus pour 1 minute d'audio.")

            translate_checkbox = st.checkbox(
                "Traduire en anglais",
                value=False,
                help="Traduit l'audio en anglais quelle que soit la langue d'origine."
            )

            use_async = st.checkbox(
                "Traitement asynchrone",
                value=True,
                help="Recommandé pour les fichiers longs."
            )

            # Source audio
            st.subheader("Source audio")

            # Options de source audio
            audio_data = get_session_value("audio_bytes_for_transcription")
            if audio_data:
                st.success("Audio chargé depuis l'extraction précédente.")
                st.audio(audio_data, format="audio/wav")

            audio_file = st.file_uploader(
                "Charger un fichier audio",
                type=["wav", "mp3", "m4a", "ogg"]
            )

            if audio_file:
                file_size_mb = audio_file.size / (1024 * 1024)
                if "user_id" in st.session_state:
                    if not PlanManager.check_file_size_limit(st.session_state["user_id"], file_size_mb):
                        st.warning(f"Ce fichier ({file_size_mb:.1f} MB) dépasse la limite de votre forfait.")
                audio_data = audio_file.read()
                st.audio(audio_data, format=f"audio/{audio_file.type.split('/')[1]}")
                st.info(f"Taille: {file_size_mb:.1f} MB")

            # Bouton de transcription
            transcribe_button = st.button(
                "Lancer la transcription",
                disabled=audio_data is None and audio_file is None,
                use_container_width=True
            )

            # Affichage des résultats
            st.subheader("Texte transcrit")

            transcribed_text = get_session_value("transcribed_text", "")
            detected_language = get_session_value("detected_language", "")

            if detected_language:
                st.info(f"Langue détectée: {detected_language}")

            text_area = st.text_area(
                "Transcription",
                value=transcribed_text,
                height=250,
                key="transcription_textarea"
            )

            # Si modifié, mettre à jour
            if text_area != transcribed_text:
                set_session_value("transcribed_text", text_area)

            # Options d'export simplifiées pour mobile
            if transcribed_text:
                if st.button("Exporter la transcription (.txt)", use_container_width=True):
                    if export_text_to_file(transcribed_text, "transcription.txt"):
                        st.success("Transcription exportée!")

        else:
            # Version desktop: colonnes côte à côte
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
                """
                use_async = st.checkbox(
                    "Utiliser le traitement asynchrone",
                    value=True,
                    help="Recommandé pour les fichiers longs. La transcription s'exécutera en arrière-plan."
                )
                """
                st.warning("Transcription asynchrone désactivée en mode développement (Redis non disponible)")
                use_async = st.checkbox(
                    "Utiliser le traitement asynchrone (désactivé)",
                    value=False,
                    disabled=True,
                    help="Nécessite Redis en mode production."
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

        # Traitement du bouton de transcription (identique pour les deux layouts)
        if transcribe_button:
            # Vérifier les quotas
            if "user_id" in st.session_state:
                if not PlanManager.check_transcription_quota(st.session_state["user_id"]):
                    st.error("Vous avez atteint votre quota de transcription pour ce mois.")
                else:
                    # Récupérer l'audio à transcrire, en priorité à partir de audio_data
                    data_to_transcribe = None

                    # D'abord vérifier si on a de l'audio en session
                    if audio_data:
                        data_to_transcribe = audio_data
                        logging.info(f"Utilisation de l'audio depuis la session: {len(data_to_transcribe)} bytes")
                    # Sinon, utiliser le fichier uploadé s'il existe
                    elif audio_file:
                        data_to_transcribe = audio_file.read()
                        logging.info(
                            f"Utilisation de l'audio depuis le fichier uploadé: {len(data_to_transcribe)} bytes")

                    if data_to_transcribe:
                        # Continuer avec le traitement comme avant...
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
                            # Si transcription réussie, effacer l'audio temporaire de la session
                            set_session_value("audio_bytes_for_transcription", None)
                        else:
                            st.error(message)
                    else:
                        st.error(
                            "Aucun audio à transcrire. Veuillez charger un fichier audio ou extraire depuis YouTube.")
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

    # Implémentation des autres onglets... (Résumé, Mots-clés, Questions/Réponses, Chapitres)
    # [Inclure le code existant pour les autres onglets ici]
    with tabs[1]:  # Onglet Résumé
        st.subheader("💡 Résumé de la transcription")

        # Vérifier si une transcription existe
        transcribed_text = get_session_value("transcribed_text", "")
        if not transcribed_text:
            st.warning("⚠️ Aucune transcription disponible. Veuillez d'abord effectuer une transcription.")
            return

        # Vérifier la longueur minimale du texte
        if len(transcribed_text.split()) < 20:
            st.warning(
                "⚠️ Le texte transcrit est trop court pour générer un résumé pertinent (minimum 20 mots requis).")
            return

        # Vérifier si une clé API est configurée
        api_key = api_key_manager.get_key("openai")
        if not api_key:
            st.error("❌ Clé API OpenAI manquante. Configurez votre clé API dans le menu 'API Clés'.")
            st.info("ℹ️ Obtenez une clé API sur https://platform.openai.com/api-keys")
            with st.expander("Comment configurer une clé API OpenAI"):
                st.markdown("""
                   1. Créez un compte sur [OpenAI](https://platform.openai.com/)
                   2. Allez dans "API Keys" et cliquez sur "Create new secret key"
                   3. Copiez la clé générée
                   4. Collez-la dans le menu "API Clés" de cette application
                   """)
            return

        # Afficher les options de résumé dans une colonne
        col1, col2 = st.columns([3, 1])

        with col1:
            # Choix du mode de prompt
            mode = st.radio(
                "Sélectionnez le mode de prompt",
                ["Prompt personnalisé", "Utiliser les évènements ci-dessus"]
            )

            if mode == "Prompt personnalisé":
                # Saisie d'un prompt personnalisé
                summary_style = st.text_area(
                    "Entrez votre prompt personnalisé",
                    key="custom_prompt",
                    height=100
                )
            else:
                # Sélection du style de résumé
                summary_style = st.radio(
                    "Style de résumé",
                    ["bullet", "concise", "detailed"],
                    horizontal=True,
                    format_func=lambda x: {
                        "bullet": "Liste à puces",
                        "concise": "Concis (quelques phrases)",
                        "detailed": "Détaillé (paragraphes)"
                    }.get(x, x)
                )

            # Sélection du modèle GPT
            gpt_model = st.selectbox(
                "Modèle GPT",
                options=list(GPT_MODELS.keys()),
                index=0,
                format_func=model_format_func,
                help="Sélectionnez le modèle GPT à utiliser"
            )

        with col2:
            st.write("")
            st.write("")
            generate_button = st.button(
                f"Générer le résumé",
                type="primary",
                use_container_width=True
            )

            # Information sur le coût
            selected_model_info = GPT_MODELS.get(gpt_model, {})
            st.caption(f"Coût estimé: {selected_model_info.get('cost', 'Inconnu')}")

        # Afficher la barre de séparation
        st.divider()

        # Résultat existant ou traitement de la génération
        summary_result = get_session_value("summary_result", "")

        if generate_button:
            with st.spinner("Génération du résumé en cours..."):
                if run_gpt_summary(api_key, summary_style, gpt_model):
                    summary_result = get_session_value("summary_result", "")
                    st.success("✅ Résumé généré avec succès!")

        # Affichage du résultat
        if summary_result:
            # Titre dynamique selon le style
            summary_title = {
                "bullet": "Résumé en points clés",
                "concise": "Résumé concis",
                "detailed": "Résumé détaillé"
            }.get(summary_style, "Résumé")

            # Affichage du résumé
            st.subheader(summary_title)
            st.markdown(summary_result)

            # Options pour télécharger ou copier
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Télécharger en TXT",
                    data=summary_result,
                    file_name=f"resume_{int(time.time())}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            with col2:
                if st.button("Copier dans le presse-papier", use_container_width=True):
                    st.code(summary_result)
                    st.info("Sélectionnez et copiez le texte ci-dessus")

    with tabs[2]:  # Onglet Mots-clés
        st.subheader("🔑 Extraction de mots-clés")

        # Vérifier si une transcription existe
        transcribed_text = get_session_value("transcribed_text", "")
        if not transcribed_text:
            st.warning("⚠️ Aucune transcription disponible. Veuillez d'abord effectuer une transcription.")
            return

        # Vérifier la longueur minimale du texte
        if len(transcribed_text.split()) < 20:
            st.warning(
                "⚠️ Le texte transcrit est trop court pour extraire des mots-clés pertinents (minimum 20 mots requis).")
            return

        # Vérifier si une clé API est configurée
        api_key = api_key_manager.get_key("openai")
        if not api_key:
            st.error("❌ Clé API OpenAI manquante. Configurez votre clé API dans le menu 'API Clés'.")
            st.info("ℹ️ Obtenez une clé API sur https://platform.openai.com/api-keys")
            return

        # Options d'extraction
        col1, col2 = st.columns([3, 1])

        with col1:
            gpt_model = st.selectbox(
                "Modèle GPT",
                options=list(GPT_MODELS.keys()),
                index=0,
                format_func=model_format_func,
                help="Sélectionnez le modèle GPT à utiliser",
                key = "model_choose"
            )

        with col2:
            st.write("")
            st.write("")
            extract_button = st.button(
                "Extraire les mots-clés",
                type="primary",
                use_container_width=True
            )

            # Information sur le coût
            selected_model_info = GPT_MODELS.get(gpt_model, {})
            st.caption(f"Coût estimé: {selected_model_info.get('cost', 'Inconnu')}")

        # Afficher la barre de séparation
        st.divider()

        # Résultat existant ou traitement de l'extraction
        keywords_result = get_session_value("keywords_result", "")

        if extract_button:
            with st.spinner("Extraction des mots-clés en cours..."):
                if run_gpt_keywords(api_key, gpt_model):
                    keywords_result = get_session_value("keywords_result", "")
                    st.success("✅ Mots-clés extraits avec succès!")

        # Affichage du résultat
        if keywords_result:
            st.subheader("Mots-clés extraits")

            # Traitement des mots-clés pour un affichage plus attrayant
            keywords_list = [k.strip() for k in keywords_result.split(',')]

            # Affichage sous forme de badges
            html_tags = ""
            for keyword in keywords_list:
                if keyword:
                    html_tags += f'<span style="background-color:#1E90FF; color:white; padding:5px 10px; margin:5px; border-radius:15px; display:inline-block;">{keyword}</span>'

            st.markdown(f"<div style='margin:10px 0;'>{html_tags}</div>", unsafe_allow_html=True)

            # Version texte pour copier ou télécharger
            st.markdown("##### Liste des mots-clés")
            st.code(keywords_result)

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Télécharger en TXT",
                    data=keywords_result,
                    file_name=f"mots_cles_{int(time.time())}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    with tabs[3]:  # Onglet Questions/Réponses
        st.subheader("❓ Questions sur le contenu")

        # Vérifier si une transcription existe
        transcribed_text = get_session_value("transcribed_text", "")
        if not transcribed_text:
            st.warning("⚠️ Aucune transcription disponible. Veuillez d'abord effectuer une transcription.")
            return

        # Vérifier la longueur minimale du texte
        if len(transcribed_text.split()) < 20:
            st.warning(
                "⚠️ Le texte transcrit est trop court pour poser des questions pertinentes (minimum 20 mots requis).")
            return

        # Vérifier si une clé API est configurée
        api_key = api_key_manager.get_key("openai")
        if not api_key:
            st.error("❌ Clé API OpenAI manquante. Configurez votre clé API dans le menu 'API Clés'.")
            st.info("ℹ️ Obtenez une clé API sur https://platform.openai.com/api-keys")
            return

        # Sélection du modèle et zone de question
        col1, col2 = st.columns([3, 1])

        with col1:
            # Question
            question_input = st.text_area(
                "Posez une question sur le contenu transcrit",
                placeholder="Exemple: Quels sont les points principaux abordés dans cette transcription?",
                height=80
            )

        with col2:
            # Modèle
            gpt_model = st.selectbox(
                "Modèle GPT",
                options=list(GPT_MODELS.keys()),
                index=0,
                format_func=model_format_func,
                help="Sélectionnez le modèle GPT à utiliser",
                key="model_choose_1"
            )

            # Bouton de génération
            ask_button = st.button(
                "Poser la question",
                type="primary",
                disabled=not question_input.strip(),
                use_container_width=True
            )

            # Information sur le coût
            selected_model_info = GPT_MODELS.get(gpt_model, {})
            st.caption(f"Coût estimé: {selected_model_info.get('cost', 'Inconnu')}")

        # Afficher la barre de séparation
        st.divider()

        # Résultat existant ou traitement de la question
        answer_result = get_session_value("answer_result", "")
        last_question = get_session_value("last_question", "")

        if ask_button and question_input.strip():
            with st.spinner("Analyse de la question en cours..."):
                if run_gpt_question(question_input, api_key, gpt_model):
                    answer_result = get_session_value("answer_result", "")
                    set_session_value("last_question", question_input)
                    last_question = question_input
                    st.success("✅ Réponse générée avec succès!")

        # Affichage du résultat
        if answer_result and last_question:
            # Encadré de la question
            st.markdown(f"""
            <div style="background-color:#333; padding:10px; border-radius:5px; margin-bottom:10px">
                <p style="color:white; font-weight:bold;">Question :</p>
                <p style="color:white;">{last_question}</p>
            </div>
            """, unsafe_allow_html=True)

            # Encadré de la réponse
            st.markdown(f"""
            <div style="background-color:#1E6FCC; padding:10px; border-radius:5px;">
                <p style="color:white; font-weight:bold;">Réponse :</p>
                <p style="color:white;">{answer_result}</p>
            </div>
            """, unsafe_allow_html=True)

            # Historique et nouvelle question
            st.markdown("##### Historique des questions")

            # Récupérer l'historique des questions/réponses
            qa_history = get_session_value("qa_history", [])

            # Vérifier si la dernière question/réponse est déjà dans l'historique
            current_qa = {"question": last_question, "answer": answer_result}
            if not qa_history or qa_history[-1] != current_qa:
                qa_history.append(current_qa)
                set_session_value("qa_history", qa_history)

            # Afficher l'historique des questions sous forme d'accordéon
            if qa_history:
                for i, qa in enumerate(qa_history):
                    with st.expander(f"Q: {qa['question'][:50]}..."):
                        st.markdown(f"**Question:** {qa['question']}")
                        st.markdown(f"**Réponse:** {qa['answer']}")

    with tabs[4]:  # Onglet Chapitres
        st.subheader("📑 Génération de chapitres")

        # Vérifier si une transcription existe avec segments
        segments = get_session_value("segments", [])
        if not segments:
            st.warning("⚠️ Aucun segment de transcription disponible. Veuillez d'abord effectuer une transcription.")
            return

        # Options de génération de chapitres
        col1, col2 = st.columns([3, 1])

        with col1:
            # Réglage de la durée des chapitres
            chunk_duration = st.slider(
                "Durée approximative des chapitres (secondes)",
                min_value=30,
                max_value=300,
                value=60,
                step=15,
                help="Durée cible pour chaque chapitre"
            )

            total_duration = segments[-1]["end"] if segments else 0
            estimated_chapters = max(1, int(total_duration / chunk_duration))
            st.caption(f"Estimation: environ {estimated_chapters} chapitres pour {total_duration:.1f} secondes d'audio")

        with col2:
            st.write("")
            st.write("")
            generate_button = st.button(
                "Générer les chapitres",
                type="primary",
                use_container_width=True
            )

        # Afficher la barre de séparation
        st.divider()

        # Résultat existant ou traitement de la génération
        chapters_result = get_session_value("chapters_result", "")

        if generate_button:
            with st.spinner("Génération des chapitres en cours..."):
                if create_text_chapters(chunk_duration):
                    chapters_result = get_session_value("chapters_result", "")
                    st.success("✅ Chapitres générés avec succès!")

        # Affichage du résultat
        if chapters_result:
            st.subheader("Chapitres générés")

            # Traitement des chapitres pour un affichage plus attrayant
            chapters_list = chapters_result.strip().split('\n')

            # Affichage sous forme de chronologie
            for i, chapter in enumerate(chapters_list):
                # Extraction du timecode
                try:
                    time_part = chapter.split("à ")[1].split(" =>")[0]
                    text_part = chapter.split("=>")[1].strip()

                    # Création d'une ligne de temps
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        st.markdown(f"""
                           <div style="background-color:#1E6FCC; color:white; text-align:center; padding:8px; 
                                       border-radius:5px; font-weight:bold;">
                               {time_part}
                           </div>
                           """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                           <div style="background-color:#333; color:white; padding:8px; border-radius:5px; 
                                       margin-bottom:5px;">
                               {text_part}
                           </div>
                           """, unsafe_allow_html=True)
                except:
                    # Fallback si le format n'est pas celui attendu
                    st.markdown(chapter)

            # Options pour télécharger
            st.download_button(
                label="Télécharger les chapitres (TXT)",
                data=chapters_result,
                file_name=f"chapitres_{int(time.time())}.txt",
                mime="text/plain"
            )