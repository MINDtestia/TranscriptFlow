# TranscriptFlow (Audio Transistor)

![logo](https://github.com/user-attachments/assets/5d6dedbd-2f53-4a26-bad9-8c866ab366e2)



Une application Streamlit pour extraire, transcrire, et analyser l'audio de vidéos YouTube ou de fichiers locaux.

## ✨ Fonctionnalités

- **Extraction audio** depuis YouTube ou fichiers vidéo locaux (MP4, MOV, AVI, etc.)
- **Transcription automatique** avec plusieurs modèles Whisper (tiny à large)
- **Traduction** audio vers texte en anglais
- **Analyses GPT** sur les transcriptions:
  - Résumés (bullet points, concis, détaillé)
  - Extraction de mots-clés
  - Questions/Réponses sur le contenu
  - Création automatique de chapitres
- **Synthèse vocale** (Text-to-Speech) avec plusieurs voix disponibles
- **Interface utilisateur** intuitive avec mode clair/sombre
- **Système d'authentification** multi-utilisateurs

## 🛠️ Technologies utilisées

- **Frontend**: Streamlit
- **Extraction audio**: yt-dlp, ffmpeg
- **Transcription**: Whisper (local)
- **Analyses textuelles**: API OpenAI (GPT-3.5, GPT-4)
- **Text-to-Speech**: API OpenAI TTS
- **Authentification**: streamlit-authenticator

## 📋 Prérequis

- Python 3.9+
- FFmpeg installé sur le système
- Une clé API OpenAI
- Git (pour cloner le dépôt)

## 🚀 Installation

1. **Cloner le dépôt**:
   ```bash
   git clone https://github.com/username/transcriptflow.git
   cd transcriptflow
   ```

2. **Créer un environnement virtuel**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # ou
   .venv\Scripts\activate  # Windows
   ```

3. **Installer les dépendances**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**:
   Créez un fichier `.env` à la racine du projet:
   ```
   OPENAI_API_KEY=votre_clé_api_openai
   ```

5. **Lancer l'application**:
   ```bash
   streamlit run app.py
   ```

## 🔑 Authentification

Par défaut, l'application est configurée avec les utilisateurs suivants:

- **Admin**: 
  - Identifiant: `admin`
  - Mot de passe: `admin`
  - Accès complet à toutes les fonctionnalités

- **Utilisateur test**:
  - Identifiant: `user1`
  - Mot de passe: `password`
  - Accès limité (visualisation uniquement)

Pour modifier les utilisateurs, éditez le fichier `core/config.yaml`.

## 📊 Structure du projet

```
transcriptflow/
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
```

## 📝 Utilisation

### 1. Extraction d'audio

#### Depuis YouTube:
1. Accédez à l'onglet "Extraction d'une vidéo YouTube"
2. Collez l'URL YouTube
3. Cliquez sur "Télécharger"

#### Depuis un fichier local:
1. Accédez à l'onglet "Extraction d'un fichier vidéo"
2. Uploadez votre fichier vidéo
3. Cliquez sur "Extraire l'audio"

### 2. Transcription

1. Accédez à l'onglet "Transcription"
2. Choisissez le modèle Whisper (base est un bon compromis vitesse/qualité)
3. Si nécessaire, cochez "Traduire en anglais"
4. Cliquez sur "Lancer la transcription"

### 3. Analyses GPT

Une fois la transcription terminée:
- **Résumé**: Choisissez le style et cliquez sur "Générer un résumé"
- **Mots-clés**: Cliquez sur "Extraire les mots-clés"
- **Q/R**: Posez une question sur le contenu et obtenez une réponse
- **Chapitres**: Divisez automatiquement le contenu en chapitres

### 4. Text-to-Speech

1. Accédez à l'onglet "Text to Audio"
2. Entrez ou collez le texte à convertir en audio
3. Choisissez le modèle et la voix
4. Cliquez sur "Générer l'audio"

## 📈 Performances

Les performances dépendent du matériel utilisé et des modèles sélectionnés:

- **Transcription**: 
  - Modèle `tiny`: ~32x temps réel (très rapide, moins précis)
  - Modèle `base`: ~16x temps réel (bon équilibre)
  - Modèle `large`: ~1x temps réel (plus lent, très précis)

- **Analyses GPT**:
  - Temps de réponse: 2-10 secondes selon la longueur du texte
  - Coût approximatif: ~$0.02 par analyse (GPT-3.5) / ~$0.20 (GPT-4)

- **Text-to-Speech**:
  - Temps de génération: ~5 secondes pour 200 mots
  - Coût approximatif: ~$0.015 par 1000 caractères (tts-1)

## 🤝 Contribution

Les contributions sont les bienvenues! Voici comment procéder:

1. Forkez le dépôt
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/amazing-feature`)
3. Committez vos changements (`git commit -m 'Add amazing feature'`)
4. Poussez vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

## 📜 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- [Streamlit](https://streamlit.io/) pour l'interface
- [Whisper](https://github.com/openai/whisper) pour la transcription
- [OpenAI](https://openai.com/) pour les API GPT et TTS
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) pour l'extraction YouTube

---

Développé avec ❤️ par [Votre Nom](https://github.com/username)
