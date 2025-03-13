from celery import Celery
import os
import logging
import whisper
import time
from .database import get_db, Transcription
from .storage_manager import storage_manager
import tempfile

# Configuration Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Création de l'application Celery
celery_app = Celery('transcriptflow', broker=REDIS_URL, backend=REDIS_URL)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
)


@celery_app.task(name="transcribe_audio")
def transcribe_audio_task(audio_path, user_id, filename, whisper_model="base", translate=False):
    """
    Tâche Celery pour transcrire un fichier audio de manière asynchrone

    Args:
        audio_path: Chemin complet vers le fichier audio (bucket/user_id/filename)
        user_id: ID de l'utilisateur
        filename: Nom du fichier original
        whisper_model: Modèle Whisper à utiliser
        translate: Si True, traduit plutôt que transcrire

    Returns:
        ID de la transcription en base de données
    """
    logging.info(f"Début de la transcription asynchrone: {audio_path}")

    try:
        # Récupérer le contenu audio
        bucket, object_name = audio_path.split('/', 1)

        # Créer un fichier temporaire pour stocker l'audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        # Télécharger le fichier dans le temporaire
        storage_manager.client.fget_object(bucket, object_name, tmp_path)

        # Charger le modèle Whisper
        start_time = time.time()
        model = whisper.load_model(whisper_model)

        # Transcrire
        result = model.transcribe(
            tmp_path,
            verbose=False,
            task="translate" if translate else "transcribe",
            temperature=0.0,
            beam_size=5,
            best_of=5,
            fp16=True,
        )

        transcription_text = result["text"]
        detected_language = result.get("language", "unknown")

        # Sauvegarder la transcription dans le stockage
        transcription_filename = f"transcription_{int(time.time())}.txt"
        transcription_path = storage_manager.save_transcription(
            user_id, transcription_text, transcription_filename
        )

        # Durée d'exécution
        duration = time.time() - start_time

        # Sauvegarder dans la base de données
        db = next(get_db())

        # Créer la transcription
        transcription = Transcription(
            user_id=user_id,
            filename=filename,
            duration=duration,
            model_used=whisper_model,
            text=transcription_text
        )

        db.add(transcription)
        db.commit()
        db.refresh(transcription)

        # Nettoyage
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        logging.info(f"Transcription terminée en {duration:.2f}s: {transcription.id}")

        return {
            "id": transcription.id,
            "text": transcription_text,
            "language": detected_language,
            "duration": duration
        }

    except Exception as e:
        logging.error(f"Erreur lors de la transcription: {str(e)}")
        # En cas d'erreur, on nettoie quand même
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

        raise