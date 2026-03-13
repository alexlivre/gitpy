"""
Central module for ai-gemini functionality.
"""
import os
from typing import Any, Dict

import google.generativeai as genai


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter para Google Gemini.
    """
    prompt = payload.get("prompt")
    system_inst = payload.get("system_instruction")
    model_name = payload.get("model") or os.getenv(
        "GEMINI_MODEL") or "gemini-pro"

    # Configura API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "AUTH_FAIL", "message": "GEMINI_API_KEY não encontrada."}

    genai.configure(api_key=api_key)

    try:
        model = genai.GenerativeModel(model_name)

        # Combinar system + prompt pois Gemini Pro 1.0 usa prompt único muitas vezes,
        # mas 1.5 aceita system. Vamos simplificar concatenando se system existir.
        final_prompt = prompt
        if system_inst:
            final_prompt = f"System: {system_inst}\n\nUser: {prompt}"

        response = model.generate_content(final_prompt)

        return {
            "text": response.text,
            "tokens_used": 0,  # Gemini API nem sempre retorna tokens fácil
            "model_used": model_name
        }

    except Exception as e:
        return {"error": "API_ERR", "message": str(e)}
