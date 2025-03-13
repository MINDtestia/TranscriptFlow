from minio import Minio
from minio.error import S3Error
import os
import tempfile
import logging
from datetime import timedelta
import shutil


MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
# Ajouter cette variable pour désactiver MinIO si nécessaire
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
USE_MINIO = os.getenv("USE_MINIO", "true").lower() == "true" and not DEVELOPMENT_MODE

# Configuration MinIO
#MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Nom des buckets
AUDIO_BUCKET = "audio-files"
TRANSCRIPTION_BUCKET = "transcriptions"
EXPORT_BUCKET = "exports"




class StorageManager:
    def __init__(self):
        """Initialise le client MinIO"""
        self.use_minio = USE_MINIO

        if self.use_minio:
            try:
                self.client = Minio(
                    MINIO_ENDPOINT,
                    access_key=MINIO_ACCESS_KEY,
                    secret_key=MINIO_SECRET_KEY,
                    secure=MINIO_SECURE
                )
                self._ensure_buckets_exist()
            except Exception as e:
                logging.error(f"Erreur lors de l'initialisation de MinIO: {e}")
                logging.warning("Désactivation de MinIO et utilisation du stockage local")
                self.use_minio = False

        # Créer un répertoire local pour le stockage si MinIO est désactivé
        if not self.use_minio:
            self.local_storage_dir = os.path.join(os.getcwd(), "local_storage")
            for bucket in [AUDIO_BUCKET, TRANSCRIPTION_BUCKET, EXPORT_BUCKET]:
                bucket_dir = os.path.join(self.local_storage_dir, bucket)
                os.makedirs(bucket_dir, exist_ok=True)

    def _ensure_buckets_exist(self):
        """S'assure que les buckets nécessaires existent"""
        if not self.use_minio:
            return

        for bucket in [AUDIO_BUCKET, TRANSCRIPTION_BUCKET, EXPORT_BUCKET]:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logging.info(f"Bucket {bucket} créé")
            except Exception as e:
                logging.error(f"Erreur lors de la création du bucket {bucket}: {e}")
                raise

    def save_audio_file(self, user_id, file_data, filename):
        """
        Sauvegarde un fichier audio dans le stockage
        """
        object_name = f"{user_id}/{filename}"

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name

        try:
            if self.use_minio:
                self.client.fput_object(
                    AUDIO_BUCKET, object_name, temp_file_path,
                    content_type="audio/wav"
                )
                logging.info(f"Fichier audio {object_name} sauvegardé avec succès dans MinIO")
                return f"{AUDIO_BUCKET}/{object_name}"
            else:
                # Stockage local
                user_dir = os.path.join(self.local_storage_dir, AUDIO_BUCKET, str(user_id))
                os.makedirs(user_dir, exist_ok=True)
                dest_path = os.path.join(user_dir, filename)
                shutil.copy(temp_file_path, dest_path)
                logging.info(f"Fichier audio {object_name} sauvegardé avec succès localement")
                return f"{AUDIO_BUCKET}/{object_name}"
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde du fichier audio: {e}")
            return None
        finally:
            # Nettoyage du fichier temporaire
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    def get_audio_file(self, user_id, filename):
        """
        Récupère un fichier audio du stockage

        Args:
            user_id: ID de l'utilisateur
            filename: Nom du fichier

        Returns:
            Contenu binaire du fichier
        """
        object_name = f"{user_id}/{filename}"

        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_path = temp_file.name

            self.client.fget_object(AUDIO_BUCKET, object_name, temp_file_path)

            with open(temp_file_path, "rb") as f:
                data = f.read()

            return data
        except S3Error as e:
            logging.error(f"Erreur lors de la récupération du fichier audio: {e}")
            return None
        finally:
            # Nettoyage du fichier temporaire
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def save_transcription(self, user_id, transcription_text, filename):
        """
        Sauvegarde une transcription dans le stockage
        """
        object_name = f"{user_id}/{filename}"

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            temp_file.write(transcription_text)
            temp_file_path = temp_file.name

        try:
            if self.use_minio:
                try:
                    self.client.fput_object(
                        TRANSCRIPTION_BUCKET, object_name, temp_file_path,
                        content_type="text/plain"
                    )
                    logging.info(f"Transcription {object_name} sauvegardée avec succès dans MinIO")
                    return f"{TRANSCRIPTION_BUCKET}/{object_name}"
                except Exception as e:
                    logging.error(f"Erreur MinIO lors de la sauvegarde de la transcription: {str(e)}")
                    # On essaie en stockage local en cas d'échec MinIO
                    self.use_minio = False

            # Stockage local (si MinIO est désactivé ou a échoué)
            user_dir = os.path.join(self.local_storage_dir, TRANSCRIPTION_BUCKET, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            dest_path = os.path.join(user_dir, filename)
            shutil.copy(temp_file_path, dest_path)
            logging.info(f"Transcription {object_name} sauvegardée avec succès localement")
            return f"{TRANSCRIPTION_BUCKET}/{object_name}"

        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde de la transcription: {str(e)}")
            return None
        finally:
            # Nettoyage du fichier temporaire
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logging.warning(f"Impossible de supprimer le fichier temporaire: {str(e)}")

    def get_presigned_url(self, bucket, object_name, expires=3600):
        """
        Génère une URL présignée pour accéder à un fichier

        Args:
            bucket: Nom du bucket
            object_name: Nom de l'objet
            expires: Durée de validité en secondes

        Returns:
            URL présignée
        """
        try:
            url = self.client.presigned_get_object(
                bucket, object_name, expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logging.error(f"Erreur lors de la génération de l'URL présignée: {e}")
            return None


# Instance globale
storage_manager = StorageManager()