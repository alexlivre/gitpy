
from cartridges.security.sec_sanitizer.main import process
import os
import sys
import unittest

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSecSanitizer(unittest.TestCase):

    def test_safe_files(self):
        payload = {"file_paths": ["README.md",
                                  "src/main.py", "tests/test_foo.py"]}
        result = process(payload)
        self.assertEqual(len(result["blocked_files"]), 0)
        self.assertEqual(result["violations"], 0)

    def test_blocked_files(self):
        payload = {"file_paths": [
            ".env", ".ssh/id_rsa", "config/secrets.yaml"]}
        result = process(payload)
        self.assertEqual(len(result["blocked_files"]), 3)
        self.assertEqual(result["violations"], 3)
        self.assertIn(".env", result["blocked_files"])

    def test_mixed_files(self):
        payload = {"file_paths": ["main.py", ".env"]}
        result = process(payload)
        self.assertIn("main.py", result["safe_files"])
        self.assertIn(".env", result["blocked_files"])

    def test_case_sensitivity(self):
        """A blocklist deve ser case-insensitive."""
        payload = {"file_paths": [".ENV", "ID_RSA"]}
        result = process(payload)
        self.assertEqual(len(result["blocked_files"]), 2)

    def test_env_example_files_should_not_be_blocked(self):
        """Arquivos .env.example, .env.sample, etc. NÃO devem ser bloqueados"""
        payload = {"file_paths": [".env.example",
                                  ".env.sample", ".env.template"]}
        result = process(payload)
        self.assertEqual(len(result["blocked_files"]), 0)
        self.assertEqual(result["violations"], 0)

        # Todos devem estar na lista de arquivos seguros
        for file_path in payload["file_paths"]:
            self.assertIn(file_path, result["safe_files"])

    def test_env_files_should_be_blocked(self):
        """Arquivos .env reais DEVEM ser bloqueados"""
        payload = {"file_paths": [".env", ".env.local", ".env.production"]}
        result = process(payload)
        self.assertEqual(len(result["blocked_files"]), 3)
        self.assertEqual(result["violations"], 3)

        # Todos devem estar na lista de arquivos bloqueados
        for file_path in payload["file_paths"]:
            self.assertIn(file_path, result["blocked_files"])

    def test_mixed_env_files(self):
        """Testa mistura de arquivos .env que devem e não devem ser bloqueados"""
        payload = {"file_paths": [
            ".env", ".env.example", "config/.env", "docs/.env.sample"]}
        result = process(payload)

        # Deve bloquear apenas .env e config/.env
        self.assertEqual(len(result["blocked_files"]), 2)
        self.assertEqual(result["violations"], 2)

        # Verifica arquivos específicos
        self.assertIn(".env", result["blocked_files"])
        self.assertIn("config/.env", result["blocked_files"])
        self.assertIn(".env.example", result["safe_files"])
        self.assertIn("docs/.env.sample", result["safe_files"])


if __name__ == '__main__':
    unittest.main()
