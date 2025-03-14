import streamlit as st

def show_integrations():
    st.title("🔗 Intégrations externes")

    if st.button("Connecter à Google Drive"):
        st.write("Connexion à Drive à implémenter avec OAuth2.")
