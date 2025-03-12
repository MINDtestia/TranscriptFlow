import ssl
import whisper
from .task_queue import transcribe_audio_task


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
            verbose=False,
            task="translate" if translate else "transcribe",
            word_timestamps=False,
            temperature=0.0,
            beam_size=5,
            best_of=5,
            fp16=True,  # si GPU dispo
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


