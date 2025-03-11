import streamlit as st
import logging
import tempfile
import os
from typing import Optional, Dict, Any, List, Tuple
import time

from core.transcription import transcribe_or_translate_locally
from core.gpt_processor import summarize_text, extract_keywords, ask_question_about_text
from core.utils import create_chapters_from_segments, export_text_file
from core.error_handling import handle_error, ErrorType, safe_execute
from core.session_manager import get_session_value, set_session_value
from core.api_key_manager import api_key_manager

# Types personnalisés pour la clarté
SegmentType = Dict[str, Any]
TranscriptionResult = Dict[str, Any]


# Fonctions de transcription avec cache
@st.cache_data(show_spinner=False, ttl=3600)
def cached_transcribe(
        file_path: str,
        whisper_model: str,
        translate: bool
) -> TranscriptionResult:
    """
    Cache le résultat de la transcription pour éviter de refaire le travail.

    Args:
        file_path: Chemin du fichier audio
        whisper_model: Modèle Whisper à utiliser
        translate: Si True, traduit plutôt que transcrire

    Returns:
        Résultat de la transcription
    """
    return transcribe_or_translate_locally(file_path, whisper_model, translate)


def process_transcription(
        audio_data: bytes,
        whisper_model: str,
        translate: bool = False
) -> Tuple[bool, str]:
    """
    Traite la transcription d'un fichier audio avec une barre de progression.

    Args:
        audio_data: Contenu du fichier audio en bytes
        whisper_model: Modèle Whisper à utiliser
        translate: Si True, traduit plutôt que transcrire

    Returns:
        (succès, message)
    """
    if not audio_data:
        return False, "Aucun fichier audio fourni."

    try:
        # Créer la barre de progression
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Préparation du fichier...")

        # Étape 1: Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(audio_data)

        progress_bar.progress(0.1)
        status_text.text("Fichier prêt. Chargement du modèle Whisper...")

        # Étape 2: Lancer la transcription
        def progress_callback(progress: float, message: str):
            progress_bar.progress(0.1 + progress * 0.8)  # 10% à 90%
            status_text.text(message)

        result = cached_transcribe(tmp_path, whisper_model, translate)

        # Étape 3: Traiter le résultat
        progress_bar.progress(0.9)
        status_text.text("Finalisation...")

        # Nettoyage du fichier temporaire
        try:
            os.remove(tmp_path)
        except:
            logging.warning(f"Impossible de supprimer le fichier temporaire: {tmp_path}")

        # Vérifier les erreurs
        if error := result.get("error"):
            progress_bar.progress(1.0)
            status_text.text("Erreur lors de la transcription.")
            return False, error

        # Stockage des résultats dans la session
        set_session_value("transcribed_text", result["text"])
        set_session_value("segments", result["segments"])
        set_session_value("detected_language", result.get("language", ""))

        # Terminer la barre de progression
        progress_bar.progress(1.0)
        status_text.text("Transcription terminée!")
        time.sleep(0.5)  # Laisser le temps de voir le message
        status_text.empty()

        return True, "Transcription terminée avec succès!"

    except Exception as e:
        return False, handle_error(e, ErrorType.PROCESSING_ERROR,
                                   "Erreur lors de la transcription.")


# Fonctions pour les analyses GPT
def run_gpt_summary(
        api_key: str,
        style: str = "bullet",
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7
) -> bool:
    """
    Exécute l'analyse de résumé GPT sur le texte transcrit.

    Args:
        api_key: Clé API OpenAI
        style: Style de résumé ("bullet", "concise", "detailed")
        model: Modèle GPT à utiliser
        temperature: Température pour la génération

    Returns:
        True si succès, False sinon
    """
    text = get_session_value("transcribed_text", "")
    if not text:
        st.warning("Aucun texte à résumer. Veuillez d'abord faire une transcription.")
        return False

    if not api_key:
        st.warning("Clé API OpenAI requise pour cette fonctionnalité.")
        return False

    try:
        with st.spinner("Génération du résumé en cours..."):
            summary = summarize_text(
                text=text,
                api_key=api_key,
                gpt_model=model,
                temperature=temperature,
                style=style
            )

        set_session_value("summary_result", summary)
        return True

    except Exception as e:
        handle_error(e, ErrorType.API_ERROR,
                     "Erreur lors de la génération du résumé.")
        return False


