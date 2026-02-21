
import unittest
from cartridges.security.sec_redactor.main import process

class TestSecRedactor(unittest.TestCase):

    def test_redact_email(self):
        text = "Contact me at user@example.com for support."
        result = process({"content": text})
        self.assertIn("[REDACTED:Email]", result["sanitized_content"])
        self.assertNotIn("user@example.com", result["sanitized_content"])

    def test_redact_aws_key(self):
        text = "My key is AKIAIOSFODNN7EXAMPLE."
        result = process({"content": text})
        self.assertIn("[REDACTED:AWS_Key]", result["sanitized_content"])
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", result["sanitized_content"])

    def test_redact_google_key(self):
        text = "API Key: AIzaSyD-1234567890abcdef1234567890abcde"
        result = process({"content": text})
        self.assertIn("[REDACTED:Google_API]", result["sanitized_content"])

    def test_no_secrets(self):
        text = "Just a simple commit message."
        result = process({"content": text})
        self.assertEqual(result["sanitized_content"], text)
        self.assertEqual(result["redacted_count"], 0)

if __name__ == '__main__':
    unittest.main()
