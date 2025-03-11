import streamlit as st
import logging
import tempfile
from core.transcription import transcribe_or_translate_locally
from core.gpt_processor import summarize_text, extract_keywords, ask_question_about_text
from core.utils import create_chapters_from_segments, export_text_file

# Gestion de la cache
@st.cache_data(show_spinner=False)
def cached_transcribe(file_path, whisper_model, translate):
    return transcribe_or_translate_locally(file_path, whisper_model, translate)

def do_transcription(uploaded_file, whisper_model, translate=False):
    """
    Désormais, 'uploaded_file' est un objet Streamlit UploadedFile,
    et non plus un chemin de fichier.
    """
    if not uploaded_file:
        st.warning("Veuillez fournir un fichier audio valide.")
        return

    try:
        progress_bar = st.progress(0)
        progress_bar.progress(10, text="Préparation...")

        # 1) Écrire le contenu du fichier téléversé dans un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(uploaded_file.read())
            tmp.flush()
            temp_filename = tmp.name  # Chemin du fichier temporaire

        # 2) Transcrire avec Whisper via la fonction cachée
        with st.spinner("Transcription/Traduction en cours..."):
            result = cached_transcribe(temp_filename, whisper_model, translate)

        progress_bar.progress(80, text="Post-traitement...")

        error = result["error"]
        text = result["text"]
        segments = result["segments"]

        if error:
            st.error(error)
            logging.error(error)
        else:
            st.success("Transcription terminée !")
            st.session_state.transcribed_text = text
            st.session_state.segments = segments

        progress_bar.progress(100)

    except Exception as e:
        logging.error(f"Erreur lors de la transcription : {e}")
        st.error(f"Erreur : {e}")

def do_summarize_text():
    full_text = st.session_state.transcribed_text
    if not full_text:
        st.warning("Aucun texte à résumer.")
        return

    api_key = st.session_state.openai_api_key
    gpt_model = st.session_state.get("gpt_model_choice", "gpt-3.5-turbo")
    style = st.session_state.get("summary_style", "bullet")
    temp = st.session_state.get("summary_temp", 0.7)

    try:
        with st.spinner("Génération du résumé..."):
            summary = summarize_text(
                text=full_text,
                api_key=api_key,
                gpt_model=gpt_model,
                temperature=temp,
                style=style
            )
        st.session_state.summary_result = summary
        st.success("Résumé généré avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors du résumé : {e}")
        st.error(f"Erreur : {e}")

def do_extract_keywords_gpt():
    full_text = st.session_state.transcribed_text
    if not full_text:
        st.warning("Aucun texte à analyser.")
        return
    api_key = st.session_state.openai_api_key
    gpt_model = st.session_state.get("gpt_model_choice", "gpt-3.5-turbo")

    try:
        with st.spinner("Extraction des mots-clés..."):
            keywords = extract_keywords(full_text, api_key, model=gpt_model)
        st.session_state.keywords_result = keywords
        st.success("Mots-clés extraits avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des mots-clés : {e}")
        st.error(f"Erreur : {e}")

def do_ask_question_gpt(question: str):
    full_text = st.session_state.transcribed_text
    if not full_text:
        st.warning("Veuillez d'abord faire une transcription.")
        return
    if not question.strip():
        st.warning("Veuillez saisir une question.")
        return
    api_key = st.session_state.openai_api_key
    gpt_model = st.session_state.get("gpt_model_choice", "gpt-3.5-turbo")

    try:
        with st.spinner("Envoi de la question à GPT..."):
            answer = ask_question_about_text(full_text, question, api_key, model=gpt_model)
        st.session_state.answer_result = answer
        st.success("Réponse générée.")
    except Exception as e:
        logging.error(f"Erreur lors de la question/réponse : {e}")
        st.error(f"Erreur : {e}")

def do_create_chapters():
    segments = st.session_state.segments
    chunk_duration = st.session_state.get("chunk_duration", 60)
    if not segments:
        st.warning("Aucun segment disponible. Veuillez faire une transcription avant.")
        return
    try:
        with st.spinner("Création des chapitres..."):
            chapters = create_chapters_from_segments(segments, chunk_duration=chunk_duration)
        st.session_state.chapters_result = "\n".join(chapters)
        st.success("Chapitres créés avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de la création de chapitres : {e}")
        st.error(f"Erreur : {e}")

