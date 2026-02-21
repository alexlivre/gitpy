
import unittest
import os
import sys
import shutil
import asyncio
from unittest.mock import MagicMock, patch

# Ensure app directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from launcher import app
from vibe_core import kernel
import typer
from typer.testing import CliRunner

class TestLocalIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = os.path.abspath("temp_local_test")
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except:
                pass
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        
        # Mock git repo
        os.system(f"git init {self.test_dir}")
        os.system(f"git -C {self.test_dir} config user.email 'test@local.dev'")
        os.system(f"git -C {self.test_dir} config user.name 'Test Bot'")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except:
                pass

    @patch("vibe_core.kernel.run")
    def test_auto_dry_run(self, mock_kernel):
        """Test gitpy auto --dry-run flow"""
        
        # Setup mock responses for the kernel
        async def side_effect(cartridge, payload):
            if cartridge == "security/sec-keyring":
                return {"value": "sk-mock-key"}
            if cartridge == "tool/tool-ignore":
                return {"suggestions": []}
            if cartridge == "core/git-scanner":
                return {
                    "is_repo": True, 
                    "has_changes": True, 
                    "files_changed": ["test.txt"],
                    "diff_data": {"mode": "text", "content": "diff content"}
                }
            if cartridge == "security/sec-sanitizer":
                return {"violations": 0}
            if cartridge == "cli/cli-renderer":
                return {"success": True}
            if cartridge == "ai/ai-brain":
                return {"success": True, "commit_message": "feat: mock commit", "removed_files": [], "excluded_files": []}
            return {"success": True}

        mock_kernel.side_effect = side_effect
        
        runner = CliRunner()
        
        # Execute
        # Fixed: --path must come BEFORE auto
        result = runner.invoke(app, ["--path", self.test_dir, "auto", "--dry-run", "--yes"])
        
        if result.exit_code != 0:
            print(f"\n[DEBUG] Exit Code: {result.exit_code}")
            print(f"[DEBUG] Stdout: {result.stdout}")
            print(f"[DEBUG] Exception: {result.exception}")
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("[DRY-RUN] Commit seria executado agora.", result.stdout if result.stdout else "No output")
        
    @patch("vibe_core.kernel.run")
    def test_ai_provider_detection_priority(self, mock_kernel):
        """Test AI provider detection priority (Groq > OpenAI > ...)"""
        
        async def side_effect(cartridge, payload):
            if cartridge == "security/sec-keyring":
                service = payload.get("service")
                if service == "groq_api_key":
                    return {"value": None} # Groq missing
                if service == "openai_api_key":
                    return {"value": "sk-openai"} # OpenAI present
                return {"value": None}
            
            if cartridge == "tool/tool-ignore": return {"suggestions": []}
            if cartridge == "core/git-scanner": return {"is_repo": True, "has_changes": False} # Stop early
            return {"success": True}

        mock_kernel.side_effect = side_effect
        
        runner = CliRunner()
        # Fixed: --path must come BEFORE auto
        result = runner.invoke(app, ["--path", self.test_dir, "auto", "--yes"])
        
        if result.exit_code != 0:
            print(f"\n[DEBUG] Exit Code: {result.exit_code}")
            print(f"[DEBUG] Stdout: {result.stdout}")
            print(f"[DEBUG] Exception: {result.exception}")

        # Should detect OpenAI and print it
        # Note: Typer/Rich capturing might be tricky with colors. 
        # Check for simple string presence or part of it.
        self.assertIn("OPENAI", result.stdout)

if __name__ == "__main__":
    unittest.main()
