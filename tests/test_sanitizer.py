
import unittest
from cartridges.security.sec_sanitizer.main import process

class TestSecSanitizer(unittest.TestCase):

    def test_safe_files(self):
        payload = {"file_paths": ["README.md", "src/main.py", "tests/test_foo.py"]}
        result = process(payload)
        self.assertEqual(len(result["blocked_files"]), 0)
        self.assertEqual(result["violations"], 0)

    def test_blocked_files(self):
        payload = {"file_paths": [".env", ".ssh/id_rsa", "config/secrets.yaml"]}
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

if __name__ == '__main__':
    unittest.main()
