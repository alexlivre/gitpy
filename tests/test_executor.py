
import unittest
import importlib.util
import sys
import os

# Dynamic import for module with dash in name
# Path: ../cartridges/core/git-executor/main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.join(current_dir, "..", "cartridges", "core", "git-executor", "main.py")

spec = importlib.util.spec_from_file_location("git_executor", module_path)
git_executor = importlib.util.module_from_spec(spec)
sys.modules["git_executor"] = git_executor
spec.loader.exec_module(git_executor)

validate_command = git_executor.validate_command
process = git_executor.process

class TestGitExecutor(unittest.TestCase):

    def test_allowed_commands(self):
        """Verifica se comandos seguros são permitidos."""
        self.assertTrue(validate_command("status"))
        self.assertTrue(validate_command("add ."))
        self.assertTrue(validate_command("commit -m 'teste'"))
        self.assertTrue(validate_command("push origin main"))

    def test_blocked_commands(self):
        """Verifica se comandos perigosos são bloqueados."""
        self.assertFalse(validate_command("rm -rf ."))
        self.assertFalse(validate_command("reset --hard HEAD~1"))
        self.assertFalse(validate_command("clean -fdx"))
        self.assertFalse(validate_command("push --force"))

    def test_force_with_lease_exception(self):
        """Verifica a exceção de segurança para --force-with-lease."""
        self.assertTrue(validate_command("push --force-with-lease"))

    def test_process_execution(self):
        """Testa o fluxo completo (simulado)."""
        payload = {
            "repo_path": ".",
            "command": "status",
            "dry_run": True
        }
        result = process(payload)
        self.assertTrue(result["success"])
        self.assertIn("[DRY-RUN]", result["stdout"])

if __name__ == '__main__':
    unittest.main()
