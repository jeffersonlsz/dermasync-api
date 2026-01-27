# tests/ux/ui_interpreter.py

from typing import List, Dict, Any


def interpret_for_ui(ux_effects: List[Dict[str, Any]]) -> List[str]:
    """
    Simulador cognitivo de UI.

    Recebe UX Effects já serializados (shape público).
    Retorna a narrativa percebida por um humano.
    """

    story: List[str] = []

    for effect in ux_effects:
        effect_type = effect.get("type")

        if effect_type == "ProcessingStartedUXEffect":
            story.append("Recebemos seu relato")

        elif effect_type == "RetryUXEffect":
            failed_effects_count = effect.get("failed_effects_count", 0)

            if failed_effects_count > 0:
                story.append("Tentando novamente...")
            else:
                story.append("Não foi possível concluir agora")

        # efeitos desconhecidos são ignorados
        else:
            continue

    return story
