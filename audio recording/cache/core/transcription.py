import ssl
import whisper
from .task_queue import transcribe_audio_task
import logging
import subprocess
import os
def transcribe_or_translate_locally(
        audio_file_path: str,
        whisper_model: str = "base",
        translate: bool = False,
        progress_callback=None
):
    """
    Transcrit (ou traduit) un fichier audio localement avec Whisper.
    Retourne { 'error', 'text', 'segments', 'language' }.
    Gère l'erreur SSL si besoin.
    """
    """
        Transcrit (ou traduit) un fichier audio localement avec Whisper.
        """
    # Ajouter des logs détaillés pour faciliter le débogage
    logging.info(f"Début de transcription: fichier={audio_file_path}, modèle={whisper_model}, translate={translate}")

    # Vérifier l'existence du fichier
    if not os.path.exists(audio_file_path):
        error_msg = f"Fichier audio introuvable: {audio_file_path}"
        logging.error(error_msg)
        return {
            "error": error_msg,
            "text": "",
            "segments": [],
            "language": "",
        }

    # Vérifier que ffmpeg est installé
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        error_msg = "FFmpeg n'est pas installé ou n'est pas accessible. FFmpeg est requis pour Whisper."
        logging.error(error_msg)
        return {
            "error": error_msg,
            "text": "",
            "segments": [],
            "language": "",
        }

    if not audio_file_path:
        return {
            "error": "Erreur: Aucun fichier audio fourni",
            "text": "",
            "segments": [],
            "language": "",
        }

    try:
        if progress_callback:
            progress_callback(0.05, f"Chargement du modèle Whisper '{whisper_model}'...")

        model = whisper.load_model(whisper_model)

        if progress_callback:
            progress_callback(0.15, "Modèle chargé. Début de la transcription...")

        result = model.transcribe(
            audio_file_path,
            verbose=True,
            task="translate" if translate else "transcribe",
            word_timestamps=False,
            temperature=0.0,
            beam_size=3,  # Réduit de 5 à 3
            best_of=3,  # Réduit de 5 à 3
            fp16=False,  # Force fp32 pour CPU
            condition_on_previous_text=False  # Désactive la conditionnalité qui consomme plus de mémoire
        )

        if progress_callback:
            progress_callback(0.8, "Analyse des segments en cours...")

        segments_data = []
        if "segments" in result and isinstance(result["segments"], list):
            for seg in result["segments"]:
                segments_data.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"]
                })

        detected_lang = result.get("language", "inconnue")

        if progress_callback:
            progress_callback(1.0, "Transcription terminée.")

        return {
            "error": "",
            "text": result["text"],
            "segments": segments_data,
            "language": detected_lang,
        }

    except ssl.SSLError as e:
        return {
            "error": (
                "Erreur SSL lors du téléchargement/chargement du modèle. "
                "Vérifiez vos certificats ou téléchargez manuellement le modèle. "
                f"Détails: {str(e)}"
            ),
            "text": "",
            "segments": [],
            "language": "",
        }
    except FileNotFoundError:
        return {
            "error": "Erreur: Fichier audio introuvable.",
            "text": "",
            "segments": [],
            "language": "",
        }
    except Exception as e:
        return {
            "error": f"Erreur lors de la transcription locale: {str(e)}",
            "text": "",
            "segments": [],
            "language": "",
        }


def request_transcription(audio_file_path, user_id, filename, whisper_model="base", translate=False):
    """
    Demande une transcription asynchrone

    Args:
        audio_file_path: Chemin du fichier audio dans le stockage
        user_id: ID de l'utilisateur
        filename: Nom du fichier original
        whisper_model: Modèle Whisper à utiliser
        translate: Si True, traduit plutôt que transcrire

    Returns:
        ID de la tâche Celery
    """
    # Lancer la tâche asynchrone
    task = transcribe_audio_task.delay(
        audio_file_path, user_id, filename, whisper_model, translate
    )

    return task.id


# Ajoutez cette fonction dans core/transcription.py
def optimize_whisper_performance():
    """Configure Whisper pour de meilleures performances"""
    import os

    # Forcer l'utilisation du CPU (évite les problèmes avec les GPU anciens/incompatibles)
    os.environ["WHISPER_FORCE_CPU"] = "1"

    # Limiter les threads pour éviter la surcharge de la RAM
    os.environ["OMP_NUM_THREADS"] = "2"

    # Désactiver le parallélisme torch si besoin
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

    # Force fp32 sur CPU (les avertissements suggèrent que c'est déjà le cas)
    os.environ["WHISPER_USE_FP16"] = "0"

# Appelez cette fonction au début de transcribe_or_translate_locally
