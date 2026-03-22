#!/usr/bin/env python3
"""Teste rápido de detecção de provedores"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_config import API_KEYS

print("=== Teste de Detecção de Provedores ===")
print()

# Verifica quais provedores têm chaves configuradas
available_providers = []
for provider, key in API_KEYS.items():
    if key:
        available_providers.append(provider)
        print(f"✓ {provider}: {key[:15]}...")
    else:
        print(f"✗ {provider}: não configurado")

print()
if available_providers:
    print(f"Provedores disponíveis: {', '.join(available_providers)}")
    print(f"Primeiro da lista: {available_providers[0]}")
else:
    print("Nenhum provedor configurado!")
