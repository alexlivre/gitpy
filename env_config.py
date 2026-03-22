"""
Gerenciamento centralizado de variáveis de ambiente do GitPy.
Garante que o .env seja carregado consistentemente em todos os módulos.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Carrega o .env imediatamente ao importar o módulo
_app_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_app_dir, ".env")
load_dotenv(_env_path)

def get_env_var(key: str, default: str = "") -> str:
    """
    Obtém uma variável de ambiente de forma segura, com sanitização.
    
    Args:
        key: Nome da variável de ambiente
        default: Valor padrão se a variável não existir
        
    Returns:
        Valor da variável sanitizado (sem comentários, sem espaços extras)
    """
    raw_value = os.getenv(key, default)
    if raw_value is None:
        return default
    
    # Remove comentários e espaços extras
    clean_value = raw_value.split("#")[0].strip()
    return clean_value if clean_value else default

def get_commit_language() -> str:
    """Obtém o idioma para mensagens de commit."""
    return get_env_var("COMMIT_LANGUAGE", "en").lower()

def get_interface_language() -> str:
    """Obtém o idioma da interface."""
    return get_env_var("LANGUAGE", "en").lower()

def get_ai_provider() -> str:
    """Obtém o provedor de IA padrão."""
    provider = get_env_var("AI_PROVIDER", "auto").lower()
    valid_providers = ["auto", "groq", "openai", "gemini", "ollama", "openrouter"]
    return provider if provider in valid_providers else "auto"

def get_model_for_provider(provider: str) -> str:
    """Obtém o modelo padrão para um provedor específico."""
    model_key = f"{provider.upper()}_MODEL"
    return get_env_var(model_key, "")

def get_api_key(provider: str) -> str:
    """Obtém a chave de API para um provedor específico."""
    key_key = f"{provider.upper()}_API_KEY"
    return get_env_var(key_key, "")

def get_github_token() -> str:
    """Obtém o token do GitHub."""
    return get_env_var("GITHUB_TOKEN", "")

# Variáveis globais para acesso rápido (carregadas uma vez)
COMMIT_LANGUAGE = get_commit_language()
INTERFACE_LANGUAGE = get_interface_language()
AI_PROVIDER = get_ai_provider()

# Dicionário de modelos
AI_MODELS = {
    "groq": get_model_for_provider("groq"),
    "openai": get_model_for_provider("openai"),
    "gemini": get_model_for_provider("gemini"),
    "openrouter": get_model_for_provider("openrouter"),
    "ollama": get_model_for_provider("ollama"),
}

# Dicionário de chaves de API
API_KEYS = {
    "groq": get_api_key("groq"),
    "openai": get_api_key("openai"),
    "gemini": get_api_key("gemini"),
    "openrouter": get_api_key("openrouter"),
    "ollama": get_api_key("ollama"),
}

# GitHub Token
GITHUB_TOKEN = get_github_token()

def print_env_status() -> None:
    """Imprime o status das variáveis de ambiente para debug."""
    print("=== GitPy Environment Status ===")
    print(f"COMMIT_LANGUAGE: {COMMIT_LANGUAGE}")
    print(f"INTERFACE_LANGUAGE: {INTERFACE_LANGUAGE}")
    print(f"AI_PROVIDER: {AI_PROVIDER}")
    print("AI_MODELS:")
    for provider, model in AI_MODELS.items():
        status = "✓" if model else "✗"
        print(f"  {provider}: {status} ({model or 'not set'})")
    print("API_KEYS:")
    for provider, key in API_KEYS.items():
        status = "✓" if key else "✗"
        masked_key = f"{key[:8]}..." if key and len(key) > 8 else "not set"
        print(f"  {provider}: {status} ({masked_key})")
    print(f"GITHUB_TOKEN: {'✓' if GITHUB_TOKEN else '✗'}")
    print("=" * 35)
