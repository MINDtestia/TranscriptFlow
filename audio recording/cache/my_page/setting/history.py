import streamlit as st
import pandas as pd

def show_history():
    st.title("📜 Historique des actions")

    # Charger les données historiques (à adapter selon ton stockage)
    if "history" not in st.session_state:
        st.session_state.history = pd.DataFrame(columns=["Date", "Action", "Utilisateur"])

    st.dataframe(st.session_state.history)

    # Effacer l'historique
    if st.button("🗑️ Effacer l'historique"):
        st.session_state.history = pd.DataFrame(columns=["Date", "Action", "Utilisateur"])
