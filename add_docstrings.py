import os

def check_and_add_docstring(filepath, module_name):
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # If the file doesn't start with a docstring, add it
    if not content.startswith('"""') and not content.startswith("'''"):
        docstring = f'"""\nCentral module for {module_name} functionality.\n"""\n'
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(docstring + content)
            print(f"Added docstring to {filepath}")

def main():
    repo_dir = r"c:\code\GitHub\gitpy"
    
    # Root files
    check_and_add_docstring(os.path.join(repo_dir, "launcher.py"), "GitPy Launcher")
    check_and_add_docstring(os.path.join(repo_dir, "vibe_core.py"), "Vibe Core Base")
    
    # Cartridges
    cartridges_dir = os.path.join(repo_dir, "cartridges")
    if os.path.exists(cartridges_dir):
        for root, _, files in os.walk(cartridges_dir):
            if "main.py" in files:
                filepath = os.path.join(root, "main.py")
                folder_name = os.path.basename(root)
                check_and_add_docstring(filepath, folder_name)

if __name__ == "__main__":
    main()
