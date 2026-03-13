
# -------------------------------------------------------------------------
# MURALHA DE CHUMBO - BLOCKLIST IMUTÁVEL
# -------------------------------------------------------------------------
# Este arquivo contém a lista hardcoded de padrões de arquivos que são
# ESTRITAMENTE PROIBIDOS de serem processados pelo GitPy.
# Nenhuma IA ou instrução de usuário pode sobrescrever esta lista em runtime.
# -------------------------------------------------------------------------

BLOCKED_PATTERNS = frozenset([
    # Diretórios de Infraestrutura e Credenciais
    ".ssh/",
    ".aws/",
    ".azure/",
    ".kube/",
    ".gnupg/",
    ".docker/",

    # Arquivos de Chaves Privadas (Private Keys)
    "id_rsa",
    "id_ed25519",
    "id_dsa",
    "id_ecdsa",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.keystore",
    "*.jks",

    # Variáveis de Ambiente e Configurações Sensíveis
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    "secrets.yaml",
    "secrets.json",
    "config.js",  # Potencial risco se contiver chaves hardcoded
    "config.ts",

    # Históricos de Shell (Contêm comandos passados com senhas)
    ".bash_history",
    ".zsh_history",
    ".python_history",
    ".mysql_history",
    ".psql_history",

    # Padrões Genéricos de Alto Risco
    "**/token.txt",
    "**/password.txt",
    "**/credentials.json"
])


def check_is_blocked(file_path: str) -> bool:
    """
    Verifica se um caminho de arquivo viola a blocklist imutável.
    Case-insensitive para maximizar segurança.
    """
    path_lower = file_path.lower().replace("\\", "/")  # Normalização

    for pattern in BLOCKED_PATTERNS:
        # Simplificação de verificação
        clean_pattern = pattern.replace("*", "")

        # 1. Match direto de nome de arquivo (ex: .env)
        if file_path.endswith(f"/{clean_pattern}") or file_path == clean_pattern:
            return True

        # 2. Match de diretório proibido (ex: .ssh/)
        if f"/{clean_pattern}" in path_lower:
            return True

        # 3. Match de arquivo no início do caminho com delimitadores
        # Verifica se começa com o padrão seguido por / ou fim de string
        if path_lower.startswith(clean_pattern):
            # Adiciona delimitadores para evitar falsos positivos
            # Se o padrão for .env, deve ser seguido por / ou fim de string
            remaining = path_lower[len(clean_pattern):]
            if not remaining or remaining[0] == "/":
                return True

    return False
