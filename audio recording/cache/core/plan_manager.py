from .database import Subscription, User, Transcription, get_db
from sqlalchemy import func
import datetime
import streamlit as st

# Définition des plans
PLANS = {
    "free": {
        "name": "Gratuit",
        "transcription_minutes": 30,  # Minutes par mois
        "max_file_size_mb": 50,  # Taille maximale de fichier en MB
        "gpt_requests": 20,  # Requêtes GPT par mois
        "models": ["tiny", "base"],  # Modèles Whisper autorisés
        "tts_characters": 10000,  # Caractères TTS par mois
        "concurrent_tasks": 1  # Tâches simultanées
    },
    "standard": {
        "name": "Standard",
        "transcription_minutes": 150,
        "max_file_size_mb": 200,
        "gpt_requests": 100,
        "models": ["tiny", "base", "small", "medium"],
        "tts_characters": 50000,
        "concurrent_tasks": 2
    },
    "premium": {
        "name": "Premium",
        "transcription_minutes": 500,
        "max_file_size_mb": 500,
        "gpt_requests": 400,
        "models": ["tiny", "base", "small", "medium", "large"],
        "tts_characters": 200000,
        "concurrent_tasks": 5
    }
}


class PlanManager:
    """Gestionnaire des plans et quotas utilisateurs"""

    @staticmethod
    def get_user_plan(user_id):
        """Récupère le plan de l'utilisateur"""
        db = next(get_db())

        # Récupérer l'abonnement actif
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.active == True
        ).first()

        # Si pas d'abonnement, plan gratuit par défaut
        if not subscription:
            return PLANS["free"]

        # Si plan inconnu, plan gratuit par défaut
        if subscription.plan not in PLANS:
            return PLANS["free"]

        return PLANS[subscription.plan]

    @staticmethod
    def check_model_access(user_id, model):
        """Vérifie si l'utilisateur a accès au modèle demandé"""
        plan = PlanManager.get_user_plan(user_id)
        return model in plan["models"]

    @staticmethod
    def check_file_size_limit(user_id, file_size_mb):
        """Vérifie si la taille du fichier est dans les limites du plan"""
        plan = PlanManager.get_user_plan(user_id)
        return file_size_mb <= plan["max_file_size_mb"]

    @staticmethod
    def get_transcription_usage(user_id):
        """Récupère l'utilisation de minutes de transcription du mois en cours"""
        db = next(get_db())

        # Début du mois courant
        start_of_month = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculer l'utilisation (minutos)
        usage = db.query(func.count(Transcription.id)).filter(
            Transcription.user_id == user_id,
            Transcription.created_at >= start_of_month
        ).scalar()

        return usage or 0

    @staticmethod
    def check_transcription_quota(user_id):
        """Vérifie si l'utilisateur a encore du quota de transcription"""
        plan = PlanManager.get_user_plan(user_id)
        usage = PlanManager.get_transcription_usage(user_id)

        return usage < plan["transcription_minutes"]

    @staticmethod
    def display_user_usage(user_id):
        """Affiche l'utilisation de l'utilisateur (pour Streamlit)"""
        plan = PlanManager.get_user_plan(user_id)
        transcription_usage = PlanManager.get_transcription_usage(user_id)

        st.sidebar.markdown("### Votre forfait")
        st.sidebar.info(f"Plan: **{plan['name']}**")

        # Barre de progression pour l'utilisation
        progress = min(100, int((transcription_usage / plan["transcription_minutes"]) * 100))
        st.sidebar.progress(progress / 100)
        st.sidebar.caption(f"Transcription: {transcription_usage}/{plan['transcription_minutes']} minutes")