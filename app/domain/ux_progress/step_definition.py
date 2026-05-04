from typing import List
from .progress_aggregator import UXStepDefinition

from typing import List
from .progress_aggregator import UXStepDefinition

def default_step_definitions() -> List[UXStepDefinition]:
    """
    Define o fluxo cognitivo padro do envio de um relato.

    IMPORTANTE:
    - Isso no descreve execuo tcnica
    - Isso descreve a narrativa que o usurio percebe
    - A ordem importa (percepo temporal)
    """

    return [
        UXStepDefinition(
            step_id="persist_relato",
            label="Enviando relato para processamento...",
            weight=1,
            completion_effect_type="PERSIST_RELATO",
        ),
        UXStepDefinition(
            step_id="upload_images",
            label="Processando imagens...",
            weight=3,
            completion_effect_type="UPLOAD_IMAGES",
        ),
        UXStepDefinition(
            step_id="enrich_metadata",
            label="Analisando o relato enviado...",
            weight=3,
            completion_effect_type="ENRICH_METADATA",
        ),
    ]
