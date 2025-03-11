# Audio Transistor

Ce projet Streamlit permet d'extraire l'audio depuis une vidéo (YouTube ou fichier local), 
de faire une transcription (avec Whisper), puis de faire des analyses GPT (Résumé, Mots-clés, Q/R).

## Installation

```bash
git clone ...
cd projet
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sur Windows
pip install -r requirements.txt
