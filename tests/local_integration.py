import launcher
from launcher import app
from typer.testing import CliRunner
import os
import shutil
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

# Ensure app directory is in path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


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
        result = runner.invoke(
            app, ["--path", self.test_dir, "auto", "--dry-run", "--yes"])

        if result.exit_code != 0:
            print(f"\n[DEBUG] Exit Code: {result.exit_code}")
            print(f"[DEBUG] Stdout: {result.stdout}")
            print(f"[DEBUG] Exception: {result.exception}")

        self.assertEqual(result.exit_code, 0)
        stdout = result.stdout if result.stdout else "No output"
        self.assertTrue(
            "[DRY-RUN] Commit seria executado agora." in stdout
            or "[DRY-RUN] Commit would be executed now." in stdout
        )

    @patch("vibe_core.kernel.run")
    def test_ai_provider_detection_priority(self, mock_kernel):
        """Test AI provider detection priority (Groq > OpenAI > ...)"""

        async def side_effect(cartridge, payload):
            if cartridge == "security/sec-keyring":
                service = payload.get("service")
                if service == "groq_api_key":
                    return {"value": None}  # Groq missing
                if service == "openai_api_key":
                    return {"value": "sk-openai"}  # OpenAI present
                return {"value": None}

            if cartridge == "tool/tool-ignore":
                return {"suggestions": []}
            if cartridge == "core/git-scanner":
                return {"is_repo": True, "has_changes": False}  # Stop early
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

    @patch("launcher._run_auto_with_guards")
    @patch("launcher_menu._inquirer_checkbox")
    @patch("launcher_menu._inquirer_text")
    @patch("launcher_menu._inquirer_select")
    @patch("launcher._is_interactive_terminal", return_value=True)
    def test_menu_auto_dispatches_options(
        self,
        _mock_tty,
        mock_select,
        mock_text,
        mock_checkbox,
        mock_run_auto,
    ):
        """Test gitpy menu -> Auto wizard passes all options."""
        mock_select.side_effect = ["auto", "current", "groq"]  # main action, path mode, model (no exit because auto flow should complete)
        mock_text.side_effect = [
            "menu hint",             # message
            "feature/menu-flow",     # branch
        ]
        mock_checkbox.return_value = ["dry_run", "nobuild", "debug"]  # Selected boolean options

        runner = CliRunner()
        result = runner.invoke(app, ["--path", self.test_dir, "menu"])

        if result.exit_code != 0:
            print(f"\n[DEBUG] Exit Code: {result.exit_code}")
            print(f"[DEBUG] Stdout: {result.stdout}")
            print(f"[DEBUG] Exception: {result.exception}")

        self.assertEqual(result.exit_code, 0)
        mock_run_auto.assert_called_once()

        call_args = mock_run_auto.call_args
        called_ctx = call_args.args[0]
        called_options = call_args.args[1]
        called_confirm = call_args.kwargs.get("confirm_fn")

        self.assertEqual(called_ctx.obj.get("path"), self.test_dir)
        self.assertIsInstance(called_options, launcher.AutoOptions)
        self.assertTrue(called_options.dry_run)
        self.assertFalse(called_options.no_push)
        self.assertTrue(called_options.nobuild)
        self.assertTrue(called_options.debug)
        self.assertFalse(called_options.yes)
        self.assertEqual(called_options.model, "groq")
        self.assertEqual(called_options.message, "menu hint")
        self.assertEqual(called_options.branch, "feature/menu-flow")
        self.assertTrue(callable(called_confirm))

    @patch("launcher._run_check_ai_diagnostics")
    @patch("launcher_menu._inquirer_select")
    @patch("launcher._is_interactive_terminal", return_value=True)
    def test_menu_check_ai_runs_diagnostics(
        self,
        _mock_tty,
        mock_select,
        mock_diagnostics,
    ):
        """Test gitpy menu -> Check AI triggers diagnostics path."""
        mock_select.side_effect = ["check_ai", "exit"]
        runner = CliRunner()
        result = runner.invoke(app, ["menu"])
        self.assertEqual(result.exit_code, 0)
        mock_diagnostics.assert_called_once()

    @patch("subprocess.run")
    @patch("launcher_menu._inquirer_confirm", return_value=False)
    @patch("launcher_menu._inquirer_select")
    @patch("launcher._is_interactive_terminal", return_value=True)
    def test_menu_reset_runs_git_reset_script(
        self,
        _mock_tty,
        mock_select,
        _mock_confirm,
        mock_subprocess,
    ):
        """Test gitpy menu -> Reset executes git_reset_to_github.py."""
        mock_select.side_effect = ["reset", "summary", "exit"]  # main action, reset mode, return to menu -> exit
        mock_subprocess.return_value = SimpleNamespace(returncode=0)

        runner = CliRunner()
        result = runner.invoke(app, ["--path", self.test_dir, "menu"])

        self.assertEqual(result.exit_code, 0)
        calls = mock_subprocess.call_args_list
        reset_calls = [c for c in calls if "git_reset_to_github.py" in " ".join(c.args[0])]
        self.assertEqual(len(reset_calls), 1)
        command = reset_calls[0].args[0]
        cwd = reset_calls[0].kwargs.get("cwd")

        self.assertIn("git_reset_to_github.py", command[1])
        self.assertIn("--summary", command)
        self.assertEqual(cwd, self.test_dir)

    @patch("launcher._run_branch_center")
    @patch("launcher_menu._inquirer_select")
    @patch("launcher._is_interactive_terminal", return_value=True)
    def test_menu_branch_center_dispatches(
        self,
        _mock_tty,
        mock_select,
        mock_branch_center,
    ):
        """Test gitpy menu -> Branch Center dispatch."""
        mock_select.side_effect = ["branch", "exit"]

        runner = CliRunner()
        result = runner.invoke(app, ["menu"])

        self.assertEqual(result.exit_code, 0)
        mock_branch_center.assert_called_once()

    @patch("launcher._run_menu_mode")
    @patch("launcher._is_interactive_terminal", return_value=False)
    def test_no_args_non_interactive_does_not_open_menu(
        self,
        _mock_tty,
        mock_run_menu,
    ):
        """No subcommand in non-interactive mode should not attempt menu prompts."""
        runner = CliRunner()
        result = runner.invoke(app, [])
        self.assertEqual(result.exit_code, 0)
        mock_run_menu.assert_not_called()
        self.assertIn("GitPy", result.stdout)


if __name__ == "__main__":
    unittest.main()