def run_gpt_keywords(api_key: str, model: str = "gpt-3.5-turbo") -> bool:
    """
    Extrait les mots-clés du texte transcrit via GPT.

    Args:
        api_key: Clé API OpenAI
        model: Modèle GPT à utiliser

    Returns:
        True si succès, False sinon
    """
    text = get_session_value("transcribed_text", "")
    if not text:
        st.warning("Aucun texte pour extraire des mots-clés. Veuillez d'abord faire une transcription.")
        return False

    if not api_key:
        st.warning("Clé API OpenAI requise pour cette fonctionnalité.")
        return False

    try:
        with st.spinner("Extraction des mots-clés en cours..."):
            keywords = extract_keywords(text, api_key, model=model)

        set_session_value("keywords_result", keywords)
        return True

    except Exception as e:
        handle_error(e, ErrorType.API_ERROR,
                     "Erreur lors de l'extraction des mots-clés.")
        return False


def run_gpt_question(question: str, api_key: str, model: str = "gpt-3.5-turbo") -> bool:
    """
    Pose une question au texte transcrit via GPT.

    Args:
        question: Question à poser
        api_key: Clé API OpenAI
        model: Modèle GPT à utiliser

    Returns:
        True si succès, False sinon
    """
    text = get_session_value("transcribed_text", "")
    if not text:
        st.warning("Aucun texte pour poser une question. Veuillez d'abord faire une transcription.")
        return False

    if not question.strip():
        st.warning("Veuillez saisir une question.")
        return False

    if not api_key:
        st.warning("Clé API OpenAI requise pour cette fonctionnalité.")
        return False

    try:
        with st.spinner("Traitement de la question en cours..."):
            answer = ask_question_about_text(text, question, api_key, model=model)

        set_session_value("answer_result", answer)
        return True

    except Exception as e:
        handle_error(e, ErrorType.API_ERROR,
                     "Erreur lors du traitement de la question.")
        return False


def create_text_chapters(chunk_duration: float = 60.0) -> bool:
    """
    Crée des chapitres à partir des segments de transcription.

    Args:
        chunk_duration: Durée en secondes pour chaque chapitre

    Returns:
        True si succès, False sinon
    """
    segments = get_session_value("segments", [])
    if not segments:
        st.warning("Aucun segment disponible. Veuillez faire une transcription avant.")
        return False

    try:
        with st.spinner("Création des chapitres en cours..."):
            chapters = create_chapters_from_segments(segments, chunk_duration=chunk_duration)
            chapter_text = "\n".join(chapters)

        set_session_value("chapters_result", chapter_text)
        return True

    except Exception as e:
        handle_error(e, ErrorType.PROCESSING_ERROR,
                     "Erreur lors de la création des chapitres.")
        return False


def export_text_to_file(text: str, filename: str) -> bool:
    """
    Exporte du texte vers un fichier et propose le téléchargement.

    Args:
        text: Texte à exporter
        filename: Nom du fichier

    Returns:
        True si succès, False sinon
    """
    if not text.strip():
        st.warning("Aucun texte à exporter.")
        return False

    try:
        export_folder = get_session_value("export_folder", "")
        path = export_text_file(text, export_folder, filename)

        # Propose le téléchargement direct
        st.download_button(
            label="Télécharger le fichier",
            data=text.encode("utf-8"),
            file_name=filename,
            mime="text/plain"
        )

        return True

    except Exception as e:
        handle_error(e, ErrorType.FILE_ERROR,
                     "Erreur lors de l'export du fichier.")
        return False


