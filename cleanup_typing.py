import os
import glob
import re

files = glob.glob('app/services/relatos/*.py') + glob.glob('app/services/effects/*.py')

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Improve typing: add `-> None:` to `def enqueue_relato_processing(relato_id: str):`
    content = re.sub(r'def enqueue_relato_processing\(relato_id: str\):', r'def enqueue_relato_processing(relato_id: str) -> None:', content)
    
    # Improve typing: `def run_submission_effects(effects: list, executor: RelatoEffectExecutor):`
    content = re.sub(r'def run_submission_effects\(effects: list, executor: RelatoEffectExecutor\):', r'def run_submission_effects(effects: list, executor: RelatoEffectExecutor) -> None:', content)

    # Improve typing: `handle_...` in handlers.py
    content = re.sub(r'def handle_([a-z_]+)\((effect: [a-zA-Z_]+, deps: dict)\):', r'def handle_\1(\2) -> None:', content)
    
    # Improve typing: `dispatch_effect` return type
    # already has -> bool:

    # 3. Save with UTF-8 encoding
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Typing cleanup complete.")
