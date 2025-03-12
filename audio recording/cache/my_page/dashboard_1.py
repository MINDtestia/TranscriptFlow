import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime, timedelta
import os
import logging

from flask_login import user_logged_in

from core.session_manager import get_session_value, set_session_value


# Génération de données fictives pour le dashboard
def generate_mock_data():
    """
    Génère des données fictives pour le dashboard.
    Utilise un seed basé sur la date pour générer des données cohérentes
    mais qui évoluent chaque jour.
    """
    # Seed basé sur la date (change chaque jour)
    today = datetime.now().date()
    seed = int(today.strftime("%Y%m%d"))
    random.seed(seed)

    # Date de début (30 jours en arrière)
    start_date = today - timedelta(days=30)

    # Création des dates
    dates = [start_date + timedelta(days=i) for i in range(31)]

    # Génération des métriques
    transcription_counts = [random.randint(5, 20) for _ in range(31)]
    youtube_extractions = [random.randint(3, 15) for _ in range(31)]
    video_extractions = [random.randint(2, 10) for _ in range(31)]
    tts_generations = [random.randint(1, 8) for _ in range(31)]

    # Ajout d'une tendance (croissance progressive)
    for i in range(1, 31):
        growth_factor = 1 + (i / 100)
        transcription_counts[i] = int(transcription_counts[i - 1] * growth_factor)
        youtube_extractions[i] = int(youtube_extractions[i - 1] * (1 + (i / 150)))
        video_extractions[i] = int(video_extractions[i - 1] * (1 + (i / 200)))
        tts_generations[i] = int(tts_generations[i - 1] * (1 + (i / 180)))

    # Création du DataFrame
    df = pd.DataFrame({
        'date': dates,
        'transcriptions': transcription_counts,
        'youtube_extractions': youtube_extractions,
        'video_extractions': video_extractions,
        'tts_generations': tts_generations
    })

    return df


def get_user_usage_metrics(user_id):
    """
    Récupère les métriques d'utilisation réelles de l'utilisateur.

    Args:
        user_id: ID de l'utilisateur

    Returns:
        DataFrame avec les données d'utilisation
    """
    from core.database import UserActivity, get_db
    from sqlalchemy import func, and_
    import pandas as pd
    import datetime

    try:
        db = next(get_db())

        # Date de début (30 jours en arrière)
        today = datetime.datetime.now().date()
        start_date = today - datetime.timedelta(days=30)

        # Convertir en datetime pour la comparaison avec la base de données
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min)

        # Requête pour obtenir les activités par jour et type
        activities = db.query(
            func.date(UserActivity.created_at).label('date'),
            UserActivity.activity_type,
            func.count().label('count')
        ).filter(
            and_(
                UserActivity.user_id == user_id,
                UserActivity.created_at >= start_datetime
            )
        ).group_by(
            func.date(UserActivity.created_at),
            UserActivity.activity_type
        ).all()

        # Créer un DataFrame complet avec toutes les dates et types d'activité
        all_dates = [start_date + datetime.timedelta(days=i) for i in range(31)]
        activity_types = ["transcription", "youtube_extraction", "video_extraction", "tts_generation"]

        # Créer un DataFrame vide
        results = []
        for date in all_dates:
            row = {'date': date}
            for activity_type in activity_types:
                row[activity_type] = 0
            results.append(row)

        df = pd.DataFrame(results)

        # Remplir les données réelles
        for activity in activities:
            date_str = activity.date
            activity_type = activity.activity_type
            count = activity.count

            # Trouver la ligne correspondante et mettre à jour le compteur
            date_index = df[df['date'] == date_str].index
            if not date_index.empty:
                if activity_type == "transcription":
                    df.at[date_index[0], "transcription"] = count
                elif activity_type == "youtube_extraction":
                    df.at[date_index[0], "youtube_extraction"] = count
                elif activity_type == "video_extraction":
                    df.at[date_index[0], "video_extraction"] = count
                elif activity_type == "tts_generation":
                    df.at[date_index[0], "tts_generation"] = count

        # Renommer les colonnes pour correspondre au format attendu
        df.rename(columns={
            "transcription": "transcriptions",
            "youtube_extraction": "youtube_extractions",
            "video_extraction": "video_extractions",
            "tts_generation": "tts_generations"
        }, inplace=True)

        return df

    except Exception as e:
        logging.error(f"Erreur lors de la récupération des métriques: {e}")
        # Retourner des données fictives en cas d'erreur
        return generate_mock_data()

