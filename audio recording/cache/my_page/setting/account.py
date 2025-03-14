import streamlit as st

def show_user_accounts():
    st.title("👤 Comptes utilisateurs")

    user = st.text_input("Nom utilisateur")
    pwd = st.text_input("Mot de passe", type="password")

    if st.button("Créer compte"):
        # Logique de création à implémenter (base de données)
        st.success(f"Compte {user} créé.")
