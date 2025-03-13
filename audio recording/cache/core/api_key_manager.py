import streamlit as st
import os
import json
from typing import Optional, Dict, Any
import logging
from .error_handling import handle_error, ErrorType


class APIKeyManager:
    """
    Gestionnaire de clés API avec plusieurs options de stockage:
    1. Variables d'environnement
    2. Session Streamlit (temporaire)
    3. Fichier local chiffré (optionnel)
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialise le gestionnaire de clés API.

        Args:
            encryption_key: Clé de chiffrement pour le stockage local (optionnel)
        """
        self.encryption_key = encryption_key
        self._api_keys = {}
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Charge les clés API depuis les variables d'environnement."""
        env_keys = {
            "openai": os.getenv("OPENAI_API_KEY", ""),
            # Ajouter d'autres services si nécessaire
        }

        # Ne garder que les clés non vides
        self._api_keys = {k: v for k, v in env_keys.items() if v}

        # Log informatif (sans les valeurs des clés)
        if self._api_keys:
            logging.info(f"Clés API chargées depuis l'environnement: {', '.join(self._api_keys.keys())}")

    def get_key(self, service: str) -> str:
        """
        Récupère une clé API avec priorité:
        1. Session Streamlit
        2. Variables d'environnement

        Args:
            service: Nom du service (ex: 'openai')

        Returns:
            Clé API ou chaîne vide si non trouvée
        """
        # Vérifier d'abord dans session_state
        session_key = f"{service}_api_key"
        if session_key in st.session_state and st.session_state[session_key]:
            return st.session_state[session_key]

        # Sinon, vérifier dans les clés chargées depuis l'environnement
        return self._api_keys.get(service, "")

    def set_key(self, service: str, key: str) -> None:
        """
        Définit une clé API dans session_state.

        Args:
            service: Nom du service (ex: 'openai')
            key: Valeur de la clé API
        """
        session_key = f"{service}_api_key"
        st.session_state[session_key] = key

    def validate_key(self, service: str, key: Optional[str] = None) -> bool:
        """
        Valide une clé API avec une vérification basique.

        Args:
            service: Nom du service
            key: Clé à valider (ou utilise la clé stockée si None)

        Returns:
            True si la clé semble valide, False sinon
        """
        if key is None:
            key = self.get_key(service)

        if not key:
            return False

        # Vérifications spécifiques par service
        if service == "openai":
            # Vérification minimale pour OpenAI (commence par sk-)
            return key.startswith("sk-") and len(key) > 20

        # Par défaut, vérifie juste que la clé a une longueur significative
        return len(key) > 8

    def render_api_key_input(self, service: str, label: Optional[str] = None) -> None:
        """
        Affiche un champ de saisie pour une clé API dans l'interface Streamlit.

        Args:
            service: Nom du service
            label: Texte à afficher (ou généré automatiquement si None)
        """
        if label is None:
            label = f"Clé API {service.title()}"

        current_key = self.get_key(service)
        placeholder = "••••••••" if current_key else f"Entrez votre clé API {service}"

        # Affichage du champ de saisie
        new_key = st.text_input(
            label,
            type="password",
            value=current_key,
            placeholder=placeholder,
            key=f"input_{service}_api_key"
        )

        # Mise à jour si changée
        if new_key != current_key:
            self.set_key(service, new_key)

            # Validation basique
            if new_key and not self.validate_key(service, new_key):
                st.warning(f"Cette clé API {service} ne semble pas valide. Vérifiez le format.")


# Instance globale pour usage dans l'application
api_key_manager = APIKeyManager()