import os
import json
from typing import Dict, Any

class I18nManager:
    """
    Sistema de internacionalização simples para o GitPy.
    Suporta Inglês (padrão) e Português.
    """
    def __init__(self, locales_dir: str = "locales"):
        self.locales_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), locales_dir)
        self.default_lang = "en"
        
        # Lê e sanitiza a variável de ambiente (remove comentários e espaços)
        raw_lang = os.getenv("LANGUAGE", self.default_lang)
        self.current_lang = raw_lang.split('#')[0].strip().lower()
        
        self.translations: Dict[str, Dict[str, str]] = {}
        
        # Carrega os idiomas básicos
        self._load_locale(self.default_lang)
        if self.current_lang != self.default_lang:
            self._load_locale(self.current_lang)

    def _load_locale(self, lang: str):
        """Carrega o arquivo JSON de um idioma específico."""
        file_path = os.path.join(self.locales_dir, f"{lang}.json")
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.translations[lang] = json.load(f)
            else:
                self.translations[lang] = {}
        except Exception:
            self.translations[lang] = {}

    def t(self, key: str, **kwargs) -> str:
        """
        Traduz uma chave para o idioma atual com fallback para o inglês.
        Suporta interpolação de variáveis via kwargs.
        """
        # Tenta no idioma atual
        text = self.translations.get(self.current_lang, {}).get(key)
        
        # Se não encontrar, tenta no padrão (en)
        if text is None:
            text = self.translations.get(self.default_lang, {}).get(key, key)
            
        # Formata com variáveis se necessário
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text

# Singleton global para fácil acesso
i18n = I18nManager()
t = i18n.t
