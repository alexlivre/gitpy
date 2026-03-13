import os
import re

def main():
    repo_dir = r"c:\code\GitHub\gitpy"
    for root, _, files in os.walk(repo_dir):
        if any(ignored in root for ignored in [".venv", ".git", "__pycache__"]):
            continue
        for file in files:
            if file.endswith(".py") and file != "fix_lints.py":
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Fix subprocess.run missing check
                    # We match subprocess.run( ... ) avoiding replacing if it already has check=
                    # Due to multiline we use a loop and balanced parentheses, or just targeted replacement
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'subprocess.run(' in line and 'check=' not in line:
                            # If it's a single line call, append check=False
                            if ')' in line and line.count('(') == line.count(')'):
                                lines[i] = line.replace(')', ', check=False)', 1)
                            # Multiline might need AST or manual fix, but let's do safe single line
                        
                        # Fix open() missing encoding
                        if 'open(' in line and 'encoding=' not in line and 'rb' not in line and 'wb' not in line:
                            if ')' in line[line.find('open('):] and line.count('(') == line.count(')'):
                                # Replace the last parenthesis of the open call safely using regex
                                lines[i] = re.sub(r'(open\([^)]+)\)', r'\1, encoding="utf-8")', line)
                                
                    new_content = '\n'.join(lines)
                    
                    if new_content != original_content:
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"Fixed {path}")
                except Exception as e:
                    print(f"Failed {path}: {e}")

if __name__ == "__main__":
    main()
