import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime, timedelta
import os
import logging

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


def get_usage_metrics():
    """
    Récupère les métriques d'utilisation.
    Utilise des données fictives pour l'exemple.
    Dans une application réelle, ces données viendraient d'une base de données.
    """
    # Dans une application réelle, on pourrait récupérer ces informations
    # depuis une base de données ou un service d'analytics

    # Pour cet exemple, on génère des données fictives
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


def afficher_page_1():
    st.title("🎛️ Dashboard")

    # Charger les données d'utilisation
    with st.spinner("Chargement des données..."):
        usage_data = get_usage_metrics()
        summary = calculate_summary_metrics(usage_data)

    # Carte des métriques principales
    st.subheader("📊 Activité des 7 derniers jours")

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
    chart_data['date'] = chart_data['date'].dt.strftime('%d/%m')

    # Sélection des métriques à afficher
    metrics_mapping = {
        'transcriptions': 'Transcriptions',
        'youtube_extractions': 'Extractions YouTube',
        'video_extractions': 'Extractions Vidéo',
        'tts_generations': 'Générations TTS'
    }

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

    # Simulation d'activités récentes (événements fictifs)
    today = datetime.now()
    recent_activities = [
        {
            'time': (today - timedelta(minutes=15)).strftime('%H:%M'),
            'action': 'Transcription',
            'details': 'interview_mars2023.mp4',
            'user': 'admin'
        },
        {
            'time': (today - timedelta(hours=2)).strftime('%H:%M'),
            'action': 'Extraction YouTube',
            'details': 'https://youtube.com/watch?v=xXxXxXx',
            'user': 'user1'
        },
        {
            'time': (today - timedelta(hours=4)).strftime('%H:%M'),
            'action': 'Text-to-Speech',
            'details': 'Génération de 345 mots',
            'user': 'admin'
        },
        {
            'time': (today - timedelta(hours=6)).strftime('%H:%M'),
            'action': 'Extraction vidéo',
            'details': 'conference_avril2023.mp4',
            'user': 'user1'
        }
    ]

    # Affichage des activités récentes
    activity_df = pd.DataFrame(recent_activities)
    st.dataframe(activity_df, use_container_width=True)

    # Statistiques globales
    st.subheader("🧮 Statistiques globales")

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