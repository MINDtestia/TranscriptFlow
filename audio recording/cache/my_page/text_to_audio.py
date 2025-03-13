import streamlit as st
import tempfile
import os
import time
import logging
from typing import Optional, Dict, Any, Tuple

from openai import OpenAI
from core.error_handling import handle_error, ErrorType
from core.session_manager import get_session_value, set_session_value
from core.api_key_manager import api_key_manager

# Constantes
VOICE_OPTIONS = {
    "alloy": "Neutre et équilibré",
    "echo": "Grave et posé",
    "fable": "Britannique et narratif",
    "onyx": "Professionnel et sérieux",
    "nova": "Féminin et chaleureux",
    "shimmer": "Enthousiaste et positif"
}

MODEL_OPTIONS = {
    "tts-1": "Standard (Rapide)",
    "tts-1-hd": "Haute Définition (Meilleure qualité)"
}


def generate_audio_from_text(
        text: str,
        api_key: str,
        model: str = "tts-1",
        voice: str = "alloy"
) -> Tuple[bool, Optional[bytes], str]:
    """
    Génère un fichier audio à partir de texte via l'API OpenAI TTS.

    Args:
        text: Texte à convertir en audio
        api_key: Clé API OpenAI
        model: Modèle TTS à utiliser
        voice: Voix à utiliser

    Returns:
        (succès, données audio en bytes, message)
    """
    if not text.strip():
        return False, None, "Le texte est vide. Veuillez saisir du texte à convertir."

    if not api_key:
        return False, None, "Clé API OpenAI manquante. Veuillez configurer votre clé API."

    try:
        # Estimation du coût (approximative)
        char_count = len(text)
        word_count = len(text.split())
        estimated_cost = (char_count / 1000) * (0.015 if model == "tts-1" else 0.030)

        # Log à des fins d'audit
        logging.info(f"TTS request: {word_count} words, model={model}, voice={voice}")

        # Création du client OpenAI
        client = OpenAI(api_key=api_key)

        # Limitation de la taille du texte (max ~4096 tokens / ~3000 mots)
        max_chars = 12000
        if len(text) > max_chars:
            return False, None, f"Le texte est trop long ({len(text)} caractères). " \
                                f"La limite est de {max_chars} caractères."

        # Création d'un fichier temporaire pour stocker l'audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        # Appel à l'API
        with st.spinner(f"Génération audio en cours... ({word_count} mots)"):
            start_time = time.time()

            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )

            # Enregistrer dans le fichier temporaire
            response.stream_to_file(tmp_path)

            # Lire le contenu en bytes
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()

            # Nettoyer le fichier temporaire
            try:
                os.unlink(tmp_path)
            except:
                pass

            elapsed_time = time.time() - start_time

        return True, audio_bytes, f"Audio généré avec succès en {elapsed_time:.1f} secondes. " \
                                  f"Coût estimé: ${estimated_cost:.4f}"

    except Exception as e:
        error_msg = handle_error(e, ErrorType.API_ERROR,
                                 "Erreur lors de la génération audio. Vérifiez votre clé API et réessayez.")
        return False, None, error_msg


