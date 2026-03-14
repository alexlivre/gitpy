"""
Central module for ai-openai functionality.
"""
import os
from typing import Any, Dict

from openai import OpenAI


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter para OpenAI (GPT).
    """
    prompt = payload.get("prompt")
    system_inst = payload.get("system_instruction",
                              "You are a helpful assistant.")
    model = payload.get("model") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    max_tokens = payload.get("max_tokens", 500)
    temperature = payload.get("temperature", 0.3)

    # Injeta a Key via ENV (carregada pelo sec-keyring no brain)
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {"error": "AUTH_FAIL", "message": "OPENAI_API_KEY não encontrada."}

    try:
        with OpenAI(api_key=api_key) as client:
            is_gpt_5 = model.startswith("gpt-5")
        
        if is_gpt_5:
            # Integração específica para a API Responses da OpenAI (GPT-5) 
            combined_input = f"{system_inst}\n\n{prompt}"
            
            # Ajuste de payload específico para gpt-5
            kwargs = {
                "model": model,
                "input": combined_input,
                "max_output_tokens": max_tokens
            }
            
            # Gpt-5-mini e nano não suportam temperatura e top_p à menos que reasoning effort seja 'none'
            # Por padrão manteremos reasoning effort 'low' e verbosity default para código
            kwargs["reasoning"] = {"effort": "low"}
            kwargs["text"] = {"verbosity": "medium"}

            response = client.responses.create(**kwargs)
            content = response.output_text
            
            # O usage na nova API de responses
            # Dependendo da versão do wrapper, o acesso muda, mas vamos assumir o padrão retornado
            usage = getattr(response, "usage", None)
            tokens_used = usage.total_tokens if usage else 0

        else:
            # Fallback para chat.completions genérico (gpt-4o, etc)
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
            tokens_used = usage.total_tokens if usage else 0

        return {
            "text": content,
            "tokens_used": tokens_used,
            "model_used": model
        }

    except Exception as e:
        return {"error": "API_ERR", "message": str(e)}
