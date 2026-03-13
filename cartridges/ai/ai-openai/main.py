import os
from typing import Dict, Any
from openai import OpenAI

def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter para OpenAI (GPT).
    """
    prompt = payload.get("prompt")
    system_inst = payload.get("system_instruction", "You are a helpful assistant.")
    model = payload.get("model") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    max_tokens = payload.get("max_tokens", 500)
    temperature = payload.get("temperature", 0.3)
    
    # Injeta a Key via ENV (carregada pelo sec-keyring no brain)
    api_key = os.getenv("OPENAI_API_KEY") 
    
    if not api_key:
        return {"error": "AUTH_FAIL", "message": "OPENAI_API_KEY não encontrada."}

    client = OpenAI(api_key=api_key)

    try:
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
