"""
Central module for Vibe Core Base functionality.
"""
import asyncio
import importlib.util
import inspect
import json
import os
import sys
import types
import uuid
from datetime import datetime
from typing import Any, Callable, Dict

# --- NOVO RECURSO: O GUARDA-VOLUMES (Vibe Vault) ---


class VibeVault:
    """
    Sistema de armazenamento em memória para evitar serialização de objetos pesados.
    Permite passar DataFrames, Imagens ou Listas gigantes por referência.
    """
    _storage = {}

    @classmethod
    def store(cls, data: Any) -> str:
        """Armazena um objeto e retorna uma chave de acesso (ref-id)."""
        ref_id = f"ref-{uuid.uuid4().hex[:8]}"
        cls._storage[ref_id] = data
        return ref_id

    @classmethod
    def retrieve(cls, ref_id: str) -> Any:
        """Recupera o objeto original da memória."""
        return cls._storage.get(ref_id)

    @classmethod
    def cleanup(cls, ref_id: str):
        """Libera memória após o uso."""
        if ref_id in cls._storage:
            del cls._storage[ref_id]
# ---------------------------------------------------


class VibeKernel:
    """
    Motor de Execução Híbrido (Async/Sync) do Vibe Engineering.

    Gerencia o ciclo de vida, carregamento dinâmico (Dynamic Loading) e
    execução segura de cartuchos, suportando tanto funções nativas
    assíncronas quanto funções síncronas legadas (via Threads).
    """

    def __init__(self, cartridges_base_dir: str = "cartridges"):
        """
        Inicializa o Kernel.

        Atenção: Usa __file__ para garantir que a pasta 'cartridges' seja encontrada
        mesmo que o script seja executado de dentro de uma subpasta (Teste de Isolamento).
        """
        # Localiza a raiz do projeto baseada na posição deste arquivo (vibe_core.py)
        # Assumindo que vibe_core.py está na RAÍZ do projeto.
        project_root = os.path.dirname(os.path.abspath(__file__))

        self.cartridges_dir = os.path.join(project_root, cartridges_base_dir)
        self.cache: Dict[str, Callable] = {}
        self.debug_mode: bool = False

        # Garante que o namespace base exista para imports relativos funcionarem
        # Garante que o namespace base exista como pacote
        if "vibe_cartridges" not in sys.modules:
            m = types.ModuleType("vibe_cartridges")
            m.__path__ = []
            sys.modules["vibe_cartridges"] = m

    def _ensure_package_structure(self, module_name: str):
        """Cria pacotes intermediários dummy para permitir imports relativos."""
        parts = module_name.split('.')
        # parts[0] é 'vibe_cartridges'
        current = parts[0]
        for part in parts[1:-1]:  # Pula o último (que é o módulo)
            current = f"{current}.{part}"
            if current not in sys.modules:
                m = types.ModuleType(current)
                m.__path__ = []  # Marca como pacote
                sys.modules[current] = m

    def _generate_cid(self) -> str:
        """
        Gera um Correlation ID (CID) único para rastreabilidade.

        Returns:
            str: Identificador no formato 'vibe-<hex>'.
        """
        return f"vibe-{uuid.uuid4().hex[:8]}"

    def log(self, cartridge: str, cid: str, message: str, level: str = "INFO") -> None:
        """
        Registra telemetria no canal STDERR para evitar poluição do STDOUT.

        Args:
            cartridge (str): Nome do módulo gerador do log.
            cid (str): ID de correlação da transação.
            message (str): Conteúdo do log.
            level (str): Nível de severidade (INFO, ERROR, WARN).
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(
            f"[{timestamp}][{level}][{cid}][{cartridge}] {message}\n")
        sys.stderr.flush()

    def trace(self, cid: str, cartridge: str, event: str, data: Any) -> None:
        """
        Registra payloads completos em um arquivo de rastreamento local para debug profundo.
        """
        if not self.debug_mode:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "cid": cid,
            "cartridge": cartridge,
            "event": event,
            "data": data
        }

        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".vibe-debug.log"), "a", encoding="utf-8") as f:
                f.write(json.dumps(
                    log_entry, ensure_ascii=False, default=str) + "\n")
        except Exception as e:
            self.log("kernel", cid,
                     f"Falha ao gravar trace: {e}", level="ERROR")

    def _load_cartridge(self, cartridge_path: str) -> Callable:
        """
        Realiza o carregamento dinâmico do módulo Python e retorna sua função 'process'.

        Args:
            cartridge_path (str): Caminho relativo do cartucho (ex: 'ai/ai-nexus').

        Returns:
            Callable: A função process (pode ser sync ou async).

        Raises:
            FileNotFoundError: Se o main.py não existir.
            AttributeError: Se a função 'process' não for encontrada.
        """
        full_path = os.path.join(
            self.cartridges_dir, cartridge_path, "main.py")

        if not os.path.exists(full_path):
            raise FileNotFoundError(
                f"Arquivo main.py não encontrado em: {full_path}")

        # Adiciona o diretório do cartucho ao sys.path para permitir imports locais (ex: import dlc)
        cartridge_dir = os.path.dirname(full_path)
        if cartridge_dir not in sys.path:
            sys.path.append(cartridge_dir)

        # Cria um namespace isolado para evitar colisão de nomes
        # Cria um namespace isolado para evitar colisão de nomes
        sanitized_check = cartridge_path.replace('/', '.').replace('\\', '.')

        # O cartucho vira um pacote (ex: vibe_cartridges.core.git_scanner)
        package_name = f"vibe_cartridges.{sanitized_check}"

        # Garante que a estrutura de pacotes exista até o cartucho
        self._ensure_package_structure(package_name)

        # Configura o pacote do cartucho com o caminho físico (permite imports relativos no main)
        if package_name not in sys.modules:
            m = types.ModuleType(package_name)
            m.__path__ = [os.path.dirname(full_path)]
            sys.modules[package_name] = m
        else:
            # Se já existe (dummy), atualiza o path para real
            sys.modules[package_name].__path__ = [os.path.dirname(full_path)]

        # O main vira um submódulo (ex: vibe_cartridges.core.git_scanner.main)
        module_name = f"{package_name}.main"

        spec = importlib.util.spec_from_file_location(module_name, full_path)
        if spec is None or spec.loader is None:
            raise ImportError(
                f"Falha na especificação do módulo: {module_name}")

        module = importlib.util.module_from_spec(spec)
        # Registro necessário para imports relativos
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if not hasattr(module, "process"):
            raise AttributeError(
                f"O cartucho '{cartridge_path}' viola o contrato: 'process' ausente.")

        return module.process

    async def run(self, cartridge_path: str, payload: dict = None, timeout: int = 60) -> dict:
        """
        Executa um cartucho de forma assíncrona, segura e monitorada.

        Suporta:
        1. Funções `async def`: Executadas com await direto.
        2. Funções `def`: Executadas em Thread separada para não bloquear o Loop.

        Args:
            cartridge_path (str): Caminho do cartucho (ex: 'ai/openai').
            payload (dict, optional): Dados de entrada. Defaults to None.
            timeout (int): Tempo máximo em segundos antes de abortar.

        Returns:
            dict: Resultado do processamento ou dicionário de erro.
        """
        if payload is None:
            payload = {}

        # 1. Injeção de Contexto (CID)
        cid = payload.get("cid") or self._generate_cid()
        payload["cid"] = cid

        try:
            # 2. Dynamic Loading (ou recuperação do Cache)
            if cartridge_path not in self.cache:
                self.log(cartridge_path, cid, "Carregando módulo...")
                self.cache[cartridge_path] = self._load_cartridge(
                    cartridge_path)

            func = self.cache[cartridge_path]

            self.trace(cid, cartridge_path, "PAYLOAD_IN", payload)

            # 3. Execução Híbrida (Sync/Async)
            self.log(cartridge_path, cid, "Iniciando execução...")
            start_time = datetime.now()

            if inspect.iscoroutinefunction(func):
                # Execução nativa assíncrona com timeout
                result = await asyncio.wait_for(func(payload), timeout=timeout)
            else:
                # Execução síncrona enviada para Thread (evita bloquear o Event Loop)
                result = await asyncio.to_thread(func, payload)

            duration = (datetime.now() - start_time).total_seconds()
            self.log(cartridge_path, cid, f"Concluído em {duration:.4f}s")

            self.trace(cid, cartridge_path, "RESULT_OUT", result)

            # Garante a persistência do rastro
            if isinstance(result, dict):
                result["cid"] = cid

            return result

        except asyncio.TimeoutError:
            error_msg = f"TIMEOUT: Execução excedeu o limite de {timeout}s"
            self.log(cartridge_path, cid, error_msg, level="ERROR")
            return {
                "status": "error", "code": "TIMEOUT",
                "message": error_msg, "cid": cid
            }

        except Exception as e:
            self.log(cartridge_path, cid,
                     f"FALHA FATAL: {str(e)}", level="ERROR")
            return {
                "status": "error", "code": "INTERNAL_FAILURE",
                "module": cartridge_path, "message": str(e), "cid": cid
            }


# Singleton Global
kernel = VibeKernel()

# Exportações públicas do módulo:
# - kernel: Instância global do VibeKernel
# - VibeKernel: Classe do motor de execução (para tipagem)
# - VibeVault: Sistema de armazenamento por referência
