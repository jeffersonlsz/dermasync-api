import os
import glob
import re

files = glob.glob('app/services/relatos/*.py') + glob.glob('app/services/effects/*.py')

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 1. Add docstring if missing
    if not content.startswith('\"\"\"') and not content.startswith('#'):
        name = os.path.basename(f)
        docstring = f'\"\"\"\nModule {name}.\n\"\"\"\n\n'
        content = docstring + content
    
    # 2. Remove specific known unused imports
    content = re.sub(r'^from google\.cloud import firestore\n', '', content, flags=re.MULTILINE)
    
    # 3. Save with UTF-8 encoding
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Cleanup complete.")
