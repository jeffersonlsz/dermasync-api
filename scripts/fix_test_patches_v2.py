import os
import re

replacements = [
    # Fix the incorrect relocation of RelatoEffectExecutor in tests
    (re.compile(r'["\']app\.application\.effects\.executor\.RelatoEffectExecutor["\']'), "'app.services.relato_effect_executor.RelatoEffectExecutor'"),
    
    # Fix decide patches to point to the UseCases where they are actually used (as they use 'from ... import')
    (re.compile(r'["\']app\.application\.relatos\.create_relato_use_case\.decide["\']'), "'app.application.relatos.create_relato_use_case.decide'"),
    (re.compile(r'["\']app\.application\.relatos\.submit_relato_use_case\.decide["\']'), "'app.application.relatos.submit_relato_use_case.decide'"),
]

# For tests that patch 'decide' globally, we might need to patch it in both UseCases
# But usually they patch 'app.routes.relatos.decide' (already handled) or 'app.domain.relato.orchestrator.decide'.

# Let's add a rule to fix ANY 'decide' patch in routes tests to patch both or the UseCase

for root, _, files in os.walk('tests'):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except:
                    continue

            new_content = content
            for pattern, replacement in replacements:
                new_content = pattern.sub(replacement, new_content)

            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Updated {file_path}')
