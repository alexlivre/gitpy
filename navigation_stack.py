"""
Módulo de Pilha de Navegação (Navigation Stack) para GitPy.
Gerencia a trilha de navegação entre menus de forma persistente em memória.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class NavItem:
    """Representa um item na pilha de navegação."""
    id: str
    name_key: str
    display_name: str


class NavigationStack:
    """
    Pilha de navegação para rastrear a trilha do usuário entre menus.
    Persiste apenas em memória durante a execução.
    """

    def __init__(self):
        self._stack: List[NavItem] = []

    def push(self, id: str, name_key: str, display_name: str) -> None:
        """Adiciona um novo nível à pilha."""
        self._stack.append(NavItem(id=id, name_key=name_key, display_name=display_name))

    def pop(self) -> Optional[NavItem]:
        """Remove e retorna o último item da pilha. Retorna None se vazia."""
        if not self._stack:
            return None
        return self._stack.pop()

    def peek(self) -> Optional[NavItem]:
        """Retorna o último item sem remover. Retorna None se vazia."""
        if not self._stack:
            return None
        return self._stack[-1]

    def get_stack(self) -> List[NavItem]:
        """Retorna uma cópia da pilha completa."""
        return self._stack.copy()

    def get_breadcrumb(self, separator: str = " > ") -> str:
        """Gera string do breadcrumb com todos os itens."""
        if not self._stack:
            return ""
        return separator.join(item.display_name for item in self._stack)

    def get_depth(self) -> int:
        """Retorna a profundidade atual da pilha."""
        return len(self._stack)

    def clear(self) -> None:
        """Limpa toda a pilha."""
        self._stack.clear()

    def is_empty(self) -> bool:
        """Verifica se a pilha está vazia."""
        return len(self._stack) == 0


# Instância global singleton
_nav_stack_instance: Optional[NavigationStack] = None


def get_nav_stack() -> NavigationStack:
    """Retorna a instância global da pilha de navegação (singleton)."""
    global _nav_stack_instance
    if _nav_stack_instance is None:
        _nav_stack_instance = NavigationStack()
    return _nav_stack_instance


def reset_nav_stack() -> None:
    """Reinicia a pilha de navegação (útil para testes)."""
    global _nav_stack_instance
    _nav_stack_instance = NavigationStack()
