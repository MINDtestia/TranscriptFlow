# core/audio_extractor.py
import os
import tempfile
import subprocess
import yt_dlp
import certifi
import logging
from .error_handling import handle_error, ErrorType

os.environ['SSL_CERT_FILE'] = certifi.where()

def download_youtube_audio(url: str):
    """
    Télécharge l'audio d'une vidéo YouTube en WAV via yt-dlp
    et renvoie le contenu binaire (bytes) du fichier WAV.
    En cas d'erreur, renvoie une chaîne commençant par "ERROR".
    """
    try:
        if not url.strip():
            return handle_error(ValueError("URL vide"), ErrorType.INPUT_ERROR,
                               "Veuillez fournir une URL YouTube valide.")

        # On crée un dossier temporaire pour stocker la sortie de yt-dlp
        with tempfile.TemporaryDirectory() as temp_dir:
            # Modèle de chemin de sortie pour yt-dlp
            output_path_template = os.path.join(temp_dir, 'downloaded_audio.%(ext)s')

            # Options pour yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path_template,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'wav',   # peut être "mp3", "flac", etc.
                        'preferredquality': '192', # n'affecte pas le WAV, mais ne gêne pas
                    }
                ],
            }

            # Téléchargement et extraction audio via yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Fichier final produit par yt-dlp
            final_file_path = os.path.join(temp_dir, 'downloaded_audio.wav')

            # Lecture du contenu en binaire
            with open(final_file_path, 'rb') as f:
                audio_bytes = f.read()

            # À la fin du bloc with, tout le dossier temp est automatiquement supprimé
            return audio_bytes

    except Exception as e:
        return handle_error(e, ErrorType.PROCESSING_ERROR,
                           f"Échec du téléchargement ou de la conversion depuis YouTube. Vérifiez l'URL et réessayez.")

def extract_audio_from_mp4(file_path: str) -> str:
    """
    Extrait la piste audio d'un fichier .mp4 local en .wav via FFmpeg.
    Retourne le chemin du fichier audio résultant.
    """
    if not file_path:
        return handle_error(ValueError("Aucun fichier fourni"), ErrorType.INPUT_ERROR,
                           "Aucun fichier vidéo n'a été fourni.")

    try:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"{base_name}.wav")

        cmd = [
            'ffmpeg', '-y',
            '-i', file_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '44100',
            '-ac', '2',
            audio_path
        ]
        subprocess.run(cmd, check=True)

        return audio_path

    except Exception as e:
        return handle_error(e, ErrorType.PROCESSING_ERROR,
                           "Échec de l'extraction audio. Vérifiez que le format vidéo est supporté et que ffmpeg est correctement installé.")