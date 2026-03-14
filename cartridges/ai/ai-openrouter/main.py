"""
Central module for ai-openrouter functionality.
"""
import os
from typing import Any, Dict

from openai import OpenAI


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter para OpenRouter (suporta chamadas padrão via compatiable API OpenAI).
    """
    prompt = payload.get("prompt")
    system_inst = payload.get("system_instruction",
                              "You are a helpful assistant.")
    model = payload.get("model") or os.getenv("OPENROUTER_MODEL") or "meta-llama/llama-4-scout"
    max_tokens = payload.get("max_tokens", 500)
    temperature = payload.get("temperature", 0.3)

    # Injeta a Key via ENV (carregada pelo sec-keyring no brain)
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return {"error": "AUTH_FAIL", "message": "OPENROUTER_API_KEY não encontrada."}

    try:
        # Inicializa o Client da OpenAI apontando para o OpenRouter
        with OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/alexlivre/gitpy",
                "X-Title": "GitPy",
            }
        ) as client:
            response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_inst},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )

        content = response.choices[0].message.content
        usage = response.usage

        return {
            "text": content,
            "tokens_used": usage.total_tokens if usage else 0,
            "model_used": response.model
        }

    except Exception as e:
        return {"error": "API_ERR", "message": str(e)}
