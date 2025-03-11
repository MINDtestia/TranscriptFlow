# core/gpt_processor.py

from openai import OpenAI
from .utils import chunk_text

def gpt_request(prompt: str, api_key: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
    """
    Envoie un prompt à l'API OpenAI GPT (chat.completions).
    """
    if not api_key:
        return "Erreur: Clé API OpenAI manquante."

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erreur lors de l'appel à GPT: {str(e)}"


def summarize_text(
    text: str,
    api_key: str,
    gpt_model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    style: str = "bullet"
) -> str:
    """
    Résume un texte via GPT, avec support du 'style' (bullet, concise, detailed).
    Gère le 'chunking' si le texte est trop long.
    """
    if not text:
        return "Erreur: Le texte à résumer est vide."

    chunks = chunk_text(text, max_chars=2500)
    partial_summaries = []

    for chunk in chunks:
        if style == "bullet":
            user_prompt = (
                "Résume le texte suivant de manière concise, sous forme de liste à puces :\n\n"
                f"{chunk}"
            )
        elif style == "concise":
            user_prompt = (
                "Fais un résumé très concis (quelques phrases seulement) du texte suivant :\n\n"
                f"{chunk}"
            )
        else:  # "detailed"
            user_prompt = (
                "Fais un résumé détaillé du texte suivant :\n\n"
                f"{chunk}"
            )

        part_summary = gpt_request(user_prompt, api_key, model=gpt_model, temperature=temperature)
        partial_summaries.append(part_summary)

    if len(partial_summaries) == 1:
        return partial_summaries[0]
    else:
        combined_text = "\n\n".join(partial_summaries)
        combine_prompt = (
            "Voici plusieurs résumés partiels. Combine-les en un seul résumé "
            f"({style} si possible) :\n\n{combined_text}"
        )
        return gpt_request(combine_prompt, api_key, model=gpt_model, temperature=temperature)


def extract_keywords(text: str, api_key: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Extrait des mots-clés (keywords) du texte via GPT.
    """
    if not text:
        return "Erreur: Le texte est vide."

    prompt = (
        "Extrait les mots-clés les plus importants du texte ci-dessous, "
        "en français si le texte est en français, en anglais sinon. "
        "Retourne-les sous forme de liste, séparés par des virgules.\n\n"
        f"{text}"
    )
    return gpt_request(prompt, api_key, model=model)


def ask_question_about_text(text: str, question: str, api_key: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Pose une question (Q/R) sur le texte transcrit et renvoie la réponse via GPT.
    """
    if not text:
        return "Erreur: Le texte est vide, impossible de répondre."
    if not question.strip():
        return "Erreur: La question est vide."

    prompt = (
        f"Voici un texte :\n\n{text}\n\n"
        f"Question : {question}\n\n"
        "Réponds de manière concise et précise, en te basant uniquement sur le texte."
    )
    return gpt_request(prompt, api_key, model=model)