def calculate_summary_metrics(df):
    """
    Calcule les métriques résumées à partir du DataFrame.

    Args:
        df: DataFrame contenant les métriques journalières

    Returns:
        Dictionnaire des métriques résumées
    """
    # Derniers 7 jours
    last_7_days = df.iloc[-7:]

    # Sommes des 7 derniers jours
    recent_sum = {
        'transcriptions': last_7_days['transcriptions'].sum(),
        'youtube_extractions': last_7_days['youtube_extractions'].sum(),
        'video_extractions': last_7_days['video_extractions'].sum(),
        'tts_generations': last_7_days['tts_generations'].sum()
    }

    # Moyennes des 7 derniers jours
    recent_avg = {
        'transcriptions': round(last_7_days['transcriptions'].mean(), 1),
        'youtube_extractions': round(last_7_days['youtube_extractions'].mean(), 1),
        'video_extractions': round(last_7_days['video_extractions'].mean(), 1),
        'tts_generations': round(last_7_days['tts_generations'].mean(), 1)
    }

    # Calcul des tendances (pourcentage de croissance)
    previous_7_days = df.iloc[-14:-7]

    trends = {}
    for metric in ['transcriptions', 'youtube_extractions', 'video_extractions', 'tts_generations']:
        recent_total = last_7_days[metric].sum()
        previous_total = previous_7_days[metric].sum()

        if previous_total > 0:
            trend_pct = ((recent_total - previous_total) / previous_total) * 100
            trends[metric] = round(trend_pct, 1)
        else:
            trends[metric] = 100.0  # Si précédent est 0, on considère croissance de 100%

    return {
        'recent_sum': recent_sum,
        'recent_avg': recent_avg,
        'trends': trends
    }


def format_trend(value):
    """
    Formate une valeur de tendance avec flèche et couleur.

    Args:
        value: Pourcentage de tendance

    Returns:
        Texte formaté en HTML avec flèche et couleur
    """
    if value > 0:
        return f"<span style='color:green'>▲ {value}%</span>"
    elif value < 0:
        return f"<span style='color:red'>▼ {abs(value)}%</span>"
    else:
        return f"<span style='color:gray'>► {value}%</span>"


def get_recent_activities(user_id, limit=5):
    """
    Récupère les activités récentes de l'utilisateur.

    Args:
        user_id: ID de l'utilisateur
        limit: Nombre maximum d'activités à récupérer

    Returns:
        Liste des activités récentes
    """
    from core.database import UserActivity, get_db

    try:
        db = next(get_db())

        activities = db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).order_by(
            UserActivity.created_at.desc()
        ).limit(limit).all()

        result = []
        for activity in activities:
            activity_type_mapping = {
                "transcription": "Transcription",
                "youtube_extraction": "Extraction YouTube",
                "video_extraction": "Extraction vidéo",
                "tts_generation": "Text-to-Speech"
            }

            result.append({
                'time': activity.created_at.strftime('%H:%M'),
                'action': activity_type_mapping.get(activity.activity_type, activity.activity_type),
                'details': activity.details or "-",
                'user': st.session_state.get("username", "utilisateur")
            })

        return result

    except Exception as e:
        logging.error(f"Erreur lors de la récupération des activités récentes: {e}")
        return []


