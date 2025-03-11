import streamlit as st
import openai
import tempfile
import os

def text_to_speech_chatgpt(text: str, api_key: str, model: str, voice: str):
    try:
        openai.api_key = api_key
        with tempfile.TemporaryDirectory() as tmpdir:
            speech_file_path = os.path.join(tmpdir, "speech.mp3")

            response = openai.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            response.stream_to_file(speech_file_path)

            with open(speech_file_path, "rb") as f:
                audio_data = f.read()
        return audio_data

    except Exception as e:
        return f"Erreur lors de l'appel à GPT TTS: {str(e)}"

def afficher_page_5():
    st.title("Génération Audio (Text-to-Speech) - ChatGPT TTS")

    if "tts_audio_data" not in st.session_state:
        st.session_state.tts_audio_data = None

    text_input = st.text_area("Entrez votre texte à convertir en audio", "")
    openai_api_key = st.text_input("Clé API OpenAI (pour TTS)", type="password")
    model_choice = st.selectbox("Choisissez le modèle TTS", ["tts-1", "tts-1-hd"])
    chatgpt_voice = st.selectbox(
        "Choisissez la voix ChatGPT",
        ["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"]
    )

    if st.button("Générer l'audio"):
        if not text_input.strip():
            st.warning("Veuillez entrer un texte.")
            return
        if not openai_api_key.strip():
            st.warning("Veuillez saisir votre clé API OpenAI.")
            return

        audio_data = text_to_speech_chatgpt(text_input, openai_api_key, model_choice, chatgpt_voice)

        if isinstance(audio_data, str) and audio_data.startswith("Erreur"):
            st.error(audio_data)
            st.session_state.tts_audio_data = None
        elif not audio_data:
            st.error("Impossible de générer l'audio (résultat vide).")
            st.session_state.tts_audio_data = None
        else:
            st.session_state.tts_audio_data = audio_data

    if st.session_state.tts_audio_data:
        st.success("Audio généré avec succès !")
        st.audio(st.session_state.tts_audio_data, format="audio/mp3")

        downloaded = st.download_button(
            label="Télécharger l'audio",
            data=st.session_state.tts_audio_data,
            file_name="tts_output.mp3",
            mime="audio/mp3"
        )

        # Si l'utilisateur télécharge, on efface l'audio
        if downloaded:
            st.session_state.tts_audio_data = None
            st.experimental_set_query_params(_reload="1")
            # Pas de st.experimental_rerun(), la modif des query params suffit
