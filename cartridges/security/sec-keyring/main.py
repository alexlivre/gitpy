"""
Central module for sec-keyring functionality.
"""
import os
from typing import Any, Dict

import keyring
# Importa configuração para garantir que o ambiente esteja carregado
import env_config

SERVICE_NAME = "gitpy-cli"


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gerenciador de Credenciais Seguro (Keyring).
    Action: get | store | delete
    Service: openai_key | gemini_key | github_token
    """
    action = payload.get("action")
    account = payload.get("service")
    value = payload.get("value")
    cid = payload.get("cid", "unknown")

    if not action or not account:
        return {"success": False, "error": "MISSING_ARGS"}

    try:
        if action == "store":
            if not value:
                return {"success": False, "error": "MISSING_VALUE"}
            keyring.set_password(SERVICE_NAME, account, value)
            return {"success": True, "message": "Token armazenado com segurança."}

        elif action == "get":
            # 1. Tenta Variável de Ambiente (Prioridade Máxima)
            # Mapeamento de nomes de serviço para provedores
            service_to_provider = {
                "openrouter": "openrouter",
                "groq": "groq",
                "openai": "openai",
                "gemini": "gemini",
                "ollama": "ollama",
                "github": "github",
                # Compatibilidade com nomes antigos
                "openai_key": "openai",
                "gemini_key": "gemini",
                "github_token": "github",
                "openrouter_api_key": "openrouter",
                "groq_api_key": "groq",
                "openai_api_key": "openai",
                "gemini_api_key": "gemini"
            }
            
            provider = service_to_provider.get(account.lower(), account.lower())
            env_val = env_config.API_KEYS.get(provider, "")
            
            if env_val:
                return {"success": True, "value": env_val, "source": "env_var"}

            # 2. Tenta Keyring do Sistema
            token = keyring.get_password(SERVICE_NAME, account)
            if token:
                return {"success": True, "value": token, "source": "keyring"}

            return {"success": False, "error": "NOT_FOUND", "source": "none"}

        elif action == "delete":
            try:
                keyring.delete_password(SERVICE_NAME, account)
                return {"success": True, "message": "Token removido."}
            except keyring.errors.PasswordDeleteError:
                return {"success": False, "error": "NOT_FOUND", "message": "Nada a deletar."}

    except Exception as e:
        return {"success": False, "error": "KEYRING_ERR", "message": str(e)}
