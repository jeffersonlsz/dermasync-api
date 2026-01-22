# app/domain/enrichment/prompts/extract_computable_metadata_v1.py

from app.domain.enrichment.vocabularies.tags_v1 import ALLOWED_TAGS
from app.domain.enrichment.vocabularies.signals_v1 import (
    ALLOWED_SIGNALS,
    ALLOWED_INTENSITIES,
    ALLOWED_FREQUENCIES,
)
from app.domain.enrichment.vocabularies.therapies_v1 import (
    ALLOWED_THERAPY_TYPES,
    ALLOWED_SUBSTANCES,
    ALLOWED_RESPONSES,
)
from app.domain.enrichment.vocabularies.body_regions_v1 import ALLOWED_BODY_REGIONS
from app.domain.enrichment.vocabularies.temporal_markers_v1 import (
    ALLOWED_TEMPORAL_MARKERS,
)

PROMPT_VERSION = "extract_computable_metadata_v1_hardened"


def build_prompt(relato_text: str) -> str:
    """
    Prompt fechado e endurecido para extração computável.

    Estratégias usadas:
    - JSON forcing explícito
    - Proibição direta de markdown / fences
    - Exemplo único (few-shot minimal)
    - Skeleton estrutural claro
    """

    return f"""
SYSTEM:
You are a medical-semantic extraction engine.
Your ONLY valid output is a single JSON object.

IMPORTANT:
- The output MUST start with '{{' and end with '}}'
- Do NOT use markdown
- Do NOT use ``` or ```json
- Do NOT include any text before or after the JSON
- Do NOT use boolean values (true/false)
- Do NOT invent field names
- All tags must be copied EXACTLY from the allowed lists bellow.
Do not guess spelling. Only from the lists prefixed with 'ALLOWED_' below.
- Follow the schema EXACTLY as provided.

CONSTRAINTS:
- Follow the schema exactly
- Do not add or remove fields
- All required fields must be present
- Use ONLY allowed vocabularies
- Use lowercase snake_case strings
- If uncertain, lower the confidence score

ALLOWED_TAGS:
{", ".join(sorted(ALLOWED_TAGS))}

ALLOWED_SIGNALS:
{", ".join(sorted(ALLOWED_SIGNALS))}
INTENSITY: {", ".join(sorted(ALLOWED_INTENSITIES))}
FREQUENCY: {", ".join(sorted(ALLOWED_FREQUENCIES))}

THERAPY_TYPE:
{", ".join(sorted(ALLOWED_THERAPY_TYPES))}
SUBSTANCE:
{", ".join(sorted(ALLOWED_SUBSTANCES))}
RESPONSE:
{", ".join(sorted(ALLOWED_RESPONSES))}

BODY_REGIONS:
{", ".join(sorted(ALLOWED_BODY_REGIONS))}

TEMPORAL_MARKERS:
{", ".join(sorted(ALLOWED_TEMPORAL_MARKERS))}

EXAMPLE OUTPUT:
{{
  "version": "v2",
  "computable": {{
    "tags": ["dermatite_atopica", "coceira"],
    "signals": [
      {{ "signal": "prurido", "intensity": "alta", "frequency": "diaria" }}
    ],
    "therapies": [
      {{ "type": "topico", "substance": "corticoide", "response": "melhora_parcial" }}
    ],
    "body_regions": ["dobra_cotovelo"],
    "temporal_markers": ["cronico"]
  }},
  "summaries": {{
    "public": "Relato descreve sintomas recorrentes de dermatite.",
    "clinical": "Prurido intenso em dobras com resposta parcial a corticoide."
  }},
  "confidence": {{
    "extraction": 0.85
  }}
}}

SCHEMA (FOLLOW EXACTLY):
{{
  "version": "v2",
  "computable": {{
    "tags": ["string"],
    "signals": [
      {{ "signal": "string", "intensity": "string", "frequency": "string" }}
    ],
    "therapies": [
      {{ "type": "string", "substance": "string", "response": "string" }}
    ],
    "body_regions": ["string"],
    "temporal_markers": ["string"]
  }},
  "summaries": {{
    "public": "string",
    "clinical": "string"
  }},
  "confidence": {{
    "extraction": 0.0
  }}
}}

RELATO:
\"\"\"
{relato_text}
\"\"\"
""".strip()
