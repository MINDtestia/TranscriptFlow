import streamlit as st

# Assure-toi que cette fonction est accessible depuis ce fichier
def toggle_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

# Fonction principale à intégrer dans ta page paramètres
def afficher_page_7():
    st.title("⚙️ Paramètres avancés")

    # Section générale
    st.header("🌐 Général")
    st.selectbox("Langue par défaut", ["français", "anglais"], key="default_language")
    if st.button("Changer mode clair/sombre"):
        toggle_mode()

    st.divider()

    # Section notifications
    st.header("🔔 Notifications")
    st.checkbox("Activer les notifications", key="enable_notifications")
    st.checkbox("Recevoir les notifications par email", key="email_notifications")
    st.checkbox("Recevoir les notifications push sur mobile", key="push_notifications")

    st.divider()

    # Section historique
    st.header("📜 Historique des actions")
    st.checkbox("Activer l'enregistrement de l'historique", key="enable_history", value=True)
    retention_period = st.slider("Durée de rétention des historiques (jours)", min_value=7, max_value=365, value=30)
    st.session_state.history_retention = retention_period

    if st.button("Effacer tout l'historique"):
        st.warning("Historique effacé !")
        st.session_state.history = []

    st.divider()

    # Section analytics
    st.header("📊 Analytics")
    st.checkbox("Activer les analytics", key="enable_analytics", value=True)

    st.divider()

    # Section utilisateurs
    st.header("👥 Comptes utilisateurs")
    st.checkbox("Autoriser la création de nouveaux utilisateurs", key="allow_user_creation", value=True)

    st.divider()

    # Section API & intégrations
    st.header("🔗 API & Intégrations")
    st.text_input("Clé API OpenAI", type="password", key="openai_api_key")
    st.checkbox("Connecter à Google Drive", key="google_drive_integration")
    st.checkbox("Connecter à Dropbox", key="dropbox_integration")

    if st.button("Sauvegarder tous les paramètres"):
        st.success("Tous les paramètres ont été sauvegardés avec succès !")


