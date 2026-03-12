from vibe_core import kernel
import os
from typing import Dict, Any
from groq import AsyncGroq

async def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter para Groq (LPU Inference).
    """
    prompt = payload.get("prompt")
    system_inst = payload.get("system_instruction", "You are a helpful assistant.")
    model = payload.get("model", "meta-llama/llama-4-scout-17b-16e-instruct")
    max_tokens = payload.get("max_tokens", 2048)
    temperature = payload.get("temperature", 0.3)
    
    # Busca Chave via Keyring (Prioridade: ENV > OS Keyring)
    try:
        key_res = await kernel.run("security/sec-keyring", {
            "action": "get",
            "service": "groq_api_key"
        })
        api_key = key_res.get("value")
    except Exception:
        api_key = None
    
    if not api_key:
        return {"error": "AUTH_FAIL", "message": "GROQ_API_KEY não encontrada (Use .env ou 'rastro auth')."}

    try:
        client = AsyncGroq(api_key=api_key)
        
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_inst},
                {"role": "user", "content": prompt}
            ],
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        content = chat_completion.choices[0].message.content
        usage = chat_completion.usage
        
        return {
            "text": content,
            "tokens_used": usage.total_tokens if usage else 0,
            "model_used": model
        }

    except Exception as e:
        return {"error": "API_ERR", "message": f"Groq Error: {str(e)}"}
