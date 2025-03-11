# core/error_handling.py
import logging
import streamlit as st
from typing import Optional, Any, Callable


class ErrorType:
    """Constantes d'erreurs pour standardiser les messages"""
    API_ERROR = "api_error"
    FILE_ERROR = "file_error"
    INPUT_ERROR = "input_error"
    PROCESSING_ERROR = "processing_error"
    AUTHENTICATION_ERROR = "auth_error"


# Messages d'erreur utilisateur en français
ERROR_MESSAGES = {
    ErrorType.API_ERROR: "Une erreur est survenue lors de la communication avec l'API. Vérifiez votre clé API et réessayez.",
    ErrorType.FILE_ERROR: "Une erreur est survenue lors du traitement du fichier. Vérifiez le format et la taille du fichier.",
    ErrorType.INPUT_ERROR: "Les données saisies sont incorrectes ou manquantes. Veuillez vérifier vos entrées.",
    ErrorType.PROCESSING_ERROR: "Une erreur s'est produite pendant le traitement. Veuillez réessayer.",
    ErrorType.AUTHENTICATION_ERROR: "Erreur d'authentification. Veuillez vous reconnecter.",
}


def handle_error(error: Exception, error_type: str, custom_message: Optional[str] = None) -> str:
    """
    Gère une erreur de manière standardisée.

    Args:
        error: L'exception capturée
        error_type: Type d'erreur (utiliser la classe ErrorType)
        custom_message: Message personnalisé optionnel

    Returns:
        Message d'erreur formaté
    """
    # Log technique complet pour les développeurs
    logging.error(f"{error_type}: {str(error)}")

    # Message utilisateur
    user_message = custom_message or ERROR_MESSAGES.get(error_type, "Une erreur s'est produite.")

    # Affichage Streamlit si dans un contexte Streamlit
    try:
        st.error(user_message)
    except:
        pass  # Ignore si pas dans un contexte Streamlit

    return user_message


def safe_execute(func: Callable, error_type: str = ErrorType.PROCESSING_ERROR,
                 custom_message: Optional[str] = None, default_return: Any = None, **kwargs) -> Any:
    """
    Exécute une fonction de manière sécurisée et gère les erreurs.

    Args:
        func: Fonction à exécuter
        error_type: Type d'erreur en cas d'échec
        custom_message: Message personnalisé en cas d'erreur
        default_return: Valeur à retourner en cas d'erreur
        **kwargs: Arguments à passer à la fonction

    Returns:
        Résultat de la fonction ou default_return en cas d'erreur
    """
    try:
        return func(**kwargs)
    except Exception as e:
        handle_error(e, error_type, custom_message)
        return default_return