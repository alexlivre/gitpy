"""
Central module for ai-ollama functionality.
"""
from typing import Any, Dict

import requests


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter para Ollama (Local AI).
    Endpoint default: http://localhost:11434/api/generate
    """
    prompt = payload.get("prompt")
    system_inst = payload.get("system_instruction", "")
    model = payload.get("model", "llama3")

    url = "http://localhost:11434/api/generate"

    final_prompt = f"{system_inst}\n\n{prompt}" if system_inst else prompt

    data = {
        "model": model,
        "prompt": final_prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=data)
        if response.status_code != 200:
            return {"error": "API_ERR", "message": f"Ollama Error: {response.text}"}

        json_resp = response.json()

        return {
            "text": json_resp.get("response", ""),
            "tokens_used": json_resp.get("eval_count", 0),
            "model_used": model
        }

    except requests.exceptions.ConnectionError:
        return {"error": "API_ERR", "message": "Não foi possível conectar ao Ollama (localhost:11434)."}
    except Exception as e:
        return {"error": "API_ERR", "message": str(e)}