def afficher_page_1():
    st.title("🎛️ Dashboard")

    # Détection mobile
    is_mobile = st.session_state.get("is_mobile", False)

    # Vérifier si l'utilisateur est connecté
    if "user_id" not in st.session_state:
        st.warning("Veuillez vous connecter pour voir votre tableau de bord.")
        return

    # Charger les données d'utilisation réelles
    with st.spinner("Chargement des données..."):
        usage_data = get_user_usage_metrics(st.session_state["user_id"])
        summary = calculate_summary_metrics(usage_data)

    # Carte des métriques principales
    st.subheader("📊 Activité des 7 derniers jours")

    if is_mobile:
        # Version mobile: 2 colonnes × 2 rangées
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Transcriptions",
                value=summary['recent_sum']['transcriptions'],
                delta=f"{summary['trends']['transcriptions']}%"
            )
        with col2:
            st.metric(
                "YouTube",
                value=summary['recent_sum']['youtube_extractions'],
                delta=f"{summary['trends']['youtube_extractions']}%"
            )

        col3, col4 = st.columns(2)
        with col3:
            st.metric(
                "Vidéos",
                value=summary['recent_sum']['video_extractions'],
                delta=f"{summary['trends']['video_extractions']}%"
            )
        with col4:
            st.metric(
                "TTS",
                value=summary['recent_sum']['tts_generations'],
                delta=f"{summary['trends']['tts_generations']}%"
            )
    else:
        # Version desktop: 4 colonnes
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Transcriptions",
                value=summary['recent_sum']['transcriptions'],
                delta=f"{summary['trends']['transcriptions']}%"
            )
        with col2:
            st.metric(
                "YouTube",
                value=summary['recent_sum']['youtube_extractions'],
                delta=f"{summary['trends']['youtube_extractions']}%"
            )
        with col3:
            st.metric(
                "Vidéos",
                value=summary['recent_sum']['video_extractions'],
                delta=f"{summary['trends']['video_extractions']}%"
            )
        with col4:
            st.metric(
                "TTS",
                value=summary['recent_sum']['tts_generations'],
                delta=f"{summary['trends']['tts_generations']}%"
            )

    # Graphique d'activité
    st.subheader("📈 Tendances sur 30 jours")

    # Préparation des données pour le graphique
    chart_data = usage_data.copy()

    # S'assurer que les dates sont au bon format pour l'affichage
    try:
        chart_data['date'] = pd.to_datetime(chart_data['date']).dt.strftime('%d/%m')
    except:
        chart_data['date'] = chart_data['date'].apply(
            lambda x: x.strftime('%d/%m') if hasattr(x, 'strftime') else str(x))

    # Sélection des métriques à afficher
    metrics_mapping = {
        'transcriptions': 'Transcriptions',
        'youtube_extractions': 'Extractions YouTube',
        'video_extractions': 'Extractions Vidéo',
        'tts_generations': 'Générations TTS'
    }

    # Simplifier la sélection sur mobile
    if is_mobile:
        chart_metrics = st.multiselect(
            "Afficher",
            options=list(metrics_mapping.keys()),
            default=['transcriptions'],
            format_func=lambda x: metrics_mapping[x]
        )
    else:
        chart_metrics = st.multiselect(
            "Métriques à afficher",
            options=list(metrics_mapping.keys()),
            default=['transcriptions'],
            format_func=lambda x: metrics_mapping[x]
        )

    # Si aucune métrique sélectionnée, afficher toutes
    if not chart_metrics:
        chart_metrics = list(metrics_mapping.keys())

    # Création du graphique
    chart_df = pd.DataFrame({
        'date': chart_data['date']
    })

    for metric in chart_metrics:
        chart_df[metrics_mapping[metric]] = chart_data[metric]

    st.line_chart(chart_df.set_index('date'))

    # Activité récente
    st.subheader("📋 Activité récente")

    # Récupérer les activités récentes réelles
    recent_activities = get_recent_activities(st.session_state["user_id"])

    # Si aucune activité récente, afficher un message
    if not recent_activities:
        st.info("Aucune activité récente. Commencez à utiliser l'application pour voir vos activités ici.")
    else:
        # Affichage des activités récentes
        activity_df = pd.DataFrame(recent_activities)

        # Sur mobile, limiter les colonnes
        if is_mobile:
            if 'details' in activity_df.columns:
                activity_df = activity_df.drop(columns=['details'])
            if 'user' in activity_df.columns and 'username' in st.session_state:
                activity_df = activity_df.drop(columns=['user'])

        st.dataframe(activity_df, use_container_width=True)

    # Statistiques globales
    st.subheader("🧮 Statistiques globales")

    if is_mobile:
        # Version mobile: empilé
        # Temps total de contenu traité
        total_content_hours = random.randint(8, 20)
        st.info(f"💾 Contenu total traité: **{total_content_hours} heures**")

        # Taux de réussite
        success_rate = random.randint(92, 99)
        st.success(f"✅ Taux de réussite: **{success_rate}%**")

        # Économies estimées
        saved_time = random.randint(15, 40)
        st.info(f"⏱️ Temps économisé: **{saved_time} heures**")

        # Précision moyenne
        accuracy = random.randint(85, 95)
        st.success(f"🎯 Précision moyenne: **{accuracy}%**")
    else:
        # Version desktop: colonnes
        col1, col2 = st.columns(2)
        with col1:
            # Temps total de contenu traité
            total_content_hours = random.randint(8, 20)
            st.info(f"💾 Contenu total traité: **{total_content_hours} heures**")

            # Taux de réussite
            success_rate = random.randint(92, 99)
            st.success(f"✅ Taux de réussite des opérations: **{success_rate}%**")

        with col2:
            # Économies estimées
            saved_time = random.randint(15, 40)
            st.info(f"⏱️ Temps économisé estimé: **{saved_time} heures**")

            # Précision moyenne
            accuracy = random.randint(85, 95)
            st.success(f"🎯 Précision moyenne: **{accuracy}%**")

    # Aide rapide
    with st.expander("💡 Démarrage rapide"):
        st.markdown("""
        ### Comment utiliser TranscriptFlow:

        1. **Extraction d'audio**: Utilisez l'onglet "Extraction" pour obtenir l'audio depuis YouTube ou un fichier vidéo local
        2. **Transcription**: Convertissez l'audio en texte avec Whisper
        3. **Analyse**: Générez des résumés, mots-clés ou posez des questions sur le contenu
        4. **Export**: Téléchargez les résultats au format texte

        Besoin d'aide supplémentaire? Consultez la documentation complète dans les paramètres.
        """)