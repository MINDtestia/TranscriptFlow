import streamlit as st

def show_admin():
    st.title("🔧 Admin Panel")

    with st.expander("🗝️ Gestion des clés API"):
        openai_key = st.text_input("Clé API OpenAI", type="password")
        if st.button("Sauvegarder"):
            st.session_state.openai_api_key = openai_key
            st.success("Clé API sauvegardée")

    with st.expander("⚙️ Logs & Erreurs"):
        st.write("Aucun problème détecté.")  # À compléter avec logs réels
