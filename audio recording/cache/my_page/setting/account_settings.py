
import streamlit as st
from core.auth_manager import change_password, reset_password_request
from core.session_manager import get_session_value


def afficher_page_compte():
    st.title("🔑 Paramètres du compte")

    if not st.session_state.get("authenticated", False):
        st.warning("Vous devez être connecté pour accéder à cette page.")
        return

    user_id = st.session_state.get("user_id")
    username = st.session_state.get("username", "")

    st.info(f"Connecté en tant que: **{username}**")

    with st.form("change_password_form"):
        st.subheader("Changer votre mot de passe")

        current_password = st.text_input("Mot de passe actuel", type="password")
        new_password = st.text_input("Nouveau mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le nouveau mot de passe", type="password")

        submit = st.form_submit_button("Mettre à jour le mot de passe")

        if submit:
            if not current_password:
                st.error("Veuillez entrer votre mot de passe actuel.")
            elif not new_password:
                st.error("Veuillez entrer un nouveau mot de passe.")
            elif new_password != confirm_password:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                if change_password(user_id, current_password, new_password):
                    st.success("Mot de passe modifié avec succès!")
                else:
                    st.error("Échec de la modification. Vérifiez votre mot de passe actuel.")