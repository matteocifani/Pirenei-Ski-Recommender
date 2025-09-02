from __future__ import annotations

import os
from typing import Tuple

import openai
import streamlit as st

from .config import (
    OPENROUTER_API_KEY_ENV,
    OPENROUTER_BASE_URL,
    DEFAULT_LLM_MODEL,
)


def _finalize_text(content: str) -> str:
    """Ensure the output ends with a complete sentence.

    - Trims trailing whitespace
    - If no sentence-ending punctuation is present at the end, trims back to the last '.', '!' or '?' when possible
    - Otherwise appends a '.'
    """
    if not content:
        return content
    text = str(content).strip()
    if not text:
        return text
    enders = ('.', '!', '?', '…')
    if text[-1] in enders:
        return text
    # Try to trim to last sentence ender
    last_period = text.rfind('.')
    last_excl = text.rfind('!')
    last_q = text.rfind('?')
    last_ellipsis = text.rfind('…')
    last = max(last_period, last_excl, last_q, last_ellipsis)
    if last != -1:
        return text[: last + 1].strip()
    # If we can't find any, ensure we end with a period
    # Remove trailing commas/colons/semicolons
    while text and text[-1] in ',;:':
        text = text[:-1]
    if not text or text[-1] in enders:
        return text
    return text + '.'


def _get_client() -> openai.OpenAI:
    # Usa i secrets di Streamlit Cloud o variabili d'ambiente
    api_key = st.secrets.get(OPENROUTER_API_KEY_ENV) or os.getenv(OPENROUTER_API_KEY_ENV)
    if not api_key:
        raise ValueError(f"API key non trovata. Configura {OPENROUTER_API_KEY_ENV} nei secrets di Streamlit Cloud o come variabile d'ambiente.")
    
    # Aggiunge header consigliati da OpenRouter per migliorare l'affidabilità
    return openai.OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "http://127.0.0.1:8510",
            "X-Title": "SkiRecommenderV2",
        },
    )


def generate_overview(prompt: str, max_tokens: int = 220) -> Tuple[str, dict]:
    client = _get_client()
    try:
        # Nota: per OpenRouter alcune integrazioni richiedono header extra; con openai>=1.30 e base_url impostato dovrebbe bastare.
        response = client.chat.completions.create(
            model=DEFAULT_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sei un assistente tecnico esperto di dati sciistici. "
                        "Rispondi in italiano, tono informativo, senza markdown o emoji. "
                        "NON troncare mai le frasi: se stai per raggiungere il limite, completa la frase e termina con un punto."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            top_p=0.5,
            max_tokens=max_tokens,
        )
        content = (getattr(response.choices[0].message, 'content', None) or "").strip()
        # Alcuni provider possono restituire 'text' invece di 'message.content'
        if not content:
            content = (getattr(response.choices[0], 'text', None) or "").strip()
        if content:
            final = _finalize_text(content)
            return final, {
                "prompt_tokens": getattr(response.usage, 'prompt_tokens', None),
                "completion_tokens": getattr(response.usage, 'completion_tokens', None),
                "model": DEFAULT_LLM_MODEL,
            }
        # Niente contenuto: lascia gestire il fallback a livello UI
        return ("", {"model": DEFAULT_LLM_MODEL, "note": "empty_response"})
    except Exception as exc:
        # Se superi il rate-limit del modello free corrente prova altri free supportati
        err_text = str(exc)
        retry_models = [
            "mistralai/mistral-nemo:free",
            "qwen/qwen2.5-32b-instruct:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "openai/gpt-oss-20b:free",
            "microsoft/phi-3.5-mini:free",
            "google/gemma-2-9b-it:free",
        ]
        # metti il modello corrente all'inizio e poi gli altri
        if DEFAULT_LLM_MODEL in retry_models:
            retry_models.remove(DEFAULT_LLM_MODEL)
        models_to_try = [DEFAULT_LLM_MODEL] + retry_models

        if "Rate limit exceeded" in err_text or "429" in err_text:
            last_exc = err_text
            for model_name in models_to_try:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "Sei un assistente tecnico esperto di dati sciistici. "
                                    "Rispondi in italiano, tono informativo, senza markdown o emoji. "
                                    "NON troncare mai le frasi: se stai per raggiungere il limite, completa la frase e termina con un punto."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.2,
                        top_p=0.5,
                        max_tokens=max_tokens,
                    )
                    content = (getattr(response.choices[0].message, 'content', None) or "").strip()
                    if not content:
                        content = (getattr(response.choices[0], 'text', None) or "").strip()
                    if content:
                        final = _finalize_text(content)
                        return final, {
                            "prompt_tokens": getattr(response.usage, 'prompt_tokens', None),
                            "completion_tokens": getattr(response.usage, 'completion_tokens', None),
                            "model": model_name,
                        }
                except Exception as exc2:
                    last_exc = str(exc2)
                    continue
            return ("", {"error": last_exc, "model": DEFAULT_LLM_MODEL})
        # ogni altro errore lo riportiamo su
        return ("", {"error": err_text, "model": DEFAULT_LLM_MODEL})