def afficher_page_4():
    st.title("Transcription / Traduction")

    # Récupérer la clé API OpenAI
    openai_api_key = api_key_manager.get_key("openai")

    # Interface principale
    tabs = st.tabs(["Transcription", "Résumé", "Mots-clés", "Questions/Réponses", "Chapitres"])

    # Tab 1: Transcription
    with tabs[0]:
        col1, col2 = st.columns([1, 1])

        with col1:
            # Options de transcription
            st.subheader("Options")

            whisper_model = st.selectbox(
                "Modèle Whisper",
                ["tiny", "base", "small", "medium", "large"],
                help="Plus le modèle est grand, plus la transcription est précise mais lente."
            )

            translate_checkbox = st.checkbox(
                "Traduire en anglais (au lieu de transcrire)",
                value=False,
                help="Traduit l'audio en anglais quelle que soit la langue d'origine."
            )

            # Source audio
            st.subheader("Source audio")

            # Option 1: Fichier depuis session (précédemment téléchargé)
            audio_data = get_session_value("audio_bytes_for_transcription")
            if audio_data:
                st.success("Fichier audio chargé depuis l'extraction précédente.")
                st.audio(audio_data, format="audio/wav")

            # Option 2: Upload direct
            audio_file = st.file_uploader(
                "Ou chargez un fichier audio",
                type=["wav", "mp3", "m4a", "ogg"],
                help="Formats supportés: WAV, MP3, M4A, OGG"
            )

            if audio_file:
                audio_data = audio_file.read()
                st.audio(audio_data, format=f"audio/{audio_file.type.split('/')[1]}")

            # Bouton de transcription
            transcribe_button = st.button(
                "Lancer la transcription",
                disabled=audio_data is None and audio_file is None,
                use_container_width=True
            )

            if transcribe_button:
                data_to_transcribe = audio_data if audio_data else audio_file.read()
                success, message = process_transcription(
                    data_to_transcribe,
                    whisper_model,
                    translate_checkbox
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

        with col2:
            # Affichage des résultats
            st.subheader("Texte transcrit")

            transcribed_text = get_session_value("transcribed_text", "")
            detected_language = get_session_value("detected_language", "")

            if detected_language:
                st.info(f"Langue détectée: {detected_language}")

            text_area = st.text_area(
                "Transcription",
                value=transcribed_text,
                height=350,
                key="transcription_textarea"
            )

            # Si modifié, mettre à jour
            if text_area != transcribed_text:
                set_session_value("transcribed_text", text_area)

            # Options d'export
            if transcribed_text:
                st.subheader("Exporter")
                export_folder = st.text_input(
                    "Dossier d'export (optionnel)",
                    placeholder="Ex: /home/user/documents"
                )
                set_session_value("export_folder", export_folder)

                if st.button("Exporter la transcription (.txt)"):
                    if export_text_to_file(transcribed_text, "transcription.txt"):
                        st.success("Transcription exportée avec succès!")

    # Tab 2: Résumé
    with tabs[1]:
        st.subheader("Résumé du texte")

        # Options
        col1, col2 = st.columns([3, 1])

        with col1:
            api_key_manager.render_api_key_input("openai", "Clé API OpenAI")

            summary_style = st.selectbox(
                "Style de résumé",
                options=["bullet", "concise", "detailed"],
                format_func=lambda x: {
                    "bullet": "Liste à puces",
                    "concise": "Résumé concis",
                    "detailed": "Résumé détaillé"
                }[x],
                help="Choisissez le format du résumé généré."
            )

        with col2:
            st.write("")  # Espacement
            st.write("")  # Espacement

            gpt_model = st.selectbox(
                "Modèle GPT",
                ["gpt-3.5-turbo", "gpt-4"],
                help="GPT-4 est plus précis mais plus coûteux."
            )

            temperature = st.slider(
                "Température",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Contrôle la créativité du modèle. Valeurs basses = plus factuel."
            )

        # Bouton de génération
        if st.button("Générer un résumé", use_container_width=True):
            if run_gpt_summary(
                    api_key_manager.get_key("openai"),
                    style=summary_style,
                    model=gpt_model,
                    temperature=temperature
            ):
                st.success("Résumé généré avec succès!")

        # Affichage du résultat
        summary_result = get_session_value("summary_result", "")
        if summary_result:
            st.markdown("### Résumé")
            st.markdown(summary_result)

            # Export
            if st.button("Exporter le résumé (.txt)"):
                if export_text_to_file(summary_result, "resume.txt"):
                    st.success("Résumé exporté avec succès!")

    # Tab 3: Mots-clés
    with tabs[2]:
        st.subheader("Extraction de mots-clés")

        # Options
        col1, col2 = st.columns([3, 1])

        with col1:
            api_key_manager.render_api_key_input("openai", "Clé API OpenAI")

        with col2:
            keywords_model = st.selectbox(
                "Modèle GPT",
                ["gpt-3.5-turbo", "gpt-4"],
                key="keywords_model",
                help="GPT-4 peut identifier des mots-clés plus précis."
            )

        # Bouton de génération
        if st.button("Extraire les mots-clés", use_container_width=True):
            if run_gpt_keywords(
                    api_key_manager.get_key("openai"),
                    model=keywords_model
            ):
                st.success("Mots-clés extraits avec succès!")

        # Affichage du résultat
        keywords_result = get_session_value("keywords_result", "")
        if keywords_result:
            st.markdown("### Mots-clés")

            # Formatage pour un affichage plus agréable
            keywords_list = [kw.strip() for kw in keywords_result.split(",")]

            # Afficher sous forme de puces ou de badges
            col1, col2, col3 = st.columns([1, 1, 1])
            for i, keyword in enumerate(keywords_list):
                if i % 3 == 0:
                    col1.markdown(f"- {keyword}")
                elif i % 3 == 1:
                    col2.markdown(f"- {keyword}")
                else:
                    col3.markdown(f"- {keyword}")

            # Export
            if st.button("Exporter les mots-clés (.txt)"):
                if export_text_to_file(keywords_result, "mots-cles.txt"):
                    st.success("Mots-clés exportés avec succès!")

    # Tab 4: Questions/Réponses
    with tabs[3]:
        st.subheader("Questions & Réponses")

        # Options
        api_key_manager.render_api_key_input("openai", "Clé API OpenAI")

        qr_model = st.selectbox(
            "Modèle GPT",
            ["gpt-3.5-turbo", "gpt-4"],
            key="qr_model",
            help="GPT-4 peut fournir des réponses plus précises pour les questions complexes."
        )

        # Zone de question
        question = st.text_input(
            "Posez une question sur le contenu transcrit",
            placeholder="Ex: Quel est le sujet principal abordé?",
            key="question_input"
        )

        # Bouton d'envoi
        if st.button("Poser la question", use_container_width=True, disabled=not question.strip()):
            if run_gpt_question(
                    question,
                    api_key_manager.get_key("openai"),
                    model=qr_model
            ):
                st.success("Question traitée avec succès!")

        # Affichage du résultat
        answer_result = get_session_value("answer_result", "")
        if answer_result:
            st.markdown("### Réponse")
            st.markdown(answer_result)

            # Export
            if st.button("Exporter la réponse (.txt)"):
                formatted_answer = f"Q: {question}\n\nR: {answer_result}"
                if export_text_to_file(formatted_answer, "reponse.txt"):
                    st.success("Réponse exportée avec succès!")

    # Tab 5: Chapitres
    with tabs[4]:
        st.subheader("Chapitres & Segmentation")

        # Options
        chunk_duration = st.slider(
            "Durée par chapitre (secondes)",
            min_value=30,
            max_value=300,
            value=60,
            step=10,
            help="Définit la durée de chaque chapitre en secondes."
        )

        # Bouton de génération
        if st.button("Générer les chapitres", use_container_width=True):
            if create_text_chapters(chunk_duration):
                st.success("Chapitres générés avec succès!")

        # Affichage du résultat
        chapters_result = get_session_value("chapters_result", "")
        if chapters_result:
            st.markdown("### Liste des chapitres")
            st.text_area("Chapitres", value=chapters_result, height=300)

            # Export
            if st.button("Exporter les chapitres (.txt)"):
                if export_text_to_file(chapters_result, "chapitres.txt"):
                    st.success("Chapitres exportés avec succès!")