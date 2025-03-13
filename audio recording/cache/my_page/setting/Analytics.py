import streamlit as st
import matplotlib.pyplot as plt

def show_analytics():
    st.title("📊 Analytics")

    # Exemple de statistiques (à adapter selon tes données)
    stats = {
        'Transcriptions': 120,
        'Extraits vidéo': 90,
        'Utilisateurs actifs': 12
    }

    fig, ax = plt.subplots()
    ax.bar(stats.keys(), stats.values())
    st.pyplot(fig)