def afficher_page_5():
    st.title("Génération Audio (Text-to-Speech)")

    # Détection mobile
    is_mobile = st.session_state.get("is_mobile", False)

    # Organisation de l'interface adaptative
    if is_mobile:
        # Version mobile: empilée
        # Zone de saisie du texte
        default_text = get_session_value("tts_input_text", "")

        # Si une transcription est disponible, proposer de l'utiliser
        transcription = get_session_value("transcribed_text", "")
        if transcription and not default_text:
            if st.button("Utiliser le texte transcrit", type="secondary", use_container_width=True):
                default_text = transcription
                set_session_value("tts_input_text", default_text)

        text_input = st.text_area(
            "Texte à convertir en audio",
            value=default_text,
            height=200,
            placeholder="Saisissez le texte à convertir en audio...",
        )

        # Sauvegarder le texte dans la session
        if text_input != default_text:
            set_session_value("tts_input_text", text_input)

        # Calcul de la longueur du texte
        word_count = len(text_input.split()) if text_input else 0
        char_count = len(text_input) if text_input else 0
        st.caption(f"{word_count} mots | {char_count} caractères")

        # Options de configuration
        st.subheader("Configuration")

        # Clé API
        api_key_manager.render_api_key_input("openai", "Clé API OpenAI")

        # Configuration simplifiée pour mobile
        col1, col2 = st.columns(2)

        with col1:
            # Modèle TTS
            model_choice = st.selectbox(
                "Modèle",
                options=list(MODEL_OPTIONS.keys()),
                format_func=lambda x: "Standard" if x == "tts-1" else "HD"
            )

        with col2:
            # Voix simplifiée
            voice_choice = st.selectbox(
                "Voix",
                options=list(VOICE_OPTIONS.keys()),
                format_func=lambda x: x.capitalize()
            )

        # Estimation du coût
        if text_input:
            cost_rate = 0.015 if model_choice == "tts-1" else 0.030
            estimated_cost = (char_count / 1000) * cost_rate
            st.caption(f"Coût estimé: ${estimated_cost:.4f}")

    else:
        # Version desktop: colonnes
        col1, col2 = st.columns([2, 1])

        with col1:
            # Zone de saisie du texte
            default_text = get_session_value("tts_input_text", "")

            # Si une transcription est disponible, proposer de l'utiliser
            transcription = get_session_value("transcribed_text", "")
            if transcription and not default_text:
                if st.button("Utiliser le texte transcrit", type="secondary"):
                    default_text = transcription
                    set_session_value("tts_input_text", default_text)

            text_input = st.text_area(
                "Texte à convertir en audio",
                value=default_text,
                height=250,
                placeholder="Saisissez le texte que vous souhaitez convertir en audio...",
                help="Maximum ~3000 mots (limite API OpenAI)"
            )

            # Sauvegarder le texte dans la session
            if text_input != default_text:
                set_session_value("tts_input_text", text_input)

            # Calcul de la longueur du texte
            word_count = len(text_input.split()) if text_input else 0
            char_count = len(text_input) if text_input else 0

            # Affichage des statistiques
            st.caption(f"{word_count} mots | {char_count} caractères")

        with col2:
            # Options de configuration
            st.subheader("Configuration")

            # Clé API
            api_key_manager.render_api_key_input("openai", "Clé API OpenAI")

            # Modèle TTS
            model_choice = st.selectbox(
                "Modèle",
                options=list(MODEL_OPTIONS.keys()),
                format_func=lambda x: MODEL_OPTIONS[x],
                help="tts-1-hd offre une meilleure qualité mais coûte plus cher."
            )

            # Voix
            voice_choice = st.selectbox(
                "Voix",
                options=list(VOICE_OPTIONS.keys()),
                format_func=lambda x: f"{x} - {VOICE_OPTIONS[x]}",
                help="Différentes voix ont différentes caractéristiques tonales."
            )

            # Estimation du coût
            if text_input:
                cost_rate = 0.015 if model_choice == "tts-1" else 0.030  # $/1K caractères
                estimated_cost = (char_count / 1000) * cost_rate
                st.caption(f"Coût estimé: ${estimated_cost:.4f}")

    # Bouton de génération
    generate_button = st.button(
        "Générer l'audio",
        disabled=not text_input.strip() or not api_key_manager.get_key("openai"),
        use_container_width=True
    )

    # Conteneur pour le résultat
    result_container = st.container()

    # Traitement
    if generate_button:
        success, audio_data, message = generate_audio_from_text(
            text_input,
            api_key_manager.get_key("openai"),
            model=model_choice,
            voice=voice_choice
        )

        if success:
            set_session_value("tts_audio_data", audio_data)
            st.success(message)
        else:
            st.error(message)

    # Affichage du résultat audio
    audio_data = get_session_value("tts_audio_data")
    if audio_data:
        with result_container:
            st.subheader("Audio généré")

            # Lecture de l'audio
            st.audio(audio_data, format="audio/mp3")

            # Options de téléchargement
            filename = f"audio_{voice_choice}_{int(time.time())}.mp3"

            if is_mobile:
                # Version mobile: boutons empilés
                download_button = st.download_button(
                    label="Télécharger l'audio",
                    data=audio_data,
                    file_name=filename,
                    mime="audio/mp3",
                    use_container_width=True
                )

                # Si téléchargé, proposition d'effacement
                if download_button and st.button("Effacer l'audio", key="clear_audio", use_container_width=True):
                    set_session_value("tts_audio_data", None)
                    st.rerun()
            else:
                # Version desktop: boutons côte à côte
                download_button = st.download_button(
                    label="Télécharger l'audio",
                    data=audio_data,
                    file_name=filename,
                    mime="audio/mp3",
                    use_container_width=True
                )

                # Si téléchargé, proposition d'effacement
                if download_button:
                    if st.button("Effacer l'audio généré", key="clear_audio"):
                        set_session_value("tts_audio_data", None)
                        st.rerun()

            # Détails techniques (masqués sur mobile)
            if not is_mobile:
                with st.expander("Détails techniques"):
                    st.markdown(f"""
                    **Fichier généré:**
                    - Format: MP3
                    - Taille: {len(audio_data) / 1024:.1f} KB
                    - Modèle: {model_choice}
                    - Voix: {voice_choice}
                    """)