def do_export_text(text_to_export, filename):
    folder = st.session_state.get("export_folder", "")
    if not text_to_export.strip():
        st.warning("Aucun texte à enregistrer.")
        return
    try:
        path = export_text_file(text_to_export, folder, filename)
        st.success(f"Fichier enregistré : {path}")
        # Proposer le téléchargement direct via un bouton
        st.download_button(
            label="Télécharger le fichier",
            data=text_to_export.encode("utf-8"),
            file_name=filename,
            mime="text/plain"
        )
    except Exception as e:
        logging.error(f"Erreur lors de l'export : {e}")
        st.error(f"Erreur : {e}")

def afficher_page_4():
    st.title("Transcription / Traduction")
    col_left, col_right = st.columns(2)

    with col_left:
        st.session_state.openai_api_key = st.text_input(
            "Clé API OpenAI (pour résumé, Q/R, etc.)",
            type="password",
            value=st.session_state.openai_api_key
        )
        whisper_model = st.selectbox(
            "Modèle Whisper",
            ["tiny", "base", "small", "medium", "large"]
        )
        translate_checkbox = st.checkbox("Traduire (EN) au lieu de transcrire", value=False)
        audio_path = st.file_uploader("Choisissez un fichier audio", type=["mp3", "wav"])#st.text_input("Chemin du fichier audio", placeholder="Ex: /tmp/ma_video.wav")

        if st.button("Transcrire / Traduire (Whisper)"):
            do_transcription(audio_path, whisper_model, translate_checkbox)

    with col_right:
        st.text_area(
            "Transcription / Traduction",
            value=st.session_state.transcribed_text,
            height=300
        )

    st.markdown("---")
    st.subheader("Actions GPT")

    st.session_state["gpt_model_choice"] = st.selectbox(
        "Modèle GPT", ["gpt-3.5-turbo", "gpt-4"], index=0
    )

    # Résumé
    with st.expander("Résumé du texte"):
        st.session_state["summary_style"] = st.selectbox(
            "Style de résumé", ["bullet", "concise", "detailed"], index=0
        )
        st.session_state["summary_temp"] = st.slider("Température GPT", 0.0, 1.0, 0.7)
        if st.button("Résumer le texte"):
            do_summarize_text()
        st.text_area("Résumé", value=st.session_state.summary_result, height=150)
        if st.button("Télécharger le résumé sous .txt"):
            do_export_text(st.session_state.summary_result, "summary.txt")

    # Mots-clés
    with st.expander("Extraction de mots-clés"):
        if st.button("Extraire les mots-clés"):
            do_extract_keywords_gpt()
        st.text_area("Mots-clés", value=st.session_state.keywords_result, height=100)
        if st.button("Télécharger les mots-clés sous .txt"):
            do_export_text(st.session_state.keywords_result, "keywords.txt")

    # Q/R
    with st.expander("Questions / Réponses"):
        question_input = st.text_input("Votre question sur le texte")
        if st.button("Poser la question"):
            do_ask_question_gpt(question_input)
        st.text_area("Réponse", value=st.session_state.answer_result, height=100)
        if st.button("Télécharger la réponse sous .txt"):
            do_export_text(st.session_state.answer_result, "answer.txt")

    # Chapitres
    with st.expander("Chapitres (division du texte)"):
        st.session_state["chunk_duration"] = st.slider("Durée par chapitre (secondes)", 30, 300, 60, 10)
        if st.button("Créer des chapitres"):
            do_create_chapters()
        st.text_area("Chapitres estimés", value=st.session_state.chapters_result, height=150)
        if st.button("Télécharger les chapitres sous .txt"):
            do_export_text(st.session_state.chapters_result, "chapters.txt")

    # Export de la transcription
    with st.expander("Exporter la transcription"):
        st.session_state["export_folder"] = st.text_input(
            "Dossier pour sauvegarder le .txt",
            placeholder="Ex: /home/user/docs"
        )
        if st.button("Enregistrer la transcription"):
            do_export_text(st.session_state.transcribed_text, "transcription.txt")