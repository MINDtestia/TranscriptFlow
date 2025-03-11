# core/utils.py

import os
import tempfile
from typing import List

def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    """
    Découpe un texte trop long en chunks ~max_chars caractères chacun.
    """
    chunks = []
    current_pos = 0
    while current_pos < len(text):
        chunk = text[current_pos: current_pos + max_chars]
        chunks.append(chunk)
        current_pos += max_chars
    return chunks


def create_chapters_from_segments(segments: List[dict], chunk_duration: float = 60.0) -> List[str]:
    """
    Regroupe les segments en chapitres toutes les X secondes.
    """
    if not segments:
        return []
    chapters = []
    current_start = 0.0
    chapter_texts = []
    chapter_index = 1

    for seg in segments:
        seg_start = seg["start"]
        seg_text = seg["text"]

        if seg_start - current_start >= chunk_duration and chapter_texts:
            start_min = int(current_start // 60)
            start_sec = int(current_start % 60)
            chapters.append(
                f"[Chapitre {chapter_index}] à {start_min:02d}:{start_sec:02d} => "
                + " ".join(chapter_texts)
            )
            chapter_index += 1
            chapter_texts = []
            current_start = seg_start

        chapter_texts.append(seg_text)

    if chapter_texts:
        start_min = int(current_start // 60)
        start_sec = int(current_start % 60)
        chapters.append(
            f"[Chapitre {chapter_index}] à {start_min:02d}:{start_sec:02d} => "
            + " ".join(chapter_texts)
        )

    return chapters


def export_text_file(text: str, output_folder: str, filename: str = "transcription.txt") -> str:
    """
    Enregistre le texte dans un fichier .txt dans output_folder (ou tmp si vide).
    Retourne le chemin complet du fichier.
    """
    if not text:
        return ""

    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
    else:
        output_folder = tempfile.gettempdir()

    out_path = os.path.join(output_folder, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return out_path
