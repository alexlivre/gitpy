import unittest
import os
import shutil
import tempfile
import importlib.util
import sys

# Dynamic import for dashed module name
spec = importlib.util.spec_from_file_location("tool_stealth", os.path.abspath("cartridges/tool/tool-stealth/main.py"))
tool_stealth = importlib.util.module_from_spec(spec)
sys.modules["tool_stealth"] = tool_stealth
spec.loader.exec_module(tool_stealth)

from tool_stealth import stash, restore, ensure_gitignore, TEMP_DIR_NAME, PRIVATE_CONFIG_FILE

class TestStealthMode(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the repo
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
    def tearDown(self):
        # Cleanup
        shutil.rmtree(self.test_dir)

    def create_file(self, path, content="content"):
        full_path = os.path.join(self.repo_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path

    def test_ensure_gitignore(self):
        # Case 1: No .gitignore
        ensure_gitignore(self.repo_path)
        with open(os.path.join(self.repo_path, ".gitignore"), "r") as f:
            content = f.read()
        self.assertIn(f"{TEMP_DIR_NAME}/", content)

        # Case 2: Append to existing
        with open(os.path.join(self.repo_path, ".gitignore"), "w") as f:
            f.write("*.log\n")
        
        ensure_gitignore(self.repo_path)
        with open(os.path.join(self.repo_path, ".gitignore"), "r") as f:
            content = f.read()
        self.assertIn("*.log", content)
        self.assertIn(f"{TEMP_DIR_NAME}/", content)

    def test_stash_restore_flow(self):
        # Setup context
        self.create_file(PRIVATE_CONFIG_FILE, ".secret/\nsecret.txt")
        
        # Files to hide
        self.create_file("secret.txt", "shh")
        self.create_file(".secret/key.pem", "KEY")
        self.create_file(".secret/config.json", "{}")
        
        # Files to keep
        self.create_file("public.txt", "hello")
        
        # 1. Stash
        res = stash({"repo_path": self.repo_path})
        self.assertTrue(res["success"])
        # Expect 2 moved items: 'secret.txt' and '.secret' (directory)
        # Note: .secret/key.pem and .secret/config.json are inside .secret, so they move with it.
        self.assertEqual(len(res["files_moved"]), 2) 

        # Verify physical move
        self.assertFalse(os.path.exists(os.path.join(self.repo_path, "secret.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.repo_path, ".secret/key.pem")))
        self.assertTrue(os.path.exists(os.path.join(self.repo_path, "public.txt")))
        
        # Verify temp exists
        temp_path = os.path.join(self.repo_path, TEMP_DIR_NAME)
        self.assertTrue(os.path.exists(os.path.join(temp_path, "secret.txt")))
        self.assertTrue(os.path.exists(os.path.join(temp_path, ".secret/key.pem")))

        # 2. Restore
        res_restore = restore({"repo_path": self.repo_path})
        self.assertTrue(res_restore["success"])
        
        # Verify return
        self.assertTrue(os.path.exists(os.path.join(self.repo_path, "secret.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.repo_path, ".secret/key.pem")))
        
        # Verify temp gone
        self.assertFalse(os.path.exists(temp_path))

    def test_restore_conflict(self):
        # 1. Setup stash
        self.create_file("conflict.txt", "original")
        self.create_file(PRIVATE_CONFIG_FILE, "conflict.txt")
        stash({"repo_path": self.repo_path})
        
        # 2. Simulate User creating a NEW file with same name
        self.create_file("conflict.txt", "new_content")
        
        # 3. Restore
        res = restore({"repo_path": self.repo_path})
        self.assertTrue(res["success"])
        
        # 4. Verify
        # "new_content" should stay in conflict.txt
        with open(os.path.join(self.repo_path, "conflict.txt"), "r") as f:
            self.assertEqual(f.read(), "new_content")
            
        # "original" should be in conflict.txt.restored
        restored_path = os.path.join(self.repo_path, "conflict.txt.restored")
        self.assertTrue(os.path.exists(restored_path))
        with open(restored_path, "r") as f:
            self.assertEqual(f.read(), "original")

    def test_startup_recovery(self):
        # Simulate a crash: .gitpy-temp exists with content, but no running process
        temp_dir = os.path.join(self.repo_path, TEMP_DIR_NAME)
        os.makedirs(temp_dir)
        
        # Create a file inside temp (representing a stashed file)
        with open(os.path.join(temp_dir, "recover_me.txt"), "w") as f:
            f.write("I survived")
            
        # Run restore (simulating launcher startup)
        res = restore({"repo_path": self.repo_path})
        self.assertTrue(res["success"])
        
        # Verify file is back in repo
        self.assertTrue(os.path.exists(os.path.join(self.repo_path, "recover_me.txt")))
        with open(os.path.join(self.repo_path, "recover_me.txt"), "r") as f:
            self.assertEqual(f.read(), "I survived")
            
        # Verify temp is gone
        self.assertFalse(os.path.exists(temp_dir))

if __name__ == '__main__':
    unittest.main()
