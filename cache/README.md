TranscriptFlow (Audio Transistor)
Show Image
Une application Streamlit pour extraire, transcrire, et analyser l'audio de vidéos YouTube ou de fichiers locaux.
✨ Fonctionnalités

Extraction audio depuis YouTube ou fichiers vidéo locaux (MP4, MOV, AVI, etc.)
Transcription automatique avec plusieurs modèles Whisper (tiny à large)
Traduction audio vers texte en anglais
Analyses GPT sur les transcriptions:

Résumés (bullet points, concis, détaillé)
Extraction de mots-clés
Questions/Réponses sur le contenu
Création automatique de chapitres


Synthèse vocale (Text-to-Speech) avec plusieurs voix disponibles
Interface utilisateur intuitive avec mode clair/sombre
Système d'authentification multi-utilisateurs

🛠️ Technologies utilisées

Frontend: Streamlit
Extraction audio: yt-dlp, ffmpeg
Transcription: Whisper (local)
Analyses textuelles: API OpenAI (GPT-3.5, GPT-4)
Text-to-Speech: API OpenAI TTS
Authentification: streamlit-authenticator

📋 Prérequis

Python 3.9+
FFmpeg installé sur le système
Une clé API OpenAI
Git (pour cloner le dépôt)

🚀 Installation

Cloner le dépôt:
bashCopygit clone https://github.com/username/transcriptflow.git
cd transcriptflow

Créer un environnement virtuel:
bashCopypython -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

Installer les dépendances:
bashCopypip install -r requirements.txt

Configurer les variables d'environnement:
Créez un fichier .env à la racine du projet:
CopyOPENAI_API_KEY=votre_clé_api_openai

Lancer l'application:
bashCopystreamlit run app.py


🔑 Authentification
Par défaut, l'application est configurée avec les utilisateurs suivants:

Admin:

Identifiant: admin
Mot de passe: admin
Accès complet à toutes les fonctionnalités


Utilisateur test:

Identifiant: user1
Mot de passe: password
Accès limité (visualisation uniquement)



Pour modifier les utilisateurs, éditez le fichier core/config.yaml.
📊 Structure du projet
Copytranscriptflow/
├── app.py                # Point d'entrée de l'application
├── requirements.txt      # Dépendances Python
├── README.md             # Documentation
├── .env                  # Variables d'environnement (à créer)
├── core/                 # Fonctionnalités principales
│   ├── api_key_manager.py     # Gestion des clés API
│   ├── audio_extractor.py     # Extraction audio
│   ├── authentication.py      # Système d'authentification
│   ├── error_handling.py      # Gestion des erreurs
│   ├── gpt_processor.py       # Communication avec GPT
│   ├── session_manager.py     # Gestion des sessions
│   ├── transcription.py       # Intégration Whisper
│   └── utils.py               # Fonctions utilitaires
├── my_page/             # Pages de l'interface
│   ├── dashboard_1.py        # Dashboard
│   ├── extraction_youtube_2.py  # Extraction YouTube
│   ├── extract_video_3.py    # Extraction fichier vidéo
│   ├── transcription_4.py    # Transcription et analyse
│   ├── text_to_audio.py      # Text-to-Speech
│   └── parametres.py         # Configuration
├── image/               # Ressources graphiques
└── tests/               # Tests unitaires
📝 Utilisation
1. Extraction d'audio
Depuis YouTube:

Accédez à l'onglet "Extraction d'une vidéo YouTube"
Collez l'URL YouTube
Cliquez sur "Télécharger"

Depuis un fichier local:

Accédez à l'onglet "Extraction d'un fichier vidéo"
Uploadez votre fichier vidéo
Cliquez sur "Extraire l'audio"

2. Transcription

Accédez à l'onglet "Transcription"
Choisissez le modèle Whisper (base est un bon compromis vitesse/qualité)
Si nécessaire, cochez "Traduire en anglais"
Cliquez sur "Lancer la transcription"

3. Analyses GPT
Une fois la transcription terminée:

Résumé: Choisissez le style et cliquez sur "Générer un résumé"
Mots-clés: Cliquez sur "Extraire les mots-clés"
Q/R: Posez une question sur le contenu et obtenez une réponse
Chapitres: Divisez automatiquement le contenu en chapitres

4. Text-to-Speech

Accédez à l'onglet "Text to Audio"
Entrez ou collez le texte à convertir en audio
Choisissez le modèle et la voix
Cliquez sur "Générer l'audio"

📈 Performances
Les performances dépendent du matériel utilisé et des modèles sélectionnés:

Transcription:

Modèle tiny: ~32x temps réel (très rapide, moins précis)
Modèle base: ~16x temps réel (bon équilibre)
Modèle large: ~1x temps réel (plus lent, très précis)


Analyses GPT:

Temps de réponse: 2-10 secondes selon la longueur du texte
Coût approximatif: ~$0.02 par analyse (GPT-3.5) / ~$0.20 (GPT-4)


Text-to-Speech:

Temps de génération: ~5 secondes pour 200 mots
Coût approximatif: ~$0.015 par 1000 caractères (tts-1)



🤝 Contribution
Les contributions sont les bienvenues! Voici comment procéder:

Forkez le dépôt
Créez une branche pour votre fonctionnalité (git checkout -b feature/amazing-feature)
Committez vos changements (git commit -m 'Add amazing feature')
Poussez vers la branche (git push origin feature/amazing-feature)
Ouvrez une Pull Request

📜 Licence
Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
🙏 Remerciements

Streamlit pour l'interface
Whisper pour la transcription
OpenAI pour les API GPT et TTS
yt-dlp pour l'extraction YouTube